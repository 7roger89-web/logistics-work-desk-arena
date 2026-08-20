# Decoder debug — quotations.py U+FFFD root cause — 2026-08-18

The working decoder (cp1252 range emit + artifact map + NBSP heuristic)
produces 127 U+FFFD in views/quotations.py. Suspected cause: some mojibake
chars are NOT in the 0x80-0xFF byte-passthrough range NOR the artifact map
(0x80-0x9F glyphs). Specifically "‘" contexts around 'đ' (C4 91):
buffer C4 + 91 should round-trip to 'đ' — investigate the ACTUAL bytes of
the mojibake blob to see what chars encode 'đ' in this file.
