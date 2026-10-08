"""FORM_07 — Biên bản giao nhận hàng hóa (Issue #168 pilot).

The first Owner-sample document family onboarded through the post-PR-164
server-owned catalog. This module is the code-owned envelope/builder for ONE
sanitized DOCX template derived from the exact Owner binary
(``assets/templates/form07/FORM07.template.json`` pins both hashes).

Bounded by design:
  * scalar canonical bindings read EXISTING truth only (authority masters,
    canonical 2.7 delivery facts, the linked contract's goods lines);
  * exactly one repeating goods table (docxtpl ``{%tr%}`` row loop);
  * two explicitly typed manual fields (``so_bien_ban``, ``ngay_dat_hang``)
    where no canonical truth exists — never defaults, never guesses;
  * any unresolved required value FAILS CLOSED through ``Readiness``;
  * output rendering is deterministic (fixed ZIP entry dates) so one input
    snapshot always produces one output SHA-256.

It is NOT a generic Office/template engine and owns no second delivery truth:
selecting FORM_07 means "this shipment wants this document", readiness is
computed here from canonical facts, and generation reuses the existing
attachment storage, docgen revision metadata and audit seams.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from core.config import BASE_DIR
from core.docgen.rules import BLOCKED, MISSING_INFO, READY, Readiness
from core.utils import parse_date_optional

FORM07_TEMPLATE_ID = "FORM_07"
FORM07_DOCUMENT_TYPE = "FORM_07"
FORM07_ADAPTER = "FORM07_DOCGEN"

_SPEC_RELATIVE_PATH = Path("assets/templates/form07/FORM07.template.json")
_MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

#: ZIP entries are repacked with this fixed date so identical inputs always
#: produce byte-identical output (auditable output_hash).
_FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)

_BANNED_PART_PATTERN = re.compile(
    r"vbaProject|activeX|embeddings|comments\d*\.xml|people\.xml|externalLinks|oleObject",
    re.IGNORECASE,
)
_BANNED_XML_PATTERN = re.compile(
    r"<w:ins[ >]|<w:del[ >]|instrText|fldSimple|w:attachedTemplate|DDE|o:OLEObject|<w:subDoc",
)


class Form07TemplateError(RuntimeError):
    """The pinned template asset is missing, unreadable or drifted."""


# ---------------------------------------------------------------------------
# Template asset + spec (Git-resident, SHA-pinned)
# ---------------------------------------------------------------------------

def template_spec_path() -> Path:
    return BASE_DIR / _SPEC_RELATIVE_PATH


def load_template_spec() -> dict[str, Any]:
    try:
        return json.loads(template_spec_path().read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Form07TemplateError(f"Không đọc được spec FORM_07: {exc}") from exc


def template_asset_path() -> Path:
    spec = load_template_spec()
    return BASE_DIR / str(spec.get("asset_path") or "")


def template_asset_available() -> bool:
    """True only when the asset exists AND matches its pinned SHA-256.

    A drifted/tampered asset fails closed exactly like a missing one; the
    catalog then projects FORM_07 as unavailable.
    """
    try:
        spec = load_template_spec()
        path = BASE_DIR / str(spec.get("asset_path") or "")
        raw = path.read_bytes()
    except (Form07TemplateError, OSError):
        return False
    pinned = str(spec.get("asset_sha256") or "").strip().lower()
    return bool(pinned) and hashlib.sha256(raw).hexdigest() == pinned


def scan_package_safety(raw: bytes) -> dict[str, Any]:
    """Bounded OPC safety scan of a DOCX payload (asset or generated file)."""
    findings: dict[str, Any] = {"ok": True, "issues": []}
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
        if archive.testzip() is not None:
            findings.update(ok=False, issues=["ZIP corrupt"])
            return findings
    except zipfile.BadZipFile:
        findings.update(ok=False, issues=["not a valid OOXML ZIP"])
        return findings

    names = archive.namelist()
    banned_parts = [name for name in names if _BANNED_PART_PATTERN.search(name)]
    if banned_parts:
        findings["issues"].append(f"banned parts: {banned_parts}")
    if any(name.endswith((".docm", ".dotm")) for name in names):
        findings["issues"].append("macro-enabled part name")
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
        payload = archive.read(name).decode("utf-8", errors="ignore")
        # Namespace URIs (Type="http://schemas...") are NOT relationships to
        # remote content; only an external Target is.
        if re.search(r'TargetMode="External"|Target="(?:https?|file|ftp|mailto):', payload):
            findings["issues"].append(f"{name}: external relationship")
    core = archive.read("docProps/core.xml").decode("utf-8", errors="ignore") if "docProps/core.xml" in names else ""
    if "Tien Thanh" in core:
        findings["issues"].append("docProps: personal author metadata from the Owner original")
    findings["ok"] = not findings["issues"]
    findings["part_count"] = len(names)
    return findings


# ---------------------------------------------------------------------------
# Canonical facts -> bind values (pure)
# ---------------------------------------------------------------------------

def _text(value: Any) -> str:
    return str(value or "").strip()


def _quantity_text(value: Any) -> str:
    """Render a canonical quantity without inventing precision."""
    raw = _text(value)
    if not raw:
        return ""
    try:
        amount = Decimal(raw.replace(",", "").replace(" ", ""))
    except (InvalidOperation, ValueError):
        return raw
    normalized = amount.normalize()
    return format(normalized, "f")


def delivery_facts_for_form07(delivery: Mapping[str, Any] | None) -> dict[str, str]:
    """The canonical 2.7 delivery facts FORM_07 prints (same truth as PXK)."""
    d = delivery or {}
    return {
        "delivered": bool(d.get("is_delivered")),
        "delivered_at": _text(d.get("delivered_at") or d.get("delivery_date")),
        "delivery_location": _text(d.get("delivery_location") or d.get("addr")),
        "receiver_name": _text(d.get("receiver_name")),
        "receiver_title": _text(d.get("receiver_title")),
    }


def delivery_facts_missing_for_form07(delivery: Mapping[str, Any] | None) -> list[str]:
    facts = delivery_facts_for_form07(delivery)
    missing: list[str] = []
    if not facts["delivered_at"]:
        missing.append("Thiếu ngày giao hàng thực tế (delivered_at).")
    if not facts["delivery_location"]:
        missing.append("Thiếu địa điểm nhận hàng thực tế.")
    if not facts["receiver_name"]:
        missing.append("Thiếu người nhận hàng (receiver_name).")
    if not facts["receiver_title"]:
        missing.append("Thiếu chức vụ người nhận (receiver_title).")
    return missing


def normalize_form07_goods_lines(lines: Any) -> tuple[list[dict[str, Any]], list[str]]:
    """Normalize contract goods lines for the receipt table.

    FORM_07 prints STT / Tên hàng / Quy cách / ĐVT / Số lượng / Ghi chú — it
    carries NO money, so unlike the contract documents an unknown price does
    not block; description, unit and a positive quantity do.
    """
    normalized: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, raw in enumerate(lines or [], start=1):
        if not isinstance(raw, Mapping):
            errors.append(f"Dòng hàng {index} không hợp lệ.")
            continue
        description = _text(raw.get("description") or raw.get("name"))
        unit = _text(raw.get("unit"))
        quantity_raw = _text(raw.get("quantity"))
        try:
            quantity = Decimal(quantity_raw.replace(",", "").replace(" ", "")) if quantity_raw else None
        except (InvalidOperation, ValueError):
            quantity = None
        if not description:
            errors.append(f"Dòng hàng {index}: thiếu mô tả hàng hóa.")
        if not unit:
            errors.append(f"Dòng hàng {index}: thiếu đơn vị tính.")
        if quantity is None:
            errors.append(f"Dòng hàng {index}: số lượng đang UNKNOWN (trống).")
        elif quantity <= 0:
            errors.append(f"Dòng hàng {index}: số lượng phải lớn hơn 0.")
        normalized.append(
            {
                "stt": index,
                "ten_hang": description,
                "quy_cach": _text(raw.get("specification_or_code")),
                "dvt": unit,
                "so_luong": _quantity_text(quantity_raw),
                "ghi_chu": _text(raw.get("note")),
                "valid": all(f"Dòng hàng {index}:" not in item for item in errors),
            }
        )
    return normalized, errors


def party_facts_missing_for_form07(
    agent: Mapping[str, Any] | None,
    company: Mapping[str, Any] | None,
) -> list[str]:
    """Required authority-master facts are exactly the ones the form prints."""
    missing: list[str] = []
    if not agent:
        missing.append("Thiếu hồ sơ pháp lý Đại lý (Bên giao hàng).")
    else:
        for field, label in (
            ("legal_name", "tên pháp lý"),
            ("legal_address", "địa chỉ"),
            ("phone", "điện thoại"),
            ("legal_representative", "người đại diện"),
            ("representative_title", "chức vụ người đại diện"),
        ):
            if not _text(agent.get(field)):
                missing.append(f"Thiếu {label} của Đại lý (Bên B).")
    if not company:
        missing.append("Thiếu hồ sơ pháp lý Công ty (Bên nhận hàng).")
    else:
        for field, label in (
            ("legal_name", "tên pháp lý"),
            ("legal_address", "địa chỉ"),
            ("phone", "điện thoại"),
        ):
            if not _text(company.get(field)):
                missing.append(f"Thiếu {label} của Công ty (Bên A).")
    return missing


def manual_facts_missing_for_form07(manual: Mapping[str, Any] | None) -> list[str]:
    """The two typed operator inputs; wording mirrors the PXK identity rule."""
    m = manual or {}
    missing: list[str] = []
    if not _text(m.get("form07_no")):
        missing.append("Thiếu số biên bản giao nhận (FORM_07).")
    order_date_raw = _text(m.get("order_date"))
    if not order_date_raw:
        missing.append("Thiếu ngày đơn đặt hàng (FORM_07).")
    elif parse_date_optional(order_date_raw) is None:
        missing.append("Ngày đơn đặt hàng không hợp lệ (DD/MM/YYYY hoặc YYYY-MM-DD).")
    return missing


def evaluate_form07_readiness(
    *,
    delivery: Mapping[str, Any] | None,
    goods_lines: Any,
    agent: Mapping[str, Any] | None,
    company: Mapping[str, Any] | None,
    contract: Mapping[str, Any] | None,
    ambiguous_source: bool = False,
    manual: Mapping[str, Any] | None = None,
) -> Readiness:
    """Server-owned FORM_07 readiness from canonical facts only.

    Gate order mirrors the existing PXK projection: delivery completion ->
    delivery facts -> exactly one source contract -> goods lines -> party
    masters -> typed manual identity. Selecting the template never makes a
    document ready; every unresolved required fact stays MISSING_INFO/BLOCKED.
    """
    facts = delivery_facts_for_form07(delivery)
    if not facts["delivered"]:
        return Readiness(
            document_type=FORM07_DOCUMENT_TYPE,
            state=BLOCKED,
            reason="Biên bản giao nhận chỉ được tạo sau khi lô hàng được xác nhận giao.",
            missing=("Xác nhận đã giao hàng",),
        )
    missing_delivery = delivery_facts_missing_for_form07(delivery)
    if missing_delivery:
        return Readiness(
            document_type=FORM07_DOCUMENT_TYPE,
            state=MISSING_INFO,
            reason="Thiếu thông tin giao nhận thực tế: " + " ".join(missing_delivery),
            missing=tuple(missing_delivery),
        )
    if ambiguous_source:
        return Readiness(
            document_type=FORM07_DOCUMENT_TYPE,
            state=BLOCKED,
            reason="Biên bản giao nhận cần đúng một hợp đồng mua bán nguồn đã liên kết với lô.",
            missing=("Chọn đúng một chứng từ nguồn",),
        )
    if not contract:
        return Readiness(
            document_type=FORM07_DOCUMENT_TYPE,
            state=BLOCKED,
            reason="Chưa liên kết hợp đồng mua bán (nguồn hàng hóa và hai bên) với lô.",
            missing=("Liên kết hợp đồng mua bán với lô",),
        )

    normalized, goods_errors = normalize_form07_goods_lines(goods_lines)
    missing: list[str] = []
    if not normalized:
        missing.append("Chưa có dòng hàng hóa mua trên hợp đồng nguồn.")
    missing.extend(goods_errors)
    missing.extend(party_facts_missing_for_form07(agent, company))
    missing.extend(manual_facts_missing_for_form07(manual))
    if missing:
        return Readiness(
            document_type=FORM07_DOCUMENT_TYPE,
            state=MISSING_INFO,
            reason=f"Thiếu {len(missing)} thông tin để xuất Biên bản giao nhận (FORM_07).",
            missing=tuple(missing),
        )
    return Readiness(
        document_type=FORM07_DOCUMENT_TYPE,
        state=READY,
        reason="Sẵn sàng xuất Biên bản giao nhận (FORM_07).",
    )


# ---------------------------------------------------------------------------
# Rendering (deterministic) + provenance
# ---------------------------------------------------------------------------

def build_form07_context(
    *,
    delivery: Mapping[str, Any] | None,
    goods_lines: Any,
    agent: Mapping[str, Any],
    company: Mapping[str, Any],
    manual: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind canonical/manual values to the template tokens (pure)."""
    facts = delivery_facts_for_form07(delivery)
    delivered = parse_date_optional(facts["delivered_at"])
    if delivered is None:
        raise Form07TemplateError("delivered_at không phân tích được ngày — không tự thay bằng hôm nay.")
    order_date = parse_date_optional(_text(manual.get("order_date")))
    if order_date is None:
        raise Form07TemplateError("Ngày đơn đặt hàng không hợp lệ.")
    normalized, errors = normalize_form07_goods_lines(goods_lines)
    if errors or not normalized:
        raise Form07TemplateError("Dòng hàng hóa chưa hợp lệ: " + " ".join(errors or ["rỗng"]))
    return {
        "cong_ty": _text(company.get("legal_name")),
        "so_bien_ban": _text(manual.get("form07_no")),
        "dia_diem": facts["delivery_location"],
        "ngay": delivered.strftime("%d"),
        "thang": delivered.strftime("%m"),
        "nam": delivered.strftime("%Y"),
        "ngay_dat_hang": order_date.strftime("%d/%m/%Y"),
        "ben_a_name": _text(company.get("legal_name")),
        "ben_a_address": _text(company.get("legal_address")),
        "ben_a_phone": _text(company.get("phone")),
        "ben_a_representative": facts["receiver_name"],
        "ben_a_representative_title": facts["receiver_title"],
        "ben_b_name": _text(agent.get("legal_name")),
        "ben_b_address": _text(agent.get("legal_address")),
        "ben_b_phone": _text(agent.get("phone")),
        "ben_b_representative": _text(agent.get("legal_representative")),
        "ben_b_representative_title": _text(agent.get("representative_title")),
        "goods_lines": [
            {key: row[key] for key in ("stt", "ten_hang", "quy_cach", "dvt", "so_luong", "ghi_chu")}
            for row in normalized
        ],
    }


