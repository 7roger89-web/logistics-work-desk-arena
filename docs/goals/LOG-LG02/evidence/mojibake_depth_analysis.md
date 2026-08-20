# Mojibake depth analysis — 2026-08-18

## Finding 1: web_app.py
After rebuild_from_mojibake.py (cp1252→bytes→utf-8 + NBSP-loss heuristic +
manual map), only 4 U+FFFD remain, all in:
- 'Daily control room · local workspace' — middle dot U+00B7 (legit!)
- f"…{display_name} · {role}…" — middle dot U+00B7 (legit!)
=> web_app.py is NOW CLEAN. The 0xFFFD are real middle dots, not corruption.

## Finding 2: core/database.py — DEEPER corruption
Rebuild left 171 U+FFFD. Pattern shows TRIPLE-layer corruption:
e.g. "khÃng" = 'không' corrupted through an EXTRA layer where 0x80..0x9F
bytes were mapped to cp1252 artifact glyphs then re-encoded.
The mojibake in database.py = result of the Owner's tooling doing
utf-8→latin-1→utf-8 TWICE (file was already mojibake when pushed again).

## Decision
Use the LAST KNOWN CLEAN version of each file from git history:
- views/web_app.py: 82c8134 is too old (pre-multiuser). Mojibake version
  (83a567c) + my decoder = clean now. DONE.
- core/database.py: 82c8134 has a CLEAN version (pre LG01 multi-user but
  with the LG-C12 database code intact — mojibake only arrived in the PR).
  Check: does 82c8134:core/database.py compile with current views? LG01 PR
  only added auth+RBAC layers; database.py LG02 hardening (delete gate) was
  applied on top — need to RE-APPLY the R4 delete_shipment gate manually
  after restoring clean database.py.

## Plan
1. Verify 82c8134:core/database.py is clean Vietnamese.
2. Restore it as base; re-apply LG02 R4 gate (backend perm check on
   delete_shipment) manually — the exact gate logic is in current broken
   file, can extract and apply to clean copy.
3. Recompile, scan, commit.
