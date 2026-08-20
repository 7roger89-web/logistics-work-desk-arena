"""Sua 2 file cuoi cung bi mojibake trong repo.

1. views/quotations.py: decode BLOB SACH tu commit 83a567c, cp1252->utf-8.
2. core/database.py: thay dong ConcurrentUpdateError bi mojibake.

BUG DA SUA: NBSP-loss heuristic truoc day ap dung ca cho byte cua ky tu
unicode >0xFF (vd 'á' = E1... khong, 'a' + E1 lead) -> pha chuoi dung.
Bay gio: heuristic chi ap dung cho byte nghi ng (mojibake glyph hoac byte
0x80-0xFF doc lap), khong cho byte tin cay tu utf-8-encode ky tu > 0xFF.
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


def decode(text: str) -> str:
    # pass 0: build byte list with trust tags
    #  (suspect = single-byte mojibake; trusted = utf-8 of valid unicode char)
    suspect_bytes = bytearray()
    trusted_bytes = bytearray()
    for char in text:
        o = ord(char)
        if char == " ":
            suspect_bytes.append(0x20)
        elif 0x0080 <= o <= 0x00FF:
            suspect_bytes.append(o)
        elif char in ARTIFACT_MAP:
            suspect_bytes.append(ARTIFACT_MAP[char])
        else:
            trusted_bytes += char.encode("utf-8")

    # pass 1: NBSP-loss heuristic ONLY on suspect bytes
    fixed = bytearray()
    i = 0
    n = len(suspect_bytes)
    while i < n:
        b = suspect_bytes[i]
        if 0xC0 <= b <= 0xDF and i + 1 < n:
            nx = suspect_bytes[i + 1]
            if not (0x80 <= nx <= 0xBF):
                fixed.append(b)
                fixed.append(0xA0 if nx == 0x20 else nx)
                i += 2
                continue
        if 0xE0 <= b <= 0xEF and i + 2 < n:
            a, bb = suspect_bytes[i + 1], suspect_bytes[i + 2]
            if not (0x80 <= a <= 0xBF and 0x80 <= bb <= 0xBF):
                fixed.append(b)
                fixed.append(a if 0x80 <= a <= 0xBF else (0xA0 if a == 0x20 else a))
                fixed.append(bb if 0x80 <= bb <= 0xBF else (0xA0 if bb == 0x20 else bb))
                i += 3
                continue
        fixed.append(b)
        i += 1

    # pass 2: decode fixed bytes to chars, then round-trip everything to utf-8
    chars = []
    for char in fixed.decode("latin-1"):
        o = ord(char)
        if 0x0080 <= o <= 0x00FF:
            chars.append(bytes([o]))
        else:
            chars.append(char.encode("utf-8"))
    merged = b"".join(chars) + bytes(trusted_bytes)
    return merged.decode("utf-8", errors="replace")


def get_blob(rel: str) -> str:
    r = subprocess.run(
        ["git", "show", "83a567c:" + rel],
        capture_output=True, cwd=str(REPO),
    )
    assert r.returncode == 0, f"khong lay duoc blob {rel}: {r.stderr.decode()}"
    return r.stdout.decode("utf-8")


def fix_quotations() -> None:
    rel = "views/quotations.py"
    dec = decode(get_blob(rel)).replace("\u00a0", " ")
    # BOM có the nằm ở bất kỳ chỗ nào line 1; loại tất cả U+FEFF
    dec = dec.replace("\ufeff", "")
    # an toàn: bỏ whitespace đầu file (blob gốc bắt đầu ngay bằng BOM+docstring)
    dec = dec.lstrip()
    # byte 91/92 → ‘/’ trong "chốt"
    dec = dec.replace("cht", "chốt").replace("Cht", "Chốt")
    dec = dec.replace("ch‘t", "chốt").replace("Ch‘t", "Chốt")
    compile(dec, rel, "exec")
    (REPO / rel).write_text(dec, encoding="utf-8")
    print(f"{rel}: fffd_remaining={dec.count(chr(0xfffd))} len={len(dec)}",
          flush=True)


def fix_database() -> None:
    rel = "core/database.py"
    p = REPO / rel
    src = p.read_text(encoding="utf-8")
    bad = ('raise ConcurrentUpdateError(f"LÃ´ {sid} vá»«a Ä‘Æ°á»£c ngÆ°á»'
           '\x9di khác cập nhật.")')
    bad2 = ('raise ConcurrentUpdateError(f"LÃ´ {sid} vá»«a Ä‘Æ°á»£c ngÆ°á»'
            '\x9di cáº\xadp nháº\xadt.")')
    new = ('raise ConcurrentUpdateError(f"Lô {sid} vừa được người khác '
           'cập nhật. Hãy Reload Data rồi lưu lại.")')
    cnt = 0
    for target in (bad, bad2):
        if target in src:
            src = src.replace(target, new)
            cnt += 1
    compile(src, str(p), "exec")
    p.write_text(src, encoding="utf-8")
    print(f"{rel}: replaced={cnt} fffd_remaining={src.count(chr(0xfffd))}",
          flush=True)


if __name__ == "__main__":
    fix_quotations()
    fix_database()