def _deterministic_repack(raw: bytes) -> bytes:
    """Rewrite the rendered OOXML package with fixed ZIP entry dates."""
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


def render_form07_docx(context: Mapping[str, Any]) -> bytes:
    """Render the pinned sanitized template with one bounded context."""
    from docxtpl import DocxTemplate

    path = template_asset_path()
    try:
        raw_asset = path.read_bytes()
    except OSError as exc:
        raise Form07TemplateError(f"Không đọc được template FORM_07: {exc}") from exc
    spec = load_template_spec()
    pinned = str(spec.get("asset_sha256") or "").strip().lower()
    if hashlib.sha256(raw_asset).hexdigest() != pinned:
        raise Form07TemplateError("Template FORM_07 trên đĩa khác SHA-256 đã ghim — từ chối sinh.")

    template = DocxTemplate(io.BytesIO(raw_asset))
    buffer = io.BytesIO()
    template.render(dict(context))
    template.save(buffer)
    rendered = _deterministic_repack(buffer.getvalue())

    document_xml = zipfile.ZipFile(io.BytesIO(rendered)).read("word/document.xml").decode("utf-8")
    if "{{" in document_xml or "{%" in document_xml:
        raise Form07TemplateError("Đầu ra còn thẻ template chưa được thay — từ chối phát hành.")
    scan = scan_package_safety(rendered)
    if not scan["ok"]:
        raise Form07TemplateError(f"Đầu ra không qua kiểm tra an toàn: {scan['issues']}")
    return rendered


