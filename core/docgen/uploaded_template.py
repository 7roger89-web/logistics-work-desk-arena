"""LOGI-193 — Admin-uploaded Office templates (one narrow component).

This module is the ONLY new engine Issue #193 adds.  It turns ONE ordinary
DOCX or XLSX file, uploaded by an Admin at runtime, into a template the
shipment document picker can already dispatch — without adding a code-owned
template family per document (the FORM_07 shape in ``core.docgen.form07``)
and without adding a second document store.

Bounded by design, in the same spirit as the rest of ``core.docgen``:

  * **Detection, not magic.**  ``detect_positions`` reports the *positions* it
    can see (explicit ``{{token}}`` markers, underscore blanks, label → empty
    neighbour) plus a keyword *suggestion*.  An arbitrary unmarked Office file
    is NOT mapped perfectly and is never claimed to be: an Admin confirms or
    refines the mapping ONCE and that confirmed mapping is what generation
    uses.
  * **Whitelist only.**  A mapping entry may bind a position to ONE key of
    :data:`CANONICAL_FIELDS`, to an operator-typed ``manual`` value, or to an
    Admin-typed ``static`` literal.  Anything else — a raw Mongo path, an
    expression, a Jinja/``${}`` construct, an unknown key — is refused.
    There is no formula engine and no expression evaluation here.
  * **Exact facts only.**  Canonical bindings read verified truth (authority
    Company master, customer master, canonical shipment blocks, the single
    linked contract, its single goods line).  Money, prices, VAT, payment
    terms, bank details and multi-line goods are NOT canonical fields at all,
    so they can only be operator-typed manual values.  UNKNOWN never becomes
    zero, today() or a guess: an unresolved mapping fails closed through the
    existing :class:`core.docgen.rules.Readiness`.
  * **Non-destructive render.**  Only the mapped runs/cells are written;
    every other ZIP part is copied byte-for-byte, so styles, merged cells,
    number formats, sheets, headers, footers and print setup survive.  Output
    is repacked with fixed ZIP dates so one input snapshot always yields one
    output SHA-256 (auditable ``output_hash``).
  * **Uploaded bytes never execute.**  No ``docxtpl``/Jinja, no macro/OLE/DDE
    part, no external relationship, no embedded object is accepted or
    re-emitted; the generated file is re-scanned before it is returned.

It owns no storage: persistence lives in ``core.docgen.uploaded_template_store``
over the app's existing ``app_settings`` + GridFS plane.
"""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from core.docgen.rules import MISSING_INFO, READY, Readiness

UPLOADED_ADAPTER = "UPLOADED_DOCGEN"
UPLOADED_DOCUMENT_TYPE = "UPLOADED_TEMPLATE"

KIND_DOCX = "DOCX"
KIND_XLSX = "XLSX"

MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

#: Hard upload ceiling for a template.  A real Office form is tens of KB; this
#: is a generous bound, not a tuning knob.
MAX_TEMPLATE_BYTES = 5 * 1024 * 1024
#: Zip-bomb guard: refuse an archive whose uncompressed parts explode.
MAX_UNCOMPRESSED_BYTES = 40 * 1024 * 1024
MAX_UNCOMPRESSED_RATIO = 100.0
MAX_PARTS = 500
#: Detection/render bound so one hostile sheet cannot produce unbounded work.
MAX_POSITIONS = 200
MAX_MAPPINGS = 200
MAX_SHEET_NAME = 128
MAX_CELL_COORD = 16
MAX_STATIC_TEXT = 500
MAX_LABEL_TEXT = 120

#: ZIP entries are repacked with this fixed date so identical inputs always
#: produce byte-identical output (auditable ``output_hash``).
_FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)

_SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_NS = {"x": _SHEET_NS}

# Same banned-part / banned-markup family FORM_07 already enforces, plus the
# spreadsheet-specific macro part.  Namespace URIs inside a ``.rels`` file are
# NOT relationships to remote content; only an external Target is.
# ``customXml/`` is deliberately NOT banned: it is inert document-property data
# present in ordinary Word files, it is never interpreted here and generation
# copies it byte-for-byte.  ``mc:AlternateContent`` is likewise ordinary
# drawing-fallback markup; the payloads that actually matter (OLE objects,
# macros, field instructions, external targets) are banned by name below.
_BANNED_PART_PATTERN = re.compile(
    r"vbaProject|activeX|embeddings|comments\d*\.xml|people\.xml|externalLinks"
    r"|oleObject|macroSheet|dialogSheet",
    re.IGNORECASE,
)
# NOTE: no bare ``DDE`` token — it matches ordinary hex theme colours such as
# ``w:fill="B6DDE8"``.  Real DDE abuse is a DDEAUTO/DDEDATA field instruction
# or a DDE ProgID, and ``instrText``/``fldSimple``/``o:OLEObject`` are already
# banned above it.
_BANNED_XML_PATTERN = re.compile(
    r"<w:ins[ >]|<w:del[ >]|instrText|fldSimple|w:attachedTemplate"
    r"|DDEAUTO|DDEDATA|ProgID=\"DDE|o:OLEObject|<w:subDoc"
)
_MARKER_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_.]{1,64})\s*\}\}")
_BLANK_RUN_PATTERN = re.compile(r"^[\s_.\-–—·]{2,}$")
# An ordinary Word line is often ONE run: "Số hợp đồng: ________".  The printed
# label is kept and only the blank tail is filled.
_INLINE_BLANK_PATTERN = re.compile(r"^(?P<label>.*?[:：])[ \t]*(?P<blank>[_\-.–—·\s]{2,})$")
_CELL_COORD_PATTERN = re.compile(r"^([A-Z]{1,3})([1-9][0-9]{0,6})$")

# Anything an operator could mistake for an executable construct inside a
# mapping payload.  Refused rather than interpreted.
_FORBIDDEN_VALUE_PATTERN = re.compile(r"[{}$<>&]|__|\.\.|jinja|eval|exec|import", re.IGNORECASE)


class UploadedTemplateError(RuntimeError):
    """The uploaded template is unusable, unsafe or drifted."""


@dataclass(frozen=True)
class CanonicalField:
    """ONE verified fact an uploaded template may be bound to."""

    key: str
    label: str
    group: str
    #: Facts that only exist once an unambiguous single source is proven.
    conditional: bool = False
    hint: str = ""


