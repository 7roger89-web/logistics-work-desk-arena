# FILE: core/excel_roundtrip.py
"""
LOG-LG05 — Excel Round-Trip & GNT Generation
Module A: Order/Shipment Excel Round-Trip

Handles import (parse → group → validate → classify) and export
(52-column compatible format) for the Logistics application.

Key principles:
- UNKNOWN != ZERO: missing values are marked as None/null, never guessed
- MISSING != SAFE_TO_GUESS: ambiguous fields left blank in export
- AMBIGUOUS != RESOLVED: conflicts shown to user, never silently overwritten
- No business mutation during import preview
"""

import io
import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


# ============================================================
# 52-COLUMN CONTRACT (exact spelling, order A→AZ)
# ============================================================
HEADERS_52: List[str] = [
    "Ngày đặt hàng",          # A
    "Ngày tạo",               # B
    "Mã ĐH",                  # C
    "Người thực hiện",        # D
    "Mã KH",                  # E
    "Tên KH",                 # F
    "Số ĐT",                  # G
    "Email",                  # H
    "Địa chỉ giao hàng",      # I
    "Người liên hệ",          # J
    "Điện thoại người liên hệ",  # K
    "Tỉnh/ TP",               # L
    "Quận/ Huyện",            # M
    "Nguồn khách hàng",       # N
    "Mã vận đơn",             # O
    "Trạng thái vận đơn",     # P
    "Mã kho",                 # Q
    "Mã SP",                  # R
    "Tên sản phẩm",           # S
    "Mô tả",                  # T
    "Đơn vị",                 # U
    "Nhóm sản phẩm",          # V
    "Số lượng",               # W
    "Giá vốn",                # X
    "Giá bán",                # Y
    "CK(%)",                  # Z
    "CK(Đ)",                  # AA
    "VAT(%)",                 # AB
    "Thành tiền",             # AC
    "Lợi nhuận SP",           # AD
    "Doanh số",               # AE
    "Chiết khấu (đ)",         # AF
    "Doanh thu sau CK",       # AG
    "Phí vận chuyển (đ)",     # AH
    "Phí lắp đặt (đ)",        # AI
    "Doanh thu trước thuế",   # AJ
    "VAT (đ)",                # AK
    "Doanh thu",              # AL
    "Đã thanh toán",          # AM
    "Còn lại",                # AN
    "Lợi nhuận",              # AO
    "Điều khoản đơn hàng",    # AP
    "Hình thức thanh toán",   # AQ
    "Hình thức thanh toán từng lần",  # AR
    "Ngày thanh toán",        # AS
    "Nguồn đơn hàng",        # AT
    "Người tạo",              # AU
    "Trạng thái",             # AV
    "Nhóm khách hàng",        # AW
    "REFUN",                  # AX
    "HOA HỒNG KH GỬI",        # AY
    "CẤP ĐỘ RỦI RO",         # AZ
]

# Column indices (0-based)
# A=0 .. N=13: master fields (14)
# O=14, P=15, Q=16: tracking/warehouse (3)
# R=17 .. AO=40: service fields (24)
# AP=41 .. AS=44: payment fields (4)
# AT=45 .. AZ=51: additional master fields (7)

# Master field column names (indices 0-13, A-N)
MASTER_FIELD_NAMES = [
    "order_date",      # A (0)
    "created_date",    # B (1)
    "shipment_id",     # C (2)
    "executor",        # D (3)
    "customer_code",   # E (4)
    "customer_name",   # F (5)
    "phone",           # G (6)
    "email",           # H (7)
    "delivery_address",# I (8)
    "contact_person",  # J (9)
    "contact_phone",   # K (10)
    "province",        # L (11)
    "district",        # M (12)
    "customer_source", # N (13)
]

# Tracking fields (indices 14-16, O-Q)
TRACKING_FIELD_NAMES = [
    "tracking_no",      # O (14)
    "tracking_status",  # P (15)
    "warehouse_code",   # Q (16)
]

