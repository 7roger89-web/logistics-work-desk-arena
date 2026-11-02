# BÁO CÁO — LOGI-G15-PUBLISH-PICKUP-20261102 (Issue #263)

> Nhiệm vụ: nhân viên cập nhật mốc **Lấy hàng** → lưu và đọc lại được → sinh nguồn chờ xác minh →
> Admin xác minh + công bố bằng **đúng bộ công bố Admin đang có** → đúng khách hàng thấy sau khi tải lại.
> Chỉ dùng DB test cô lập; không chạm production/Cloud.

## 1. PHÁN QUYẾT

**PROVEN** — chuỗi nghiệp vụ chạy thật trong Chromium (desktop 1440×900 + mobile 390×844),
36/36 check PASS, mỗi bước đối chiếu với ảnh chụp DB chứ không dựa vào chữ trên màn hình.

## 2. Nhánh / HEAD / PR

| mục | giá trị |
| --- | --- |
| Branch | `arena/e8d51a0b-logistics-work-desk-arena` |
| Base HEAD (staging) | `d4c7365b3d99485321da2f40e836757535e50a01` (`arena/ae5f9f47-logistics-work-desk-arena`) |
| Final HEAD | `f3ea036852dd5cef2d261d2ef9f299e3d3364000` |
| PR | **#264** — draft, base `arena/ae5f9f47-logistics-work-desk-arena`, 35 file `+2509/−1` |
| Trạng thái | draft, **chưa merge, chưa deploy** |
| OE_GATE | `OE_VERDICT=DO_IT` (SIMPLER_PATH: tái dùng `shipment_transport_save` + publisher Admin sẵn có, không thêm DB/dịch vụ/khung/duyệt mới) |
| LEARNING_RECONCILIATION | `NONE` |

## 3. Nghiệm thu A–I

| # | Tiêu chí | Bằng chứng (nhánh bằng chứng → kết quả) | Kết luận |
| --- | --- | --- | --- |
| A | Nhân viên cập nhật mốc và đọc lại đúng | Browser: gõ `2026-11-02` vào ô **ATD** của `Chặng 1` → `LƯU CÁC CHẶNG`; dispatch log `shipment_transport_save ok=true`; DB `pickup_atd=2026-11-02`; nguồn `pickup:CUST-263-A:LO-263-A` version `54b43afaa0d88e89` `state=PENDING`, `recorded_by=qa.263.support` | PASS |
| B | Khách A **chưa** thấy mốc trước khi công bố | Browser: `customer A does NOT see the milestone before publication`, `publications=0`, `published=""`; ảnh `*-3b-customer-a-before.png` | PASS |
| C | Admin xác minh **đúng nguồn + đúng version** | Browser: khối "Nguồn chờ xác minh" hiện `Đã lấy hàng · pickup · 2026-11-02 · pickup:CUST-263-A:LO-263-A / 54b43afaa0d88e89`; sau khi tick xác nhận + `Xác minh nguồn`: DB `verified=true, verified_by=qa.263.admin, state=VERIFIED`, **không** đổi `occurred_at`/version | PASS |
| D | Admin công bố bằng **workflow công bố hiện có** | Browser: danh sách chọn của publisher chỉ có **1** lựa chọn = đúng version đã xác minh; nút công bố bị khoá cho tới khi tick xác nhận; sau đó sinh publication `state=PUBLISHED, approved_by=qa.263.admin`, `event_versions={pickup:…: 54b43afaa0d88e89}`, lot `published=g15-…` | PASS |
| E | Khách A tải lại thấy cập nhật đã duyệt | Browser: trang khách A sau reload có hàng `LO-263-A … Lấy hàng → Đã lấy hàng`, `1 lô đã công bố`; ảnh `*-7-customer-a-milestone.png` | PASS |
| F | Khách B **không** thấy gì của A | Browser: portal khách B `0 lô đã công bố`, không có `LO-263-A`, không có `Đã lấy hàng`; ảnh `*-8-customer-b-empty.png` | PASS |
| G | Không lộ dữ liệu INTERNAL/tài chính | Browser: `driver_name=SECRET_263_INTERNAL_MARGIN`, SĐT `0900263999`, biển số `桂A-26399`, chi phí `987654321` **không** xuất hiện trong payload khách; pytest `test_customer_portal_publish_g15.py::test_admin_can_select_and_publish_existing_verified_versions` (`"SECRET" not in payload and "987654321" not in payload`), `test_g15_pickup_producer.py:130` (`INTERNAL_SECRET not in str(row)`) | PASS |
| H | Version cũ / nguồn chưa xác minh / nguồn bị sửa sau duyệt **không** bị công bố sai | pytest `tests/test_g15_pickup_producer.py`: `test_old_version_cannot_be_published_after_the_staff_fact_changes`, `test_withdrawn_pickup_is_unverified_and_unpublishable`, `test_published_source_edited_after_approval_fails_closed`, `test_verify_requires_admin_exact_version_and_intact_content`; browser: "xác minh **không** tự công bố" (`publications=0` sau bước verify) | PASS |
| I | Browser thật, desktop + mobile, đủ chuỗi | `ISSUE263_PICKUP_BROWSER=PASS (36 checks)`; ảnh + JSON ở `evidence/LOGI-G15-PUBLISH-PICKUP-20261102/browser/` | PASS |

### Chống WRONG_PASS
`playwright/issue263_runtime.py` có `?as=reset`: **xoá sạch** `public_events`, `customer_publications`,
`public_documents` của `LO-263-A/B` trước mỗi viewport. Không có fixture `public_events` nào được seed.
Mọi check đọc snapshot DB **sau** hành động của nhân viên, nên nguồn mà Admin xác minh chính là bản ghi
do hành động đó sinh ra trong cùng phiên chạy.