# ---------------------------------------------------------------------------
# The canonical field whitelist (the ONLY auto-fillable facts)
# ---------------------------------------------------------------------------
#
# Deliberately absent on purpose: every money/price/VAT/total/currency field,
# every payment term and bank detail, and every multi-line goods fact.  They
# are not "ambiguous fields we handle carefully" — they are not bindable at
# all, so an uploaded template can only print them from an operator-typed
# manual value.  That is what makes "never invent financial facts" structural
# instead of a review habit.
CANONICAL_FIELDS: tuple[CanonicalField, ...] = (
    # --- Legal Company master (authority_companies, the Owner's own entity) ---
    CanonicalField("company.legal_name", "Tên pháp lý công ty", "Công ty"),
    CanonicalField("company.legal_address", "Địa chỉ pháp lý công ty", "Công ty"),
    CanonicalField("company.phone", "Điện thoại công ty", "Công ty"),
    CanonicalField("company.tax_code", "Mã số thuế công ty", "Công ty"),
    CanonicalField("company.legal_representative", "Người đại diện công ty", "Công ty"),
    CanonicalField("company.representative_title", "Chức vụ người đại diện công ty", "Công ty"),
    # --- Customer master ---
    CanonicalField("customer.name", "Tên khách hàng", "Khách hàng"),
    CanonicalField("customer.address", "Địa chỉ khách hàng", "Khách hàng"),
    CanonicalField("customer.phone", "Điện thoại khách hàng", "Khách hàng"),
    CanonicalField("customer.tax_code", "Mã số thuế khách hàng", "Khách hàng"),
    CanonicalField("customer.email", "Email khách hàng", "Khách hàng"),
    CanonicalField("customer.contact_person", "Người liên hệ khách hàng", "Khách hàng"),
    # --- Canonical shipment blocks (data.0.0 / 1.2 / 2.4 / 2.6 / 2.7) ---
    CanonicalField("shipment.id", "Mã lô hàng", "Lô hàng"),
    CanonicalField("shipment.status", "Trạng thái lô hàng", "Lô hàng"),
    CanonicalField("shipment.created_at", "Ngày tạo lô", "Lô hàng"),
    CanonicalField("shipment.mode", "Phương thức vận chuyển", "Lô hàng"),
    CanonicalField("shipment.incoterm", "Incoterms", "Lô hàng"),
    CanonicalField("shipment.booking_no", "Số booking", "Lô hàng"),
    CanonicalField("shipment.carrier", "Hãng vận chuyển", "Lô hàng"),
    CanonicalField("shipment.mbl", "Số vận đơn (MBL)", "Lô hàng"),
    CanonicalField("shipment.hbl", "Số vận đơn (HBL)", "Lô hàng"),
    CanonicalField("shipment.vessel", "Tên tàu", "Lô hàng"),
    CanonicalField("shipment.etd", "Ngày khởi hành (ETD)", "Lô hàng"),
    CanonicalField("shipment.pol", "Cảng đi (POL)", "Lô hàng"),
    CanonicalField("shipment.pod", "Cảng đến (POD)", "Lô hàng"),
    CanonicalField("shipment.container_no", "Số container", "Lô hàng"),
    CanonicalField("shipment.qty_pkg", "Số kiện", "Lô hàng"),
    CanonicalField("shipment.pickup_truck_type", "Loại xe lấy hàng", "Lô hàng"),
    CanonicalField("shipment.tk_no", "Số tờ khai hải quan", "Hải quan"),
    CanonicalField("shipment.tk_date", "Ngày tờ khai hải quan", "Hải quan"),
    CanonicalField("shipment.customs_status", "Trạng thái thông quan", "Hải quan"),
    CanonicalField("shipment.arrival_date", "Ngày hàng về", "Hải quan"),
    CanonicalField("shipment.free_time", "Thời gian miễn lưu (free time)", "Hải quan"),
    # --- Canonical 2.7 delivery facts (the same truth PXK/FORM_07 print) ---
    CanonicalField("delivery.delivered_at", "Ngày giao hàng thực tế", "Giao hàng"),
    CanonicalField("delivery.delivery_location", "Địa điểm nhận hàng thực tế", "Giao hàng"),
    CanonicalField("delivery.receiver_name", "Người nhận hàng", "Giao hàng"),
    CanonicalField("delivery.receiver_title", "Chức vụ người nhận", "Giao hàng"),
    CanonicalField("delivery.receiver_phone", "Điện thoại người nhận", "Giao hàng"),
    CanonicalField("delivery.truck_no", "Biển số xe giao hàng", "Giao hàng"),
    CanonicalField("delivery.seal_no", "Số seal", "Giao hàng"),
    # --- The single linked contract (identity only, never money) ---
    CanonicalField("contract.contract_no", "Số hợp đồng", "Hợp đồng", conditional=True),
    CanonicalField("contract.contract_date", "Ngày hợp đồng", "Hợp đồng", conditional=True),
    # --- The single goods line of that contract (no money by construction) ---
    CanonicalField("goods.description", "Tên hàng hóa (dòng duy nhất)", "Hàng hóa", conditional=True),
    CanonicalField("goods.specification", "Quy cách (dòng duy nhất)", "Hàng hóa", conditional=True),
    CanonicalField("goods.unit", "Đơn vị tính (dòng duy nhất)", "Hàng hóa", conditional=True),
    CanonicalField("goods.quantity", "Số lượng (dòng duy nhất)", "Hàng hóa", conditional=True),
)

CANONICAL_FIELD_KEYS: frozenset[str] = frozenset(field.key for field in CANONICAL_FIELDS)
CANONICAL_FIELDS_BY_KEY: dict[str, CanonicalField] = {field.key: field for field in CANONICAL_FIELDS}

#: Conditional facts need an unambiguous single source; without it they are
#: MISSING, never a guess.  The reason is surfaced verbatim to the operator.
_CONDITIONAL_REASON = {
    "contract": "Cần đúng một hợp đồng liên kết với lô.",
    "goods": "Cần đúng một hợp đồng và đúng một dòng hàng hóa trên hợp đồng đó.",
}

# Keyword → canonical field, longest phrase first so "mã số thuế công ty" wins
# over "công ty".  A miss yields no suggestion (the Admin picks manually); a
# suggestion is never an assignment.
_LABEL_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("mã số thuế công ty", "company.tax_code"),
    ("mst công ty", "company.tax_code"),
    ("địa chỉ công ty", "company.legal_address"),
    ("địa chỉ cty", "company.legal_address"),
    ("điện thoại công ty", "company.phone"),
    ("người đại diện", "company.legal_representative"),
    ("tên công ty", "company.legal_name"),
    ("công ty tnhh", "company.legal_name"),
    ("mã số thuế khách hàng", "customer.tax_code"),
    ("mst khách hàng", "customer.tax_code"),
    ("địa chỉ khách hàng", "customer.address"),
    ("điện thoại khách hàng", "customer.phone"),
    ("khách hàng", "customer.name"),
    ("người liên hệ", "customer.contact_person"),
    ("mã lô", "shipment.id"),
    ("số lô", "shipment.id"),
    ("lô hàng", "shipment.id"),
    ("booking", "shipment.booking_no"),
    ("hãng tàu", "shipment.carrier"),
    ("người vận chuyển", "shipment.carrier"),
    ("tên tàu", "shipment.vessel"),
    ("số tàu", "shipment.vessel"),
    ("cảng đi", "shipment.pol"),
    ("cảng xếp", "shipment.pol"),
    ("cảng đến", "shipment.pod"),
    ("cảng dỡ", "shipment.pod"),
    ("container", "shipment.container_no"),
    ("số cont", "shipment.container_no"),
    ("số seal", "delivery.seal_no"),
    ("vận đơn", "shipment.mbl"),
    ("bill of lading", "shipment.mbl"),
    ("ngày khởi hành", "shipment.etd"),
    ("số tờ khai", "shipment.tk_no"),
    ("ngày tờ khai", "shipment.tk_date"),
    ("trạng thái thông quan", "shipment.customs_status"),
    ("ngày hàng về", "shipment.arrival_date"),
    ("free time", "shipment.free_time"),
    ("số kiện", "shipment.qty_pkg"),
    ("loại xe lấy hàng", "shipment.pickup_truck_type"),
    ("số xe", "delivery.truck_no"),
    ("biển số xe", "delivery.truck_no"),
    ("chức vụ người nhận", "delivery.receiver_title"),
    ("chức vụ", "delivery.receiver_title"),
    ("người nhận hàng", "delivery.receiver_name"),
    ("người nhận", "delivery.receiver_name"),
    ("điện thoại người nhận", "delivery.receiver_phone"),
    ("địa điểm giao", "delivery.delivery_location"),
    ("địa điểm nhận", "delivery.delivery_location"),
    ("nơi giao hàng", "delivery.delivery_location"),
    ("ngày giao hàng", "delivery.delivered_at"),
    ("ngày giao", "delivery.delivered_at"),
    ("số hợp đồng", "contract.contract_no"),
    ("ngày hợp đồng", "contract.contract_date"),
    ("tên hàng", "goods.description"),
    ("hàng hóa", "goods.description"),
    ("quy cách", "goods.specification"),
    ("đơn vị tính", "goods.unit"),
    ("đvt", "goods.unit"),
    ("số lượng", "goods.quantity"),
)