# Service field column names (indices 17-40, R-AO)
SERVICE_FIELD_NAMES = [
    "product_code",      # R (17)
    "product_name",      # S (18)
    "description",       # T (19)
    "unit",              # U (20)
    "product_group",     # V (21)
    "qty",               # W (22)
    "cost_price",        # X (23)
    "sale_price",        # Y (24)
    "discount_pct",      # Z (25)
    "discount_amt",      # AA (26)
    "vat_pct",           # AB (27)
    "line_total",        # AC (28)
    "line_profit",       # AD (29)
    "revenue",           # AE (30)
    "discount_vnd",      # AF (31)
    "revenue_after_disc",# AG (32)
    "shipping_fee",      # AH (33)
    "install_fee",       # AI (34)
    "revenue_pre_tax",   # AJ (35)
    "vat_vnd",           # AK (36)
    "total_revenue",     # AL (37)
    "paid_amount",       # AM (38)
    "remaining_amount",  # AN (39)
    "profit",            # AO (40)
]

# Payment field column names (indices 41-44, AP-AS)
PAYMENT_FIELD_NAMES = [
    "payment_terms",          # AP (41)
    "payment_method",         # AQ (42)
    "payment_method_each",    # AR (43)
    "payment_date",           # AS (44)
]

# Additional master fields (indices 45-51, AT-AZ)
ADDITIONAL_FIELD_NAMES = [
    "order_source",      # AT (45)
    "creator",           # AU (46)
    "status",            # AV (47)
    "customer_group",    # AW (48)
    "refund",            # AX (49)
    "referral_bonus",    # AY (50)
    "risk_level",        # AZ (51)
]

# All field names in order
ALL_FIELD_NAMES = (
    MASTER_FIELD_NAMES + TRACKING_FIELD_NAMES + 
    SERVICE_FIELD_NAMES + PAYMENT_FIELD_NAMES + 
    ADDITIONAL_FIELD_NAMES
)


# ============================================================
# DATA STRUCTURES
# ============================================================

class ImportRow:
    """One raw row from the Excel file."""
    def __init__(self, row_idx: int, values: Dict[str, Any]):
        self.row_idx = row_idx
        self.values = values

    def get(self, key: str, default=None) -> Any:
        v = self.values.get(key)
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return default
        return v

    @property
    def has_master(self) -> bool:
        """Row has master order fields (C = Mã ĐH)."""
        return bool(self.get("shipment_id"))

    @property
    def has_service(self) -> bool:
        """Row has service line fields (R = Mã SP)."""
        return bool(self.get("product_code"))


class ImportGroup:
    """One shipment/order = master row + following detail rows."""
    def __init__(self, master_row: ImportRow):
        self.master = master_row
        self.details: List[ImportRow] = []
        self.status: str = "new"  # new, existing, conflict, unchanged
        self.conflicts: List[str] = []

    @property
    def shipment_id(self) -> str:
        return self.master.get("shipment_id", "")

    @property
    def customer_name(self) -> str:
        return self.master.get("customer_name", "")


class ImportParseResult:
    """Result of parsing an Excel file."""
    def __init__(self):
        self.groups: List[ImportGroup] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.row_count: int = 0
        self.group_count: int = 0

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