## 4. Lệnh test, exit code, bằng chứng browser

| Lệnh | Exit | Kết quả |
| --- | --- | --- |
| `ruff check .` | 0 | 1700 findings — **trùng khít** tập (file, code) với cây trước khi sửa ⇒ **không phát sinh finding mới** |
| `python scripts/check_router.py` | 1 | Lỗi **có sẵn từ trước** (`/lo-hang/:id` page chưa import), không đổi bởi nhánh này |
| `python -m pytest tests -q --continue-on-collection-errors` | 1 | `9 failed, 2391 passed, 45 skipped` — tập FAILED **đúng bằng** baseline 9 test nợ cũ (`evidence/…/baseline/failed-set.txt`); passed +14 (suite mới) |
| `python -m pytest tests/test_g15_pickup_producer.py tests/test_customer_portal_publish_g15.py tests/test_customer_portal_sources_g15.py tests/test_customer_portal_g15_independent_challenge.py -q` | 0 | `79 passed` |
| `node playwright/issue263_pickup_publish_qa.mjs --url http://127.0.0.1:9513/ --out evidence/…/browser` | 0 | `ISSUE263_PICKUP_BROWSER=PASS (36 checks)` |

Ghi chú trung thực:
* Một lần chạy full-suite đầu tiên có thêm `test_inbox_snippets.py::test_search_finds_note_beyond_page`;
  test này **pass khi chạy riêng** và pass ở lần chạy full lặp lại ⇒ flaky phụ thuộc thứ tự, không do nhánh này.
* Sandbox bị dựng lại giữa phiên (repo re-clone, `/tmp` mất). Nhánh đã được khôi phục từ remote về đúng
  `f3ea036`, working tree sạch, và **toàn bộ lệnh ở trên đã chạy lại** sau khi dựng lại môi trường
  (Python venv mới, streamlit 1.66.1) với kết quả y hệt: `9 failed, 2391 passed`, `79 passed`, ruff 1700.

### Bằng chứng browser (đã commit)
`evidence/LOGI-G15-PUBLISH-PICKUP-20261102/browser/`
* `browser-checks.json` — 36 check + snapshot DB từng bước (`*_staff_state`, `*_verified_state`, `*_published_state`)
* `00-summary.json`, `README.md` — bảng ánh xạ bước ↔ bằng chứng
* 20 ảnh: `desktop|mobile` × (lô trước khi có mốc, gõ ATD, đã lưu, khách A trước công bố, Admin thấy nguồn chờ, Admin đã xác minh, Admin đã công bố, khách A thấy mốc, khách B trống)
* `final-state-readback.json`, `staff-dispatch-log.json`

## 5. Blocker thật (chưa xử lý được)

1. **Không đăng được SPEC_LOCK thành comment trên Issue #263.** Token của tích hợp chỉ có quyền đọc issue;
   `POST /repos/…/issues/263/comments` trả **403 `Resource not accessible by integration`** (đã thử 2 lần, cả
   nội dung đầy đủ và bản ngắn). Đã bù bằng cách: (a) commit `evidence/LOGI-G15-PUBLISH-PICKUP-20261102/SPEC_LOCK.md`;
   (b) đính toàn văn SPEC_LOCK làm phụ lục trong thân PR #264. Cần người có quyền `issues: write` đăng hộ,
   hoặc mở quyền cho tích hợp.
2. **PR base là `arena/ae5f9f47-logistics-work-desk-arena`**, không phải tên `staging` — repo **không có**
   nhánh `origin/staging`; `arena/ae5f9f47…` đang ở đúng `d4c7365b…` (HEAD staging hiện hành) nên nội dung
   tương đương. Đây là ràng buộc của host, không phải lựa chọn của người thực thi.

Không có blocker kỹ thuật nào khác: không merge, không deploy, không đụng `main`/production/Cloud.

## 6. Phạm vi thay đổi (một lát cắt, chỉ trên seam sẵn có)

| file | vai trò |
| --- | --- |
| `core/customer_portal_milestones.py` (mới) | producer: suy ra fact công khai của mốc Lấy hàng từ chặng pickup của chính lô, ghi **một** bản ghi nguồn content-addressed (`PENDING/VERIFIED/WITHDRAWN`) |
| `core/customer_portal_publish.py` | `verify_source` kiểm lại id+version+hash nội dung trước khi Admin xác minh; `list_pending_sources` cấp dữ liệu cho màn Admin |
| `views/logi_view_model.py` | hành động lưu chặng **sẵn có** của nhân viên ghi/rút nguồn pickup sau khi ghi atomic + đọc lại |
| `views/customer_dashboard.py` | Admin xác minh nguồn chờ trên **chính** màn công bố sẵn có, rồi công bố bằng publisher sẵn có |
| `tests/test_g15_pickup_producer.py` (mới) | 14 test: producer, đọc lại, không công bố sớm, version cũ, nguồn chưa xác minh, sửa sau duyệt |
| `playwright/issue263_runtime.py`, `playwright/issue263_pickup_publish_qa.mjs` (mới) | harness browser cô lập + kịch bản nghiệm thu |

Không thêm database/dịch vụ/framework/lớp duyệt mới. Không sửa `main`, production hay dữ liệu Cloud.

## 7. Việc còn lại cho người review

* Review đúng `f3ea036852dd5cef2d261d2ef9f299e3d3364000` (draft → ready khi review xong).
* Đăng SPEC_LOCK lên #263 nếu chính sách yêu cầu comment trên Issue (xem blocker 1).
* Quyết định của Owner về việc merge vào staging; người thực thi **không** tự merge.
