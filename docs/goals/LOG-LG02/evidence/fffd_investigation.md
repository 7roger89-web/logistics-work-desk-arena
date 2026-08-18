# U+FFFD investigation in batch decode — 2026-08-18

## Observed FFFD contexts (views/tariff.py after decode)
- 'cấu trc' = 'cấu trúc' (ư intact, ứ broken)
- 'Gỗ tự nhin' = 'Gỗ tự nhiên' (ê broken)
- 'Khc' = 'Khác' (á broken)
- 'ti' / 'ápdụng' (ế/ấ broken)

## Analysis
The mojibake chars for Vietnamese combining-tone vowels are the CP1252
chars in range 0x80-0x9F AND 0xA0-0xFF — my decoder maps ALL of those
(0x80-0xFF byte passthrough + artifact map for 0x80-0x9F glyphs). So WHY
do tones break?

Hypothesis: double mojibake layer. Original UTF-8 bytes -> cp1252 -> utf-8
(1st layer, gives chars like Á é ư...). Then the tool that produced the
repo version may have ALSO normalized combining marks, OR the first layer
used a different encoding (iso-8859-2?).

Actual mojibake source for 'trúc' in repo: need to inspect raw bytes of
the 83a567c blob around "trúc" mojibake to determine exact char sequence.
Bytes 0xC3 0xBA 0xE1 0xB8 0xA9 = ú (Latin small u with acute... no wait:
"trúc" = 74 72 C3 BA (ú) — just ú, combining not needed).
In double-mojibake: C3 BA -> "Ãº" -> when re-encoded... hmm.

## Next step
Hex-dump the mojibake sequence around 'trc' in 83a567c:views/tariff.py to
see exact code points and derive the true decode map.