def _text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def field_catalog_projection() -> list[dict[str, Any]]:
    """Server-owned field list for the mapping editor (no client-side copy)."""
    return [
        {
            "key": field.key,
            "label": field.label,
            "group": field.group,
            "conditional": bool(field.conditional),
            "hint": field.hint,
        }
        for field in CANONICAL_FIELDS
    ]


def suggest_field(text: str) -> str:
    """Best-effort canonical field for a Vietnamese label; "" when unsure."""
    needle = _text(text).lower()
    if not needle:
        return ""
    for phrase, key in _LABEL_KEYWORDS:
        if phrase in needle:
            return key
    return ""


# ---------------------------------------------------------------------------
# Upload validation + bounded OOXML safety scan
# ---------------------------------------------------------------------------

def _column_letters_to_index(letters: str) -> int:
    value = 0
    for char in letters:
        value = value * 26 + (ord(char) - ord("A") + 1)
    return value


def _index_to_column_letters(index: int) -> str:
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def detect_kind(file_name: str, data: bytes) -> str:
    """Return ``DOCX``/``XLSX`` or raise; legacy .doc/.xls are refused."""
    name = _text(file_name).lower()
    if name.endswith((".doc", ".xls")):
        raise UploadedTemplateError(
            "Định dạng .doc/.xls cũ không được hỗ trợ; hãy lưu lại thành .docx/.xlsx."
        )
    if name.endswith((".docm", ".dotm", ".xlsm", ".xltm")):
        raise UploadedTemplateError("Tệp có macro (.docm/.dotm/.xlsm/.xltm) bị từ chối.")
    if not name.endswith((".docx", ".xlsx")):
        raise UploadedTemplateError("Chỉ chấp nhận tệp .docx hoặc .xlsx.")
    if len(data) > MAX_TEMPLATE_BYTES:
        raise UploadedTemplateError(
            f"Tệp vượt quá {MAX_TEMPLATE_BYTES // (1024 * 1024)} MB; không có gì được lưu."
        )
    if not data or data[:2] != b"PK":
        raise UploadedTemplateError("Tệp không phải OOXML (thiếu chữ ký ZIP).")

    try:
        names = set(zipfile.ZipFile(io.BytesIO(data)).namelist())
    except zipfile.BadZipFile as exc:
        raise UploadedTemplateError("Tệp OOXML hỏng, không đọc được.") from exc

    if name.endswith(".docx"):
        if "word/document.xml" not in names:
            raise UploadedTemplateError("Tệp .docx thiếu word/document.xml.")
        return KIND_DOCX
    if "xl/workbook.xml" not in names:
        raise UploadedTemplateError("Tệp .xlsx thiếu xl/workbook.xml.")
    return KIND_XLSX


_EXTERNAL_SCHEMES = ("http:", "https:", "file:", "ftp:", "mailto:", "\\\\")


def _external_relationship_parts(payload: str) -> list[str]:
    """Parse a .rels part as XML and report every external relationship.

    A regex over the serialised text can be dodged by anything XML allows but
    the pattern did not enumerate — single-quoted attributes, reordered
    attributes, unusual whitespace, entity-encoded values.  Parsing removes the
    whole class: the parser normalises quoting and whitespace, so the check is
    on the *value*, not on how it was written.

    A part that does not parse is reported, never silently passed.
    """
    import xml.etree.ElementTree as ET

    problems: list[str] = []
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        return [f"unparseable relationships xml ({exc})"]
    for rel in root.iter():
        if not rel.tag.endswith("Relationship"):
            continue
        attribs = rel.attrib
        mode = _text(attribs.get("TargetMode")).strip().lower()
        target = _text(attribs.get("Target")).strip()
        if mode == "external":
            problems.append(f"TargetMode=External -> {target[:120]!r}")
            continue
        # No TargetMode at all must still not smuggle an absolute/external URI.
        lowered = target.lower()
        if any(lowered.startswith(scheme) for scheme in _EXTERNAL_SCHEMES):
            problems.append(f"external target scheme -> {target[:120]!r}")
    return problems


