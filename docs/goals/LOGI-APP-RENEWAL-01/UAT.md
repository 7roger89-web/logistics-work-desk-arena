# LOGI #199 — Owner UAT guide (bản dùng thử đã sẵn sàng)

**Current gate:** `INDEPENDENT_REVIEW=PASS` for the bounded **Journey G2** interface scope;
`REVIEWED_HEAD=7ef144c22081d64806fde6e3149c4d69afd1552a`; `OWNER_UAT_READY=YES`;
`OWNER_UAT=NOT_RUN` (Owner UAT counts as complete only after the Owner actually uses the app and
reports back); `PRODUCTION_READY=NO`; `NO_MERGE_MAIN=YES`; `NO_DEPLOY_PRODUCTION=YES`.

This file is a focused LOGI #199 follow-up, not a restart of accepted G0–G5 work. The Independent
Supervisor PASS covers the Journey **G2** interface (Vietnam map, 11 nodes, zero-node, touch-pan,
save/read-back on sample data). It does not cover the rest of the goal, finance/auth breadth, or
production readiness.

## Owner: how to open the app (3 steps)

**BƯỚC 1 — Mở app.** Cách chắc chắn nhất: **tải gói dùng thử trong khung xem tệp của phiên này**
(`LOGI199-GOI-DUNG-THU.zip`), giải nén ra một thư mục **mới**, rồi:

- **Mac:** nhấp đúp `MO-APP-DUNG-THU-MAC.command` (lần đầu chạy 1–3 phút để tự cài thư viện; macOS hỏi thì nhấp chuột phải → **Open**).
- **Windows:** nhấp đúp `MO-APP-DUNG-THU-WINDOWS.cmd` (cần Python 3.11 trở lên).

Hướng dẫn đầy đủ bằng tiếng Việt nằm trong gói: `HUONG-DAN-DUNG-THU.txt`.
Không cần GitHub, không cần gõ lệnh. Trình duyệt sẽ tự mở (hoặc mở `http://localhost:9501`).

*Phương án không cần tải gì:* bấm khung **LIVE PREVIEW** của phiên đang chạy này. Lưu ý đã kiểm chứng
bên ngoài: địa chỉ dạng `https://<cổng>-<sandbox-id>.e2b.app` **không dùng trực tiếp được** bằng
trình duyệt điện thoại/máy tính — nền tảng chặn bằng token riêng tư (`403 Missing traffic access token`),
và mỗi lần sandbox được tạo lại thì địa chỉ cũ chết (`502 Sandbox not found`, đúng lỗi của link cũ).
Vì vậy đừng dùng lại link cũ; chỉ dùng khung preview của phiên đang chạy hoặc gói tải về.

**BƯỚC 2 — Thử các chức năng:** xem checklist bên dưới (lô `T6-FCL` có sơ đồ Journey đầy đủ,
lô `SEA-188` là lô mới chưa có Journey; bấm vào một node trên bản đồ để mở bong bóng và form;
nhập một mốc ngày thử rồi lưu, tải lại trang để đọc lại).

**BƯỚC 3 — Tắt và phản hồi:**
- Gói tải về: **đóng cửa sổ đen** vừa hiện (hoặc **Control + C** trong cửa sổ đó).
- Khung preview của phiên: bấm **Control + C** ở cửa sổ môi trường tạm (hoặc nút dừng của nền tảng).
- Gửi phản hồi cho người phụ trách (ảnh chụp màn hình càng tốt): chỗ nào đúng, chỗ nào sai, chỗ nào khó hiểu.
  Owner UAT chỉ được coi là hoàn thành khi có phản hồi này.

Dữ liệu là **mẫu trong bộ nhớ tạm**: tắt app là dữ liệu biến mất. Không có gì được ghi vào
production và không cần tài khoản thật.

## Exact reviewed artifact (acceptance record) and trial package

