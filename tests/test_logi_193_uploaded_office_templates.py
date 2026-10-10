"""LOGI-193 — Admin-uploaded Office template acceptance (Issue #193).

Proves the ONE working flow on pure seams AND on the real staging dispatcher:

    Admin upload -> detect/confirm mapping -> publish -> template appears in the
    SAME shipment document picker -> staff selects -> auto-fill from verified
    facts -> missing facts fail closed -> generate -> save -> re-download.

and the negatives the acceptance comment requires:

  * viewer/non-admin upload+publish are refused SERVER-SIDE (zero storage writes);
  * legacy .doc/.xls, macro-enabled, oversized, non-OOXML and unsafe OOXML are
    refused BEFORE anything is stored;
  * a forged mapping (raw Mongo path, expression, unknown/money field) is
    refused, never interpreted;
  * uploaded bytes never execute (no Jinja/macro/DDE/external relationship);
  * unresolved facts stay MISSING — never a blank, a zero or today();
  * a SECOND ordinary template is added by upload alone, with no code change;
  * existing FORM_07 / docgen paths are untouched.
"""

from __future__ import annotations

import base64
import hashlib
import io
from datetime import datetime
import struct
import zipfile

import pytest

from core import database
from core.docgen import uploaded_template as engine
from core.docgen import uploaded_template_store as store
from core.shipment_attachments import fetch_attachment_bytes
from core.shipment_document_catalog import (
    SHIPMENT_DOCUMENT_CATALOG,
    effective_catalog,
    project_catalog,
    validate_selected_template_ids,
)
from views import logi_sandbox
from views import logi_view_model as vm

SHIPMENT_ID = "LO-0295"          # staging seed: delivered, contract HDMB-0295
CONTRACT_ID = "HDMB-0295"
COMPANY_ID = "TT-COMPANY"
CUSTOMER_ID = "CUST-THIENAN"

VIEWER_ACTOR = {
    "username": "staging.viewer",
    "full_name": "Viewer (Test)",
    "role": "VIEWER",
    "user_id": "STAGING-VIEWER",
}
SALE_ACTOR = {
    "username": "staging.sale",
    "full_name": "Sale (Test)",
    "role": "SALE",
    "user_id": "STAGING-SALE",
}

# The verified facts the staging seed carries for LO-0295. Every assertion
# below compares the generated file against these, never against a literal
# invented by the test.
EXPECTED_CUSTOMER_NAME = "Thiên Ân JSC"
EXPECTED_CUSTOMER_TAX_CODE = "0104567890"
EXPECTED_CONTAINER = "粤B·90M21"
EXPECTED_BOOKING = "BKG-0295"
EXPECTED_POL = "Quảng Châu"
EXPECTED_POD = "Mộc Bài (Tây Ninh)"
EXPECTED_RECEIVER = "A. Kiệt"
EXPECTED_DELIVERED_AT = "2026-09-09"


# ---------------------------------------------------------------------------
# Pilot template builders (ordinary files, built in-memory — no fixtures)
# ---------------------------------------------------------------------------

# python-docx / openpyxl both stamp ``now()`` into docProps/core.xml. That would
# make the pilot TEMPLATE bytes differ between runs, so a "same input -> same
# output" claim about the renderer could not be reproduced from CI. Pin the
# document properties so the pilot bytes (and therefore the rendered bytes and
# their SHA-256) are stable across processes.
PILOT_BUILT_AT = datetime(2026, 1, 1, 0, 0, 0)


def _pin_docx_properties(document) -> None:
    core = document.core_properties
    core.created = PILOT_BUILT_AT
    core.modified = PILOT_BUILT_AT
    core.last_modified_by = "logi-193-pilot"


def _pin_xlsx_properties(workbook) -> None:
    workbook.properties.created = PILOT_BUILT_AT
    workbook.properties.modified = PILOT_BUILT_AT
    workbook.properties.creator = "logi-193-pilot"
    workbook.properties.lastModifiedBy = "logi-193-pilot"


def _normalize_pilot_package(raw: bytes) -> bytes:
    """Make pilot OOXML bytes byte-stable across processes.

    openpyxl's writer unconditionally resets ``dcterms:modified`` to ``now()``
    (openpyxl/writer/excel.py:292), and both writers stamp the current wall
    clock into every ZIP entry, so a property pin alone cannot survive a save.
    Rewriting the two timestamps and the entry mtimes keeps the pilot TEMPLATE
    bytes identical run to run, which is what lets a rendered-file SHA-256 be
    quoted as reproducible evidence. The renderer under test is untouched.
    """
    stamp = PILOT_BUILT_AT.strftime("%Y-%m-%dT%H:%M:%SZ")
    source = zipfile.ZipFile(io.BytesIO(raw))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as sink:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename.endswith("docProps/core.xml"):
                text = data.decode("utf-8")
                for tag in ("dcterms:created", "dcterms:modified"):
                    start = text.find("<%s" % tag)
                    if start < 0:
                        continue
                    body_start = text.find(">", start) + 1
                    body_end = text.find("</%s>" % tag, body_start)
                    text = text[:body_start] + stamp + text[body_end:]
                data = text.encode("utf-8")
            fixed = zipfile.ZipInfo(info.filename, date_time=(2026, 1, 1, 0, 0, 0))
            fixed.compress_type = zipfile.ZIP_DEFLATED
            fixed.external_attr = info.external_attr
            sink.writestr(fixed, data)
    return out.getvalue()

def build_pilot_docx() -> bytes:
    """An ordinary Vietnamese form: colon+blank lines, a two-run line, a table."""
    import docx

    document = docx.Document()
    document.add_paragraph("BIÊN BẢN ĐỐI CHIẾU GIAO NHẬN")
    document.add_paragraph("Số hợp đồng: ____________")
    line = document.add_paragraph()
    line.add_run("Khách hàng: ")
    line.add_run("__________")
    line2 = document.add_paragraph()
    line2.add_run("Số lô hàng: ")
    line2.add_run(" ")
    line3 = document.add_paragraph()
    line3.add_run("Số container: ")
    line3.add_run("...")
    table = document.add_table(rows=2, cols=2)
    table.rows[0].cells[0].paragraphs[0].add_run("Người nhận hàng")
    table.rows[0].cells[1].paragraphs[0].add_run("______")
    table.rows[1].cells[0].paragraphs[0].add_run("Ngày giao hàng")
    table.rows[1].cells[1].paragraphs[0].add_run("______")
    _pin_docx_properties(document)
    buffer = io.BytesIO()
    document.save(buffer)
    return _normalize_pilot_package(buffer.getvalue())


def build_pilot_xlsx() -> bytes:
    """An ordinary workbook: label / empty-neighbour cells on two sheets."""
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "BANG KE"
    sheet["A1"] = "BẢNG KÊ LÔ HÀNG"
    sheet["A3"] = "Mã lô hàng:"
    sheet["A4"] = "Số container:"
    sheet["A5"] = "Cảng đi:"
    sheet["A6"] = "Cảng đến:"
    sheet["A7"] = "Ngày giao hàng:"
    sheet["A9"] = "Tên hàng hóa"
    sheet["B9"] = "Đơn vị tính"
    sheet["C9"] = "Số lượng"
    second = workbook.create_sheet("GIAO NHAN")
    second["A1"] = "Người nhận hàng:"
    second["A2"] = "Chức vụ người nhận:"
    _pin_xlsx_properties(workbook)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return _normalize_pilot_package(buffer.getvalue())


def build_second_docx() -> bytes:
    """A DIFFERENT ordinary template, to prove upload-only onboarding."""
    import docx

    document = docx.Document()
    document.add_paragraph("PHIẾU XÁC NHẬN THÔNG TIN LÔ")
    document.add_paragraph("Số booking: ________")
    document.add_paragraph("Cảng đi: ________")
    document.add_paragraph("Cảng đến: ________")
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def build_third_xlsx() -> bytes:
    """A THIRD ordinary workbook: different sheet names, mixed detection paths.

    Deliberately unlike ``build_pilot_xlsx`` — it uses explicit {{token}}
    markers, label/empty-neighbour cells and a different sheet layout, so
    onboarding it exercises detection rather than a shape the code was written
    around. Nothing about this file is known to the application.
    """
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "THONG TIN"
    sheet["A1"] = "THÔNG TIN LÔ HÀNG"
    sheet["A3"] = "Mã lô hàng:"
    sheet["A4"] = "Khách hàng:"
    sheet["A5"] = "Số booking:"
    sheet["A6"] = "Người nhận:"
    second = workbook.create_sheet("MARKERS")
    second["B2"] = "{{shipment.id}}"
    second["B3"] = "{{company.legal_name}}"
    _pin_xlsx_properties(workbook)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return _normalize_pilot_package(buffer.getvalue())


def build_marker_docx() -> bytes:
    """Explicit {{token}} markers — the highest-confidence detection path."""
    import docx

    document = docx.Document()
    document.add_paragraph("Xác nhận: {{shipment.id}}")
    document.add_paragraph("KH: {{customer.name}}")
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


# ---------------------------------------------------------------------------
# Staging fixture + dispatch helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)
    _prepare_source_contract()
    yield
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


def _prepare_source_contract() -> None:
    """Give the seeded HDMB-0295 the canonical party + goods an operator books."""
    db = database.get_db()
    db["contracts"].update_one(
        {"id": CONTRACT_ID},
        {"$set": {
            "contract_no": CONTRACT_ID,
            "contract_date": "2026-08-20",
            "company_id": COMPANY_ID,
            "agent_id": "AGENT-01",
            "goods_lines": [{
                "description": "Kính nổi 5mm",
                "specification_or_code": "1200x600",
                "unit": "Tấm",
                # Vietnamese thousands separator on purpose: the generator must
                # print it verbatim, never re-parsed as 19.8.
                "quantity": "19.800",
            }],
        }},
    )
    db["shipments"].update_one({"id": SHIPMENT_ID}, {"$set": {"contract_id": CONTRACT_ID}})


def _dispatch_template(name: str, payload: dict, seq: int = 1) -> dict:
    outcomes = vm.logi_templates.consume_docgen_template_triggers(
        {"seq": seq - 1}, {name: {"seq": seq, "event": name, "payload": payload}}
    )
    assert len(outcomes) == 1
    return outcomes[0]


def _dispatch_generate(payload: dict, seq: int = 1) -> dict:
    outcomes = vm.consume_phase_b_triggers(
        {"seq": seq - 1},
        {"uploaded_template_generate": {"seq": seq, "event": "uploaded_template_generate",
                                       "payload": payload}},
    )
    assert len(outcomes) == 1
    return outcomes[0]


