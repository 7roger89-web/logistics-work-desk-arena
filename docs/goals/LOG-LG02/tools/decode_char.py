"""Decoder chu-ly-ky-tu cho mojibake — mojet bai boc tuong minh.

Quy tac: moi ky tu trong file mojibake duoc chuyen thanh byte goc:
- 0x80..0x9F: cp1252 artifact -> byte tuong ung (80..9F)
- 0xA0..0xFF: byte truc tiep (A0..FF)
- Khac: UTF-8 binh thuong.
Sau do:
- fix_nbsp_loss: byte lead (C0..DF) truoc continuation khong hop le ->
  gia dinh continuation la A0 (NBSP bi thay bang space).
- Pass 2: decode latin-1; ky tu 0x80..0xFF con sot -> byte.
- Cuoi cung: ky tu 0xFFFD khong the phuc hoi tu dong -> danh dau,
  sua bang bang anh xa thu cong trong fix_replacement_chars.py.
"""
from __future__ import annotations

_ARTIFACT_MAP: dict[str, int] = {
    "€": 0x80, "‚": 0x82, "ƒ": 0x83, "„": 0x84, "…": 0x85, "†": 0x86,
    "‡": 0x87, "ˆ": 0x88, "‰": 0x89, "Š": 0x8A, "‹": 0x8B, "Œ": 0x8C,
    "Ž": 0x8E, "‘": 0x91, "’": 0x92, "“": 0x93, "”": 0x94, "•": 0x95,
    "–": 0x96, "—": 0x97, "˜": 0x98, "™": 0x99, "š": 0x9A, "›": 0x9B,
    "œ": 0x9C, "ž": 0x9E, "Ÿ": 0x9F,
    # U+00A0 (NBSP) da bi chuan hoa thanh space trong mot so truong hop;
    # nhung NBSP that (byte A0 goc) cung map ve byte A0.
}
_ARTIFACT_MAP[" "] = 0xA0  # khong dung — space that khong the phan biet!


def decode_text(text: str) -> str:
    buf = bytearray()
    for char in text:
        code = ord(char)
        if 0x0080 <= code <= 0x00FF:
            buf.append(code)
        elif char in _ARTIFACT_MAP and char != " ":
            buf.append(_ARTIFACT_MAP[char])
        else:
            buf.extend(char.encode("utf-8"))

    # NBSP-loss: lead byte C0..DF truoc byte khong phai 80..BF -> A0
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
