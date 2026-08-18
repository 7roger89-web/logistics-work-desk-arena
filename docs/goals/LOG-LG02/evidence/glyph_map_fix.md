# Glyph map fix — root cause of 127 FFFD — 2026-08-18

Trace test PASSED in isolation ('á»‹'→'ị' correct), so the file-level FFFD
come from glyph code points my artifact map does not cover.

The mojibake tool ALSO produced "math" angle quotes OUTSIDE cp1252:
U+2039 '‹' (single left) and U+203A '›' (single right) — these represent
bytes 0x8B and 0x9B respectively, same as cp1252 '‹' (U+2039... wait
cp1252 0x8B = U+2039, so they ARE the same char). The blob's 'á»›' uses
U+203A '›' — and cp1252 0x9B = U+203A '›' — SAME again. So my map DOES
cover both ('‹':0x8B, '›':0x9B).

Remaining suspect: NBSP-loss heuristic fires on 'á»‹' when FOLLOWED by a
non-continuation byte in context. e.g. 'á»‹h' → E1 BB 8B 68. E1 lead, next
two: BB ✓ continuation, 8B NOT continuation (0x8B < 0x80? 0x8B >= 0x80 ✓
and 0x8B <= 0xBF ✓ — it IS a continuation!). So E1 BB 8B valid 3-byte →
'ị' then 68 'h' → fine.

So FFFD must come from clusters whose glyphs include chars my loop's
0x80-0xFF range misses: glyphs above U+00FF that are NOT in artifact map.
From the 75 clusters, check chars: 'ô'.. all in range. 'á»±' → ị? shown 'ự' ✓.
'á»‹' trace passed... Then WHY 127 FFFD in file? The file-level decode
applied to the CORRUPT working tree version (after my earlier broken
fix_repo_mojibake.py already wrote FFFD into views/quotations.py) —
fix_last_two_files.py decoded THAT, not the clean blob. FIX: decode the
CLEAN blob from 83a567c directly, not the working tree file.
