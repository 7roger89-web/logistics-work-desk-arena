"""ONE customer-facing text map for the Step-3 preview and the XLSX export.

LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1.

Why this module exists
----------------------
The quotation screen lets a Sale click any *text* in the customer document and
edit it in place. The same edited wording must reach the exported XLSX, so the
preview and the exporter may not each invent their own strings. This module is
the single resolution point:

    UI (inline edit) -> backend draft -> customer_quote_snapshot()["text"] -> XLSX

Two kinds of region
-------------------
* **bound** — the region already has a canonical writable field on the quote
  (goods description/model/material/note, service name, published note, scope,
  extra public notes, route, goods description). An inline edit writes that
  field; no parallel copy is created, so the existing Bước 1/2 editors and the
  customer document can never disagree.
* **presentation** — the region is pure wording with no business field (document
  title, greeting, column labels, section headings, closing paragraph, an extra
  paragraph). An edit is stored as a small text override next to the quote.

Amounts, FX rates, tax percentages and totals are **not** regions. They stay
backend-computed numbers; the preview renders them read-only.

Safety
------
Only plain text is accepted and stored (no HTML/rich text). Unknown region ids,
bound ids and over-limit values are dropped at the persistence boundary, so a
browser cannot inject an arbitrary document into either the preview or the XLSX.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any, Mapping

CUSTOMER_TEXT_SCHEMA = "quote-customer-text/1"
MAX_REGION_CHARS = 2000
MAX_MULTILINE_CHARS = 6000
MAX_OVERRIDES = 200

SHORT = "SHORT"
LONG = "LONG"

GROUP_DOCUMENT = "Tiêu đề tài liệu"
GROUP_GREETING = "Lời giới thiệu"
GROUP_CUSTOMER = "Thông tin khách"
GROUP_SCOPE = "Phạm vi dịch vụ"
GROUP_GOODS = "Hàng hóa"
GROUP_SERVICE = "Dịch vụ"
GROUP_LABEL = "Nhãn bảng & tiêu đề nhóm"
GROUP_TERMS = "Điều kiện & ghi chú"
GROUP_CLOSING = "Kết thúc báo giá"

# Presentation defaults. They are exactly the strings the Trường Thành template
# exports today, so an untouched quotation renders byte-for-byte as before.
DOC_TITLE_DEFAULT = "BÁO GIÁ DỊCH VỤ LOGISTICS"
GREETING_DEFAULT = ("Trân trọng cảm ơn Quý khách đã quan tâm dịch vụ của chúng tôi. "
                    "Chúng tôi xin gửi báo giá như sau:")
CLOSING_DEFAULT = "Rất mong được hợp tác cùng Quý khách."
SERVICE_SUMMARY_DEFAULT = "Dịch vụ: giao nhận / vận chuyển / thủ tục theo các khoản mục dưới đây."
GOODS_HEADING_DEFAULT = "DANH MỤC HÀNG HÓA — giá theo bảng khách gửi"
SERVICE_HEADING_DEFAULT = "PHÍ DỊCH VỤ — chỉ giá bán đã xác nhận"
TOTALS_HEADING_DEFAULT = "TỔNG CỘNG THEO TỪNG LOẠI TIỀN (không quy đổi gộp)"
CUSTOMS_HEADING_DEFAULT = "THUẾ NHẬP KHẨU DỰ KIẾN (không phải kết luận pháp lý)"
NOTES_HEADING_DEFAULT = "Ghi chú:"
GOODS_COLUMNS = (
    ("stt", "STT"),
    ("name", "Hàng hóa / Model / Vật liệu"),
    ("length", "Dài mm"),
    ("width", "Rộng mm"),
    ("height", "Cao mm"),
    ("qty", "Số lượng"),
    ("unit_price", "Đơn giá"),
    ("currency", "Tiền tệ"),
    ("line_total", "Thành tiền"),
)
SERVICE_COLUMNS = (
    ("stt", "STT"),
    ("name", "Chi tiết"),
    ("unit_price", "Đơn giá"),
    ("qty", "Số lượng"),
    ("amount", "Thành tiền"),
    ("vat_pct", "VAT"),
    ("amount_with_vat", "thành tiền"),
    ("currency", "Đơn vị tiền"),
    ("contingent", "Phát sinh (nếu có)"),
)
PUBLISHED_OPTION_LABEL = {"A": "Khách tự đứng tên nhập khẩu", "B": "Dịch vụ nhập khẩu ủy thác"}

# Commercial LABELS that sit in front of a value on the customer document. They
# never carry a trailing colon in their stored value: the preview and the XLSX
# both add ": " themselves, so one region reads the same in both places.
LABEL_DEFAULTS: dict[str, str] = {
    "label.attn": "Kính gửi",
    "label.goods": "Mặt hàng",
    "label.route": "Tuyến",
    "label.ports": "Cảng / điểm",
    "label.pickup": "Nơi lấy hàng",
    "label.delivery": "Giao tại",
    "label.delivery_date": "Ngày giao dự kiến",
    "label.cbm": "Đóng hàng đã xác nhận",
    "label.goods_note": "Ghi chú",
    "label.scope": "Phạm vi dịch vụ đã xác nhận",
    "label.duty": "Thuế NK dự kiến",
    "label.vat": "VAT NK dự kiến",
    "label.before_tax": "Tạm tính hàng + dịch vụ trước mọi thuế",
    "label.estimate_total": "Tổng dự toán gồm thuế đã xác định",
    "label.customs_basis": "Cơ sở hải quan riêng đã xác nhận",
    "label.duty_rate": "Thuế NK",
    "label.vat_rate": "VAT NK",
}
NO_SERVICES_DEFAULT = "Chưa có phí dịch vụ có giá bán được xác nhận để công bố."
DOC_DISCLAIMER_DEFAULT = ("Báo giá là dự toán, chưa phải hóa đơn hoặc nghĩa vụ thanh toán. "
                          "Thuế dự kiến không thay thế kết luận pháp lý / hải quan.")

# ---- XLSX mapping contract -------------------------------------------------
# Every published region must name WHERE in the customer XLSX its wording is
# printed. A region with no rule is a silent omission, which is exactly what this
# task forbids — ``unmapped_regions()`` makes that state machine-checkable and
# the cross-check script refuses to pass while it is non-empty.
EXPORT_STATIC_RULES: dict[str, str] = {
    "doc.title": "narrative · tiêu đề A5/A11",
    "doc.greeting": "narrative · lời giới thiệu",
    "doc.customer_name": "khối From/To · ô To và dòng Kính gửi",
    "doc.goods_description": "narrative · dòng Mặt hàng",
    "doc.route": "narrative · dòng Tuyến",
    "doc.option_line": "narrative · dòng phương án",
    "doc.closing": "kết báo giá",
    "doc.addendum": "đoạn bổ sung",
    "doc.disclaimer": "cuối trang · dòng miễn trừ",
    "scope": "narrative · dòng phạm vi dịch vụ",
    "notes.additional": "khối ghi chú công bố",
    "sec.goods": "tiêu đề nhóm · bảng hàng hóa",
    "sec.services": "tiêu đề nhóm · bảng phí dịch vụ",
    "sec.totals": "tiêu đề nhóm · tổng cộng",
    "sec.customs": "tiêu đề nhóm · thuế nhập khẩu",
    "sec.notes": "tiêu đề nhóm · ghi chú",
    "sec.service_summary": "narrative · dòng tóm tắt dịch vụ",
    "sec.no_services": "bảng phí dịch vụ · dòng chưa có phí",
}
EXPORT_PREFIX_RULES: tuple[tuple[str, str], ...] = (
    ("col.", "nhãn cột trong bảng"),
    ("label.", "nhãn dòng trong narrative / khối tổng"),
    ("goods.", "dòng hàng hóa trong bảng hàng"),
    ("service.", "dòng phí trong bảng phí dịch vụ"),
    ("note.", "dòng nội dung công bố"),
)


def export_rule(region_id: str) -> str | None:
    """WHERE the customer XLSX prints this region, or ``None`` if nowhere.

    ``None`` is a defect, not a policy: the XLSX and the Step-3 preview must show
    the same customer document.
    """
    if region_id in EXPORT_STATIC_RULES:
        return EXPORT_STATIC_RULES[region_id]
    for prefix, where in EXPORT_PREFIX_RULES:
        if region_id.startswith(prefix):
            return where
    return None


def unmapped_regions(text: Mapping[str, Any] | None) -> list[str]:
    """Published region ids with no declared XLSX rule (must stay empty)."""
    regions = (text or {}).get("regions") if isinstance(text, Mapping) else None
    return sorted(str(r.get("id")) for r in regions or [] if not export_rule(str(r.get("id"))))


def folded(value: Any) -> str:
    text = unicodedata.normalize("NFD", str(value or "")).lower().replace("đ", "d")
    return re.sub(r"\s+", " ", "".join(c for c in text if not unicodedata.combining(c))).strip()


def sanitize_text(value: Any, *, multiline: bool = False) -> str:
    """Plain, bounded text. Never HTML, never a control character.

    Newlines survive (a multi-line note is a real customer-facing shape); every
    other control character is replaced by a space. A leading "=" is prefixed
    with a zero-width-free space-free marker so a stored value can never become
    a spreadsheet formula — the exporter also rewrites any formula cell type.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    limit = MAX_MULTILINE_CHARS if multiline else MAX_REGION_CHARS
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch if (ch == "\n" or ch.isprintable()) else " " for ch in text)
    text = "\n".join(line.rstrip() for line in text.split("\n")).strip("\n")
    if len(text) > limit:
        text = text[:limit]
    if text.lstrip().startswith("="):
        text = "'" + text.lstrip()
    return text