def scan_package_safety(raw: bytes) -> dict[str, Any]:
    """Bounded OPC safety scan for an uploaded template OR a generated file.

    Order matters.  Everything here that can be answered from the ZIP CENTRAL
    DIRECTORY runs before a single member is inflated, because ``testzip()``
    and ``read()`` both fully decompress — calling them first would hand a zip
    bomb the memory it is trying to deny.  Only after the part-count,
    uncompressed-size and compression-ratio limits pass does anything read
    member bytes.
    """
    findings: dict[str, Any] = {"ok": True, "issues": []}
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        findings.update(ok=False, issues=["not a valid OOXML ZIP"])
        return findings

    # --- Phase 1: central-directory-only limits. No member is decompressed. ---
    try:
        infos = archive.infolist()
    except (zipfile.BadZipFile, NotImplementedError) as exc:
        findings.update(ok=False, issues=[f"unreadable central directory: {exc}"])
        return findings

    names = [info.filename for info in infos]
    findings["part_count"] = len(names)
    if len(names) > MAX_PARTS:
        findings["issues"].append(f"too many parts ({len(names)})")

    total = 0
    ratio_offenders: list[str] = []
    for info in infos:
        total += int(info.file_size or 0)
        compressed = int(info.compress_size or 0)
        if info.file_size and compressed:
            if info.file_size / max(compressed, 1) > MAX_UNCOMPRESSED_RATIO:
                ratio_offenders.append(info.filename)
    if ratio_offenders:
        findings["issues"].append(
            "suspicious compression ratio: " + ", ".join(ratio_offenders[:5])
        )
    findings["uncompressed_bytes"] = total
    if total > MAX_UNCOMPRESSED_BYTES:
        findings["issues"].append(f"uncompressed size too large ({total})")

    # A RESOURCE limit failing is what must short-circuit: continuing would mean
    # inflating members of a package that has already proven unbounded.
    if findings["issues"]:
        findings["ok"] = False
        return findings

    # Part-NAME checks are free (no decompression), so they are reported
    # alongside the content scan rather than instead of it — a trojan carrying
    # both a macro part and an external relationship must report both.
    banned_parts = [name for name in names if _BANNED_PART_PATTERN.search(name)]
    if banned_parts:
        findings["issues"].append(f"banned parts: {banned_parts}")
    if any(n.lower().endswith((".docm", ".dotm", ".xlsm", ".xltm")) for n in names):
        findings["issues"].append("macro-enabled part name")

    # --- Phase 2: the package is bounded, so reading members is now safe. ---
    if archive.testzip() is not None:
        findings.update(ok=False, issues=["ZIP corrupt"])
        return findings

    for name in names:
        if not name.endswith((".xml", ".rels")):
            continue
        try:
            payload = archive.read(name).decode("utf-8", errors="ignore")
        except KeyError:  # pragma: no cover - defensive
            continue
        match = _BANNED_XML_PATTERN.search(payload)
        if match:
            findings["issues"].append(f"{name}: banned markup {match.group(0)!r}")

    for name in names:
        if not name.endswith(".rels"):
            continue
        try:
            payload = archive.read(name).decode("utf-8", errors="ignore")
        except KeyError:  # pragma: no cover - defensive
            continue
        for problem in _external_relationship_parts(payload):
            findings["issues"].append(f"{name}: external relationship ({problem})")

    findings["ok"] = not findings["issues"]
    return findings


def validate_uploaded_template(file_name: str, data: bytes) -> dict[str, Any]:
    """Refuse-before-store gate: kind, size, structure, safety scan, SHA-256."""
    kind = detect_kind(file_name, data)
    scan = scan_package_safety(data)
    if not scan["ok"]:
        raise UploadedTemplateError("Tệp không qua kiểm tra an toàn: " + "; ".join(scan["issues"]))
    return {
        "kind": kind,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
        "part_count": int(scan.get("part_count") or 0),
        "mime": MIME_DOCX if kind == KIND_DOCX else MIME_XLSX,
    }


# ---------------------------------------------------------------------------
# Position detection
# ---------------------------------------------------------------------------

def _label_before(text: str) -> str:
    """The label part of a paragraph/cell string (before ':' or a blank run)."""
    head = re.split(r"[:：]", text, maxsplit=1)[0]
    return _text(head)[:MAX_LABEL_TEXT]


def _parse_docx_positions(raw: bytes) -> list[dict[str, Any]]:
    """Body paragraphs + table cells; marker tokens, blanks and label→gap."""
    import docx

    document = docx.Document(io.BytesIO(raw))
    positions: list[dict[str, Any]] = []

    def add_paragraph_runs(paragraphs: list[Any], *, table: int | None, row: int | None, col: int | None) -> None:
        for para_index, paragraph in enumerate(paragraphs):
            runs = list(paragraph.runs)
            full_text = "".join(run.text or "" for run in runs)
            for run_index, run in enumerate(runs):
                if len(positions) >= MAX_POSITIONS:
                    return
                current = run.text or ""
                position_id = _docx_position_id(
                    paragraph=para_index, run=run_index, table=table, row=row, col=col
                )
                marker = _MARKER_PATTERN.search(current)
                if marker:
                    positions.append(
                        {
                            "id": position_id,
                            "kind": KIND_DOCX,
                            "sheet": "",
                            "cell": position_id,
                            "label": marker.group(1)[:MAX_LABEL_TEXT],
                            "text": current[:MAX_LABEL_TEXT],
                            "prefix": "",
                            "suggestion": suggest_field(marker.group(1)) or _match_token(marker.group(1)),
                            "detectedBy": "marker",
                        }
                    )
                    continue

                # ONE-run line: "Số hợp đồng: ________" — keep the label, fill
                # only the blank tail.
                inline = _INLINE_BLANK_PATTERN.match(current)
                if inline:
                    label = _label_before(inline.group("label"))
                    positions.append(
                        {
                            "id": position_id,
                            "kind": KIND_DOCX,
                            "sheet": "",
                            "cell": position_id,
                            "label": label,
                            "text": current[:MAX_LABEL_TEXT],
                            "prefix": inline.group("label") + " ",
                            "suggestion": suggest_field(label),
                            "detectedBy": "inline-blank",
                        }
                    )
                    continue

                # The label of a blank run is the text BEFORE it in the
                # paragraph ("Khách hàng: " + "____"), not the underscores.
                prefix = "".join(item.text or "" for item in runs[:run_index])
                label = _label_before(prefix)
                blank = bool(_BLANK_RUN_PATTERN.match(current))
                if not blank and not (label and not current.strip()):
                    continue
                if not label:
                    label = _label_before(full_text) if not blank else ""
                positions.append(
                    {
                        "id": position_id,
                        "kind": KIND_DOCX,
                        "sheet": "",
                        "cell": position_id,
                        "label": label,
                        "text": current[:MAX_LABEL_TEXT],
                        "prefix": "",
                        "suggestion": suggest_field(label),
                        "detectedBy": "blank",
                    }
                )

    add_paragraph_runs(list(document.paragraphs), table=None, row=None, col=None)
    for table_index, table in enumerate(document.tables):
        for row_index, row in enumerate(table.rows):
            cells = list(row.cells)
            for col_index, cell in enumerate(cells):
                if len(positions) >= MAX_POSITIONS:
                    break
                add_paragraph_runs(
                    list(cell.paragraphs), table=table_index, row=row_index, col=col_index
                )
            # Label cell -> empty neighbour cell: the single most common layout
            # in an ordinary Vietnamese form table ("Người nhận hàng" | "____").
            for col_index, cell in enumerate(cells[:-1]):
                if len(positions) >= MAX_POSITIONS:
                    break
                label = _label_before(cell.text or "")
                if not label:
                    continue
                neighbour = cells[col_index + 1]
                if (neighbour.text or "").strip() and not _BLANK_RUN_PATTERN.match(
                    (neighbour.text or "").strip()
                ):
                    continue
                neighbour_runs = [
                    (paragraph_index, run_index)
                    for paragraph_index, paragraph in enumerate(neighbour.paragraphs)
                    for run_index in range(len(paragraph.runs))
                ]
                if not neighbour_runs:
                    continue
                paragraph_index, run_index = neighbour_runs[0]
                position_id = _docx_position_id(
                    paragraph=paragraph_index, run=run_index,
                    table=table_index, row=row_index, col=col_index + 1,
                )
                existing = next((item for item in positions if item["id"] == position_id), None)
                if existing is not None:
                    # The blank run was already detected without a label; the
                    # label cell to its left supplies the missing context.
                    if not existing.get("label"):
                        existing["label"] = label
                    if not existing.get("suggestion"):
                        existing["suggestion"] = suggest_field(label)
                    existing["detectedBy"] = "table-label-neighbour"
                    continue
                positions.append(
                    {
                        "id": position_id,
                        "kind": KIND_DOCX,
                        "sheet": "",
                        "cell": position_id,
                        "label": label,
                        "text": (neighbour.text or "")[:MAX_LABEL_TEXT],
                        "prefix": "",
                        "suggestion": suggest_field(label),
                        "detectedBy": "table-label-neighbour",
                    }
                )
    return positions