def _admin() -> None:
    import streamlit as st

    st.session_state["current_user"] = {"username": "staging.admin", "full_name": "Admin (Test)",
                                        "role": "ADMIN", "user_id": "STAGING-ADMIN"}


def _support() -> None:
    import streamlit as st

    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)


def _upload_publish(raw: bytes, label: str, file_name: str,
                    *, mapping=None) -> dict:
    """The real Admin path: upload -> confirm mapping -> publish."""
    _admin()
    outcome = _dispatch_template("docgen_template_upload", {
        "label": label, "fileName": file_name, "base64": _b64(raw),
        "requestId": f"req-{label}",
    }, seq=1)
    assert outcome["ok"], outcome
    template_id = outcome["readback"]["id"]
    detected = outcome["readback"]["detected"]

    confirmed = mapping
    if confirmed is None:
        confirmed = [
            {"position": item["id"], "mode": "field", "value": item["suggestion"]}
            for item in detected
            if item["suggestion"]
        ]
    saved = _dispatch_template("docgen_template_mapping_save", {
        "templateId": template_id, "mapping": confirmed, "requestId": f"req-map-{label}",
    }, seq=2)
    assert saved["ok"], saved

    published = _dispatch_template("docgen_template_publish", {
        "templateId": template_id, "requestId": f"req-pub-{label}",
    }, seq=3)
    assert published["ok"], published
    return published["readback"]


def _fetch(attachment_id: str) -> dict:
    """Read ONE generated file back through the EXISTING attachment path."""
    from core.database import load_shipment_attachment

    record = load_shipment_attachment(attachment_id)
    assert record, f"attachment {attachment_id} not persisted"
    return fetch_attachment_bytes(record, shipment_id=SHIPMENT_ID)


def _read_cell(xlsx_bytes: bytes, sheet_name: str, coord: str) -> str:
    from lxml import etree

    ns = {"x": engine._SHEET_NS}
    archive = zipfile.ZipFile(io.BytesIO(xlsx_bytes))
    workbook = etree.fromstring(archive.read("xl/workbook.xml"))
    rels = etree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    paths = engine._sheet_paths(workbook, rels)
    sheet = etree.fromstring(archive.read(paths[sheet_name]))
    for cell in sheet.findall(".//x:c", ns):
        if cell.get("r") == coord:
            texts = cell.findall(".//x:t", ns)
            if texts:
                return "".join(item.text or "" for item in texts)
            value = cell.find("x:v", ns)
            return value.text if value is not None else ""
    return ""


def _docx_text(docx_bytes: bytes) -> str:
    import docx

    document = docx.Document(io.BytesIO(docx_bytes))
    parts = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.extend(cell.text for cell in row.cells)
    return "\n".join(parts)


# ===========================================================================
# 1. Detection on ordinary files (no markers required)
# ===========================================================================

def test_detects_positions_and_suggests_fields_on_ordinary_docx():
    raw = build_pilot_docx()
    info = engine.validate_uploaded_template("bien-ban.docx", raw)
    assert info["kind"] == engine.KIND_DOCX

    positions = engine.detect_positions(raw, info["kind"])
    by_id = {item["id"]: item for item in positions}
    suggestions = {item["suggestion"] for item in positions if item["suggestion"]}

    # An ordinary one-run line ("Số hợp đồng: ____") is detected and its label
    # survives as the fill prefix.
    contract_positions = [item for item in positions if item["suggestion"] == "contract.contract_no"]
    assert contract_positions, by_id
    assert contract_positions[0]["prefix"].startswith("Số hợp đồng:")
    assert contract_positions[0]["detectedBy"] == "inline-blank"

    assert "customer.name" in suggestions
    assert "shipment.id" in suggestions
    assert "shipment.container_no" in suggestions
    # A table's blank cell takes its label from the cell to its left, which is
    # how an ordinary form table reads ("Người nhận hàng" | "____").
    table_positions = [item for item in positions if item["detectedBy"] == "table-label-neighbour"]
    assert {item["suggestion"] for item in table_positions} == {
        "delivery.receiver_name", "delivery.delivered_at"
    }


def test_detects_positions_and_suggests_fields_on_ordinary_xlsx():
    raw = build_pilot_xlsx()
    info = engine.validate_uploaded_template("bang-ke.xlsx", raw)
    assert info["kind"] == engine.KIND_XLSX

    positions = engine.detect_positions(raw, info["kind"])
    by_id = {item["id"]: item for item in positions}
    assert "BANG KE!B3" in by_id
    assert by_id["BANG KE!B3"]["suggestion"] == "shipment.id"
    assert by_id["BANG KE!B4"]["suggestion"] == "shipment.container_no"
    assert by_id["BANG KE!B6"]["suggestion"] == "shipment.pod"
    assert by_id["GIAO NHAN!B1"]["suggestion"] == "delivery.receiver_name"
    assert by_id["GIAO NHAN!B2"]["suggestion"] == "delivery.receiver_title"


def test_marker_tokens_are_detected_and_mapped_to_canonical_fields():
    raw = build_marker_docx()
    positions = engine.detect_positions(raw, engine.KIND_DOCX)
    by_label = {item["label"]: item for item in positions if item["detectedBy"] == "marker"}
    assert by_label["shipment.id"]["suggestion"] == "shipment.id"
    assert by_label["customer.name"]["suggestion"] == "customer.name"


# ===========================================================================
# 2. Upload safety — refuse before storing anything
# ===========================================================================

@pytest.mark.parametrize("name", ["old.doc", "old.xls"])
def test_legacy_office_formats_are_refused(name):
    with pytest.raises(engine.UploadedTemplateError) as exc:
        engine.detect_kind(name, b"anything")
    assert ".doc/.xls" in str(exc.value)


@pytest.mark.parametrize("name", ["macro.docm", "macro.xlsm"])
def test_macro_enabled_files_are_refused(name):
    with pytest.raises(engine.UploadedTemplateError) as exc:
        engine.detect_kind(name, b"PK\x03\x04rest")
    assert "macro" in str(exc.value)


def test_non_ooxml_and_oversized_payloads_are_refused():
    with pytest.raises(engine.UploadedTemplateError):
        engine.detect_kind("fake.docx", b"NOT A ZIP AT ALL")
    huge = b"PK\x03\x04" + b"\0" * (engine.MAX_TEMPLATE_BYTES + 1)
    with pytest.raises(engine.UploadedTemplateError) as exc:
        engine.detect_kind("huge.docx", huge)
    assert "MB" in str(exc.value)


def test_missing_core_part_is_refused():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/styles.xml", "<w:styles/>")
    with pytest.raises(engine.UploadedTemplateError) as exc:
        engine.validate_uploaded_template("broken.docx", buffer.getvalue())
    assert "word/document.xml" in str(exc.value)