def line_key(kind: str, item: Mapping[str, Any], index: int, *, fields: tuple[str, ...]) -> str:
    """A region id that survives reordering.

    The stored ``id`` of a row (``row-7`` from the workbook, or the id the
    service editor created) is the identity whenever it exists. Only when a row
    genuinely has none is a deterministic content digest used, disambiguated by
    occurrence so two identical rows never collide. Array position is never the
    identity.
    """
    explicit = sanitize_text(item.get("id"), multiline=False)[:48]
    key = re.sub(r"[^A-Za-z0-9_.-]+", "-", explicit).strip("-")
    if key:
        return key
    identity = "|".join(str(item.get(f) or "") for f in fields)
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:10]
    return f"{kind}-{digest}-{index}"


def sanitize_customer_text(raw: Any) -> dict[str, Any]:
    """Persistence boundary: keep only presentation overrides, drop everything else.

    Bound regions are refused because their canonical field is the only writer;
    keeping a second copy would be exactly the divergence this task forbids.
    """
    stored = raw if isinstance(raw, Mapping) else {}
    incoming = stored.get("overrides") if isinstance(stored.get("overrides"), Mapping) else {}
    overrides: dict[str, str] = {}
    for region_id, value in list(incoming.items())[:MAX_OVERRIDES]:
        rid = sanitize_text(region_id)[:120]
        if not rid or is_bound_region(rid):
            continue
        text = sanitize_text(value, multiline=True)
        if not text:
            continue
        overrides[rid] = text
    return {"schema": CUSTOMER_TEXT_SCHEMA, "overrides": overrides}


