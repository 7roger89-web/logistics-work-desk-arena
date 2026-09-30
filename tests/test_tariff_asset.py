from __future__ import annotations

import io
import lzma
import sqlite3

from openpyxl import Workbook

from core.tariff_asset import build_tariff_asset


def _workbook_bytes() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "BT2026"
    for _ in range(3):
        ws.append([None] * 39)

    row = [None] * 39
    row[0] = "01"
    row[1] = "01012900"
    row[2] = "Ngựa sống loại khác"
    row[3] = "con"
    row[4] = "5"
    row[5] = "0"
    row[6] = "8"
    row[37] = "Kiểm dịch động vật"
    row[38] = "Giảm 2% VAT"
    ws.append(row)

    out = io.BytesIO()
    wb.save(out)
    wb.close()
    return out.getvalue()


def test_admin_xlsx_builds_indexed_sqlite(tmp_path):
    built = build_tariff_asset(
        _workbook_bytes(),
        source_filename="BIEU THUE XNK 2026.xlsx",
    )

    assert built["metadata"]["indexed_rows"] == 1
    assert built["metadata"]["source_sheet"] == "BT2026"
    assert built["metadata"]["year"] == "2026"
    assert len(built["db_sha256"]) == 64
    assert len(built["payload_lzma"]) < len(lzma.decompress(built["payload_lzma"]))

    db_path = tmp_path / "tariff.db"
    db_path.write_bytes(lzma.decompress(built["payload_lzma"]))

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            'SELECT "Mã HS", "NK ưu đãi", "VAT", "Chính sách mặt hàng" '
            'FROM tariff_table WHERE "Mã HS" = ?',
            ("01012900",),
        ).fetchone()
        assert row == ("01012900", "0", "8", "Kiểm dịch động vật")

        index_names = {
            item[1] for item in conn.execute("PRAGMA index_list(tariff_table)")
        }
        assert "idx_tariff_hs" in index_names

        match = conn.execute(
            """
            SELECT t."Mã HS"
            FROM tariff_fts
            JOIN tariff_table AS t ON t.id = tariff_fts.rowid
            WHERE tariff_fts MATCH ?
            """,
            ('"kiểm"*',),
        ).fetchone()
        assert match == ("01012900",)


def test_builder_skips_heading_rows_without_hs_codes():
    built = build_tariff_asset(
        _workbook_bytes(),
        source_filename="BIEU THUE XNK 2026.xlsx",
    )
    assert built["metadata"]["source_rows"] == 4
    assert built["metadata"]["indexed_rows"] == 1