- Reviewed HEAD (source of the acceptance record): [`7ef144c22081d64806fde6e3149c4d69afd1552a`](https://github.com/7roger89-web/logistics-work-desk-arena/commit/7ef144c22081d64806fde6e3149c4d69afd1552a)
- **[Download the exact reviewed artifact ZIP](https://github.com/7roger89-web/logistics-work-desk-arena/archive/7ef144c22081d64806fde6e3149c4d69afd1552a.zip)** — the reviewed acceptance package (requires GitHub sign-in; the repository is private). Its bundle identity was re-derived in this session: `component/dist/logi-shell.js` sha256 `3b650f8f2d7171113ddcd927f885133898d60d5cd22dece16a95dfc092089e5c`, `component/dist/logi-shell.css` sha256 `412f27aa81d65b5c0a3bafadd98f3c3123ee6a2d5ec5ea4957ca3084409917fb` — identical to the recorded values.
- **Owner trial package: `LOGI199-GOI-DUNG-THU.zip`** — 5.2 MB, 382 entries, built from the reviewed content (reviewed HEAD `7ef144c` + launchers + Vietnamese guide, heavy evidence/docs/testing-mock folders excluded). The Mac launcher keeps mode `0755` inside the ZIP and `component/dist` inside it matches the reviewed artifact exactly. Verified by fresh extraction: launcher created `.venv`, installed requirements, started the app on a free port, `APP_BOOT_EXCEPTIONS=0` after `STAGING_ISOLATION_PROOF=PASS` (Mongomock, `db=logistics_staging`, `real_uri=NO`), `T6-FCL` 11 nodes/11 edges `PROFILE_READY`, `SEA-188` 0 nodes `PROFILE_INCOMPLETE`.
  - **GitHub download (survives every sandbox reset):** pinned tag [`logi199-owner-trial`](https://github.com/7roger89-web/logistics-work-desk-arena/blob/logi199-owner-trial/LOGI199-GOI-DUNG-THU.zip) → button **“Download raw file”**, or the direct link `https://github.com/7roger89-web/logistics-work-desk-arena/raw/logi199-owner-trial/LOGI199-GOI-DUNG-THU.zip`. The repository is private, so the download requires being signed in to GitHub. Verified end-to-end in this session: the committed blob (`3652985db13f8dc51dd4a73daeb7697eee7e6f81`, 5 284 685 bytes) equals the local file, and a real download of the tagged archive from GitHub reproduced the file with SHA-256 `8558e13596d44fb69906b2351d42cbca8b359157aae7485a7bad699f59804f3d` — an exact match. GitHub release assets could not be used because this sandbox's network allowlist blocks `uploads.github.com` (TLS refused), so the file is delivered as a tracked repository blob plus this pinned tag instead.
- Reviewed source candidate of the G2 evidence: `1e899553cc1ad7dbd720eb805e061ec61ae0871a`. Its disclosed
  raw-capture SHA reconciliation (`751f64f…` unavailable; dist/harness hashes matched) is not re-litigated
  here and remains recorded in `state.json`; the Supervisor PASS for G2 accepted this candidate and its
  chain up to reviewed HEAD `7ef144c`.
- Sole visual reference: `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html`
  (SHA-256 `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`).
- Current browser evidence of record: `evidence/logi-199-g2/current-source/` and `evidence/logi-199-g2/metrics.json`.
- Pre-handover receipt for this trial delivery (environment, real checks, honest limits):
  `evidence/logi-199-uat/OWNER_TRIAL_READINESS.md`.

## Focused Owner checklist

| Check | Action | Expected result / record |
|---|---|---|
| Mở app | Mở link dùng thử (hoặc nhấp đúp launcher trên Mac). | Trang Logistics Work Desk mở ra, không hỏi đăng nhập (chế độ dùng thử một người dùng). |
| Nền Việt Nam / Biển Đông | Mở sơ đồ Journey của một lô. | Nền là bản đồ biển Việt Nam có `VIỆT NAM`, `BIỂN ĐÔNG`, `Quần đảo Hoàng Sa (Việt Nam)`, `Quần đảo Trường Sa (Việt Nam)`. Ghi PASS/FAIL + ảnh. |
| Lô `T6-FCL` — Journey đầy đủ | Mở lô `T6-FCL` trong mục Lô Hàng. | Sơ đồ Journey hiển thị đầy đủ 11 công đoạn trên bản đồ (không bị chia đôi, không chỉ còn một dải dọc bên trái). Ghi PASS/FAIL + ảnh. |
| Lô `SEA-188` — chưa có Journey | Mở lô `SEA-188`. | Báo đúng “chưa có sơ đồ Journey”, không bịa công đoạn, chỉ có một nút “BỔ SUNG HỒ SƠ”. Ghi PASS/FAIL + ảnh. |
| Bấm vào node | Bấm một node (ví dụ `ON BOARD`) trên bản đồ. | Mở đúng bong bóng thông tin của công đoạn đó, và mở được form công việc/bằng chứng của công đoạn. Ghi PASS/FAIL. |
| Lưu và đọc lại (dữ liệu thử) | Trong form công đoạn, nhập ngày thử: `2026-10-04`, bấm lưu, rồi tải lại trang. | Sau khi tải lại, đúng ngày `2026-10-04` vẫn còn. Không có giao dịch/thanh toán thật. Ghi kết quả lưu và đọc lại riêng. |
| Tắt app | Xem qua link: Control + C ở cửa sổ môi trường tạm. Chạy trên Mac: đóng cửa sổ hoặc Control + C. | App dừng; dữ liệu mẫu trong bộ nhớ biến mất; không có gì còn lại trên máy hay production. |
| Gửi phản hồi | Ghi lại PASS/FAIL từng mục + ảnh chụp màn hình. | Owner UAT hoàn thành khi phản hồi này được gửi lại cho người phụ trách. |

## Current release boundary

- `INDEPENDENT_REVIEW=PASS` — bounded **Journey G2 interface** scope only (Owner-provided gate), recorded at reviewed HEAD `7ef144c`.
- `OWNER_UAT_READY=YES`; `OWNER_UAT=NOT_RUN` until the Owner uses the app and reports back.
- `PRODUCTION_READY=NO`; `FULL_GOAL_199=IN_PROGRESS`; `SUPERVISOR_PASS` for the whole goal is not claimed.
- `NO_MERGE_MAIN_WITHOUT_OWNER_APPROVAL=YES`; `NO_PRODUCTION_DEPLOY_WITHOUT_OWNER_APPROVAL=YES`.

Honest limits of this trial package: the macOS launcher was executed and verified on Linux only —
macOS itself and Gatekeeper were not run; the Windows launcher remains NOT_RUN; this session had no
browser binary, so no new pixel capture was made and the visual evidence of record is still the
reviewed G2 capture. Unrelated auth/bootstrap/finance coverage gaps and the reproduced snapshot
retry-idempotency blocker remain separate and unwaived; GitHub issue-comment permission is not a
release gate.
