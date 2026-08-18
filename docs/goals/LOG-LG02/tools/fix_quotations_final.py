"""Giai ma views/quotations.py — decoder hieu dung cho blob hon hop
(char tieng Viet sach 0x80-0xFF + mojibake glyph).

Thuat toan tham-lam: tai moi vi tri, thu phan doan lien tiep ky tu
(0x80-0xFF hoac artifact glyph) dai nhat ma bytes phat ra hop le utf-8.
Neu duoc → giai ma doan do thanh text goc. Neu khong → ky tu hien tai
la char sach > khong phai mojibake → phat utf-8 bytes cua no, tien 1.

Artifact glyph (e.g. ‘=U+2018, ƒ=U+0192) phat byte cp1252 tuong ung.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

ARTIFACT_MAP = {
    "€": 0x80, "‚": 0x82, "ƒ": 0x83, "„": 0x84, "…": 0x85, "†": 0x86,
    "‡": 0x87, "ˆ": 0x88, "‰": 0x89, "Š": 0x8A, "‹": 0x8B, "Œ": 0x8C,
    "Ž": 0x8E, "‘": 0x91, "’": 0x92, "“": 0x93, "”": 0x94, "•": 0x95,
    "–": 0x96, "—": 0x97, "˜": 0x98, "™": 0x99, "š": 0x9A, "›": 0x9B,
    "œ": 0x9C, "ž": 0x9E, "Ÿ": 0x9F,
}


def char_byte(char: str):
    """Byte phat ra cho ky tu nghi mojibake; None neu khong phai."""
    o = ord(char)
    if 0x0080 <= o <= 0x00FF:
        return o
    if char in ARTIFACT_MAP:
        return ARTIFACT_MAP[char]
    return None


def is_valid_utf8(b: bytes) -> bool:
    try:
        b.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def decode(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        b = char_byte(c)
        if b is None:
            # char sach (thuoc ASCII hoac unicode > 0xFF khong phai glyph)
            out.append(c)
            i += 1
            continue
        # thu phan doan dai nhat bat dau tai i ma bytes hop le utf-8
        best = None
        buf = bytearray()
        j = i
        while j < n:
            bb = char_byte(text[j])
            if bb is None:
                break
            buf.append(bb)
            if is_valid_utf8(buf):
                best = (buf.decode("utf-8"), j + 1)
            j += 1
        if best is not None:
            out.append(best[0])
            i = best[1]
        else:
            # ky tu nay khong bat dau duoc doan mojibake hop le → sach
            out.append(c)
            i += 1
    return "".join(out)


def main() -> None:
    rel = "views/quotations.py"
    r = subprocess.run(
        ["git", "show", "83a567c:" + rel],
        capture_output=True, cwd=str(REPO),
    )
    assert r.returncode == 0, r.stderr.decode()
    src = r.stdout.decode("utf-8")

    dec = decode(src)
    if dec.startswith("\ufeff"):
        dec = dec[1:]
    p = REPO / rel
    compile(dec, str(p), "exec")
    p.write_text(dec, encoding="utf-8")

    import re
    print(f"{rel}: fffd={dec.count(chr(0xfffd))} len={len(dec)}", flush=True)
    moj = re.findall(r"KhÃ|LÃ´|Táº|Báº|cháº|triá»|Ä\x90|khng|b o gi", dec)
    print("mojibake samples remaining:", len(moj))
    for k in ["Khách hàng", "Lô {index", "Tạo", "Đã gửi khách", "Khách chốt",
              "tài chính", "Báo giá", "Khách hỏi giá", "thu thập thông tin",
              "Bạn không có quyền", "thay đổi báo giá", "Trung Quốc",
              "Điện thoại", "Số tiền", "đang theo dõi", "một báo giá"]:
        print(("OK " if k in dec else "MISS"), k)


if __name__ == "__main__":
    main()