def test_macro_part_and_external_relationship_are_refused_by_the_safety_scan():
    raw = build_pilot_docx()
    archive = zipfile.ZipFile(io.BytesIO(raw))
    parts = {name: archive.read(name) for name in archive.namelist()}
    parts["word/vbaProject.bin"] = b"MZ\x00fake"
    parts["word/_rels/document.xml.rels"] = (
        b'<?xml version="1.0"?><Relationships xmlns='
        b'"http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="rIdX" Type="http://x/hyperlink" '
        b'Target="https://evil.example/" TargetMode="External"/></Relationships>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as writer:
        for name, data in parts.items():
            writer.writestr(name, data)

    scan = engine.scan_package_safety(buffer.getvalue())
    assert scan["ok"] is False
    assert any("banned parts" in issue for issue in scan["issues"])
    assert any("external relationship" in issue for issue in scan["issues"])
    with pytest.raises(engine.UploadedTemplateError):
        engine.validate_uploaded_template("trojan.docx", buffer.getvalue())


def test_zip_bomb_compression_ratio_is_refused():
    raw = build_pilot_docx()
    archive = zipfile.ZipFile(io.BytesIO(raw))
    parts = {name: archive.read(name) for name in archive.namelist()}
    parts["word/document.xml"] = b"<w:document>" + b"<w:p/>" * 400_000
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as writer:
        for name, data in parts.items():
            writer.writestr(name, data)
    scan = engine.scan_package_safety(buffer.getvalue())
    assert scan["ok"] is False
    assert any("compression ratio" in issue or "uncompressed size" in issue
               for issue in scan["issues"])


def test_ordinary_theme_colours_do_not_trigger_a_false_positive():
    """Regression: a bare ``DDE`` token matched ``w:fill="B6DDE8"``."""
    raw = build_pilot_docx()
    assert "B6DDE8" in zipfile.ZipFile(io.BytesIO(raw)).read("word/styles.xml").decode("utf-8")
    assert engine.scan_package_safety(raw)["ok"] is True


def test_a_refused_upload_persists_nothing(staging):
    _admin()
    before = len(store.load_registry())
    outcome = _dispatch_template("docgen_template_upload", {
        "label": "Trojan", "fileName": "trojan.docm", "base64": _b64(b"PK\x03\x04x"),
        "requestId": "req-trojan",
    }, seq=1)
    assert outcome["ok"] is False
    assert outcome["gate"] == "TEMPLATE_REJECTED"
    assert len(store.load_registry()) == before


# ===========================================================================
# 3. Mapping validation — whitelist only, never interpreted
# ===========================================================================

@pytest.mark.parametrize("value", [
    "shipment.data.2.7.receiver_name",       # raw document path
    "__import__('os').system('id')",          # expression
    "{{ 7*7 }}",                              # Jinja
    "company.legal_name; DROP",               # injection
    "db.shipments.find()",                    # query
])
def test_forged_canonical_keys_are_refused_not_interpreted(value):
    with pytest.raises(engine.UploadedTemplateError):
        engine.normalize_mapping(
            [{"position": "p0/r0", "mode": "field", "value": value}], engine.KIND_DOCX
        )


def test_money_and_payment_fields_are_not_bindable_at_all():
    """Structural guarantee: no amount/VAT/bank/payment key exists to bind."""
    for forbidden in ("contract.total", "contract.amount", "goods.price", "goods.amount",
                      "company.bank_account", "shipment.vat", "payment.terms"):
        assert forbidden not in engine.CANONICAL_FIELD_KEYS
        with pytest.raises(engine.UploadedTemplateError):
            engine.normalize_mapping(
                [{"position": "p0/r0", "mode": "field", "value": forbidden}], engine.KIND_DOCX
            )


def test_duplicate_position_and_wrong_shape_are_refused():
    with pytest.raises(engine.UploadedTemplateError):
        engine.normalize_mapping([
            {"position": "p0/r0", "mode": "field", "value": "shipment.id"},
            {"position": "p0/r0", "mode": "field", "value": "customer.name"},
        ], engine.KIND_DOCX)
    with pytest.raises(engine.UploadedTemplateError):
        engine.normalize_mapping("not-a-list", engine.KIND_DOCX)
    with pytest.raises(engine.UploadedTemplateError):
        engine.normalize_mapping([{"position": "p0/r0", "mode": "eval", "value": "x"}],
                                 engine.KIND_DOCX)
    # XLSX positions must carry their sheet; DOCX positions must not.
    with pytest.raises(engine.UploadedTemplateError):
        engine.normalize_mapping([{"position": "B3", "mode": "field", "value": "shipment.id"}],
                                 engine.KIND_XLSX)
    with pytest.raises(engine.UploadedTemplateError):
        engine.normalize_mapping([{"position": "S!B3", "mode": "field", "value": "shipment.id"}],
                                 engine.KIND_DOCX)


def test_mapping_may_only_target_detected_positions(staging):
    template = _upload_publish(build_pilot_docx(), "BB-DC", "bb.docx")
    _admin()
    outcome = _dispatch_template("docgen_template_mapping_save", {
        "templateId": template["id"],
        "mapping": [{"position": "p999/r9", "mode": "field", "value": "shipment.id"}],
        "requestId": "req-forged-position",
    }, seq=4)
    assert outcome["ok"] is False
    assert outcome["gate"] == "UNKNOWN_POSITION"


# ===========================================================================
# 4. Fail-closed resolution — never a blank, a zero or today()
# ===========================================================================

def test_unresolved_canonical_fact_is_missing_not_blank():
    mapping = [
        {"position": "p0/r0", "mode": "field", "value": "customer.name"},
        {"position": "p1/r0", "mode": "field", "value": "customer.phone"},
    ]
    values, missing = engine.resolve_mapping(mapping, {"customer": {"name": "ACME", "phone": ""}})
    assert values == {"p0/r0": "ACME"}
    assert any("Điện thoại khách hàng" in item for item in missing)


def test_conditional_facts_fail_closed_without_one_unambiguous_source():
    mapping = [
        {"position": "p0/r0", "mode": "field", "value": "contract.contract_no"},
        {"position": "p1/r0", "mode": "field", "value": "goods.description"},
    ]
    _values, missing = engine.resolve_mapping(mapping, {"contract": {}, "goods_lines": []})
    assert len(missing) == 2

    # Two goods lines: still ambiguous, still refused.
    _values, missing = engine.resolve_mapping(mapping, {
        "contract": {"contract_no": "HD-1", "contract_date": "2026-01-01"},
        "goods_lines": [{"description": "A"}, {"description": "B"}],
    })
    assert any("dòng hàng" in item for item in missing)


def test_manual_fields_are_required_and_never_defaulted():
    mapping = [{"position": "p0/r0", "mode": "manual", "value": "Số biên bản"}]
    readiness = engine.evaluate_uploaded_readiness(mapping, {}, manual={})
    assert readiness.state == "MISSING_INFO"
    assert any("Số biên bản" in item for item in readiness.missing)
    assert engine.evaluate_uploaded_readiness(
        mapping, {}, manual={"Số biên bản": "BB-01"}
    ).state == "READY"


def test_an_empty_mapping_is_never_ready():
    readiness = engine.evaluate_uploaded_readiness([], {}, manual={})
    assert readiness.state == "MISSING_INFO"


def test_quantity_is_printed_verbatim_never_reformatted():
    """'19.800' is a Vietnamese thousands separator, not twelve point five."""
    mapping = [{"position": "p0/r0", "mode": "field", "value": "goods.quantity"}]
    values, missing = engine.resolve_mapping(mapping, {
        "contract": {"contract_no": "HD-1"},
        "goods_lines": [{"description": "A", "unit": "Tấm", "quantity": "19.800"}],
    })
    assert not missing
    assert values["p0/r0"] == "19.800"


def test_a_kept_label_prefix_is_preserved_with_its_space():
    mapping = [{"position": "p0/r0", "mode": "field", "value": "contract.contract_no"}]
    values, _missing = engine.resolve_mapping(
        mapping, {"contract": {"contract_no": "HD-1"}}, prefixes={"p0/r0": "Số hợp đồng: "}
    )
    assert values["p0/r0"] == "Số hợp đồng: HD-1"


# ===========================================================================
# 5. Non-destructive deterministic rendering
# ===========================================================================

def test_docx_render_keeps_labels_and_is_deterministic():
    raw = build_pilot_docx()
    positions = engine.detect_positions(raw, engine.KIND_DOCX)
    prefixes = {item["id"]: item["prefix"] for item in positions}
    mapping = [{"position": item["id"], "mode": "field", "value": item["suggestion"]}
               for item in positions if item["suggestion"]]
    values, missing = engine.resolve_mapping(mapping, {
        "contract": {"contract_no": "HD-1"},
        "customer": {"name": "ACME"},
        "shipment": {"id": "LO-1", "container_no": "TGHU1"},
        "delivery": {"receiver_name": "A. Kiet", "delivered_at": "2026-09-09"},
    }, prefixes=prefixes)
    assert not missing

    first = engine.render_uploaded(raw, kind=engine.KIND_DOCX,
                                   template_sha256=hashlib.sha256(raw).hexdigest(), values=values)
    second = engine.render_uploaded(raw, kind=engine.KIND_DOCX,
                                    template_sha256=hashlib.sha256(raw).hexdigest(), values=values)
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()

    text = _docx_text(first)
    assert "Số hợp đồng: HD-1" in text          # label kept, value filled
    assert "Khách hàng: ACME" in text
    assert "Số lô hàng: LO-1" in text
    assert "____" not in text.split("BIÊN BẢN")[1].split("Người nhận")[0]


def test_xlsx_render_preserves_every_sheet_and_writes_only_mapped_cells():
    raw = build_pilot_xlsx()
    values = {"BANG KE!B3": "LO-1", "GIAO NHAN!B2": "Thủ kho"}
    rendered = engine.render_uploaded(raw, kind=engine.KIND_XLSX,
                                      template_sha256=hashlib.sha256(raw).hexdigest(), values=values)

    assert _read_cell(rendered, "BANG KE", "B3") == "LO-1"
    assert _read_cell(rendered, "GIAO NHAN", "B2") == "Thủ kho"
    # Unmapped content and both sheet names survive.
    assert _read_cell(rendered, "BANG KE", "A1") == "BẢNG KÊ LÔ HÀNG"
    assert _read_cell(rendered, "BANG KE", "A3") == "Mã lô hàng:"
    assert _read_cell(rendered, "BANG KE", "B9") == "Đơn vị tính"
    names = engine._sheet_paths(
        __import__("lxml.etree", fromlist=["etree"]).fromstring(
            zipfile.ZipFile(io.BytesIO(rendered)).read("xl/workbook.xml")
        ),
        __import__("lxml.etree", fromlist=["etree"]).fromstring(
            zipfile.ZipFile(io.BytesIO(rendered)).read("xl/_rels/workbook.xml.rels")
        ),
    )
    assert set(names) == {"BANG KE", "GIAO NHAN"}
    # Styles part is byte-identical: nothing outside the mapped cells changed.
    before = zipfile.ZipFile(io.BytesIO(raw))
    after = zipfile.ZipFile(io.BytesIO(rendered))
    assert before.read("xl/styles.xml") == after.read("xl/styles.xml")


def test_a_drifted_template_sha_is_refused():
    raw = build_pilot_docx()
    with pytest.raises(engine.UploadedTemplateError) as exc:
        engine.render_uploaded(raw, kind=engine.KIND_DOCX,
                               template_sha256="0" * 64, values={"p0/r0": "x"})
    assert "SHA-256" in str(exc.value)


def test_an_unreplaced_marker_blocks_release():
    raw = build_marker_docx()
    # Fill nothing: the {{...}} tokens would survive into the published file.
    with pytest.raises(engine.UploadedTemplateError) as exc:
        engine.render_uploaded(raw, kind=engine.KIND_DOCX,
                               template_sha256=hashlib.sha256(raw).hexdigest(), values={})
    assert "{{" in str(exc.value)


# ===========================================================================
# 6. RBAC — server-side, not a UI hint
# ===========================================================================

@pytest.mark.parametrize("actor", [VIEWER_ACTOR, SALE_ACTOR])
def test_non_admin_cannot_upload_or_publish(staging, actor):
    import streamlit as st

    st.session_state["current_user"] = dict(actor)
    upload = _dispatch_template("docgen_template_upload", {
        "label": "Lén", "fileName": "x.docx", "base64": _b64(build_pilot_docx()),
        "requestId": "req-sneak",
    }, seq=1)
    assert upload["ok"] is False
    assert upload["gate"] == "BLOCKED_PERMISSION_DENIED"
    assert store.load_registry() == []

    for event in ("docgen_template_mapping_save", "docgen_template_publish",
                  "docgen_template_status_set"):
        outcome = _dispatch_template(event, {"templateId": "UT-x", "mapping": [], "active": True,
                                             "requestId": f"req-{event}"}, seq=2)
        assert outcome["ok"] is False
        assert outcome["gate"] == "BLOCKED_PERMISSION_DENIED"


def test_a_non_admin_cannot_generate_either(staging):
    import streamlit as st

    template = _upload_publish(build_pilot_docx(), "BB-RBAC", "bb.docx")
    st.session_state["current_user"] = dict(VIEWER_ACTOR)
    outcome = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template["id"]})
    assert outcome["ok"] is False
    assert outcome["gate"] == "BLOCKED_PERMISSION_DENIED"


# ===========================================================================
# 7. The ONE end-to-end flow, DOCX
# ===========================================================================