def _docx_position_id(
    *, paragraph: int, run: int, table: int | None, row: int | None, col: int | None
) -> str:
    if table is None:
        return f"p{paragraph}/r{run}"
    return f"t{table}:{row}:{col}/p{paragraph}/r{run}"


_TOKEN_ALIASES = {
    "company": "company.legal_name",
    "customer": "customer.name",
    "shipment": "shipment.id",
    "container": "shipment.container_no",
    "seal": "delivery.seal_no",
    "vessel": "shipment.vessel",
    "pol": "shipment.pol",
    "pod": "shipment.pod",
    "etd": "shipment.etd",
    "mbl": "shipment.mbl",
    "hbl": "shipment.hbl",
    "booking": "shipment.booking_no",
    "receiver": "delivery.receiver_name",
}


def _match_token(token: str) -> str:
    key = _text(token).lower().strip(".")
    if key in CANONICAL_FIELD_KEYS:
        return key
    return _TOKEN_ALIASES.get(key, "")


def _shared_strings(sst_element) -> list[str]:
    values: list[str] = []
    for si in sst_element.findall("x:si", _NS):
        values.append("".join(t.text or "" for t in si.findall(".//x:t", _NS)))
    return values


def _cell_text(cell, shared: list[str]) -> str:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        return "".join(t.text or "" for t in cell.findall(".//x:t", _NS))
    value = cell.find("x:v", _NS)
    if value is None or value.text is None:
        return ""
    if cell_type == "s":
        try:
            index = int(value.text)
        except ValueError:
            return ""
        return shared[index] if 0 <= index < len(shared) else ""
    return value.text


def _split_coord(coord: str) -> tuple[int, int]:
    match = _CELL_COORD_PATTERN.match(_text(coord).upper())
    if not match:
        raise UploadedTemplateError(f"Tọa độ ô không hợp lệ: {coord!r}")
    return _column_letters_to_index(match.group(1)), int(match.group(2))


def _sheet_paths(workbook_element, rels_element) -> dict[str, str]:
    """Map sheet name → worksheet part path (e.g. ``xl/worksheets/sheet1.xml``)."""
    rel_map = {
        rel.get("Id"): rel.get("Target")
        for rel in rels_element.findall(f"{{{_PKG_REL_NS}}}Relationship")
    }
    paths: dict[str, str] = {}
    for sheet in workbook_element.findall(".//x:sheet", _NS):
        target = rel_map.get(sheet.get(f"{{{_REL_NS}}}id"), "")
        if not target:
            continue
        # Targets appear either relative ("worksheets/sheet1.xml") or absolute
        # ("/xl/worksheets/sheet1.xml"); strip the leading slash FIRST so an
        # absolute target is never prefixed twice.
        target = target.lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        name = _text(sheet.get("name"))[:MAX_SHEET_NAME]
        if name:
            paths[name] = target
    return paths


def _parse_xlsx_positions(raw: bytes) -> list[dict[str, Any]]:
    """Every text cell; a marker cell maps to itself, a label maps to its
    empty right (or below) neighbour."""
    from lxml import etree

    reader = zipfile.ZipFile(io.BytesIO(raw))
    parts = {info.filename: reader.read(info.filename) for info in reader.infolist()}
    workbook = etree.fromstring(parts.get("xl/workbook.xml", b"<workbook/>"))
    rels = etree.fromstring(parts.get("xl/_rels/workbook.xml.rels", b"<Relationships/>"))
    shared: list[str] = []
    if "xl/sharedStrings.xml" in parts:
        shared = _shared_strings(etree.fromstring(parts["xl/sharedStrings.xml"]))

    positions: list[dict[str, Any]] = []
    for sheet_name, path in _sheet_paths(workbook, rels).items():
        if path not in parts:
            continue
        sheet = etree.fromstring(parts[path])
        grid: dict[tuple[int, int], tuple[str, Any]] = {}
        for cell in sheet.findall(".//x:c", _NS):
            coord = _text(cell.get("r")).upper()
            if not _CELL_COORD_PATTERN.match(coord):
                continue
            text = _cell_text(cell, shared).strip()
            grid[_split_coord(coord)] = (text, cell)

        for (col, row), (text, _cell) in sorted(grid.items(), key=lambda item: (item[0][1], item[0][0])):
            if len(positions) >= MAX_POSITIONS:
                break
            if not text:
                continue
            marker = _MARKER_PATTERN.search(text)
            if marker:
                positions.append(
                    {
                        "id": f"{sheet_name}!{_index_to_column_letters(col)}{row}",
                        "kind": KIND_XLSX,
                        "sheet": sheet_name,
                        "cell": f"{_index_to_column_letters(col)}{row}",
                        "label": marker.group(1)[:MAX_LABEL_TEXT],
                        "text": text[:MAX_LABEL_TEXT],
                        "prefix": "",
                        "suggestion": suggest_field(marker.group(1)) or _match_token(marker.group(1)),
                        "detectedBy": "marker",
                    }
                )
                continue
            target_col, target_row = col + 1, row
            if (target_col, target_row) in grid and grid[(target_col, target_row)][0]:
                target_col, target_row = col, row + 1
            if (target_col, target_row) in grid and grid[(target_col, target_row)][0]:
                continue
            label = _label_before(text)
            positions.append(
                {
                    "id": f"{sheet_name}!{_index_to_column_letters(target_col)}{target_row}",
                    "kind": KIND_XLSX,
                    "sheet": sheet_name,
                    "cell": f"{_index_to_column_letters(target_col)}{target_row}",
                    "label": label,
                    "text": text[:MAX_LABEL_TEXT],
                    "prefix": "",
                    "suggestion": suggest_field(label),
                    "detectedBy": "label-neighbour",
                }
            )
    return positions


def detect_positions(raw: bytes, kind: str) -> list[dict[str, Any]]:
    """Server-owned candidate positions; never a final mapping."""
    if kind == KIND_DOCX:
        return _parse_docx_positions(raw)
    if kind == KIND_XLSX:
        return _parse_xlsx_positions(raw)
    raise UploadedTemplateError(f"Loại template không hỗ trợ: {kind!r}")


# ---------------------------------------------------------------------------
# Mapping validation (whitelist only — no paths, no expressions)
# ---------------------------------------------------------------------------

MODE_FIELD = "field"
MODE_MANUAL = "manual"
MODE_STATIC = "static"
MAPPING_MODES = (MODE_FIELD, MODE_MANUAL, MODE_STATIC)


