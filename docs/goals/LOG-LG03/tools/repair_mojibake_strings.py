#!/usr/bin/env python3
"""LG03: Tự động sửa mojibake dạng double-encoding UTF-8 trong string literal Python.

Cơ chế: với mỗi string literal, thử decode chuỗi bytes UTF-8 'giả latin-1':
    text.encode('utf-8').decode('latin-1')  -> chuỗi mojibake hiển thị
nghịch đảo: chuỗi hiển thị (mojibake) encode('utf-8').decode('latin-1') -> văn bản gốc.
Điều kiện áp dụng:
 - chuỗi chứa ít nhất 2 cặp byte mojibake điển hình (\xc3\x83, \xc4\x90\xc3\x83, \xc3\xa1\xc2\xba...)
 - kết quả nghịch đảo phải là chuỗi hợp lệ chứa chữ có dấu tiếng Việt
 - kết quả phải round-trip được (encode utf-8 -> decode latin-1 -> encode utf-8 == ban đầu)
 - không chạm các file ngoài danh sách được phép
An toàn: mặc định dry-run (--apply để ghi), backup .mojibake.bak.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

# Marker bytes điển hình của chuỗi mojibake double-encoded (UTF-8 bị đọc lại thành latin-1 rồi encode lần 2)
MOJI_MARKERS = [b'\xc3\xa1\xc2\xba', b'\xc3\xa1\xc2\xbb', b'\xc3\x83\xc2\xa1', b'\xc3\x83\xc2\xba', b'\xc3\x83\xc2\xb9', b'\xc3\x83\xc2\xaa', b'\xc3\x83\xc2\xb4', b'\xc3\x83\xc2\xaf', b'\xc3\x83\xc2\xb3', b'\xc3\xa1\xc2\xa2', b'\xc3\x83\xc2\xa2', b'\xc3\x83\xc2\xb0', b'\xc3\x83\xc2\xad', b'\xc3\x83\xc2\xb7', b'\xc3\x83\xc2\xa0']


def looks_mojibake(text: str) -> bool:
    b = text.encode('utf-8')
    return any(m in b for m in MOJI_MARKERS)


SMART_Q = {'\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"', '\u2039': '<', '\u203a': '>'}
NBSP_MOJI = '\u00c2\u00a0'  # mojibake của NBSP (\xc2\xa0) — giữ nguyên NBSP gốc


def _normalize_mojibake_for_decode(text: str) -> str:
    """Xử lý các ký tự hiển thị mojibake không phải là double-encoding chuẩn.
    NBSP (\u00a0) bị double-encode thành \u00c2\u00a0 (hai ký tự nhìn giống 'Â + ').
    Khôi phục về NBSP gốc để round-trip đúng."""
    out = []
    i = 0
    while i < len(text):
        if text[i:i + 2] == NBSP_MOJI and (i == 0 or text[i - 1] != '\u00c2'):
            out.append('\u00a0')
            i += 2
        else:
            out.append(text[i])
            i += 1
    return ''.join(out)


def reverse_double_encoding(text: str) -> str | None:
    """Mojibake = utf8(original).decode('latin-1') -> hiển thị sai.
    Khôi phục: displayed.encode('latin-1').decode('utf-8') = original."""
    try:
        normalized = ''.join(SMART_Q.get(c, c) for c in _normalize_mojibake_for_decode(text))
        original = normalized.encode('latin-1').decode('utf-8')
    except Exception:
        return None
    # Verify round-trip và phải chứa dấu tiếng Việt hợp lệ
    try:
        if original.encode('utf-8').decode('latin-1') != text:
            return None
    except Exception:
        return None
    if not re.search(r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ]', original):
        return None
    # Không được chứa control chars lạ sau reverse
    if '\ufffd' in original or '\x7f' in original or not all(ord(c) < 0x2000 or c in ('‘', '’', '“', '”', '‹', '›') for c in original):
        return None
    return original


def fix_file(path: Path, apply: bool) -> int:
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    replacements = []  # (start, end, new_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if not looks_mojibake(v):
                continue
            fixed = reverse_double_encoding(v)
            if fixed is None or fixed == v:
                continue
            # ast node positions dùng để thay trực tiếp trong source
            replacements.append((node.lineno, node.col_offset, node.end_lineno, node.end_col_offset, fixed))
    if not replacements:
        return 0
    lines = source.split('\n')
    # thay từ dưới lên trên để không lệch offset
    for ln1, col1, ln2, col2, fixed in sorted(replacements, key=lambda r: (r[0], r[1]), reverse=True):
        r1, r2 = ln1 - 1, ln2 - 1
        old = '\n'.join(lines[r1:r2 + 1])
        # trích phần nằm giữa (col1, col2)
        if r1 == r2:
            seg = lines[r1][col1:col2]
        else:
            seg = lines[r1][col1:] + '\n' + '\n'.join(lines[r1 + 1:r2]) + '\n' + lines[r2][:col2]
        if seg.startswith(('"', "'")) and seg.endswith(('"', "'")) and seg[0] == seg[-1]:
            quote = seg[0]
            new_seg = quote + fixed + quote
        else:
            new_seg = '"' + fixed.replace('\\', '\\\\').replace('"', '\\"') + '"'
        if r1 == r2:
            lines[r1] = lines[r1][:col1] + new_seg + lines[r1][col2:]
        else:
            head = lines[r1][:col1]
            tail = lines[r2][col2:]
            lines[r1] = head + new_seg
            for i in range(r1 + 1, r2 + 1):
                lines[i] = None
            lines[r2] = tail
    lines = [ln for ln in lines if ln is not None]
    new_source = '\n'.join(lines)
    try:
        ast.parse(new_source)
    except SyntaxError as e:
        print(f"SYNTAX ERROR sau thay đổi {path}: {e}")
        return -1
    if apply:
        backup = path.with_suffix(path.suffix + '.mojibake.bak')
        backup.write_text(source, encoding='utf-8')
        path.write_text(new_source, encoding='utf-8')
    print(f"{'APPLIED' if apply else 'WOULD FIX'}: {path.relative_to(REPO)} — {len(replacements)} chuỗi")
    return len(replacements)


def main() -> None:
    apply_mode = '--apply' in sys.argv
    targets = [
        'views/review_queue.py', 'views/shipment.py', 'views/shipment_360.py',
        'views/proxy_payment.py', 'views/entrustment.py',
        'core/database.py', 'core/shipment_dashboard.py', 'core/excel_utils.py',
        'core/getfly_reader.py', 'core/shipment_360.py',
        'core/commercial_agreements.py', 'core/config.py',
    ]
    total = 0
    for t in targets:
        p = REPO / t
        if p.exists():
            total += fix_file(p, apply_mode)
    print(f"\nTotal strings: {total}")


if __name__ == '__main__':
    main()
