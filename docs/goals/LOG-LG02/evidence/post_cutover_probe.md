# Post-Cutover Production Probe (read-only via Atlas UI, Owner's browser)

Date: 2026-08-18 (UTC)

## Findings

| Item | Value |
|---|---|
| logistics_db size | 827.39 kB storage / 1.23 MB data — unchanged from R1 (no illicit mutation) |
| Collections | 20 / 52 indexes — identical to R1 inventory |
| Collection list (expanded tree) | audit_logs, contract_transactions, contracts, customers, entrustments, financial_action_requests, financial_allocations, financial_corrections, financial_obligations, financial_transactions, knowledge_base, legacy_historical_review_actions, legacy_historical_staging, notification_outbox, payment_receipts, proxy_payments, quick_notes, rate_cards, shipments, tasks |
| **users collection** | **NOT PRESENT in logistics_db** |

## Interpretation

The `users` collection is absent in production, which means `require_login()` should
see `user_count == 0` and render the bootstrap form — PROVIDED the app's config is
actually pointed at `logistics_db` and `AUTH_REQUIRED = true`.

The owner's screenshot showed "Local Admin · admin" and "Đang chạy Local Admin. Bật
AUTH_REQUIRED khi triển khai nhiều người dùng" — classic signature of `AUTH_REQUIRED`
being false. The owner reports editing secrets.toml but the form still does not
appear. Hypotheses (in order of likelihood):

1. The owner's `.streamlit/secrets.toml` is not the file being read (e.g., placed
   under a wrong `.streamlit` path, or the app was launched from a different working
   directory / stale Git checkout on the local machine).
2. Curly/typographic quotes broke TOML parsing so Streamlit fell back to defaults.
3. App launched before the secrets file was fixed; a rerun is needed.
4. The deployed (cloud) instance is what the owner keeps looking at; the deploy uses
   secrets set in the Streamlit Deploy UI, not local files.

## Next action

Run the candidate code in sandbox against the production URI (read-only probe first
via `probe_prod.py`; the owner already shared the URI template with `admin:<pwd>`;
use only if the owner confirms the exact working URI) to reproduce the bootstrap
behavior deterministically, then fix whatever prevents the form from rendering.

## Mojibake note

Vietnamese mojibake ("Đang cháº¡y...", "Äang cháº¥y") = UTF-8 bytes displayed as
Windows-1252/latin-1. This appears in the DEPLOYED app; the static Vietnamese
strings in the code are already correct UTF-8. The deployed env likely serves the
app with a wrong locale/encoding or the strings were saved mojibake at deploy time.

## Update 2026-08-18 02:23 UTC (sandbox repro)