def _refuse_forged(value: str) -> None:
    if _FORBIDDEN_VALUE_PATTERN.search(value):
        raise UploadedTemplateError(
            f"Giá trị mapping không hợp lệ (chứa ký tự/cấu trúc bị cấm): {value[:40]!r}"
        )


def normalize_mapping(payload: Any, kind: str) -> list[dict[str, Any]]:
    """Validate ONE confirmed mapping list against the whitelist.

    Every entry is ``{"position": <detected id>, "mode": field|manual|static,
    "value": <canonical key | manual key | literal>}``.  Unknown positions are
    refused (a mapping must point at something detection actually reported),
    unknown canonical keys are refused, and two entries may never target the
    same position.
    """
    if not isinstance(payload, list):
        raise UploadedTemplateError("Mapping phải là một danh sách.")
    if len(payload) > MAX_MAPPINGS:
        raise UploadedTemplateError(f"Mapping vượt quá {MAX_MAPPINGS} vị trí.")

    seen_positions: set[str] = set()
    seen_manual: set[str] = set()
    entries: list[dict[str, Any]] = []
    for index, raw in enumerate(payload, start=1):
        if not isinstance(raw, Mapping):
            raise UploadedTemplateError(f"Mapping dòng {index} không hợp lệ.")
        position = _text(raw.get("position"))
        if not position or len(position) > MAX_CELL_COORD * 8:
            raise UploadedTemplateError(f"Mapping dòng {index} thiếu vị trí hợp lệ.")
        _refuse_forged(position)
        if kind == KIND_XLSX and "!" not in position:
            raise UploadedTemplateError(f"Vị trí XLSX phải ở dạng 'Sheet!A1': {position[:32]!r}")
        if kind == KIND_DOCX and "/" not in position:
            raise UploadedTemplateError(f"Vị trí DOCX không hợp lệ: {position[:32]!r}")
        if position in seen_positions:
            raise UploadedTemplateError(f"Vị trí {position[:32]!r} bị gán hai lần.")
        seen_positions.add(position)

        mode = _text(raw.get("mode")).lower()
        if mode not in MAPPING_MODES:
            raise UploadedTemplateError(f"Mapping dòng {index}: chế độ {mode!r} không hỗ trợ.")

        value = _text(raw.get("value"))
        if mode == MODE_FIELD:
            if value not in CANONICAL_FIELD_KEYS:
                raise UploadedTemplateError(
                    f"Trường {value[:40]!r} không có trong danh mục dữ liệu được phép tự điền."
                )
            label = CANONICAL_FIELDS_BY_KEY[value].label
        elif mode == MODE_MANUAL:
            if not value or len(value) > MAX_LABEL_TEXT:
                raise UploadedTemplateError(f"Mapping dòng {index}: thiếu nhãn cho ô nhập tay.")
            _refuse_forged(value)
            if value in seen_manual:
                raise UploadedTemplateError(f"Ô nhập tay {value[:32]!r} bị lặp.")
            seen_manual.add(value)
            label = value
        else:
            if len(value) > MAX_STATIC_TEXT:
                raise UploadedTemplateError(f"Mapping dòng {index}: nội dung cố định quá dài.")
            _refuse_forged(value)
            label = value[:MAX_LABEL_TEXT]

        entries.append({"position": position, "mode": mode, "value": value, "label": label})
    return entries


def manual_field_labels(mapping: list[Mapping[str, Any]]) -> list[str]:
    """Operator-typed fields this template needs, in mapping order."""
    return [
        _text(entry.get("label"))
        for entry in mapping
        if _text(entry.get("mode")) == MODE_MANUAL and _text(entry.get("label"))
    ]


# ---------------------------------------------------------------------------
# Fact resolution (exact truth only; UNKNOWN stays MISSING)
# ---------------------------------------------------------------------------

def resolve_mapping(
    mapping: list[Mapping[str, Any]],
    facts: Mapping[str, Any],
    *,
    manual: Mapping[str, Any] | None = None,
    prefixes: Mapping[str, str] | None = None,
) -> tuple[dict[str, str], list[str]]:
    """Resolve each confirmed entry to a value; return ``(values, missing)``.

    ``missing`` entries are Vietnamese, name the exact fact and the position,
    and are surfaced verbatim to the operator.  Nothing is defaulted.

    ``prefixes`` carries the printed label a detection kept in the same run
    ("Số hợp đồng: "), so filling a one-run line never erases its label.
    """
    manual_values = manual if isinstance(manual, Mapping) else {}
    label_prefixes = prefixes if isinstance(prefixes, Mapping) else {}
    shipment = facts.get("shipment") if isinstance(facts.get("shipment"), Mapping) else {}
    delivery = facts.get("delivery") if isinstance(facts.get("delivery"), Mapping) else {}
    company = facts.get("company") if isinstance(facts.get("company"), Mapping) else {}
    customer = facts.get("customer") if isinstance(facts.get("customer"), Mapping) else {}
    contract = facts.get("contract") if isinstance(facts.get("contract"), Mapping) else {}
    goods_lines = facts.get("goods_lines") if isinstance(facts.get("goods_lines"), list) else []
    single_line = goods_lines[0] if len(goods_lines) == 1 and isinstance(goods_lines[0], Mapping) else {}
    contract_ok = bool(contract)
    goods_ok = contract_ok and bool(single_line)

    values: dict[str, str] = {}
    missing: list[str] = []

    def put(target: str, resolved: str) -> None:
        # NOTE: not ``_text`` — a kept label prefix legitimately ends with a
        # space ("Số hợp đồng: ") and stripping it would glue the value on.
        values[target] = str(label_prefixes.get(target) or "") + resolved

    for entry in mapping:
        position = _text(entry.get("position"))
        mode = _text(entry.get("mode"))
        key = _text(entry.get("value"))
        label = _text(entry.get("label")) or key

        if mode == MODE_STATIC:
            put(position, key)
            continue
        if mode == MODE_MANUAL:
            typed = _text(manual_values.get(label))
            if typed:
                put(position, typed)
            else:
                missing.append(f"Thiếu thông tin nhập tay: {label}.")
            continue
        if mode != MODE_FIELD:
            missing.append(f"Mapping không hợp lệ tại {position[:24]}.")
            continue

        group = key.split(".", 1)[0]
        if group == "contract" and not contract_ok:
            missing.append(f"{CANONICAL_FIELDS_BY_KEY[key].label}: {_CONDITIONAL_REASON['contract']}")
            continue
        if group == "goods" and not goods_ok:
            missing.append(f"{CANONICAL_FIELDS_BY_KEY[key].label}: {_CONDITIONAL_REASON['goods']}")
            continue

        source = {"company": company, "customer": customer, "shipment": shipment,
                  "delivery": delivery, "contract": contract, "goods": single_line}[group]
        attribute = key.split(".", 1)[1]
        # Verbatim canonical text.  A quantity is NEVER re-parsed or
        # reformatted: "12.500" (a Vietnamese thousands separator) would
        # otherwise print as 12.5, i.e. a different number than the truth.
        resolved = _text(source.get(attribute))
        if resolved:
            put(position, resolved)
        else:
            missing.append(f"Thiếu {CANONICAL_FIELDS_BY_KEY[key].label} (chưa có dữ liệu xác nhận).")
    return values, missing