class ExportRow:
    """One row in the 52-column export format."""
    def __init__(self):
        self.values: List[Any] = [None] * 52

    def set_master(self, group: ImportGroup, is_first: bool):
        """Set master fields only on first row of group."""
        if not is_first:
            return
        m = group.master
        self.values[0] = m.get("order_date")
        self.values[1] = m.get("created_date")
        self.values[2] = m.get("shipment_id")
        self.values[3] = m.get("executor")
        self.values[4] = m.get("customer_code")
        self.values[5] = m.get("customer_name")
        self.values[6] = m.get("phone")
        self.values[7] = m.get("email")
        self.values[8] = m.get("delivery_address")
        self.values[9] = m.get("contact_person")
        self.values[10] = m.get("contact_phone")
        self.values[11] = m.get("province")
        self.values[12] = m.get("district")
        self.values[13] = m.get("customer_source")

    def set_service(self, detail: ImportRow):
        """Set service line fields."""
        d = detail
        self.values[17] = d.get("product_code")
        self.values[18] = d.get("product_name")
        self.values[19] = d.get("description")
        self.values[20] = d.get("unit")
        self.values[21] = d.get("product_group")
        self.values[22] = d.get("qty")
        self.values[23] = d.get("cost_price")
        self.values[24] = d.get("sale_price")
        self.values[25] = d.get("discount_pct")
        self.values[26] = d.get("discount_amt")
        self.values[27] = d.get("vat_pct")
        self.values[28] = d.get("line_total")
        self.values[29] = d.get("line_profit")
        self.values[30] = d.get("revenue")
        self.values[31] = d.get("discount_vnd")
        self.values[32] = d.get("revenue_after_disc")
        self.values[33] = d.get("shipping_fee")
        self.values[34] = d.get("install_fee")
        self.values[35] = d.get("revenue_pre_tax")
        self.values[36] = d.get("vat_vnd")
        self.values[37] = d.get("total_revenue")
        self.values[38] = d.get("paid_amount")
        self.values[39] = d.get("remaining_amount")
        self.values[40] = d.get("profit")

    def set_payment(self, group: ImportGroup, is_first: bool):
        """Set payment fields on first row of group."""
        if not is_first:
            return
        m = group.master
        self.values[41] = m.get("payment_terms")
        self.values[42] = m.get("payment_method")
        self.values[43] = m.get("payment_method_each")
        self.values[44] = m.get("payment_date")
        self.values[45] = m.get("order_source")
        self.values[46] = m.get("creator")
        self.values[47] = m.get("status")
        self.values[48] = m.get("customer_group")
        self.values[49] = m.get("refund")
        self.values[50] = m.get("referral_bonus")
        self.values[51] = m.get("risk_level")


# ============================================================
# IMPORT: PARSE → GROUP → VALIDATE
# ============================================================

def parse_excel_bytes(file_bytes: bytes) -> ImportParseResult:
    """
    Parse Excel file bytes into grouped ImportGroups.
    Uses calamine engine (handles invalid stylesheet XML).
    """
    result = ImportParseResult()

    try:
        df = pd.read_excel(io.BytesIO(file_bytes), engine="calamine", header=0)
    except Exception as e:
        result.errors.append(f"Lỗi đọc file Excel: {e}")
        return result

    result.row_count = len(df)
    if len(df) == 0:
        result.errors.append("File Excel không có dòng dữ liệu.")
        return result

    # Validate headers
    actual_headers = list(df.columns)
    if len(actual_headers) != 52:
        result.warnings.append(
            f"File có {len(actual_headers)} cột (kỳ vọng 52). "
            "Xuất có thể không tương thích đầy đủ."
        )

    # Map to field names using ALL_FIELD_NAMES (52 columns)
    for row_idx, (_, row) in enumerate(df.iterrows()):
        excel_row = row_idx + 2  # 1-based, +1 for header

        values = {}
        for i in range(min(len(df.columns), len(ALL_FIELD_NAMES))):
            field_name = ALL_FIELD_NAMES[i]
            if i < len(row):
                values[field_name] = row.iloc[i]
            else:
                values[field_name] = None

        import_row = ImportRow(excel_row, values)
        result.groups.append(import_row)

    return result


def group_rows(rows: List[ImportRow]) -> List[ImportGroup]:
    """
    Group rows into shipments:
    - Master row (has shipment_id) starts a new group
    - Detail rows (has product_code but no shipment_id) belong to current group
    """
    groups: List[ImportGroup] = []
    current_group: Optional[ImportGroup] = None

    for row in rows:
        if row.has_master:
            current_group = ImportGroup(row)
            # If this row also has service data, add it as the first detail line
            if row.has_service:
                current_group.details.append(row)
            groups.append(current_group)
        elif row.has_service and current_group is not None:
            current_group.details.append(row)
        elif row.has_service and current_group is None:
            # Detail row without preceding master - orphan (ignored)
            pass
        # Rows with neither master nor service are skipped (blank rows)

    return groups