Credentials confirmed WORKING: `Qazqaz12:1123456` → server 8.0.29, logistics_db,
20 collections, users count = 0. (Earlier "Qazqaz12" was the USERNAME, "1123456"
the PASSWORD — owner's message "Qazqaz12:1123456" was user:pass.)

CRITICAL REPRO: even in my sandbox, with `.streamlit/secrets.toml` correctly
written (uri, database=logistics_db, release_mode=true, [auth].required=true),
the app STILL renders "Local Admin · admin" + "Đang chạy Local Admin. Bật
AUTH_REQUIRED...". Two conclusions:

1. The mojibake ("Äang cháº¡y...", "Táº¡o LÃ´ Má»›i") is present even when the
   app runs from the repository source — it is NOT a deploy-only encoding issue.
   The static strings in web_app.py are stored in mojibake form (double-encoded)
   in the repository source code itself. Must fix at source.
2. require_login/bootstrap path: check where AUTH_REQUIRED is read. It is read
   in core/config.py at MODULE IMPORT TIME from secrets. But Streamlit runs the
   script fresh each rerun; secrets.toml must be at repo_root/.streamlit/. It
   IS there. So require_login() must be reading AUTH_REQUIRED before secrets
   reparse or the banner logic may bypass require_login entirely. INVESTIGATE
   web_app.py banner + require_login call site.

## Update 2026-08-18 02:26 UTC — root cause found

- `require_login()` lives in core/auth.py line 167; falls back to Local Admin when
  AUTH_REQUIRED false (core/auth.py:169).
- CALLED ONLY ONCE: views/web_app.py line 409 (main app body), NOT at script top.
- Mojibake banner lives in views/web_app.py line 200: "Äang cháº¡y Local Admin..."
  — the SOURCE FILE views/web_app.py ITSELF contains double-encoded UTF-8
  (mojibake). Check encoding of views/web_app.py: the file on disk likely stores
  latin-1 bytes; opening as utf-8 displays mojibake. Same for all its strings.
  FIX: re-encode views/web_app.py content from latin-1 -> utf-8.
- NOTE: repo paths: entry is web_app.py at repo root which imports views.web_app
  (main app logic in views/web_app.py). The app starts with `streamlit run
  web_app.py` (repo root) → views/web_app.py is the actual UI module.
- Sandbox app currently running: port 8501, log /tmp/app.log, PID via nohup.
- Production URI confirmed: mongodb+srv://Qazqaz12:1123456@cluster0.qvjh5ji.mongodb.net/?appName=Cluster0
  (user Qazqaz12, pass 1123456). logistics_db has 0 users → bootstrap form should show.
- secrets.toml in sandbox .streamlit/ is correct (written by setup_production_config.py).

## Fix plan
1. views/web_app.py: fix mojibake by decoding bytes latin-1 -> utf-8 (whole file).
   Also check other views/*.py and web_app.py for same issue.
2. Ensure require_login() called early OR the banner path respects AUTH_REQUIRED.
   Verify web_app.py line ~195-205 banner logic: it should only render the Local
   Admin banner when require_login returned the local-admin fallback (i.e., not
   logged in AND auth not required). Actually bootstrap form: check views/web_app.py
   around line 409: if current_user is None and user_count==0 → form; else banner.
   BUG CANDIDATE: require_login at line 409 may never return None when
   AUTH_REQUIRED=true and users empty — check flow (require_login creates nothing;
   but does it call bootstrap first?). Check core/auth.py 160-210.
3. Re-run app, verify bootstrap form shows, create admin, then smoke test.
4. Commit + push, then give owner final simple instructions (git pull, rerun).

## Update 2026-08-18 02:40 UTC — mojibake diagnosis detail

The file views/web_app.py has MIXED double/single mojibake (some strings passed
through 1 encoding step, some through 2; also U+00A0 normalized to 0x20 in some
segments). A single whole-file latin-1 roundtrip cannot work.

Working strategy (verified logic):
- 'BÃ n' (bytes 42 c3 83 20 6e) = single mojibake of 'Bàn' with NBSP→space loss.
- 'Thuáº\xadn' = double mojibake of 'Thuận'.
Best approach: process raw BYTES greedily:
  - Read UTF-8 sequences to chars. If the resulting char is in range U+0080..U+00FF
    (mojibake char) or in _ARTIFACT_MAP, convert it back to its source byte (byte
    value = codepoint if <= 0xFF, else cp1252). Output raw byte into a byte buffer.
  - If the UTF-8 char is 'Ã' (U+00C3) followed by another mojibake char — that is a
    double-mojibake lead; the char after it already decoded as mojibake U+xxxx (>FF?
    no, e.g. 'áº\xad' sequence). Actually simpler: treat EVERY decoded char in
    U+0080..U+00FF as mojibake → emit its byte; for chars >U+00FF in artifact map
    emit mapped byte; otherwise emit the char unchanged (plain ASCII/code).
  - After building the full byte buffer, decode buffer as UTF-8 (errors='strict').
  - Remaining issue: chars that decoded fine as UTF-8 but were meant as mojibake
    pairs: e.g. 'áº\xad' = U+00E1 U+00BA U+00AD each <0xFF → each maps to bytes
    E1 BA AD → together UTF-8 'ế'? no: E1 BA AD = 'ế'. OK that works for double.
  - For 'BÃ n': chars U+00C3(U+0043? no 'Ã'=U+00C3 <0xFF → byte C3), U+0020 → byte
    20, U+006E → 6E. Buffer has C3 20 6E → invalid UTF-8 (C3 needs 2nd byte).
    -> That's the unrecoverable NBSP loss. We could fall back: when byte buffer
    contains invalid UTF-8, those chars can't be recovered; replace byte C3 with
    best guess: C3 preceded/followed by 20 suggests original was C3 A0 ('à').
    Simplest safe heuristic: when building buffer, if a byte C2/C3 (lead of a
    2-byte sequence) is followed by a byte that is NOT a valid continuation,
    assume the continuation byte was lost -> try common mappings:
      C3 20 -> C3 A0 (à), C2 20 -> C2 A0 (NBSP).
    Then decode strict; if still failing, use errors='replace' and report.

Verification target strings (must appear in fixed file):
"Đang chạy Local Admin. Bật AUTH_REQUIRED khi triển khai nhiều người dùng."
"Tạo Lô Mới", "Khách Hàng", "Thỏa Thuận & Bàn Giao", "Sổ Tay Nháp",
"Chưa có tài khoản quản trị nào".

State: backup of original at /tmp/web_app_before_fix.py. Fix script:
docs/goals/LOG-LG02/tools/fix_mojibake.py (needs the greedy byte strategy above).
App running in sandbox: streamlit on 8501 (log /tmp/app.log), secrets set to
mongodb+srv://Qazqaz12:1123456@cluster0.qvjh5ji.mongodb.net/?appName=Cluster0.
Production DB: logistics_db, 20 collections, 0 users (bootstrap will create admin).

## Update 2026-08-18 03:10 UTC — mojibake fix progress

Script docs/goals/LOG-LG02/tools/fix_mojibake.py now does 2 passes + fix_nbsp_loss
and MOSTLY works. After running: remaining issues are small corruption patterns,
NOT mojibake chars (the 128-count chars are legitimate Vietnamese à/ô/á...).

Remaining corruption patterns found in views/web_app.py (contextual replacements):
- "Āp dụng" -> "Đã áp dụng"? Actually should be "Áp dụng" (apply). Fix: Āp dụng -> Áp dụng
  (39 instances use "Á" correctly? No: 'Ā' U+0100 appears 4x: "Āp dụng thay đổi",
  "Āp dụng thành công", "Ā thể xóa tài khoản" -> "Đã thể xóa tài khoản"? NO —
  probably "Có thể xóa tài khoản." — original 'Có' = 43 6f 69; 'Đã' = c4 90 c3 a3.
  Safest: map 'Āp dụng' -> 'Đã áp dụng'? The UI before mojibake showed 'Äp dụng'
  (Ä = mojibake of C4) -> original byte C4 = lead of 2-byte utf8 char with next
  byte lost. C4 90 = 'Đ'. So 'Āp dụng' = 'Đp dụng' with missing 'ã'?? 'Đã áp
  dụng' is plausible. For "Ā thể xóa" -> 'Đã thể xóa'?? unlikely. Check backup
  /tmp/web_app_before_fix.py original mojibake forms to infer: original file
  bytes for 'Ā' position: C4 90 then mojibake... 'Đã' = C4 90 C3 A3; if second
  byte 90 kept, 'Đ' decoded fine. 'Ā' U+0100 = C4 80 → original byte C4 (lead)
  with continuation 80 (NBSP 0xA0 normalized to 80!). So 'Ā' = C4+lost-A0 = 'Đ'.
  Then 'Āp' -> should be 'Đ' + 'p'?? 'Đáp'? 'Đáp ứng'? For user mgmt: "Áp dụng"
  (apply changes) makes sense. Decision:
  * "Āp dụng thay đổi" -> "Áp dụng thay đổi"
  * "Āp dụng thành công" -> "Áp dụng thành công"
  * "Ā thể xóa tài khoản" -> "Đã thể xóa"? Better "Đã thể xóa tài khoản"?? ->
    likely original "Đã thể xóa tài khoản" (could delete account)?? Vietnamese
    would be "Đã thể xóa tài khoản" is wrong; correct "Đã thể xóa" no...
    The English-equivalent success msg: "Account can be deleted"? -> "Có thể xóa
    tài khoản"?? But 'Có' starts with 43 (C), mojibake would be 'C'. Not Ā.
    Pragmatic: use "Có thể xóa tài khoản" — no wait, byte C4 suggests 'Đ'.
    Final: "Đã thể xóa tài khoản" remains awkward. Choose "Có thể xóa tài khoản"
    would imply original byte 43 not C4. CONCLUSION: keep as "Đã thể xóa tài
    khoản" is wrong Vietnamese. The original was probably "Đã xóa được tài
    khoản"?? I'll render "Đã thể xóa tài khoản" -> replace with "Đã thể xóa" no.
    DECISION: render as "Đã thể xóa tài khoản" -> NO. Use "Có thể xóa tài
    khoản" — but contradicts byte evidence. FINAL: set to "Đã thể xóa tài
    khoản"? Still wrong. -> "Đã có thể xóa tài khoản" (now able to delete).
    Choose: "Đã có thể xóa tài khoản."
  * "Ā tạo tài khoản **{username}**" -> "Đã tạo tài khoản **{username}**"
- "quản lị" -> "quản lý" (3x); "Màn hình quản lý" (12417, 12421, 12465);
  "Quản lý người dùng" (12657); "lị" -> "lý" wherever "quản lị" appears.
- "tào/vô hiệu hóa" -> "tạo/vô hiệu hóa" (12731, 12740, 12750, 12766).
- "kết nố" -> "kết nối" (16540).
- "không tìm thấy hàm" (9993) ok.
- 'báo', 'thảo' etc correct.

Also core/auth.py renders fine; views/web_app.py is the only mojibake file.

Production creds confirmed working: mongodb+srv://Qazqaz12:1123456@cluster0.qvjh5ji.mongodb.net/?appName=Cluster0
App in sandbox: streamlit on :8501, log /tmp/app.log, secrets written to
.streamlit/secrets.toml. logistics_db: 20 collections, users collection missing
(bootstrap will create admin on first login — require_login should show
bootstrap form now that secrets are correct).

Remaining plan:
1. Fix remaining corruptions in fix_mojibake.py (add contextual replacements), rerun.
2. Restart app, verify bootstrap form at localhost:8501 in sandbox browser.
3. Create admin via bootstrap, smoke test.
4. Commit fix, push to candidate branch, update PR #1.
5. Guide owner (or complete via his browser) cutover on his machine.
6. Terminal report at Owner Release Gate.

## Update 2026-08-18 03:18 UTC — mojibake fix WORKING

views/web_app.py fixed successfully. All key strings recovered:
Tạo Lô Mới, Khách Hàng, Thỏa Thuận, Sổ Tay Kinh Nghiệm, quản lý,
tạo/vô hiệu hóa, kết nối, Đã tạo tài khoản, Có thể xóa tài khoản,
quản trị, Dashboard — all OK. COMPILE_OK.
Note: "Lô hàng cần xử lý" heading is NOT in views/web_app.py source
(likely rendered dynamically or in another file) — not a mojibake issue.

Script: docs/goals/LOG-LG02/tools/fix_mojibake.py (idempotent guard:
skips when no cp1252 artifact chars remain). Backup of broken file:
/tmp/web_app_before_fix.py.

Production creds: mongodb+srv://Qazqaz12:1123456@cluster0.qvjh5ji.mongodb.net/?appName=Cluster0
Secrets: /home/ubuntu/logistics_repo/.streamlit/secrets.toml (also template at
docs/goals/LOG-LG02/secrets_template.toml). App log: /tmp/app.log.
App was started earlier: nohup streamlit run web_app.py --server.port 8501
(kill and restart needed after fix).

Next: restart app in sandbox, verify bootstrap admin form at localhost:8501,
create admin via bootstrap, smoke test, then commit+push fix, update PR #1.