def _file_name_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-").upper()
    return slug or "BBGN"


def form07_output_file_name(shipment_id: str, form07_no: str) -> str:
    return f"FORM07_{_text(shipment_id).upper()}_{_file_name_slug(form07_no)}.docx"


def build_form07_file(
    *,
    shipment_id: str,
    delivery: Mapping[str, Any] | None,
    goods_lines: Any,
    agent: Mapping[str, Any],
    company: Mapping[str, Any],
    contract: Mapping[str, Any],
    manual: Mapping[str, Any],
) -> dict[str, Any]:
    """Readiness-gated generation: bytes + name + mime + hashes + snapshot."""
    readiness = evaluate_form07_readiness(
        delivery=delivery,
        goods_lines=goods_lines,
        agent=agent,
        company=company,
        contract=contract,
        manual=manual,
    )
    if readiness.state != READY:
        raise Form07Blocked(readiness)

    context = build_form07_context(
        delivery=delivery,
        goods_lines=goods_lines,
        agent=agent,
        company=company,
        manual=manual,
    )
    raw = render_form07_docx(context)
    spec = load_template_spec()
    facts = delivery_facts_for_form07(delivery)
    file_name = form07_output_file_name(shipment_id, _text(manual.get("form07_no")))
    return {
        "bytes": raw,
        "file_name": file_name,
        "mime": _MIME_DOCX,
        "output_hash": hashlib.sha256(raw).hexdigest(),
        "template_id": FORM07_TEMPLATE_ID,
        "template_version": int(spec.get("template_version") or 1),
        "template_sha256": str(spec.get("asset_sha256") or ""),
        "context_snapshot": dict(context),
        "source_snapshot": {
            "document_type": FORM07_DOCUMENT_TYPE,
            "form07_no": _text(manual.get("form07_no")),
            "order_date": context["ngay_dat_hang"],
            "contract_id": _text(contract.get("id") or contract.get("contract_no")),
            "agent_id": _text(agent.get("agent_id") or agent.get("id")),
            "company_id": _text(company.get("company_id") or company.get("id")),
            "delivered_at": facts["delivered_at"],
            "delivery_location": facts["delivery_location"],
            "receiver_name": facts["receiver_name"],
            "receiver_title": facts["receiver_title"],
            "goods_lines": list(context["goods_lines"]),
            "manual_fields": {
                "form07_no": _text(manual.get("form07_no")),
                "order_date": _text(manual.get("order_date")),
            },
        },
    }