def validate_groups(groups: List[ImportGroup],
                    existing_shipment_ids: set) -> ImportParseResult:
    """
    Validate grouped data and classify against existing records.
    Does NOT mutate any database.
    """
    result = ImportParseResult()
    result.groups = groups
    result.group_count = len(groups)

    seen_ids: set = set()

    for group in groups:
        sid = group.shipment_id

        # Check for duplicate IDs within the file
        if sid in seen_ids:
            group.status = "conflict"
            group.conflicts.append(f"Trùng Mã ĐH '{sid}' trong file")
            result.warnings.append(f"Trùng Mã ĐH: {sid}")
        else:
            seen_ids.add(sid)

        # Check against existing DB records
        if sid in existing_shipment_ids:
            group.status = "existing"
            result.warnings.append(
                f"Mã ĐH '{sid}' đã tồn tại trong hệ thống. "
                "Import sẽ cập nhật dịch vụ, không ghi đè tài chính."
            )
        else:
            group.status = "new"

        # Validate required fields
        if not sid:
            result.errors.append(
                f"Dòng {group.master.row_idx}: Thiếu Mã ĐH (cột C)"
            )
            group.status = "conflict"

        if not group.customer_name:
            result.warnings.append(
                f"Mã ĐH '{sid}': Thiếu Tên KH (cột F)"
            )

        if not group.details:
            result.warnings.append(
                f"Mã ĐH '{sid}': Không có dòng dịch vụ"
            )

                # Validate financial values
        for detail in group.details:
            # UNKNOWN != ZERO: if price is None, it's unknown, not zero
            if detail.get("sale_price") is None and detail.get("product_code"):
                result.warnings.append(
                    f"  Dòng {detail.row_idx}: Giá bán không xác định (UNKNOWN)"
                )

    return result


# ============================================================
# SERVICE-LINE IDEMPOTENCY: Deterministic matching + dedup
# ============================================================

def _service_line_key(line: Dict[str, Any]) -> Tuple:
    """
    Deterministic identity key for a service line.
    Uses business-critical fields only (not position, not auto-generated IDs).
    
    Identity = (code, name, qty, cost, price)
    
    These are the fields that a human would use to identify "the same service":
    - code: product/service code (e.g., "DVK" = Phí dịch vụ khác)
    - name: product/service name
    - qty: quantity
    - cost: cost price (price_in)
    - price: sale price (price_out)
    
    Fields like VAT, discount, line_total are NOT part of identity because
    they can legitimately change between GETFLY exports (e.g., VAT updated).
    """
    # Normalize name: use 'name' if present, else 'name_full', else 'display_name'
    raw_name = (
        line.get("name")
        or line.get("name_full")
        or line.get("display_name")
        or ""
    )
    
    # Smart normalization: strip "(CODE)" suffix from name
    # This handles the case where existing was manually created with name="X (CODE)"
    # while GETFLY export has name="X" (without suffix)
    # e.g., "Phí dịch vụ khác (DVK)" → "Phí dịch vụ khác"
    import re
    code = str(line.get("code", "")).strip().upper()
    if code:
        # Remove trailing " (CODE)" or " (code)" from the name
        cleaned = re.sub(rf"\s*\({re.escape(code)}\)\s*$", "", raw_name, flags=re.IGNORECASE).strip()
    else:
        cleaned = str(raw_name).strip()
    
    return (
        str(line.get("code", "")).strip(),
        cleaned,
        line.get("qty", 0),
        line.get("cost", 0),
        line.get("price", 0),
    )


