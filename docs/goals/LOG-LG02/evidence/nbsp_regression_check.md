# NBSP regression check — 2026-08-18

After repo-wide fix, grep shows patterns like:
"BnGiao", "Khch Hng", "BoGi", "người dng", "cho phpruntime"

Analysis: byte 0xA0 in original mojibake text = NBSP that was later
displayed. The fixer restored 0xA0 back to U+00A0 (NBSP char), which grep
renders as "" (replacement char in narrow terminal). So these may NOT be
corruption — U+00A0 is a valid Unicode char.

However, original healthy files should use regular space in these strings
(e.g., "Bàn Giao" with normal spaces). Presence of NBSP inside words is a
regression from the ORIGINAL pre-mojibake text? Unknown — original file was
never available.

Decision: post-process: replace NBSP (U+00A0) with regular space in .py
files, then verify compile + no mojibake artifacts. This is safe because
Python source code never needs NBSP; all string literals render identically
with regular spaces for Streamlit UI.

Files affected (grep ""): views/web_app.py lines 44,68,200; core/database.py
line 183. Verify after replacement.
