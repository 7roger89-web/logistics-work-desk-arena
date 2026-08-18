# Full-repo mojibake scan — 2026-08-18

## CRITICAL FINDING (explains Owner's persistent mojibake)

My earlier fix only targeted `views/web_app.py`. A full-repo scan shows
mojibake in several MORE Python source files that are RENDERED at runtime:

| File | Artifact count | Has visible-VN mojibake? |
|---|---|---|
| core/database.py | 100 | YES (Ä, LÃ´ samples) |
| views/quotations.py | 237 | YES (KhÃ¡ch, Ä, LÃ´) |
| views/historical_review.py | 15 | unknown |
| views/shipment_360.py | 13 | unknown |
| views/web_app.py | 0 | fixed earlier |
| core/historical_review_analysis.py | 12 | no VN samples |

Markdown docs also contain mojibake but those are docs, not rendered UI.

## Why Owner's UI still broken
- `views/web_app.py` on Owner's machine is now CLEAN (findstr confirmed).
- But the LEFT SIDEBAR navigation labels he sees ("Táº¡o LÃ´ Má»›i",
  "KhÃ¡ch HÃ ng", "Thá»a Thuáº­n") are mojibake — and some UI strings may come
  from OTHER view files or from core/database.py constants.
- Also Streamlit 1.61 uses uvicorn + bytecode cache: any stale .pyc in
  __pycache__ serves old strings.

## Required fix
1. Apply the same double-mojibake decoder to ALL python files in the repo
   (idempotent, artifact-char guarded).
2. Verify each fixed file compiles (py_compile) and spot-check VN strings.
3. Commit + push as a single LG02 fix commit.
4. Give Owner ONE command to run: `python docs\goals\LOG-LG02\tools\clean_pycache.py`
   (or manual: `rd /s /q __pycache__` per folder), then restart app.

## Note on Ä artifacts
"Ä" alone can be a legitimate mojibake of "Đ" (U+0110) OR part of real text;
the decoder already handles byte-range 0x80-0xFF chars (which includes Ä).
Must verify fixed output reads correctly in Vietnamese.