def classify_service_lines(
    existing_details: List[Dict[str, Any]],
    incoming_details: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Classify incoming service lines against existing canonical lines.
    
    Returns:
        (same_lines, new_lines, conflict_lines, ambiguous_lines)
        
    Rules:
    - EXISTING_SAME: identical identity key → skip (do NOT append)
    - NEW_SERVICE: identity key not found → append once
    - CONFLICT: same identity key but materially different values
      (e.g., VAT changed) → flag for Owner review, do NOT silently overwrite
    - AMBIGUOUS: cannot determine → flag for Owner review
    """
    existing_keys = set(_service_line_key(d) for d in existing_details)
    existing_by_key = [(_service_line_key(d), d) for d in existing_details]
    
    same_lines = []
    new_lines = []
    conflict_lines = []
    ambiguous_lines = []
    
    # Track which existing lines have been consumed (one-to-one matching)
    consumed_indices = set()
    
    for inc_line in incoming_details:
        inc_key = _service_line_key(inc_line)
        
        if inc_key in existing_keys:
            # Find the matching existing line (one-to-one: skip already consumed)
            matching_ex = None
            matching_idx = None
            for idx, (k, d) in enumerate(existing_by_key):
                if k == inc_key and idx not in consumed_indices:
                    matching_ex = d
                    matching_idx = idx
                    break
            
            if matching_ex is None:
                ambiguous_lines.append(inc_line)
                continue
            
            # Mark this existing line as consumed
            if matching_idx is not None:
                consumed_indices.add(matching_idx)
            
            # Check for material differences beyond identity fields
            material_fields = ["vat", "vat_line", "discount_pct", "discount_amt",
                             "note", "unit", "product_group", "display_name"]
            has_material_diff = False
            for field in material_fields:
                inc_val = inc_line.get(field)
                ex_val = matching_ex.get(field)
                # Skip if both are None/empty
                if inc_val is None and ex_val is None:
                    continue
                if str(inc_val) != str(ex_val):
                    has_material_diff = True
                    break
            
            if has_material_diff:
                # Same identity but values changed → CONFLICT (needs review)
                conflict_lines.append(inc_line)
            else:
                # Truly identical → EXISTING_SAME (skip)
                same_lines.append(inc_line)
        else:
            # New service line → append
            new_lines.append(inc_line)
    
    return same_lines, new_lines, conflict_lines, ambiguous_lines


def merge_details_idempotent(
    existing_details: List[Dict[str, Any]],
    incoming_details: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Merge incoming details into existing, with full idempotency.
    
    Returns:
        (merged_details, stats)
        where stats = {"same": N, "new": N, "conflict": N, "ambiguous": N}
    """
    same, new, conflict, ambiguous = classify_service_lines(
        existing_details, incoming_details
    )
    
    # Start with existing (preserve all)
    merged = list(existing_details)
    
    # Append only NEW lines
    merged.extend(new)
    
    # Conflicts and ambiguous: do NOT auto-merge, flag for review
    stats = {
        "same": len(same),
        "new": len(new),
        "conflict": len(conflict),
        "ambiguous": len(ambiguous),
    }
    
    return merged, stats


# ============================================================
# EXPORT: Canonical → 52-column Excel
# ============================================================
def shipment_to_export_rows(ship: Dict[str, Any]) -> List[ExportRow]:
    """
    Convert a canonical shipment document to 52-column export rows.
    One master row + one row per service line.
    """
    rows: List[ExportRow] = []
    data = ship.get("data", {})
    master_data = data.get("0.0", {})
    finance_data = data.get("3.4", {})
    details = finance_data.get("details", [])
    payments = finance_data.get("payments", [])

    # Payment history (flattened)
    payment_methods = ",".join(
        str(p.get("method", "")) for p in payments if p.get("method")
    )
    payment_dates = ",".join(
        str(p.get("date", "")) for p in payments if p.get("date")
    )
    paid_total = finance_data.get("paid", 0)

    for i, detail in enumerate(details):
        row = ExportRow()
        is_first = (i == 0)

        # Master fields (only on first row)
        row.values[0] = master_data.get("order_date", ship.get("created_at", ""))
        row.values[1] = ship.get("created_at", "")
        row.values[2] = ship.get("id", "")
        row.values[3] = master_data.get("executor", "")
        row.values[4] = ship.get("customer_id", "")
        row.values[5] = ship.get("customer", "")
        row.values[6] = master_data.get("phone", "")
        row.values[7] = master_data.get("email", "")
        row.values[8] = master_data.get("delivery_address", "")
        row.values[9] = master_data.get("contact_person", "")
        row.values[10] = master_data.get("contact_phone", "")
        row.values[11] = master_data.get("province", "")
        row.values[12] = master_data.get("district", "")
        row.values[13] = master_data.get("customer_source", "")
        row.values[14] = master_data.get("tracking_no", "")  # O
        row.values[15] = master_data.get("tracking_status", "")  # P
        row.values[16] = master_data.get("warehouse_code", "")  # Q

        # Service fields
        row.values[17] = detail.get("code", "")  # R
        row.values[18] = detail.get("name", "")  # S
        row.values[19] = detail.get("note", "")  # T
        row.values[20] = detail.get("unit", "")  # U
        row.values[21] = detail.get("product_group", "")  # V
        row.values[22] = detail.get("qty", 0)  # W
        row.values[23] = detail.get("cost", 0)  # X
        row.values[24] = detail.get("price", 0)  # Y
        row.values[25] = detail.get("discount_pct", 0)  # Z
        row.values[26] = detail.get("discount_amt", 0)  # AA
        row.values[27] = detail.get("vat", 0)  # AB
        row.values[28] = detail.get("line_total", 0)  # AC
        row.values[29] = detail.get("profit", 0)  # AD
        row.values[30] = detail.get("revenue", 0)  # AE
        row.values[31] = detail.get("discount_vnd", 0)  # AF
        row.values[32] = detail.get("revenue_after_disc", 0)  # AG
        row.values[33] = detail.get("shipping_fee", 0)  # AH
        row.values[34] = detail.get("install_fee", 0)  # AI
        row.values[35] = detail.get("revenue_pre_tax", 0)  # AJ
        row.values[36] = detail.get("vat_vnd", 0)  # AK
        row.values[37] = detail.get("total_revenue", 0)  # AL
        row.values[38] = detail.get("paid", 0)  # AM
        row.values[39] = detail.get("debt", 0)  # AN
        row.values[40] = detail.get("profit", 0)  # AO

        # Payment fields (only on first row)
        row.values[41] = finance_data.get("payment_terms", "")  # AP
        row.values[42] = finance_data.get("payment_method", "")  # AQ
        row.values[43] = payment_methods  # AR
        row.values[44] = payment_dates  # AS
        row.values[45] = master_data.get("order_source", "")  # AT
        row.values[46] = ship.get("updated_by", "")  # AU
        row.values[47] = ship.get("status", "")  # AV
        row.values[48] = master_data.get("customer_group", "")  # AW
        row.values[49] = master_data.get("refund", "")  # AX
        row.values[50] = master_data.get("referral_bonus", "")  # AY
        row.values[51] = master_data.get("risk_level", "")  # AZ

        rows.append(row)

    return rows


def export_to_excel_bytes(ships: List[Dict[str, Any]]) -> bytes:
    """
    Export shipments to 52-column Excel format.
    Returns bytes of the xlsx file.
    """
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"

    # Header row
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=10)
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    for col_idx, header in enumerate(HEADERS_52, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    # Data rows
    current_row = 2
    for ship in ships:
        export_rows = shipment_to_export_rows(ship)
        for row in export_rows:
            for col_idx, value in enumerate(row.values, 1):
                if value is not None and value != "":
                    cell = ws.cell(row=current_row, column=col_idx, value=value)
                    cell.border = thin_border
                    if col_idx in (23, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40):
                        # Numeric columns
                        cell.number_format = "#,##0"
            current_row += 1

    # Set column widths
    widths = [12, 12, 35, 15, 10, 30, 12, 25, 35, 15, 15, 12, 12, 15,
              12, 12, 10, 8, 25, 30, 8, 15, 8, 12, 12, 8, 12, 8, 15,
              12, 15, 12, 15, 12, 12, 15, 10, 15, 15, 12, 12, 20, 15,
              20, 18, 12, 15, 10, 15, 8, 15, 12]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    # Freeze top row
    ws.freeze_panes = "A2"

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# ============================================================
# CONVERSION HELPERS: ImportGroup → Canonical shipment doc
# ============================================================

def group_to_shipment_doc(group: ImportGroup) -> Dict[str, Any]:
    """
    Convert an ImportGroup to a canonical shipment document.
    Used during the WRITE phase of import (after user confirmation).
    """
    sid = group.shipment_id
    data = {
        "0.0": {
            "created_at": group.master.get("created_date"),
            "order_date": group.master.get("order_date"),
            "executor": group.master.get("executor"),
            "customer_code": group.master.get("customer_code"),
            "phone": group.master.get("phone"),
            "email": group.master.get("email"),
            "delivery_address": group.master.get("delivery_address"),
            "contact_person": group.master.get("contact_person"),
            "contact_phone": group.master.get("contact_phone"),
            "province": group.master.get("province"),
            "district": group.master.get("district"),
            "customer_source": group.master.get("customer_source"),
        },
        "3.4": {
            "details": [],
            "commission": {"total": 0, "list": []},
            "payments": [],
            "currency": "VND",
        },
    }

    # Service lines
    total_out = 0.0
    total_in = 0.0
    total_paid = 0.0
    total_profit = 0.0

    for detail in group.details:
        line = {
            "code": detail.get("product_code", ""),
            "name": detail.get("product_name", ""),
            "display_name": detail.get("product_name", ""),
            "name_full": detail.get("product_name", ""),
            "note": detail.get("description", ""),
            "unit": detail.get("unit", ""),
            "product_group": detail.get("product_group", ""),
            "qty": safe_num(detail.get("qty")),
            "cost": safe_num(detail.get("cost_price")),
            "price": safe_num(detail.get("sale_price")),
            "price_in": safe_num(detail.get("cost_price")),
            "price_out": safe_num(detail.get("sale_price")),
            "vat": safe_num(detail.get("vat_pct")),
            "vat_line": safe_num(detail.get("vat_pct")),
            "discount_pct": safe_num(detail.get("discount_pct")),
            "discount_amt": safe_num(detail.get("discount_amt")),
            "line_total": safe_num(detail.get("line_total")),
            "profit": safe_num(detail.get("line_profit")),
        }
        data["3.4"]["details"].append(line)
        total_out += line.get("price_out", 0) * line.get("qty", 0)
        total_in += line.get("price_in", 0) * line.get("qty", 0)
        total_profit += line.get("profit", 0)
        total_paid += safe_num(detail.get("paid_amount"))

    data["3.4"]["out"] = total_out
    data["3.4"]["in"] = total_in
    data["3.4"]["paid"] = total_paid
    data["3.4"]["debt"] = max(0, total_out - total_paid)
    data["3.4"]["profit"] = total_profit

    doc = {
        "id": sid,
        "shipment_id": sid,
        "client": group.customer_name,
        "customer": group.customer_name,
        "created_at": group.master.get("created_date"),
        "status": group.master.get("status", "pending"),
        "data": data,
        "is_archived": False,
        "is_deleted": False,
        "version": 1,
    }

    return doc


def safe_num(value: Any) -> float:
    """Convert value to number, treating None/empty as UNKNOWN (return 0 but flag)."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return 0.0
        return float(value)
    try:
        s = str(value).replace(",", "").strip()
        return float(s)
    except (ValueError, TypeError):
        return 0.0