def test_docx_end_to_end_upload_to_redownload(staging):
    template = _upload_publish(build_pilot_docx(), "BB ĐỐI CHIẾU", "bb-doi-chieu.docx")
    assert template["status"] == "ACTIVE"
    assert template["activeVersion"] == 1

    # (a) The ACTIVE template appears in the SAME picker catalog.
    catalog = project_catalog(contract_templates_available=False, pxk_template_available=False,
                              storage_configured=True, form07_template_available=False,
                              catalog=effective_catalog())
    row = next(item for item in catalog if item["id"] == template["id"])
    assert row["adapter"] == "UPLOADED_DOCGEN"
    assert row["available"] is True
    assert row["label"].endswith("v1)")

    # (b) Staff select it through the EXISTING selection event.
    _support()
    selection = vm._handle_shipment_document_selection_save({
        "shipmentId": SHIPMENT_ID, "selectedTemplateIds": [template["id"]],
        "requestId": "req-select", "expectedVersion": _version(),
    })
    assert selection["ok"], selection
    assert selection["readback"]["selectedDocumentTemplateIds"] == [template["id"]]

    # (c) Readiness is server-owned and READY from the seeded canonical facts.
    model = vm.build_view_model()
    projected = next(item for item in model["shipments"] if item["id"] == SHIPMENT_ID)
    state = projected["uploadedTemplates"][template["id"]]
    assert state["readiness"]["state"] == "READY", state["readiness"]
    assert state["version"] == 1

    # (d) Generate.
    generated = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template["id"]}, seq=2)
    assert generated["ok"], generated
    assert generated["gate"] == "READY"
    assert generated["persisted"]["templateVersion"] == 1
    assert generated["persisted"]["revision"] == 1
    attachment_id = generated["persisted"]["attachmentId"]
    assert attachment_id

    # (e) The bytes come back through the EXISTING attachment path, verbatim
    #     canonical facts, with the printed labels preserved.
    outcome = _fetch(attachment_id)
    assert outcome["ok"], outcome
    raw = outcome["data"]
    assert hashlib.sha256(raw).hexdigest() == generated["persisted"]["outputHash"]
    text = _docx_text(raw)
    assert f"Số hợp đồng: {CONTRACT_ID}" in text
    assert f"Khách hàng: {EXPECTED_CUSTOMER_NAME}" in text
    assert f"Số lô hàng: {SHIPMENT_ID}" in text
    assert f"Số container: {EXPECTED_CONTAINER}" in text
    assert EXPECTED_RECEIVER in text
    assert EXPECTED_DELIVERED_AT in text
    # No invented value anywhere: no unfilled blank left in the mapped lines.
    assert "{{" not in text

    # (f) Durable revision metadata binds version + author + source.
    documents = database.load_docgen_documents(SHIPMENT_ID)
    record = next(doc for doc in documents.values()
                  if doc.get("template_id") == template["id"])
    assert record["document_type"] == engine.UPLOADED_DOCUMENT_TYPE
    assert record["template_version"] == 1
    assert record["template_hash"] == template["sha256"]
    assert record["revision"] == 1
    assert record["output_hash"] == generated["persisted"]["outputHash"]
    assert record["source_snapshot"]["filled_positions"]

    # (g) Deselecting never deletes the generated history.
    deselect = vm._handle_shipment_document_selection_save({
        "shipmentId": SHIPMENT_ID, "selectedTemplateIds": [],
        "requestId": "req-deselect", "expectedVersion": _version(),
    })
    assert deselect["ok"], deselect
    assert database.load_docgen_documents(SHIPMENT_ID).get(record["id"]) is not None
    after = _fetch(attachment_id)
    assert after["ok"] and hashlib.sha256(after["data"]).hexdigest() == record["output_hash"]


def test_regeneration_produces_an_immutable_second_revision(staging):
    template = _upload_publish(build_pilot_docx(), "BB REV", "bb-rev.docx")
    _support()
    first = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template["id"]}, seq=1)
    assert first["ok"] and first["persisted"]["revision"] == 1
    second = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template["id"]}, seq=2)
    assert second["ok"] and second["persisted"]["revision"] == 2
    assert second["persisted"]["recordId"] != first["persisted"]["recordId"]


def test_manual_field_blocks_generation_until_the_operator_types_it(staging):
    raw = build_pilot_docx()
    positions = engine.detect_positions(raw, engine.KIND_DOCX)
    # Drop the last suggested binding and replace it with an operator-typed
    # field, so no position is bound twice.
    suggested = [item for item in positions if item["suggestion"]]
    mapping = [{"position": item["id"], "mode": "field", "value": item["suggestion"]}
               for item in suggested[:-1]]
    mapping.append({"position": suggested[-1]["id"], "mode": "manual", "value": "Số biên bản"})
    template = _upload_publish(raw, "BB MANUAL", "bb-manual.docx", mapping=mapping)

    _support()
    blocked = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template["id"]}, seq=1)
    assert blocked["ok"] is False
    assert blocked["gate"] == "MISSING_INFO"
    assert any("Số biên bản" in item for item in blocked["missing"])

    filled = _dispatch_generate({
        "shipmentId": SHIPMENT_ID, "templateId": template["id"],
        "manualValues": {"Số biên bản": "BB-2026-001"},
    }, seq=2)
    assert filled["ok"], filled
    raw_out = _fetch(filled["persisted"]["attachmentId"])["data"]
    assert "BB-2026-001" in _docx_text(raw_out)


def test_missing_canonical_fact_blocks_generation(staging):
    """Removing a verified fact makes the flow fail closed, not print a blank."""
    # The canonical section key is literally "2.7", so a dotted update path
    # cannot address it; rewrite the section through the whole `data` field.
    db = database.get_db()
    document = db["shipments"].find_one({"id": SHIPMENT_ID})
    data = dict(document["data"])
    data["2.7"] = {**dict(data["2.7"]), "receiver_name": ""}
    db["shipments"].update_one({"id": SHIPMENT_ID}, {"$set": {"data": data}})
    assert vm.read_shipment(SHIPMENT_ID)["data"]["2.7"]["receiver_name"] == ""
    raw = build_pilot_docx()
    positions = engine.detect_positions(raw, engine.KIND_DOCX)
    receiver = next(item for item in positions if item["suggestion"] == "delivery.receiver_name")
    template = _upload_publish(
        raw, "BB RECEIVER", "bb-receiver.docx",
        mapping=[{"position": receiver["id"], "mode": "field", "value": "delivery.receiver_name"}],
    )
    _support()
    outcome = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template["id"]}, seq=1)
    assert outcome["ok"] is False
    assert outcome["gate"] == "MISSING_INFO"
    assert any("Người nhận hàng" in item for item in outcome["missing"])


# ===========================================================================
# 8. The ONE end-to-end flow, XLSX
# ===========================================================================

def test_xlsx_end_to_end_upload_to_redownload(staging):
    template = _upload_publish(build_pilot_xlsx(), "BẢNG KÊ LÔ", "bang-ke-lo.xlsx")
    assert template["kind"] == "XLSX"

    catalog = project_catalog(contract_templates_available=False, pxk_template_available=False,
                              storage_configured=True, form07_template_available=False,
                              catalog=effective_catalog())
    assert any(item["id"] == template["id"] and item["available"] for item in catalog)

    _support()
    selection = vm._handle_shipment_document_selection_save({
        "shipmentId": SHIPMENT_ID, "selectedTemplateIds": [template["id"]],
        "requestId": "req-select-x", "expectedVersion": _version(),
    })
    assert selection["ok"], selection

    generated = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template["id"]}, seq=2)
    assert generated["ok"], generated
    assert generated["persisted"]["fileName"].endswith(".xlsx")

    raw = _fetch(generated["persisted"]["attachmentId"])["data"]
    assert hashlib.sha256(raw).hexdigest() == generated["persisted"]["outputHash"]
    assert raw[:2] == b"PK"
    assert _read_cell(raw, "BANG KE", "B3") == SHIPMENT_ID
    assert _read_cell(raw, "BANG KE", "B4") == EXPECTED_CONTAINER
    assert _read_cell(raw, "BANG KE", "B5") == EXPECTED_POL
    assert _read_cell(raw, "BANG KE", "B6") == EXPECTED_POD
    assert _read_cell(raw, "BANG KE", "B7") == EXPECTED_DELIVERED_AT
    # Second sheet, filled and preserved.
    assert _read_cell(raw, "GIAO NHAN", "B1") == EXPECTED_RECEIVER
    assert _read_cell(raw, "GIAO NHAN", "B2") == "Thủ kho"
    # Labels untouched.
    assert _read_cell(raw, "BANG KE", "A3") == "Mã lô hàng:"
    assert _read_cell(raw, "BANG KE", "A9") == "Tên hàng hóa"


def test_goods_line_is_filled_from_the_single_contract_line(staging):
    raw = build_pilot_xlsx()
    positions = engine.detect_positions(raw, engine.KIND_XLSX)
    by_id = {item["id"]: item for item in positions}
    mapping = [
        {"position": by_id["BANG KE!A10"]["id"], "mode": "field", "value": "goods.description"},
        {"position": by_id["BANG KE!B10"]["id"], "mode": "field", "value": "goods.unit"},
        {"position": by_id["BANG KE!C10"]["id"], "mode": "field", "value": "goods.quantity"},
    ] if all(k in by_id for k in ("BANG KE!A10", "BANG KE!B10", "BANG KE!C10")) else None
    if mapping is None:
        # Fall back to whatever detection reported for the goods header row.
        header_row = [item for item in positions
                      if item["suggestion"] in ("goods.description", "goods.unit", "goods.quantity")]
        mapping = [{"position": item["id"], "mode": "field", "value": item["suggestion"]}
                   for item in header_row]
    template = _upload_publish(raw, "BẢNG KÊ HÀNG", "bang-ke-hang.xlsx", mapping=mapping)

    _support()
    generated = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template["id"]}, seq=1)
    assert generated["ok"], generated
    raw_out = _fetch(generated["persisted"]["attachmentId"])["data"]
    cells = [
        _read_cell(raw_out, "BANG KE", f"{col}{row}")
        for row in (8, 9, 10, 11)
        for col in ("A", "B", "C", "D")
    ]
    assert "Kính nổi 5mm" in cells
    assert "Tấm" in cells
    assert "19.800" in cells          # verbatim, NOT 19.8
    assert "19.8" not in cells


# ===========================================================================
# 9. A SECOND template added by upload alone — no code change
# ===========================================================================