def evaluate_uploaded_readiness(
    mapping: list[Mapping[str, Any]],
    facts: Mapping[str, Any],
    *,
    manual: Mapping[str, Any] | None = None,
    template_label: str = "",
) -> Readiness:
    """Reuse the existing Readiness contract; never a parallel gate."""
    name = _text(template_label) or "biểu mẫu tải lên"
    if not mapping:
        return Readiness(
            document_type=UPLOADED_DOCUMENT_TYPE,
            state=MISSING_INFO,
            reason=f"Biểu mẫu {name} chưa có mapping nào được xác nhận.",
            missing=("Admin cần xác nhận ít nhất một vị trí.",),
        )
    _values, missing = resolve_mapping(mapping, facts, manual=manual)
    if missing:
        return Readiness(
            document_type=UPLOADED_DOCUMENT_TYPE,
            state=MISSING_INFO,
            reason=f"Thiếu {len(missing)} thông tin để xuất {name}.",
            missing=tuple(missing),
        )
    return Readiness(
        document_type=UPLOADED_DOCUMENT_TYPE,
        state=READY,
        reason=f"Sẵn sàng xuất {name}.",
    )


# ---------------------------------------------------------------------------
# Non-destructive deterministic rendering
# ---------------------------------------------------------------------------

def _deterministic_repack(raw: bytes) -> bytes:
    """Rewrite the package with fixed ZIP entry dates (stable output hash)."""
    reader = zipfile.ZipFile(io.BytesIO(raw))
    names = reader.namelist()
    parts = {name: reader.read(name) for name in names}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as writer:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=_FIXED_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            writer.writestr(info, parts[name])
    return buffer.getvalue()


def _docx_table_cell(document: Any, head: str) -> Any:
    """Resolve a ``t<table>:<row>:<col>`` position head to one table cell."""
    if not head.startswith("t"):
        return None
    try:
        table_index, row_index, col_index = (int(part) for part in head[1:].split(":"))
    except ValueError:
        return None
    tables = list(document.tables)
    if table_index >= len(tables):
        return None
    rows = list(tables[table_index].rows)
    if row_index >= len(rows):
        return None
    cells = list(rows[row_index].cells)
    if col_index >= len(cells):
        return None
    return cells[col_index]


def _docx_run_for(document: Any, position: str) -> Any:
    """Resolve one detected position id (``p3/r1`` or ``t0:1:2/p0/r0``) to a run."""
    segments = _text(position).split("/")
    if len(segments) == 2:
        container, para_segment, run_segment = document, segments[0], segments[1]
    elif len(segments) == 3:
        container = _docx_table_cell(document, segments[0])
        if container is None:
            return None
        para_segment, run_segment = segments[1], segments[2]
    else:
        return None

    para_match = re.fullmatch(r"p(\d+)", para_segment)
    run_match = re.fullmatch(r"r(\d+)", run_segment)
    if not para_match or not run_match:
        return None
    paragraphs = list(container.paragraphs)
    para_index = int(para_match.group(1))
    if para_index >= len(paragraphs):
        return None
    runs = list(paragraphs[para_index].runs)
    run_index = int(run_match.group(1))
    if run_index >= len(runs):
        return None
    return runs[run_index]


def _replace_tokens_in_run(run: Any, value: str) -> None:
    """Fill ONLY the ``{{token}}`` placeholders, keeping the run's own words.

    ``Xác nhận: {{shipment.id}} (đã kiểm)`` is a single ordinary Word run.  A
    whole-run assignment would silently delete the printed label and the
    trailing note — a legal wording change nobody can see happen.  So the label
    and every non-token character are preserved verbatim and only the token
    spans are substituted.

    One position carries one confirmed value, so every token span in that run
    receives it.  Detection offers one position per run, which is the limit of
    what an Admin can map; this neither adds nor removes placeholders.
    """
    current = run.text or ""
    if not _MARKER_PATTERN.search(current):
        # No token here (a blank run, or a kept label + blank tail): the whole
        # run is the fill target, exactly as before.
        run.text = str(value)
        return
    run.text = _MARKER_PATTERN.sub(lambda _match: str(value), current)


def _render_docx(raw: bytes, values: Mapping[str, str]) -> bytes:
    """Run-level writes only: ``rPr`` and every other part stay untouched."""
    import docx

    document = docx.Document(io.BytesIO(raw))
    for position, value in values.items():
        run = _docx_run_for(document, position)
        if run is None:
            continue
        _replace_tokens_in_run(run, value)

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _set_cell_value(sheet, cell, value: str) -> None:
    """Write one string value as an inline string, preserving the cell style."""
    from lxml import etree

    for tag in ("v", "f", "is"):
        for child in cell.findall(f"x:{tag}", _NS):
            cell.remove(child)
    cell.set("t", "inlineStr")
    inline = etree.SubElement(cell, f"{{{_SHEET_NS}}}is")
    text = etree.SubElement(inline, f"{{{_SHEET_NS}}}t")
    text.text = str(value)
    if str(value) != str(value).strip():
        text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def _ensure_cell(sheet, coord: str):
    """Return the cell for ``coord``, creating row/cell in valid order."""
    from lxml import etree

    col, row = _split_coord(coord)
    sheet_data = sheet.find(f"{{{_SHEET_NS}}}sheetData")
    if sheet_data is None:
        sheet_data = etree.SubElement(sheet, f"{{{_SHEET_NS}}}sheetData")

    target_row = None
    for row_element in sheet_data.findall(f"{{{_SHEET_NS}}}row"):
        if row_element.get("r") == str(row):
            target_row = row_element
            break
    if target_row is None:
        target_row = etree.Element(f"{{{_SHEET_NS}}}row")
        target_row.set("r", str(row))
        inserted = False
        for row_element in sheet_data.findall(f"{{{_SHEET_NS}}}row"):
            if int(row_element.get("r") or "0") > row:
                row_element.addprevious(target_row)
                inserted = True
                break
        if not inserted:
            sheet_data.append(target_row)

    for cell in target_row.findall(f"{{{_SHEET_NS}}}c"):
        if cell.get("r") == coord:
            return cell

    cell = etree.Element(f"{{{_SHEET_NS}}}c")
    cell.set("r", coord)
    inserted = False
    for existing in target_row.findall(f"{{{_SHEET_NS}}}c"):
        existing_coord = _text(existing.get("r")).upper()
        if _CELL_COORD_PATTERN.match(existing_coord) and _split_coord(existing_coord)[0] > col:
            existing.addprevious(cell)
            inserted = True
            break
    if not inserted:
        target_row.append(cell)
    return cell


