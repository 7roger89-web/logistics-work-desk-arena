# Publication checkpoint — NOT posted to GitHub comments

`gh issue comment 199 --body-file ...` returned `Resource not accessible by integration`.
No issue comment was published by this continuation. The chained PR #198 comment was **not attempted** after that failure. Read/fetch/push succeeded; issue-comment mutation permission is blocked. Do not treat this draft as an independent review, acceptance, or a posted comment.

The prepared update follows; immutable source/evidence links remain valid. Latest state also records this publication blocker.

---

## LEAD_EXECUTOR — preview tích hợp #198 đã sửa & kiểm; dừng tại independent-review gate

**Không merge/deploy/production write; không tự đóng review.** `main` vẫn `5c6642a`.

### HEAD / CI đúng nguồn
- Nhánh phiên cố định: `arena/d8927583-logistics-work-desk-arena`; **HEAD `4f1b8744cc0aa207b709f85d202bc6b9b1b3f303`**.
- **Tested source `1889d2a874365bf59265b721503a0538f90586b0`**, [T6 run **38683678222 SUCCESS**](https://github.com/7roger89-web/logistics-work-desk-arena/actions/runs/38683678222).
- Evidence-only commit `ae6787852f0ed762241dfb07ed631e67d4e3dd36`, sau đó chỉ `state.json` ở `4f1b874`. Đã diff chứng minh source/dist/tests/workflows/scripts ở HEAD **không đổi** so với SHA được CI kiểm. Không gán nhầm CI cho một HEAD sản phẩm mới.
- Khôi phục preview `d96d951`, merge `f0aec79`, chỉ conflict evidence; giữ source #198 + T5 mới và rebuild dist. Worktree mới không có patch mobile chưa push; đã tái lập trên cơ chế zoom/pan/Fit sẵn có. Không làm lại T1–T4.
- `ct/logi199-int198-preview` cũ vẫn `d96d951` do phiên Arena chỉ được push nhánh phiên nêu trên. Không force-push, không sửa nhánh #198, PR #198/#200–204 vẫn open draft.

### Kết quả có bằng chứng
- Focused local: **281 passed**; CI business regressions PASS. Current-bundle DOM #197 + same-instance zero↔populated hook test PASS; typecheck/Vite/scan/dist equality PASS.
- [Full-suite paired parity](https://github.com/7roger89-web/logistics-work-desk-arena/blob/ae6787852f0ed762241dfb07ed631e67d4e3dd36/evidence/logi-199-t6/full_suite_parity.txt): main **31 failed / 1807 passed / 45 skipped / 1 error**, nhánh **31 failed / 1872 passed / 45 skipped / 1 error**; **0 failure ID mới**. Đây KHÔNG phải full-suite green hay release acceptance.
- [T6 real Streamlit/Chromium](https://github.com/7roger89-web/logistics-work-desk-arena/blob/ae6787852f0ed762241dfb07ed631e67d4e3dd36/evidence/logi-199-t6/browser_metrics.json): cả **6 variants × desktop 1440×900/mobile 390×844** — FCL/LCL, AIR direct/consolidated, ROAD FTL/LTL. UI ghi on-board → backend readback COMPLETED → mở lô khác/quay lại, trường ngày vẫn `2026-10-03`.
- [T5 audit](https://github.com/7roger89-web/logistics-work-desk-arena/blob/ae6787852f0ed762241dfb07ed631e67d4e3dd36/evidence/logi-199-t5/route_audit.json): đúng **21 màn hình độc lập × 2 viewport**, không page/shell overflow, clipped controls, tiny visible body text hay page errors. 3 legacy redirects kiểm target riêng, không đếm thành màn hình.
- Báo giá mobile giữ PASS. Tên **“Bộ Thông Tin Truyền Thông”** hiển thị đủ, icon mở trong thẻ. Be Vietnam Pro / IBM Plex Mono được bundle có license, browser chứng minh **loaded FontFaceSet**, không chỉ tên trong CSS; không thêm runtime dependency, không đổi font tài liệu pháp lý/xuất file.
- Popup chứng cứ giữ ≤5 trường chính; CFS 4 chính + 2 phụ trong Chi tiết phụ, browser chứng minh phụ vẫn editable; không xóa/bịa trường để đạt số lượng.
- Không dùng `continue-on-error` cho acceptance. Các bước tiếp tục thu thập bằng chứng sau failure nhưng job vẫn phải fail.

### 5 test lỗi cũ đã đối chiếu, không xoá hàng loạt
[Reconciliation từng ID + authority + bằng chứng](https://github.com/7roger89-web/logistics-work-desk-arena/blob/4f1b8744cc0aa207b709f85d202bc6b9b1b3f303/evidence/logi-199-t6/RECONCILIATION.md): #186 six-stage và 3 #190 zero-node/collapse/summary là **SUPERSEDED** bởi #197 rồi Owner correction 13/10; #190 geometry/module affordance **REPAIRED**. Giữ ID để trace, thay bằng persistent-map/unknown/optional-module/scoped-work contracts + runtime challenge. Invariants declaration≠clearance, GNT≠paid, UNKNOWN≠0/done, completion≠CLOSED, canonical Attention/action/owner và writer/RBAC vẫn giữ.

### A/B thực tế — không xin Owner chọn lúc này
Mặc định **100%**, title node **16px**, kéo/pan/zoom đã kiểm; **Fit ~27%** là overview riêng, nút **Đọc rõ** trở lại 100%. Desktop map 340px trái / nội dung rộng phải; mobile giữ cách xếp dọc sẵn có. Không coi hết overflow là đạt UX.

| Viewport | A — Fit toàn bộ | B — Mặc định đọc rõ |
|---|---|---|
| Desktop | ![Desktop Fit](https://github.com/7roger89-web/logistics-work-desk-arena/blob/ae6787852f0ed762241dfb07ed631e67d4e3dd36/evidence/logi-199-t6/desktop-map-A-fit.png) | ![Desktop Readable](https://github.com/7roger89-web/logistics-work-desk-arena/blob/ae6787852f0ed762241dfb07ed631e67d4e3dd36/evidence/logi-199-t6/desktop-map-B-readable.png) |
| Mobile | ![Mobile Fit](https://github.com/7roger89-web/logistics-work-desk-arena/blob/ae6787852f0ed762241dfb07ed631e67d4e3dd36/evidence/logi-199-t6/mobile-map-A-fit.png) | ![Mobile Readable](https://github.com/7roger89-web/logistics-work-desk-arena/blob/ae6787852f0ed762241dfb07ed631e67d4e3dd36/evidence/logi-199-t6/mobile-map-B-readable.png) |

### Release risks không được parity che đi
- Auth unknown-role test whole-suite fail nhưng clean-process PASS; bootstrap và mounted legacy RBAC oracles còn gap. Không đủ bằng chứng authenticated production acceptance.
- Finance/reconciliation legacy tests bị chặn bởi API patch/import cũ; không tuyên bố zero-write UI oracle đã được thực thi.
- Probe **authorized + unique-indexed mongomock** ở baseline và nhánh cùng kết quả: tamper bị từ chối, 1 row, nhưng **same-payload retry trả false**. Có script + JSON tái hiện trong `evidence/logi-199-t6/risk-probes/`. Đây là lỗi/rủi ro có sẵn cần reviewer gate riêng, **không sửa lan auth/finance**, không tự waive.

### CURRENT / NEXT / BLOCKERS
- [state.json đã cập nhật](https://github.com/7roger89-web/logistics-work-desk-arena/blob/4f1b8744cc0aa207b709f85d202bc6b9b1b3f303/docs/goals/LOGI-APP-RENEWAL-01/state.json).
- Preview Arena sandbox port 9501 đã mount app thật, no page errors, nhận preview Host HTTP 200; chỉ fixture mongomock trong bộ nhớ, không credentials/production DB. Không phải một deploy production hay human UAT.
- [UAT local đơn giản](https://github.com/7roger89-web/logistics-work-desk-arena/blob/4f1b8744cc0aa207b709f85d202bc6b9b1b3f303/docs/goals/LOGI-APP-RENEWAL-01/UAT.md): ZIP → giải nén thư mục mới → nhấp đúp launcher Windows; không bắt Owner xử lý Git/code. Launcher Windows chưa chạy trong host Linux; runtime Python tương ứng đã kiểm. Chưa yêu cầu Owner nghiệm thu/chọn phương án.
- **Independent reviewer=PENDING**; host không có actor độc lập, không mô phỏng review/quorum. Bằng chứng sẵn để Control Tower/reviewer kiểm lại. Sau đó mới Owner UAT và quyết định release; mọi production gate vẫn đóng.

`FINAL_VERDICT=INCOMPLETE_FULL_GOAL / TECHNICAL_PREVIEW_PROOF_PASS / BLOCKED_AT_INDEPENDENT_REVIEW_GATE`.
`OE_VERDICT=DO_IT` — tái dùng component/runner/state hiện có, không engine/router/library mới. `LEARNING_RECONCILIATION=CANDIDATE` (font load thực trong shadow-root/offline UI), không tự promotion.