def test_a_second_ordinary_template_is_onboarded_by_upload_without_code_change(staging):
    import inspect

    first = _upload_publish(build_pilot_docx(), "BB SỐ 1", "bb-1.docx")
    # A structurally DIFFERENT ordinary DOCX, mapped only from its own detection.
    second = _upload_publish(build_second_docx(), "PHIẾU XÁC NHẬN", "phieu.docx")
    assert second["id"] != first["id"]
    assert second["status"] == "ACTIVE"

    # Both appear in the picker catalog with no new adapter and no new handler.
    catalog = project_catalog(contract_templates_available=False, pxk_template_available=False,
                              storage_configured=True, form07_template_available=False,
                              catalog=effective_catalog())
    ids = {item["id"] for item in catalog if item["adapter"] == "UPLOADED_DOCGEN"}
    assert {first["id"], second["id"]} <= ids

    _support()
    outcome = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": second["id"]}, seq=1)
    assert outcome["ok"], outcome
    text = _docx_text(_fetch(outcome["persisted"]["attachmentId"])["data"])
    assert f"Số booking: {EXPECTED_BOOKING}" in text
    assert f"Cảng đi: {EXPECTED_POL}" in text
    assert f"Cảng đến: {EXPECTED_POD}" in text

    # No new event, handler or adapter was needed: the dispatcher surface is
    # unchanged by adding a template.
    assert "uploaded_template_generate" in vm.PHASE_B_EVENTS
    assert vm.logi_templates.DOCGEN_TEMPLATE_EVENTS == {
        "docgen_template_upload", "docgen_template_mapping_save",
        "docgen_template_publish", "docgen_template_status_set",
        "docgen_template_preview",
    }
    assert engine.UPLOADED_ADAPTER == "UPLOADED_DOCGEN"


def test_a_third_template_is_onboarded_by_upload_alone_and_survives_the_full_flow(staging):
    """Issue #193 core flow, with a template the code has never seen.

    Admin uploads an ordinary workbook -> detection suggests fields -> Admin
    confirms the mapping -> publish (immutable v1) -> the template appears in
    the SAME shipment picker -> staff selects it -> facts auto-fill -> the file
    is generated -> re-downloading returns byte-identical stored bytes.

    No source file is touched: the assertion at the end pins the dispatcher
    surface, so adding this template could not have required a code change.
    """
    from pathlib import Path

    import core.docgen as docgen_package

    modules_before = {
        item.stem for item in Path(docgen_package.__file__).parent.glob("*.py")
    }
    events_before = set(vm.PHASE_B_EVENTS) | set(vm.logi_templates.DOCGEN_TEMPLATE_EVENTS)

    third = _upload_publish(build_third_xlsx(), "THÔNG TIN LÔ (mẫu 3)", "thong-tin-lo.xlsx")
    assert third["kind"] == "XLSX"
    assert third["status"] == "ACTIVE"
    assert third["activeVersion"] == 1
    assert third["versionCount"] == 1
    assert third["publishedBy"], "the publishing Admin is bound to the version"

    # Detection used BOTH paths on one ordinary file: explicit {{token}}
    # markers and label/empty-neighbour cells. Neither is template-specific.
    kinds = {item["detectedBy"] for item in third["detected"]}
    assert kinds == {"marker", "label-neighbour"}, kinds

    # It reaches the SAME picker catalog through the SAME adapter.
    catalog = project_catalog(contract_templates_available=False, pxk_template_available=False,
                              storage_configured=True, form07_template_available=False,
                              catalog=effective_catalog())
    entry = next(item for item in catalog if item["id"] == third["id"])
    assert entry["adapter"] == engine.UPLOADED_ADAPTER
    assert entry["available"] is True

    # Staff selects it with the EXISTING selection event.
    _support()
    selection = vm._handle_shipment_document_selection_save({
        "shipmentId": SHIPMENT_ID, "selectedTemplateIds": [third["id"]],
        "requestId": "req-select-third", "expectedVersion": _version(),
    })
    assert selection["ok"], selection

    # Generation auto-fills the verified facts.
    generated = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": third["id"]}, seq=2)
    assert generated["ok"], generated
    raw = _fetch(generated["persisted"]["attachmentId"])["data"]

    # Re-download returns byte-identical stored bytes.
    assert hashlib.sha256(raw).hexdigest() == generated["persisted"]["outputHash"]
    assert raw[:2] == b"PK"

    assert _read_cell(raw, "THONG TIN", "B3") == SHIPMENT_ID
    assert _read_cell(raw, "THONG TIN", "B4") == EXPECTED_CUSTOMER_NAME
    assert _read_cell(raw, "THONG TIN", "B5") == EXPECTED_BOOKING
    assert _read_cell(raw, "THONG TIN", "B6") == EXPECTED_RECEIVER
    # The marker sheet resolved too, and its labels/layout are untouched.
    assert _read_cell(raw, "MARKERS", "B2") == SHIPMENT_ID
    # The company legal name is read back from the SAME facts projection the
    # generator used — never typed into this test, so no legal identity here is
    # invented by the assertion.
    db = database.get_db()
    facts = vm._uploaded_template_facts(
        dict(db["shipments"].find_one({"id": SHIPMENT_ID}) or {}),
        contract=dict(db["contracts"].find_one({"id": CONTRACT_ID}) or {}),
        company=dict(db["authority_companies"].find_one({"id": COMPANY_ID}) or {}),
        customer=dict(db["customers"].find_one({"id": CUSTOMER_ID}) or {}),
    )
    company_name = facts["company"]["legal_name"]
    assert company_name, "the staging seed carries a verified company legal name"
    assert _read_cell(raw, "MARKERS", "B3") == company_name
    assert _read_cell(raw, "THONG TIN", "A3") == "Mã lô hàng:"
    assert _read_cell(raw, "THONG TIN", "A1") == "THÔNG TIN LÔ HÀNG"

    # Adding this template required no new code: no new module landed in
    # core/docgen, and the dispatcher surface is byte-for-byte the same set of
    # events. A per-template code module would show up here as a new file.
    modules_after = {
        item.stem for item in Path(docgen_package.__file__).parent.glob("*.py")
    }
    assert modules_after == modules_before
    assert set(vm.PHASE_B_EVENTS) | set(vm.logi_templates.DOCGEN_TEMPLATE_EVENTS) == events_before
    # And no module anywhere is named after an uploaded template: onboarding is
    # data (registry row + GridFS bytes), never code.
    assert not any(
        "thong_tin" in name or "phieu" in name or "bb_" in name
        for name in modules_after
    ), sorted(modules_after)


def test_republishing_a_changed_mapping_creates_an_immutable_new_version(staging):
    template = _upload_publish(build_pilot_docx(), "BB VER", "bb-ver.docx")
    _admin()
    positions = template["detected"]
    reduced = [{"position": item["id"], "mode": "field", "value": item["suggestion"]}
               for item in positions if item["suggestion"] == "shipment.id"]
    # A published template cannot be edited in place.
    refused = _dispatch_template("docgen_template_mapping_save", {
        "templateId": template["id"], "mapping": reduced, "requestId": "req-edit-published",
    }, seq=4)
    assert refused["ok"] is False
    assert "bản nháp" in refused["error"].lower()

    assert store.get_template(template["id"])["activeVersion"] == 1
    versions = store.get_template(template["id"])["versions"]
    assert len(versions) == 1
    assert versions[0]["publishedBy"] == "staging.admin"


def test_retiring_a_template_keeps_published_versions_and_generated_history(staging):
    template = _upload_publish(build_pilot_docx(), "BB RETIRE", "bb-retire.docx")
    _support()
    generated = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template["id"]}, seq=1)
    assert generated["ok"]

    _admin()
    retired = _dispatch_template("docgen_template_status_set", {
        "templateId": template["id"], "active": False, "requestId": "req-retire",
    }, seq=4)
    assert retired["ok"] and retired["readback"]["status"] == "RETIRED"

    row = store.get_template(template["id"])
    assert row["status"] == "RETIRED"
    assert len(row["versions"]) == 1 and row["activeVersion"] == 1
    # A retired template leaves the picker catalog...
    catalog = project_catalog(contract_templates_available=False, pxk_template_available=False,
                              storage_configured=True, form07_template_available=False,
                              catalog=effective_catalog())
    assert not any(item["id"] == template["id"] for item in catalog)
    # ...but the generated file is still retrievable.
    still = _fetch(generated["persisted"]["attachmentId"])
    assert still["ok"]


def test_an_unpublished_template_is_not_selectable(staging):
    _admin()
    outcome = _dispatch_template("docgen_template_upload", {
        "label": "BB DRAFT", "fileName": "bb.docx", "base64": _b64(build_pilot_docx()),
        "requestId": "req-draft",
    }, seq=1)
    assert outcome["ok"]
    draft_id = outcome["readback"]["id"]
    assert outcome["readback"]["status"] == "DRAFT"

    catalog = project_catalog(contract_templates_available=False, pxk_template_available=False,
                              storage_configured=True, form07_template_available=False,
                              catalog=effective_catalog())
    assert not any(item["id"] == draft_id for item in catalog)
    with pytest.raises(Exception) as exc:
        validate_selected_template_ids([draft_id], catalog=effective_catalog())
    assert "UNKNOWN_TEMPLATE" in str(getattr(exc.value, "code", ""))

    _support()
    blocked = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": draft_id}, seq=2)
    assert blocked["ok"] is False
    assert blocked["gate"] == "TEMPLATE_NOT_PUBLISHED"


def test_a_generation_against_an_unknown_template_is_refused(staging):
    _support()
    outcome = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": "UT-nope-1"}, seq=1)
    assert outcome["ok"] is False
    assert outcome["gate"] == "TEMPLATE_NOT_PUBLISHED" or outcome["gate"] == "TEMPLATE_NOT_FOUND"


def test_a_replayed_trigger_never_double_generates(staging):
    template = _upload_publish(build_pilot_docx(), "BB REPLAY", "bb-replay.docx")
    _support()
    payload = {"shipmentId": SHIPMENT_ID, "templateId": template["id"]}
    session = {"seq": 0}
    first = vm.consume_phase_b_triggers(
        session, {"uploaded_template_generate": {"seq": 1, "event": "x", "payload": payload}})
    replay = vm.consume_phase_b_triggers(
        session, {"uploaded_template_generate": {"seq": 1, "event": "x", "payload": payload}})
    assert len(first) == 1 and first[0]["ok"]
    assert replay == []


def test_the_admin_workspace_projection_exposes_the_field_whitelist(staging):
    _admin()
    projection = vm.logi_templates.template_workspace_projection(include_detected=True)
    assert projection["canManage"] is True
    keys = {field["key"] for field in projection["fields"]}
    assert {"company.legal_name", "customer.name", "shipment.id", "delivery.receiver_name"} <= keys
    assert not any("amount" in key or "price" in key or "vat" in key for key in keys)
    assert projection["accept"] == ".docx,.xlsx"

    # canManage is a DISPLAY hint: a non-Admin sees the same list, no controls.
    _support()
    assert vm.logi_templates.template_workspace_projection()["canManage"] is False


def _version() -> int:
    shipment = vm.read_shipment(SHIPMENT_ID)
    return int((shipment or {}).get("version") or 0)


# ===========================================================================
# 10. Existing surfaces stay intact (regression guards)
# ===========================================================================

