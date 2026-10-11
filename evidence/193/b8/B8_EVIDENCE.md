# B8 — RED→GREEN evidence (LOGI-193 dispatcher allowlist)

Reviewed-then-fixed: `b737aaba1bb58d634a00e3cdfeee00a8d5a9a8c4` → **NEW_HEAD `ac7411aee52af9f5a32dd866ba7f35072fe1a79a`**
Branch: `arena/a5762bf9-logistics-work-desk-arena` (pushed, PR #194, draft — NOT merged, NOT deployed)
Commit: "LOGI-193: fix B8 - add six template events to dispatcher ALLOWED_EVENTS"
(4 files: component/src/lib/dispatcher.ts +9, tests/component/lib_loader.mjs +1,
tests/component/unit_dispatcher_allowlist_logi193.mjs new, component/dist/logi-shell.js rebuilt)

## The defect (B8)
`component/src/lib/dispatcher.ts`: six LOGI-193 events in the `LogiEventName` type
were absent from the runtime `ALLOWED_EVENTS` set → `dispatchLogiEvent()` returned
`false` for every browser write/preview; UI showed "Component chưa kết nối backend".

## RED (at b737aaba — fix stashed, test kept)
`node tests/component/unit_dispatcher_allowlist_logi193.mjs` →
`AssertionError: actual false, expected true` on the first of the six events.
Real Chromium 152 click on "Xem thử (dữ liệu giả)" (prior QA session) →
`window.__logi193Triggers == []` + red notice "Component chưa kết nối backend".

## GREEN (at ac7411a)
- `node tests/component/unit_dispatcher_allowlist_logi193.mjs` → PASS
  ("6/6 LOGI-193 events dispatch; fail-closed intact"), exit 0.
  Covers: (a) bound spy receives each of the six exact events with templateId/requestId/seq;
  fail-closed with no transport; unknown events stay blocked; pre-existing
  `attachment_download` still dispatches.
- Real Chromium 152 click on "Xem thử (dữ liệu giả)" on the NEW built bundle →
  `[{event:"docgen_template_preview", templateId:"UT-bb-i-chi-u-giao--261011053617wwbu",
  requestId:"docgen_template_preview-1791697032686-s70pbm", seq:1}]`, no error notice.
- `npx tsc --noEmit` exit 0; `npm run build` OK (dist 1,411,627 B, bundle verified to
  contain the six events in the allowlist literal); `npm run scan` →
  `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`.
- JS: 5/5 unit suites PASS (incl. new), dom_acceptance_logi193 PASS,
  dom_acceptance_form07_delivery_receipt PASS.
- Python: `tests/test_logi_193_uploaded_office_templates.py` 75/75 PASS.
- Fresh browser re-QA on NEW_HEAD: desktop 1440x900 + mobile 390x844 /bieu-mau —
  geometry identical to pre-fix QA (only a Set literal changed), zero horizontal overflow.
  Screenshots: b8/b8-desktop-bieumau.png
  (sha256 43a0b81af56a3209cf8cc469fd25f31da1e15ec2dd1d6f4a1c9d92f41e078d72),
  b8/b8-mobile-bieumau.png
  (sha256 1629406450e965daa8edecc0e6cba81daa8b28bfc9c59a5c5fa2fa36b62bdaa2).

## Scope honesty
- No new dispatch path, no RBAC relaxation, no UI/geometry change (rebuild is byte-equivalent
  except the allowlist Set).
- Staging only (logi_sandbox mongomock); no production DB, no secrets, no tienthanhlog.
- The preview harness records browser triggers; it does not run backend writes.