def overrides_of(details: Mapping[str, Any] | None) -> dict[str, str]:
    stored = (details or {}).get("customer_text")
    return sanitize_customer_text(stored)["overrides"]


def _bound_ids() -> frozenset[str]:
    return frozenset({
        "doc.goods_description", "doc.route", "scope", "notes.additional",
        "goods.*.name", "goods.*.model", "goods.*.material", "goods.*.note",
        "service.*.name", "service.*.public_note",
    })


BOUND_REGION_IDS = _bound_ids()
BOUND_PREFIXES = ("goods.", "service.")


def is_bound_region(region_id: str) -> bool:
    """True for a region whose text is owned by a canonical quote field.

    Such an id may NEVER be stored as an override: the canonical field is the
    only writer, which is exactly what keeps Bước 1/2 and the customer document
    from diverging.
    """
    return region_id in BOUND_REGION_IDS or region_id.startswith(BOUND_PREFIXES)


def _region_source(region_id: str, value: str, *, bound: bool, default_is_source: bool, overridden: bool) -> str:
    """Truthful provenance of one region's displayed value."""
    if bound:
        return "SOURCE" if value.strip() else "UNKNOWN"
    if overridden:
        return "SALE_EDITED"
    if not value.strip():
        return "UNKNOWN"
    return "SOURCE" if default_is_source else "SYSTEM_DEFAULT"