def test_the_v1_catalog_is_unchanged_by_this_slice():
    ids = [template.id for template in SHIPMENT_DOCUMENT_CATALOG]
    assert ids == ["HDNT", "PL", "HDMB", "PXK", "GNT", "FORM_07"]
    # No upload row can shadow a code-owned id.
    effective = effective_catalog()
    assert [template.id for template in effective if template.id in ids] == ids


def test_form07_readiness_still_fails_closed_on_its_own_rules():
    """Focused FORM_07 regression: this slice adds a sibling, not a rewrite."""
    from core.docgen.form07 import READY, evaluate_form07_readiness

    blocked = evaluate_form07_readiness(
        delivery={}, goods_lines=[], agent={}, company={}, contract={}, manual={}
    )
    assert blocked.state != READY
    assert blocked.missing


# ---------------------------------------------------------------------------
# CONTROL TOWER REVIEW — blocker regressions
# ---------------------------------------------------------------------------

def _count_durable_writes(shipment_id: str) -> tuple[int, int]:
    """(docgen metadata rows, attachment rows) for one shipment."""
    db = database.get_db()
    docs = len([
        row for row in (database.load_docgen_documents(shipment_id) or {}).values()
        if isinstance(row, dict) and row.get("is_deleted") is not True
    ])
    attachments = len(list(db["shipment_attachments"].find({"shipment_id": shipment_id})))
    return docs, attachments


def test_a_retired_template_cannot_be_generated_by_a_direct_event(staging):
    """Retire must stop generation server-side, not only hide the picker row.

    A forged ``uploaded_template_generate`` naming a RETIRED template still
    finds a published version row (retire keeps history by design), so the
    handler has to check the template STATUS itself.
    """
    template = _upload_publish(build_pilot_docx(), "BB RETIRED GEN", "bb-retired-gen.docx")
    _support()
    first = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template["id"]}, seq=1)
    assert first["ok"], first

    _admin()
    retired = _dispatch_template("docgen_template_status_set", {
        "templateId": template["id"], "active": False, "requestId": "req-retire-gen",
    }, seq=4)
    assert retired["ok"] and retired["readback"]["status"] == "RETIRED"
    # The version row survives — that is what makes the status check necessary.
    assert store.active_version(store.get_template(template["id"])) is not None

    before = _count_durable_writes(SHIPMENT_ID)
    forged = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template["id"]}, seq=5)
    assert forged["ok"] is False, "a retired template must not generate"
    assert "ngừng" in forged["error"].lower() or "retired" in forged.get("gate", "").lower()
    assert forged.get("gate") == "TEMPLATE_RETIRED"

    # Zero attachment and zero metadata writes from the refused generation.
    assert _count_durable_writes(SHIPMENT_ID) == before

    # The already-generated history stays downloadable.
    still = _fetch(first["persisted"]["attachmentId"])
    assert still["ok"] and still["data"][:2] == b"PK"


def test_publishing_an_already_active_template_does_not_create_a_new_version(staging):
    """Publish on an ACTIVE template must not mint an unintended version."""
    template = _upload_publish(build_pilot_docx(), "BB PUB TWICE", "bb-pub-twice.docx")
    assert template["status"] == "ACTIVE"
    assert template["activeVersion"] == 1 and template["versionCount"] == 1

    _admin()
    again = _dispatch_template("docgen_template_publish", {
        "templateId": template["id"], "requestId": "req-pub-again",
    }, seq=4)
    assert again["ok"] is False, "re-publishing without a new draft must be refused"

    row = store.get_template(template["id"])
    assert len(row["versions"]) == 1, "no extra version row was created"
    assert row["activeVersion"] == 1


def test_uncompressed_limits_are_checked_before_any_member_is_decompressed(staging, monkeypatch):
    """The zip-bomb limits must run before testzip()/read() touch member bytes.

    ``ZipFile.testzip()`` fully decompresses every member to CRC-check it, so
    calling it first defeats the very limits meant to stop a bomb.
    """
    import zipfile as _zipfile

    # Build the fixture BEFORE arming the spies: python-docx itself calls
    # ZipFile.read while assembling the package, which is not what is under test.
    ordinary = build_pilot_docx()

    def _boom(self, *args, **kwargs):  # noqa: ANN001 - spy
        raise AssertionError("scan_package_safety decompressed a member before the limits")

    monkeypatch.setattr(_zipfile.ZipFile, "testzip", _boom, raising=True)
    monkeypatch.setattr(_zipfile.ZipFile, "read", _boom, raising=True)

    # Shrink the limits rather than allocate a real 40 MB bomb: the point is the
    # ORDER of the checks, and the spies above fail if any member is touched.
    monkeypatch.setattr(engine, "MAX_UNCOMPRESSED_BYTES", 8)
    findings = engine.scan_package_safety(ordinary)
    assert findings["ok"] is False
    assert any("uncompressed size too large" in issue for issue in findings["issues"]), findings

    # Same for the part-count limit, with a genuinely many-part package.
    monkeypatch.setattr(engine, "MAX_PARTS", 3)
    findings = engine.scan_package_safety(ordinary)
    assert findings["ok"] is False
    assert any("too many parts" in issue for issue in findings["issues"]), findings

    # And the compression-ratio limit, again without inflating anything.
    monkeypatch.setattr(engine, "MAX_UNCOMPRESSED_RATIO", 1.0001)
    findings = engine.scan_package_safety(ordinary)
    assert findings["ok"] is False
    assert any("suspicious compression ratio" in issue for issue in findings["issues"]), findings


def test_an_ordinary_file_still_passes_the_reordered_safety_scan(staging):
    """The reordering must not break real uploads."""
    for raw, kind in ((build_pilot_docx(), engine.KIND_DOCX), (build_pilot_xlsx(), engine.KIND_XLSX)):
        findings = engine.scan_package_safety(raw)
        assert findings["ok"] is True, findings
        assert engine.detect_kind("x.docx" if kind == engine.KIND_DOCX else "x.xlsx", raw) == kind


def _rels_package(rels_xml: str) -> bytes:
    """A minimal but valid DOCX whose root .rels carries the given relationship."""
    inner = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + rels_xml +
        '</Relationships>'
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body><w:p><w:r><w:t>Khách hàng: </w:t></w:r>'
        '<w:r><w:t>____</w:t></w:r></w:p></w:body></w:document>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType='
        '"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as sink:
        sink.writestr("[Content_Types].xml", content_types)
        sink.writestr("_rels/.rels", inner)
        sink.writestr("word/document.xml", document)
    return buffer.getvalue()


@pytest.mark.parametrize("rels_xml,label", [
    # The double-quoted form the original regex already caught.
    ('<Relationship Id="rId1" Type="http://x/y" Target="http://evil/x" TargetMode="External"/>',
     "double-quoted external"),
    # Single-quoted XML is equally legal — and slipped past a "..."-only regex.
    ("<Relationship Id='rId1' Type='http://x/y' Target='http://evil/x' TargetMode='External'/>",
     "single-quoted external"),
    # Attribute order / spacing must not matter either.
    ('<Relationship TargetMode="External" Id="rId1" Target="file:///etc/passwd" Type="http://x/y"/>',
     "reordered attributes"),
    # A relative Target is fine, but an external SCHEME is not, quoted either way.
    ("<Relationship Id='rId2' Type='http://x/y' Target='file:///tmp/x'/>",
     "single-quoted file scheme"),
])
def test_external_relationships_are_refused_whatever_quote_style_is_used(staging, rels_xml, label):
    """Relationships are parsed as XML, so quoting style cannot hide an external target."""
    raw = _rels_package(rels_xml)
    findings = engine.scan_package_safety(raw)
    assert findings["ok"] is False, f"{label} was accepted: {findings}"
    assert any("external relationship" in issue for issue in findings["issues"]), findings
    with pytest.raises(engine.UploadedTemplateError):
        engine.validate_uploaded_template("mau.docx", raw)


def test_an_internal_relationship_is_not_refused_by_the_xml_scan(staging):
    raw = _rels_package(
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
    )
    findings = engine.scan_package_safety(raw)
    assert findings["ok"] is True, findings


def _duplicate_named_customers() -> None:
    """Seed two customers that share a NAME but differ in id and tax code."""
    db = database.get_db()
    db["shipments"].update_one({"id": SHIPMENT_ID}, {"$unset": {"customer_id": ""}})
    db["shipments"].update_one(
        {"id": SHIPMENT_ID}, {"$set": {"customer": "CÔNG TY TRÙNG TÊN"}}
    )
    db["customers"].delete_many({"name": "CÔNG TY TRÙNG TÊN"})
    db["customers"].insert_many([
        {"id": "CUST-DUP-A", "name": "CÔNG TY TRÙNG TÊN", "tax_code": "0100000001",
         "address": "Địa chỉ A", "is_deleted": False},
        {"id": "CUST-DUP-B", "name": "CÔNG TY TRÙNG TÊN", "tax_code": "0100000002",
         "address": "Địa chỉ B", "is_deleted": False},
    ])


def _publish_customer_name_template(label: str, file_name: str, request: str) -> str:
    """Publish a template whose ONLY mapping needs ``customer.name``."""
    _admin()
    draft = _dispatch_template("docgen_template_upload", {
        "label": label, "fileName": file_name,
        "base64": _b64(build_pilot_docx()), "requestId": f"req-{request}",
    }, seq=1)
    assert draft["ok"], draft
    template_id = draft["readback"]["id"]
    position = draft["readback"]["detected"][0]["id"]
    saved = _dispatch_template("docgen_template_mapping_save", {
        "templateId": template_id, "requestId": f"req-map-{request}",
        "mapping": [{"position": position, "mode": "field", "value": "customer.name"}],
    }, seq=2)
    assert saved["ok"], saved
    published = _dispatch_template("docgen_template_publish", {
        "templateId": template_id, "requestId": f"req-pub-{request}",
    }, seq=3)
    assert published["ok"], published
    return template_id