class Form07Blocked(RuntimeError):
    """Fail-closed refusal carrying the exact Readiness for the UI/audit."""

    def __init__(self, readiness: Readiness) -> None:
        self.readiness = readiness
        super().__init__(readiness.reason)


def build_form07_metadata(
    *,
    shipment_id: str,
    generated: Mapping[str, Any],
    revision: int,
    contract_id: str,
    counterparty_id: str,
    generated_at: str,
    generated_by: str,
) -> dict[str, Any]:
    """Provenance metadata shaped like the existing GNT/PXK durable rows.

    ``create_or_observe_docgen_revision`` keeps these rows immutable; the extra
    template_id/version/sha + output_mime keys are the bounded provenance the
    Issue #168 contract requires on top of the existing shape.
    """
    logical_document_id = f"{FORM07_DOCUMENT_TYPE}::{_text(shipment_id)}"
    record_id = f"{logical_document_id}::R{int(revision)}"
    return {
        "id": record_id,
        "document_id": logical_document_id,
        "document_type": FORM07_DOCUMENT_TYPE,
        "shipment_id": _text(shipment_id),
        "contract_id": contract_id,
        "parent_contract_id": None,
        "counterparty_id": counterparty_id,
        "template_id": generated.get("template_id") or FORM07_TEMPLATE_ID,
        "template_version": int(generated.get("template_version") or 1),
        "template_hash": _text(generated.get("template_sha256")),
        "generation_revision": int(revision),
        "revision": int(revision),
        "status": "GENERATED",
        "generated_at": generated_at,
        "generated_by": generated_by,
        "source_snapshot": dict(generated.get("source_snapshot") or {}),
        "source_reference": f"{FORM07_DOCUMENT_TYPE}:{_text(shipment_id)}",
        "output_file_name": _text(generated.get("file_name")),
        "output_mime": _text(generated.get("mime")) or _MIME_DOCX,
        "output_hash": _text(generated.get("output_hash")),
        "supersedes_document_id": None,
        "superseded_by_document_id": None,
    }