def build_customer_text(quote: Mapping[str, Any], details: Mapping[str, Any]) -> dict[str, Any]:
    """The resolved customer text map. Both preview and XLSX read this.

    ``quote`` is the customer-facing snapshot (already allow-listed); ``details``
    is the stored ``excel_quote`` the overrides live in.
    """
    overrides = overrides_of(details)
    goods = [g for g in (details.get("goods") or quote.get("goods") or []) if isinstance(g, Mapping)]
    services = [s for s in (quote.get("service_lines") or []) if isinstance(s, Mapping)]
    active = str(details.get("active_option") or quote.get("option") or "A")
    published = [d for d in (details.get("disclosures") or []) if isinstance(d, Mapping) and d.get("selected")]
    regions: list[dict[str, Any]] = []

    def add(region_id: str, kind: str, group: str, label: str, default: str, *,
            binding: dict[str, Any] | None = None, guarded: bool = False,
            mismatch: bool = False, value: str | None = None,
            default_is_source: bool = False) -> None:
        bound = binding is not None
        resolved = sanitize_text(value if bound and value is not None else overrides.get(region_id, default),
                                 multiline=(kind == LONG))
        default_text = sanitize_text(default, multiline=(kind == LONG))
        regions.append({
            "id": region_id, "kind": kind, "group": group, "label": label,
            "value": resolved, "default": default_text,
            "source": _region_source(region_id, resolved, bound=bound,
                                     default_is_source=default_is_source,
                                     overridden=region_id in overrides),
            "editable": True, "bound": bound, "binding": binding,
            "guarded": guarded, "mismatch": bool(guarded and mismatch and resolved != default_text),
            "multiline": kind == LONG,
        })

    # ---- document title / greeting / customer identity ---------------------
    add("doc.title", SHORT, GROUP_DOCUMENT, "Tiêu đề báo giá", DOC_TITLE_DEFAULT)
    add("doc.greeting", LONG, GROUP_GREETING, "Lời giới thiệu", GREETING_DEFAULT)
    confirmed_customer = sanitize_text(quote.get("customer_name"), multiline=False)
    add("doc.customer_name", SHORT, GROUP_CUSTOMER, "Tên khách hiển thị", confirmed_customer,
        guarded=True, mismatch=True)
    add("doc.goods_description", SHORT, GROUP_GOODS, "Mặt hàng (dòng mô tả)", "",
        binding={"scope": "header", "field": "goods_description"},
        value=quote.get("goods_description"))
    add("doc.route", SHORT, GROUP_SCOPE, "Tuyến hiển thị", "",
        binding={"scope": "header", "field": "route"}, value=quote.get("route"))
    add("doc.option_line", SHORT, GROUP_SCOPE, "Dòng phương án",
        f"Phương án {active}: {PUBLISHED_OPTION_LABEL.get(active, '')}".rstrip(": "))
    add("scope", LONG, GROUP_SCOPE, "Diễn giải phạm vi dịch vụ", "",
        binding={"scope": "option", "field": "scope"}, value=quote.get("scope"))

    # ---- goods lines ------------------------------------------------------
    for index, item in enumerate(goods):
        key = line_key("goods", item, index, fields=("description", "model", "material", "length_mm", "width_mm", "height_mm"))
        for field, label in (("description", "Tên hàng"), ("model", "Model"), ("material", "Vật liệu")):
            add(f"goods.{key}.{'name' if field == 'description' else field}", SHORT, GROUP_GOODS,
                f"{label} · dòng {index + 1}", "",
                binding={"scope": "goods", "field": field, "key": key, "index": index},
                value=item.get(field))
        add(f"goods.{key}.note", LONG, GROUP_GOODS, f"Ghi chú hàng · dòng {index + 1}", "",
            binding={"scope": "goods", "field": "note", "key": key, "index": index},
            value=item.get("note"))

    # ---- service lines of the published option ----------------------------
    for index, item in enumerate(services):
        key = line_key("service", item, index, fields=("service_name", "unit", "currency"))
        add(f"service.{key}.name", SHORT, GROUP_SERVICE, f"Tên dịch vụ · dòng {index + 1}", "",
            binding={"scope": "service", "field": "service_name", "key": key, "index": index},
            value=item.get("service_name"))
        add(f"service.{key}.public_note", LONG, GROUP_SERVICE, f"Ghi chú công bố · dòng {index + 1}", "",
            binding={"scope": "service", "field": "public_note", "key": key, "index": index},
            value=item.get("public_note"))

    # ---- published notes (source disclosures the Sale chose to publish) ---
    for index, item in enumerate(published):
        rid = f"note.{sanitize_text(item.get('id'))[:40] or f'row-{index + 1}'}"
        add(rid, LONG, GROUP_TERMS, f"Nội dung công bố · {index + 1}", str(item.get("text") or ""),
            default_is_source=True)
    add("notes.additional", LONG, GROUP_TERMS, "Ghi chú công bố thêm", "",
        binding={"scope": "header", "field": "additional_public_notes"},
        value=details.get("additional_public_notes"))

    # ---- column labels and section headings -------------------------------
    for key, default in GOODS_COLUMNS:
        add(f"col.goods.{key}", SHORT, GROUP_LABEL, f"Nhãn cột hàng hóa · {default}", default)
    for key, default in SERVICE_COLUMNS:
        add(f"col.service.{key}", SHORT, GROUP_LABEL, f"Nhãn cột dịch vụ · {default}", default)
    for rid, default in (("sec.goods", GOODS_HEADING_DEFAULT), ("sec.services", SERVICE_HEADING_DEFAULT),
                         ("sec.totals", TOTALS_HEADING_DEFAULT), ("sec.customs", CUSTOMS_HEADING_DEFAULT),
                         ("sec.notes", NOTES_HEADING_DEFAULT), ("sec.service_summary", SERVICE_SUMMARY_DEFAULT)):
        add(rid, SHORT, GROUP_LABEL, f"Tiêu đề nhóm · {default[:40]}", default)
    # Descriptive labels printed in front of a value. Without them the Owner had
    # to leave the Step-3 preview to change a single word of the document.
    #
    # A label is published ONLY when its line is really on the customer document
    # (same condition the paper renders with). Otherwise the label would be an
    # editable region that can never appear in the XLSX — the silent omission
    # this task forbids. Each published label is also checked against the export
    # contract below.
    shipment = dict(quote.get("shipment") or {})
    label_lines = {
        "label.goods": True,
        "label.route": True,
        "label.ports": True,
        "label.scope": True,
        "label.attn": True,
        "label.duty": True,
        "label.vat": True,
        "label.duty_rate": True,
        "label.vat_rate": True,
        "label.before_tax": True,
        "label.estimate_total": True,
        "label.customs_basis": True,
        "label.pickup": bool(str(shipment.get("pickup") or "").strip()),
        "label.delivery": bool(str(shipment.get("delivery") or "").strip()),
        "label.delivery_date": bool(str(quote.get("expected_delivery_date") or "").strip()),
        "label.cbm": shipment.get("cbm") is not None or shipment.get("weight_kg") is not None,
        "label.goods_note": any(str(g.get("note") or "").strip() for g in goods),
    }
    for rid, default in LABEL_DEFAULTS.items():
        if label_lines.get(rid):
            add(rid, SHORT, GROUP_LABEL, f"Nhãn dòng · {default}", default)
    if not services:
        add("sec.no_services", LONG, GROUP_LABEL, "Dòng báo chưa có phí dịch vụ", NO_SERVICES_DEFAULT)

    # ---- closing and an optional extra paragraph --------------------------
    add("doc.closing", LONG, GROUP_CLOSING, "Câu kết báo giá", CLOSING_DEFAULT)
    add("doc.disclaimer", LONG, GROUP_CLOSING, "Dòng miễn trừ cuối báo giá", DOC_DISCLAIMER_DEFAULT)
    add("doc.addendum", LONG, GROUP_CLOSING, "Đoạn văn bổ sung (ẩn khi để trống)", "")

    values = {r["id"]: r["value"] for r in regions}
    out = {
        "schema": CUSTOMER_TEXT_SCHEMA,
        "regions": regions,
        "values": values,
        "overridden": sorted(r["id"] for r in regions if r["id"] in overrides),
        "mismatches": sorted(r["id"] for r in regions if r["mismatch"]),
        "editable_region_count": len(regions),
        # Every published region names where the customer XLSX prints it. The
        # list is machine-checkable so "we forgot to export this region" can
        # never pass silently.
        "export_rules": {r["id"]: export_rule(r["id"]) for r in regions},
        "unmapped": unmapped_regions({"regions": regions}),
    }
    return out


def text_values(quote: Mapping[str, Any]) -> dict[str, str]:
    """``{region_id: value}`` for the exporter; {} for a quote without the map."""
    text = quote.get("text")
    if not isinstance(text, Mapping):
        return {}
    values = text.get("values")
    return dict(values) if isinstance(values, Mapping) else {}


def published_notes(quote: Mapping[str, Any], details: Mapping[str, Any]) -> list[str]:
    """Selected disclosures + extra notes, with the Sale's published wording.

    The source disclosure text itself is never rewritten: the override lives in
    ``customer_text`` and only replaces what is *published*.
    """
    overrides = overrides_of(details)
    notes: list[str] = []
    for index, item in enumerate(details.get("disclosures") or []):
        if not isinstance(item, Mapping) or not item.get("selected"):
            continue
        rid = f"note.{sanitize_text(item.get('id'))[:40] or f'row-{index + 1}'}"
        text = sanitize_text(overrides.get(rid, str(item.get("text") or "")), multiline=True)
        if text:
            notes.append(text)
    extra = sanitize_text(details.get("additional_public_notes"), multiline=True)
    if extra:
        notes.append(extra)
    return notes