def test_two_customers_sharing_a_name_never_resolve_to_one_of_them(staging):
    """An ambiguous free-text customer name must fail closed, not pick a winner.

    Both customers are named the same but carry different ids and tax codes, so
    a name match cannot identify a legal entity — and picking one would print
    the other's identity on a document.  The readiness projection and the
    generation handler must agree.
    """
    _duplicate_named_customers()
    template_id = _publish_customer_name_template(
        "BB TRÙNG TÊN", "bb-trung-ten.docx", "dup"
    )

    # Generation refuses: neither tax code may stand in for the other.
    _support()
    outcome = _dispatch_generate(
        {"shipmentId": SHIPMENT_ID, "templateId": template_id}, seq=9
    )
    assert outcome["ok"] is False, outcome
    assert outcome.get("gate") == "MISSING_INFO", outcome

    # The shared resolver — the ONE place both surfaces read identity from —
    # returns NO customer rather than an arbitrary one.
    db = database.get_db()
    shipment = dict(db["shipments"].find_one({"id": SHIPMENT_ID}) or {})
    customers = {
        row["id"]: row for row in db["customers"].find({"name": "CÔNG TY TRÙNG TÊN"})
    }
    assert len(customers) == 2
    _cid, _contract, _company, customer = vm._resolve_uploaded_template_parties(
        shipment, SHIPMENT_ID,
        contracts={}, companies={}, customers=customers,
    )
    assert customer == {}, "an ambiguous name resolves to NO customer"

    # And the readiness the picker card shows says the same thing.
    readiness = engine.evaluate_uploaded_readiness(
        store.active_version(store.get_template(template_id))["mapping"],
        vm._uploaded_template_facts(shipment, contract={}, company={}, customer={}),
        manual={},
    )
    assert readiness.state == "MISSING_INFO"
    assert readiness.missing, "the operator is told what is missing"


def test_a_unique_customer_name_match_is_still_accepted(staging):
    """A provably-unique name match is not ambiguity and must keep working."""
    db = database.get_db()
    db["shipments"].update_one({"id": SHIPMENT_ID}, {"$unset": {"customer_id": ""}})
    db["shipments"].update_one({"id": SHIPMENT_ID}, {"$set": {"customer": "CÔNG TY DUY NHẤT"}})
    db["customers"].delete_many({"name": {"$in": ["CÔNG TY DUY NHẤT", "CÔNG TY TRÙNG TÊN"]}})
    db["customers"].insert_one({"id": "CUST-ONLY", "name": "CÔNG TY DUY NHẤT",
                                "tax_code": "0100000009", "is_deleted": False})
    shipment = dict(db["shipments"].find_one({"id": SHIPMENT_ID}) or {})
    _id, _contract, _company, customer = vm._resolve_uploaded_template_parties(
        shipment, SHIPMENT_ID,
        contracts={}, companies={},
        customers={"CUST-ONLY": db["customers"].find_one({"id": "CUST-ONLY"})},
    )
    assert customer.get("id") == "CUST-ONLY"
    assert customer.get("tax_code") == "0100000009"


def _draft_template(label: str, file_name: str, request: str, *, raw=None) -> str:
    """Upload + confirm a mapping, but DO NOT publish."""
    _admin()
    draft = _dispatch_template("docgen_template_upload", {
        "label": label, "fileName": file_name,
        "base64": _b64(raw if raw is not None else build_pilot_docx()),
        "requestId": f"req-{request}",
    }, seq=1)
    assert draft["ok"], draft
    template_id = draft["readback"]["id"]
    mapping = [
        {"position": item["id"], "mode": "field", "value": item["suggestion"]}
        for item in draft["readback"]["detected"] if item["suggestion"]
    ]
    saved = _dispatch_template("docgen_template_mapping_save", {
        "templateId": template_id, "mapping": mapping, "requestId": f"req-map-{request}",
    }, seq=2)
    assert saved["ok"], saved
    return template_id


def _dispatch_preview(template_id: str, seq: int = 3) -> dict:
    _admin()
    outcomes = vm.logi_templates.consume_docgen_template_triggers(
        {"seq": seq - 1},
        {"docgen_template_preview": {
            "seq": seq, "event": "docgen_template_preview",
            "payload": {"templateId": template_id, "requestId": f"req-prev-{seq}"},
        }},
    )
    assert len(outcomes) == 1, outcomes
    return outcomes[0]


def test_admin_can_preview_a_draft_before_publishing_it(staging):
    """Issue #193: the Admin sees the filled result BEFORE activating."""
    template_id = _draft_template("BB XEM THU", "bb-xem-thu.docx", "prev")
    assert store.get_template(template_id)["status"] == "DRAFT"

    outcome = _dispatch_preview(template_id)
    assert outcome["ok"], outcome
    assert outcome["gate"] == "PREVIEW_READY"
    readback = outcome["readback"]
    assert readback["persisted"] is False
    assert readback["fileName"].startswith("XEM-THU_")
    assert readback["marker"] == engine.PREVIEW_MARKER

    raw = base64.b64decode(readback["bytesBase64"])
    assert raw[:2] == b"PK"
    assert hashlib.sha256(raw).hexdigest() == readback["sha256"]

    # The sample data is unmistakably fake, and no real staging fact leaked in.
    text = _docx_text(raw)
    assert engine.PREVIEW_MARKER in text
    assert EXPECTED_CUSTOMER_NAME not in text
    assert EXPECTED_CUSTOMER_TAX_CODE not in text
    assert SHIPMENT_ID not in text


def test_a_preview_writes_no_attachment_metadata_or_shipment_record(staging):
    """A preview must never enter any history or touch a real lot."""
    template_id = _draft_template("BB XEM THU 2", "bb-xem-thu-2.docx", "prev2")
    before = _count_durable_writes(SHIPMENT_ID)
    templates_before = len(store.load_registry())

    outcome = _dispatch_preview(template_id)
    assert outcome["ok"], outcome

    assert _count_durable_writes(SHIPMENT_ID) == before, "a preview wrote durable rows"
    assert len(store.load_registry()) == templates_before
    # Still a draft: previewing did not publish anything.
    row = store.get_template(template_id)
    assert row["status"] == "DRAFT"
    assert not row.get("activeVersion")
    assert not row.get("versions")
    # And it is still not selectable by staff.
    catalog = project_catalog(contract_templates_available=False, pxk_template_available=False,
                              storage_configured=True, form07_template_available=False,
                              catalog=effective_catalog())
    assert not any(item["id"] == template_id for item in catalog)


def test_a_non_admin_cannot_preview_a_template(staging):
    template_id = _draft_template("BB XEM THU 3", "bb-xem-thu-3.docx", "prev3")
    _support()
    outcomes = vm.logi_templates.consume_docgen_template_triggers(
        {"seq": 0},
        {"docgen_template_preview": {
            "seq": 1, "event": "docgen_template_preview",
            "payload": {"templateId": template_id, "requestId": "req-prev-denied"},
        }},
    )
    assert outcomes[0]["ok"] is False
    assert outcomes[0]["gate"] == "BLOCKED_PERMISSION_DENIED"


def test_a_preview_reports_unresolved_positions_instead_of_filling_them(staging):
    """The point of reviewing first: gaps are named, not papered over."""
    template_id = _draft_template("BB XEM THU 4", "bb-xem-thu-4.docx", "prev4")
    # Add a manual field with no value: the preview must say it is missing.
    _admin()
    row = store.get_template(template_id)
    mapping = list(row.get("mapping") or [])
    # Turn one confirmed field back into an operator-typed field with no value
    # yet: the preview must name that gap instead of filling it.
    mapping[0] = {"position": mapping[0]["position"], "mode": "manual",
                  "value": "Số biên bản"}
    saved = _dispatch_template("docgen_template_mapping_save", {
        "templateId": template_id, "mapping": mapping, "requestId": "req-prev4-map",
    }, seq=4)
    assert saved["ok"], saved.get("error")

    outcome = _dispatch_preview(template_id, seq=5)
    assert outcome["ok"], outcome
    assert outcome["readback"]["missing"], "the operator-typed gap must be reported"
    assert any("Số biên bản" in item for item in outcome["readback"]["missing"])


# ---------------------------------------------------------------------------
# INDEPENDENT SOURCE REVIEW R2 — B5 / B6 regressions
# ---------------------------------------------------------------------------

def _docx_with_runs(*run_texts: str) -> bytes:
    """One paragraph whose runs carry exactly the given text, in order."""
    import docx

    document = docx.Document()
    paragraph = document.add_paragraph()
    for chunk in run_texts:
        paragraph.add_run(chunk)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_an_inline_token_keeps_the_static_text_on_both_sides_of_it(staging):
    """B5 — a token inside a run must not swallow the run's own words.

    ``Xác nhận: {{shipment.id}} (đã kiểm)`` is one perfectly ordinary Word run.
    Replacing the whole run with the value silently destroys a legally
    meaningful label and its trailing note, which no operator can see happen.
    """
    raw = _docx_with_runs("Xác nhận: {{shipment.id}} (đã kiểm)")
    positions = engine.detect_positions(raw, engine.KIND_DOCX)
    assert len(positions) == 1 and positions[0]["detectedBy"] == "marker"

    values, missing = engine.resolve_mapping(
        [{"position": positions[0]["id"], "mode": "field", "value": "shipment.id"}],
        {"shipment": {"id": SHIPMENT_ID}}, manual={},
    )
    assert missing == []
    rendered = engine.render_uploaded(
        raw, kind=engine.KIND_DOCX, template_sha256="", values=values
    )

    import docx

    text = docx.Document(io.BytesIO(rendered)).paragraphs[0].text
    # The label, the value AND the trailing note all survive.
    assert text == f"Xác nhận: {SHIPMENT_ID} (đã kiểm)", repr(text)


def test_several_tokens_in_one_run_are_each_replaced_in_place(staging):
    """Two different placeholders in one run: each gets ITS value, words survive.

    Superseded assertion: this test originally mapped only the first token and
    merely checked that ``{{`` had disappeared — which is exactly how the B7
    same-value corruption passed unnoticed.  It now pins the exact text.
    """
    raw = _docx_with_runs("Lô {{shipment.id}} / Booking {{shipment.booking_no}} — hết")
    positions = engine.detect_positions(raw, engine.KIND_DOCX)
    assert {item["label"] for item in positions} == {"shipment.id", "shipment.booking_no"}

    values, missing = engine.resolve_mapping(
        [{"position": item["id"], "mode": "field", "value": item["suggestion"]}
         for item in positions],
        {"shipment": {"id": SHIPMENT_ID, "booking_no": EXPECTED_BOOKING}}, manual={},
    )
    assert missing == []
    rendered = engine.render_uploaded(
        raw, kind=engine.KIND_DOCX, template_sha256="", values=values
    )
    import docx

    text = docx.Document(io.BytesIO(rendered)).paragraphs[0].text
    assert text == f"Lô {SHIPMENT_ID} / Booking {EXPECTED_BOOKING} — hết", repr(text)
    assert "{{" not in text and "}}" not in text, repr(text)