def _render_xlsx(raw: bytes, values: Mapping[str, str]) -> bytes:
    """Cell-level writes only; sheets, styles and everything else survive."""
    from lxml import etree

    reader = zipfile.ZipFile(io.BytesIO(raw))
    parts = {info.filename: reader.read(info.filename) for info in reader.infolist()}
    entry_order = [info.filename for info in reader.infolist()]
    workbook = etree.fromstring(parts.get("xl/workbook.xml", b"<workbook/>"))
    rels = etree.fromstring(parts.get("xl/_rels/workbook.xml.rels", b"<Relationships/>"))
    sheet_paths = _sheet_paths(workbook, rels)

    by_sheet: dict[str, dict[str, str]] = {}
    for position, value in values.items():
        if "!" not in position:
            continue
        sheet_name, _, coord = position.rpartition("!")
        coord = _text(coord).upper()
        if not _CELL_COORD_PATTERN.match(coord):
            continue
        by_sheet.setdefault(_text(sheet_name), {})[coord] = str(value)

    for sheet_name, payload in by_sheet.items():
        path = sheet_paths.get(sheet_name)
        if not path or path not in parts:
            continue
        sheet = etree.fromstring(parts[path])
        for coord, value in payload.items():
            _set_cell_value(sheet, _ensure_cell(sheet, coord), value)
        parts[path] = etree.tostring(sheet, xml_declaration=True, encoding="UTF-8", standalone=True)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as writer:
        for name in entry_order:
            writer.writestr(name, parts[name])
    return buffer.getvalue()


def render_uploaded(
    raw: bytes,
    *,
    kind: str,
    template_sha256: str,
    values: Mapping[str, str],
) -> bytes:
    """Render + re-scan.  A drifted template or unsafe output is refused."""
    pinned = _text(template_sha256).lower()
    if pinned and hashlib.sha256(raw).hexdigest() != pinned:
        raise UploadedTemplateError("Template trên kho khác SHA-256 đã ghim — từ chối sinh.")

    if kind == KIND_DOCX:
        rendered = _render_docx(raw, values)
    elif kind == KIND_XLSX:
        rendered = _render_xlsx(raw, values)
    else:
        raise UploadedTemplateError(f"Loại template không hỗ trợ: {kind!r}")

    rendered = _deterministic_repack(rendered)

    scan = scan_package_safety(rendered)
    if not scan["ok"]:
        raise UploadedTemplateError(f"Đầu ra không qua kiểm tra an toàn: {scan['issues']}")
    residual = _residual_markers(rendered, kind)
    if residual:
        raise UploadedTemplateError(
            "Đầu ra còn thẻ {{...}} chưa được thay — từ chối phát hành: " + ", ".join(residual[:5])
        )
    return rendered


def _residual_markers(raw: bytes, kind: str) -> list[str]:
    """A mapped-away marker must not survive into the published file."""
    reader = zipfile.ZipFile(io.BytesIO(raw))
    targets = ["word/document.xml"] if kind == KIND_DOCX else [
        name for name in reader.namelist()
        if name.startswith("xl/worksheets/") and name.endswith(".xml")
    ]
    found: list[str] = []
    for name in targets:
        try:
            payload = reader.read(name).decode("utf-8", errors="ignore")
        except KeyError:  # pragma: no cover - defensive
            continue
        found.extend(match.group(0) for match in _MARKER_PATTERN.finditer(payload))
    return found


def _slug(value: str, fallback: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", _text(value)).strip("-").upper()
    return slug or fallback


PREVIEW_MARKER = "[DU LIEU THU]"


def preview_facts() -> dict[str, Any]:
    """Obviously-fake, clearly-labelled sample facts for a pre-publish preview.

    Derived from ``CANONICAL_FIELDS`` itself, so the preview can never drift
    from what is bindable and can never contain a real legal identity, tax
    code, amount or date.  Every value carries ``PREVIEW_MARKER`` so a preview
    file is unmistakable if it is ever opened or forwarded by mistake.
    """
    facts: dict[str, Any] = {}
    for field in CANONICAL_FIELDS:
        group, _, name = field.key.partition(".")
        facts.setdefault(group, {})[name] = f"{PREVIEW_MARKER} {field.label}"
    facts.setdefault("goods_lines", []).append({
        "description": f"{PREVIEW_MARKER} Tên hàng hóa mẫu",
        "specification": f"{PREVIEW_MARKER} Quy cách mẫu",
        "unit": f"{PREVIEW_MARKER} ĐVT",
        "quantity": f"{PREVIEW_MARKER} Số lượng",
    })
    return facts


def render_preview(
    raw: bytes, *, kind: str, template_sha256: str, mapping: list[Mapping[str, Any]]
) -> tuple[bytes, list[str]]:
    """Render one trial file from labelled sample data. Returns ``(bytes, missing)``.

    Reuses the production renderer, so what the Admin sees is exactly what a
    real generation would produce — same detection-independent fill, same
    re-scan, same determinism.  Unresolved positions are reported rather than
    silently filled, which is the whole point of reviewing before publishing.
    """
    values, missing = resolve_mapping(mapping, preview_facts(), manual={})
    rendered = render_uploaded(
        raw, kind=kind, template_sha256=template_sha256, values=values
    )
    return rendered, missing


def output_file_name(shipment_id: str, template_label: str, kind: str) -> str:
    extension = "docx" if kind == KIND_DOCX else "xlsx"
    return f"{_slug(template_label, 'BIEU-MAU')}_{_slug(shipment_id, 'LO')}.{extension}"


def build_generated_metadata(
    *,
    shipment_id: str,
    template_id: str,
    template_label: str,
    template_version: int,
    template_sha256: str,
    mime: str,
    file_name: str,
    output_hash: str,
    revision: int,
    contract_id: str,
    counterparty_id: str,
    generated_at: str,
    generated_by: str,
    values: Mapping[str, str],
) -> dict[str, Any]:
    """Provenance shaped exactly like the existing PXK/GNT/FORM_07 rows.

    ``create_or_observe_docgen_revision`` keeps these rows immutable; the extra
    ``template_*`` keys are the bounded provenance Issue #193 requires on top
    of the existing shape (version + author/source binding).
    """
    logical_document_id = f"{UPLOADED_DOCUMENT_TYPE}::{_text(template_id)}::{_text(shipment_id)}"
    record_id = f"{logical_document_id}::R{int(revision)}"
    return {
        "id": record_id,
        "document_id": logical_document_id,
        "document_type": UPLOADED_DOCUMENT_TYPE,
        "shipment_id": _text(shipment_id),
        "contract_id": _text(contract_id),
        "parent_contract_id": None,
        "counterparty_id": _text(counterparty_id),
        "template_id": _text(template_id),
        "template_label": _text(template_label),
        "template_version": int(template_version),
        "template_hash": _text(template_sha256),
        "generation_revision": int(revision),
        "revision": int(revision),
        "status": "GENERATED",
        "generated_at": _text(generated_at),
        "generated_by": _text(generated_by),
        "source_snapshot": {
            "template_id": _text(template_id),
            "template_version": int(template_version),
            "template_sha256": _text(template_sha256),
            "filled_positions": dict(values),
        },
        "source_reference": f"{UPLOADED_DOCUMENT_TYPE}:{_text(template_id)}:{_text(shipment_id)}",
        "output_file_name": _text(file_name),
        "output_mime": _text(mime),
        "output_hash": _text(output_hash),
        "supersedes_document_id": None,
        "superseded_by_document_id": None,
    }
