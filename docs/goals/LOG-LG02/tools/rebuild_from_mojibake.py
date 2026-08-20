"""Xay dung lai file .py sach tu ban mojibake goc trong commit 83a567c.

Tai sao: phien ban hien tai trong repo (sau PR #1 merge) CHINH LA ban
mojibake. Bo decoder truoc da tao ra U+FFFD o nhung cho khong phuc hoi duoc.
Cach tot nhat: lay string mojibake GOC (encode: utf-8 -> decode latin-1 ->
encode utf-8 lai), giai ma nguoc lai = encode cp1252 -> decode utf-8.

Thu nghiem: "Táº¡o LÃ´ Má»›i" encode('cp1252').decode('utf-8') = "Tạo Lô Mới".
Mot so ky tu bi mat byte (NBSP-loss) -> bo sung heuristics nhu decode_char.py.
U+FFFD con sot -> sua thu cong.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
MOJIBAKE_SHA = "83a567c"  # PR #1 merge — chua file mojibake goc


def get_mojibake(rel: str) -> str:
    r = subprocess.run(
        ["git", "show", f"{MOJIBAKE_SHA}:{rel}"],
        capture_output=True, cwd=str(REPO),
    )
    if r.returncode != 0:
        raise RuntimeError(f"khong lay duoc {rel}: {r.stderr.decode()}")
    return r.stdout.decode("utf-8")


def decode(text: str) -> str:
    # cp1252 -> bytes -> utf-8, voi fallback replace
    out_chars = []
    for char in text:
        code = ord(char)
        if char == " ":
            # space co the la NBSP goc (0xA0) — giu byte space, pass sau sua NBSP
            out_chars.append(b" ")
            continue
        if 0x0080 <= code <= 0x00FF and char in (
            "€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•–—˜™š›œžŸ"
            "\u0080\u0081\u0082\u0083\u0084\u0085\u0086\u0087\u0088\u0089"
            "\u008a\u008b\u008c\u008e\u0091\u0092\u0093\u0094\u0095\u0096"
            "\u0097\u0098\u0099\u009a\u009b\u009c\u009e\u009f\u00a0\u00a1"
            "\u00a2\u00a3\u00a4\u00a5\u00a6\u00a7\u00a8\u00a9\u00aa\u00ab"
            "\u00ac\u00ae\u00af\u00b0\u00b1\u00b2\u00b3\u00b4\u00b5\u00b6"
            "\u00b7\u00b8\u00b9\u00ba\u00bb\u00bc\u00bd\u00be\u00bf"
        ):
            out_chars.append(bytes([code]))
        else:
            out_chars.append(char.encode("utf-8"))
    buf = b"".join(out_chars)
    # NBSP-loss repair: lead C0..DF truoc byte khong hop le -> A0
    fixed = bytearray()
    i = 0
    n = len(buf)
    while i < n:
        byte = buf[i]
        if 0xC0 <= byte <= 0xDF and i + 1 < n:
            nxt = buf[i + 1]
            if not (0x80 <= nxt <= 0xBF):
                fixed.append(byte)
                fixed.append(0xA0 if nxt == 0x20 else nxt)
                i += 2
                continue
        if 0xE0 <= byte <= 0xEF and i + 2 < n:
            a, b = buf[i + 1], buf[i + 2]
            if not (0x80 <= a <= 0xBF and 0x80 <= b <= 0xBF):
                fixed.append(byte)
                fixed.append(a if 0x80 <= a <= 0xBF else (0xA0 if a == 0x20 else a))
                fixed.append(b if 0x80 <= b <= 0xBF else (0xA0 if b == 0x20 else b))
                i += 3
                continue
        fixed.append(byte)
        i += 1
    chars = []
    for char in fixed.decode("latin-1"):
        code = ord(char)
        if 0x0080 <= code <= 0x00FF:
            chars.append(char.encode("latin-1"))
        else:
            chars.append(char.encode("utf-8"))
    return b"".join(chars).decode("utf-8", errors="replace")


MANUAL = {
    "Thỏa Thuận & B\ufffdn\ufffdGiao": "Thỏa Thuận & Bàn Giao",
    "Kh\ufffdch H\ufffdng": "Khách Hàng",
    "B\ufffdo Gi\ufffd": "Báo Giá",
    "B\ufffdo gi\ufffd": "Báo giá",
    "ng\ufffdi d\ufffdng": "người dùng",
    "cho ph\ufffdp": "cho phép",
    "ghi \ufffdè": "ghi đè",
    "B\ufffdt AUTH_REQUIRED": "Bật AUTH_REQUIRED",
    "b\ufffdng": "bảng",
    "B\ufffdng": "Bảng",
    "th\ufffdy": "thấy",
    "g\ufffd": "gì",
    "G\ufffd": "Gì",
    "v\ufffd": "và",
    "V\ufffd": "Và",
    "kh\ufffd": "khó",
    "th\ufffd": "thể",
    "Th\ufffd": "Thể",
    "h\ufffd": "hàm",
    "m\ufffd": "mở",
    "M\ufffd": "Mở",
    "d\ufffd": "dữ",
    "D\ufffd": "Dữ",
    "t\ufffd": "tìm",
    "T\ufffd": "Tìm",
    "l\ufffd": "lỗi",
    "c\ufffd": "có",
    "C\ufffd": "Có",
    "ph\ufffd": "phép",
    "Ph\ufffd": "Phép",
    "k\ufffd": "khóa",
    "n\ufffd": "nội",
    "N\ufffd": "Nội",
    "x\ufffd": "xóa",
    "X\ufffd": "Xóa",
    "t\ufffdn": "tồn",
    "s\ufffd": "sẵn",
    "S\ufffd": "Sẵn",
    "đ\ufffd": "đã",
    "Đ\ufffd": "Đã",
    "t\ufffdo": "tạo",
    "T\ufffdo": "Tạo",
    "o\ufffd": "ời",
    "O\ufffd": "Ờ",
    "á\ufffd": "áp",
    "Á\ufffd": "Áp",
    "u\ufffd": "ủ",
    "U\ufffd": "Ủ",
    "i\ufffd": "ỉ",
    "e\ufffd": "ể",
    "E\ufffd": "Ể",
    "ư\ufffd": "ừ",
    "a\ufffd": "ả",
    "A\ufffd": "Ả",
    "ă\ufffd": "ằn",
    "ă\ufffdn": "ằn",
    "ơ\ufffd": "ờ",
    "ô\ufffd": "ổ",
    "Ô\ufffd": "Ổ",
    "ơ\ufffdi": "ời",
    "ư\ufffd": "ử",
    "ư\ufffd d\ufffd": "ử d",
    "o\ufffdng": "ộng",
    "a\ufffdo": "ào",
    "A\ufffdo": "À",
    "ă\ufffd": "ắ",
    "u\ufffdng": "ùng",
    "a\ufffdnh": "ành",
    "a\ufffdn": "àn",
    "A\ufffdn": "À",
    "ă\ufffdng": "ắng",
    "o\ufffdn": "òn",
    "a\ufffdm": "ảm",
    "a\ufffdc": "ắc",
    "u\ufffda": "ủa",
    "a\ufffdt": "ắt",
    "a\ufffdng": "ảng",
    "ă\ufffdng": "ẳng",
    "u\ufffdi": "ủi",
    "a\ufffdo": "ảo",
    "ă\ufffdi": "ải",
    "o\ufffdi": "ỏi",
    "e\ufffdu": "ểu",
    "i\ufffdu": "iểu",
    "a\ufffdy": "ảy",
    "ă\ufffdy": "ẩy",
    "a\ufffdu": "ầu",
    "u\ufffdu": "ựu",
    "u\ufffdc": "ực",
    "ă\ufffdc": "ắc",
    "a\ufffdc": "ặc",
    "o\ufffdc": "ộc",
    "ă\ufffdu": "ấu",
    "e\ufffdc": "ệc",
    "i\ufffdc": "iệc",
    "ă\ufffdp": "ấp",
    "u\ufffdp": "ụp",
    "ă\ufffdt": "ặt",
    "ă\ufffdm": "ặm",
    "ă\ufffdn": "ặn",
    "u\ufffdn": "ụn",
    "ă\ufffd": "ặ",
    "a\ufffd": "ạ",
    "A\ufffd": "Ạ",
    "ă\ufffd": "ắ",
    "e\ufffd": "ẹ",
    "i\ufffd": "ị",
    "o\ufffd": "ọ",
    "u\ufffd": "ụ",
    "y\ufffd": "ỵ",
    "ă\ufffd": "ẵ",
    "ư\ufffd": "ữ",
    "ê\ufffd": "ệ",
    "ô\ufffd": "ộ",
    "ơ\ufffd": "ợ",
    "ư\ufffd": "ự",
}

# Danh sach file .py can xay dung lai (tu mojibake goc 83a567c).
FILES = [
    "views/web_app.py",
    "core/database.py",
]


def fix_manual(text: str) -> str:
    for old, new in MANUAL.items():
        text = text.replace(old, new)
    # NBSP -> space (an toan trong source code)
    text = text.replace("\u00a0", " ")
    return text


def main() -> None:
    for rel in FILES:
        moj = get_mojibake(rel)
        fixed = decode(moj)
        fixed = fix_manual(fixed)
        fffd = fixed.count("\ufffd")
        dest = REPO / rel
        fixed.encode("utf-8")  # validate
        compile(fixed, str(dest), "exec")
        dest.write_text(fixed, encoding="utf-8")
        print(f"{rel}: fffd_remaining={fffd} LEN={len(fixed)}", flush=True)
        if fffd:
            import re
            for m in re.finditer(r".{25}\ufffd.{25}", fixed):
                print("  REMAIN:", repr(m.group(0)), flush=True)


if __name__ == "__main__":
    main()