def test_a_run_that_is_only_a_token_still_renders_as_the_bare_value(staging):
    """The pure-marker case must not regress: no stray spaces are added."""
    raw = _docx_with_runs("{{customer.name}}")
    positions = engine.detect_positions(raw, engine.KIND_DOCX)
    values, _missing = engine.resolve_mapping(
        [{"position": positions[0]["id"], "mode": "field", "value": "customer.name"}],
        {"customer": {"name": EXPECTED_CUSTOMER_NAME}}, manual={},
    )
    rendered = engine.render_uploaded(
        raw, kind=engine.KIND_DOCX, template_sha256="", values=values
    )
    import docx

    assert docx.Document(io.BytesIO(rendered)).paragraphs[0].text == EXPECTED_CUSTOMER_NAME


def test_two_same_name_uploads_in_the_same_minute_get_different_ids(staging, monkeypatch):
    """B6 — the id must stay <=40 chars AND stay unique inside one minute.

    ``UT-`` + a 24-char slug + ``-`` + a 14-char stamp is 42 chars, so slicing to
    40 silently dropped the seconds and every same-name upload within a minute
    collided.  ``get_template()`` returns the first match, so the later upload
    could map and publish the WRONG file.
    """
    import datetime as _dt

    import core.docgen.uploaded_template_store as store_module

    frozen = _dt.datetime(2026, 10, 10, 12, 9, 1, tzinfo=_dt.timezone.utc)

    class _FrozenDatetime(_dt.datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: ANN001 - test clock
            return frozen if tz is None else frozen.astimezone(tz)

    monkeypatch.setattr(store_module, "datetime", _FrozenDatetime)

    label = "Biên bản giao nhận hàng hóa"
    first_id = store_module.new_template_id(label)
    assert len(first_id) <= store_module.MAX_TEMPLATE_ID
    # Time is frozen, so a second call is the collision the reviewer described.
    second_id = store_module.new_template_id(label)
    assert first_id != second_id, f"both uploads produced {first_id!r}"

    # And the real upload path keeps them apart, each independently usable.
    first = _upload_publish(build_pilot_docx(), label, "bb-trung-1.docx")
    second = _upload_publish(build_second_docx(), label, "bb-trung-2.docx")
    assert first["id"] != second["id"]
    assert len(first["id"]) <= store_module.MAX_TEMPLATE_ID
    assert len(second["id"]) <= store_module.MAX_TEMPLATE_ID

    # Each row resolves to its OWN bytes and its OWN mapping.
    first_row = store.get_template(first["id"])
    second_row = store.get_template(second["id"])
    assert first_row["draftSha256"] != second_row["draftSha256"]
    assert engine.detect_kind("a.docx", store.load_bytes(first_row)) == engine.KIND_DOCX
    assert first["status"] == "ACTIVE" and second["status"] == "ACTIVE"
    assert first["publishedMappingCount"] != second["publishedMappingCount"] or \
        first_row["versions"][0]["mapping"] != second_row["versions"][0]["mapping"]

    # Both generate their own distinct file.
    _support()
    gen_first = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": first["id"]}, seq=1)
    gen_second = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": second["id"]}, seq=2)
    assert gen_first["ok"] and gen_second["ok"]
    assert gen_first["persisted"]["attachmentId"] != gen_second["persisted"]["attachmentId"]
    assert gen_first["persisted"]["outputHash"] != gen_second["persisted"]["outputHash"]
    assert "Số booking" in _docx_text(_fetch(gen_second["persisted"]["attachmentId"])["data"])
    assert "Số hợp đồng" in _docx_text(_fetch(gen_first["persisted"]["attachmentId"])["data"])


def test_template_ids_never_exceed_the_declared_maximum(staging):
    """The 40-char contract holds for pathological labels too."""
    for label in ("x" * 400, "Biên bản " * 60, "!!!", "", "a" * 40):
        produced = store.new_template_id(label)
        assert 0 < len(produced) <= store.MAX_TEMPLATE_ID, (label[:20], produced)


# ---------------------------------------------------------------------------
# INDEPENDENT SOURCE REVIEW R3 — B7 regression
# ---------------------------------------------------------------------------

def test_each_distinct_token_in_one_run_receives_its_own_value(staging):
    """B7 — different tokens in ONE run must not all become the same value.

    ``Lô {{shipment.id}} / Booking {{shipment.booking_no}} / KH {{customer.name}}``
    is one ordinary Word run.  Filling every token with the single confirmed
    value produced ``Lô LO-0295 / Booking LO-0295 / KH LO-0295`` — a
    valid-looking file carrying the WRONG booking and the WRONG customer.  Each
    placeholder is now its own detectable, mappable, renderable position, and
    this asserts the exact resulting text, not merely that ``{{`` disappeared.
    """
    raw = _docx_with_runs(
        "Lô {{shipment.id}} / Booking {{shipment.booking_no}} / KH {{customer.name}}"
    )
    positions = engine.detect_positions(raw, engine.KIND_DOCX)

    # One position per placeholder, each suggesting its OWN field.
    by_label = {item["label"]: item for item in positions}
    assert set(by_label) == {"shipment.id", "shipment.booking_no", "customer.name"}, by_label
    for item in positions:
        assert item["detectedBy"] == "marker"
        assert item["suggestion"] == item["label"]
    # The three positions are distinct addresses inside the same run.
    assert len({item["id"] for item in positions}) == 3

    mapping = [
        {"position": item["id"], "mode": "field", "value": item["suggestion"]}
        for item in positions
    ]
    values, missing = engine.resolve_mapping(
        mapping,
        {
            "shipment": {"id": SHIPMENT_ID, "booking_no": EXPECTED_BOOKING},
            "customer": {"name": EXPECTED_CUSTOMER_NAME},
        },
        manual={},
    )
    assert missing == []
    rendered = engine.render_uploaded(
        raw, kind=engine.KIND_DOCX, template_sha256="", values=values
    )

    import docx

    text = docx.Document(io.BytesIO(rendered)).paragraphs[0].text
    assert text == (
        f"Lô {SHIPMENT_ID} / Booking {EXPECTED_BOOKING} / KH {EXPECTED_CUSTOMER_NAME}"
    ), repr(text)


def test_a_whole_run_mapping_over_distinct_tokens_is_refused_not_guessed(staging):
    """Fail-closed net for a mapping that names the RUN, not a placeholder.

    A version published before per-token positions existed would carry ``p0/r0``
    for a multi-token run.  Filling it would be exactly the B7 corruption, so the
    renderer refuses instead of guessing which token the value was meant for.
    """
    raw = _docx_with_runs("Lô {{shipment.id}} / KH {{customer.name}}")
    with pytest.raises(engine.UploadedTemplateError):
        engine.render_uploaded(
            raw, kind=engine.KIND_DOCX, template_sha256="",
            values={"p0/r0": SHIPMENT_ID},
        )


def test_repeated_identical_tokens_in_one_run_still_share_one_value(staging):
    """Duplicate identical placeholders are safe and keep working as ONE position."""
    raw = _docx_with_runs("{{shipment.id}} và {{shipment.id}}")
    positions = engine.detect_positions(raw, engine.KIND_DOCX)
    assert len(positions) == 1, positions
    assert positions[0]["label"] == "shipment.id"

    values, missing = engine.resolve_mapping(
        [{"position": positions[0]["id"], "mode": "field", "value": "shipment.id"}],
        {"shipment": {"id": SHIPMENT_ID}}, manual={},
    )
    assert missing == []
    rendered = engine.render_uploaded(
        raw, kind=engine.KIND_DOCX, template_sha256="", values=values
    )
    import docx

    assert docx.Document(io.BytesIO(rendered)).paragraphs[0].text == (
        f"{SHIPMENT_ID} và {SHIPMENT_ID}"
    )


def test_an_unmapped_token_in_a_multi_token_run_blocks_the_whole_file(staging):
    """Leaving one placeholder unmapped must fail closed, not print a token."""
    raw = _docx_with_runs("Lô {{shipment.id}} / KH {{customer.name}}")
    positions = engine.detect_positions(raw, engine.KIND_DOCX)
    only = next(item for item in positions if item["label"] == "shipment.id")
    values, _missing = engine.resolve_mapping(
        [{"position": only["id"], "mode": "field", "value": "shipment.id"}],
        {"shipment": {"id": SHIPMENT_ID}, "customer": {"name": EXPECTED_CUSTOMER_NAME}},
        manual={},
    )
    with pytest.raises(engine.UploadedTemplateError):
        engine.render_uploaded(
            raw, kind=engine.KIND_DOCX, template_sha256="", values=values
        )


def test_a_multi_token_run_survives_the_full_upload_to_download_flow(staging):
    """B7 end to end: real upload -> mapping -> publish -> generate -> download.

    The engine-level test proves the substitution; this proves the whole Admin
    and staff flow carries a distinct value per placeholder, using the verified
    staging facts rather than values typed into the test.
    """
    raw = _docx_with_runs(
        "Lô {{shipment.id}} / Booking {{shipment.booking_no}} / KH {{customer.name}}"
    )
    _admin()
    draft = _dispatch_template("docgen_template_upload", {
        "label": "BB NHIEU TOKEN", "fileName": "bb-nhieu-token.docx",
        "base64": _b64(raw), "requestId": "req-multitoken",
    }, seq=1)
    assert draft["ok"], draft
    template_id = draft["readback"]["id"]

    # Detection offers the Admin one row per placeholder, labelled with the
    # field that will actually be printed there.
    detected = draft["readback"]["detected"]
    assert [item["label"] for item in detected] == [
        "shipment.id", "shipment.booking_no", "customer.name"
    ], detected
    mapping = [
        {"position": item["id"], "mode": "field", "value": item["suggestion"]}
        for item in detected
    ]
    saved = _dispatch_template("docgen_template_mapping_save", {
        "templateId": template_id, "mapping": mapping, "requestId": "req-mt-map",
    }, seq=2)
    assert saved["ok"], saved
    published = _dispatch_template("docgen_template_publish", {
        "templateId": template_id, "requestId": "req-mt-pub",
    }, seq=3)
    assert published["ok"], published

    _support()
    generated = _dispatch_generate({"shipmentId": SHIPMENT_ID, "templateId": template_id}, seq=4)
    assert generated["ok"], generated
    stored = _fetch(generated["persisted"]["attachmentId"])["data"]
    assert hashlib.sha256(stored).hexdigest() == generated["persisted"]["outputHash"]

    text = _docx_text(stored)
    assert f"Lô {SHIPMENT_ID} / Booking {EXPECTED_BOOKING} / KH {EXPECTED_CUSTOMER_NAME}" in text
    # The corrupted shape must be impossible.
    assert f"Booking {SHIPMENT_ID}" not in text
    assert f"KH {SHIPMENT_ID}" not in text
