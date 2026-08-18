# Decoder bug cuối — cô lập được — 2026-08-18

## Bug
decode() trong fix_quotations_final.py: ký tự > 0xFF (vd ô=0xF4, á=0xE1,
đ=0x111, ề=0x1EC1 — NHỮNG KÝ TỰ TIẾNG VIỆT ĐÚNG TRONG BLOB) rơi vào nhánh
`else: buf += char.encode('utf-8')`. Ví dụ 'ô' → thêm bytes C3 B4 vào buf
GIỮA các suspect bytes. Khi buf (hỗn hợp) decode('utf-8'): C3 B4 hợp lệ →
'ô' ✓ — NHƯNG nếu byte suspect tiếp theo là 0x20 và trước đó C3 chưa ghép
đủ... thực tế bug: F4 (char 0xF4) → encode utf-8 = C3 B4. Sau đó char 'n'
(0x6E) → byte 6E. Buffer: ... C3 B4 6E ... decode utf-8: C3 B4 → 'ô', 6E →
'n' ✓ STILL OK!

## Test isolated line STILL gives 4 FFFD: 'báo giá' → 'bo gi'
'á' = 0xE1 → utf-8 C3 A1. Buffer: 62 C3 A1 6F 20 67 69 C3 A1.
decode('utf-8'): 62='b', C3 A1='á', 6F='o', 20=' ', 67='g', 69='i',
C3 A1='á'. All valid! WHY FFFD???

## REAL ROOT CAUSE (guess): C3 A1 decode: C3 lead 2-byte needs NEXT byte
in 0x80-0xBF. A1 = 0xA1 ✓ valid continuation. C3 A1 → U+00E1 'á' ✓.
Hmm, so why FFFD? → BECAUSE my else branch uses char.encode('utf-8') which
for U+00E1 gives C3 A1 ✓ valid. UNLESS... the Python in sandbox is fine;
maybe the import got a STALE module? No — subprocess each time.

## Next action: print intermediate buf hex for the failing line to see
exactly what bytes land, then fix accordingly.
