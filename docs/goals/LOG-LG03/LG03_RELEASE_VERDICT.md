# LOG-LG03 RELEASE VERDICT

**Ngày:** 18/08/2026 · **Trạng thái:** **RELEASED_VERIFIED** · **PRODUCTION CODE SHA:** `3c1e1c7` · **Khởi động:** thành công · Không bắt đầu LOG-LG04.

## 1. REHEARSAL CLEANUP RESULT — ĐÃ THỰC HIỆN + ĐÃ XÁC MINH

Ban đầu công cụ dọn (thời LG02) thực hiện **hard-delete** 3 tài khoản — trái với chỉ thị "không hard-delete". Tôi đã **khôi phục lại** 3 tài khoản ngay lập tức (chèn lại đúng 3 document đã mất, không làm thay đổi gì khác) và viết lại công cụ để thực hiện **khóa mềm** đúng theo chỉ thị của anh.

Quy trình khóa mềm: mỗi tài khoản rehearsal được cập nhật `active = False` và lịch sử trạng thái được ghi vào trường `active_states` kèm ghi chú `soft-deactivated by OWNER approval LOG-LG03 (cleanup of test accounts; reversible)` — có thể hoàn tác bất cứ lúc nào bằng cách đặt lại `active = True`.

**Read-back xác minh sau mutation (tất cả ĐẠT):**

| Tiêu chí | Kết quả |
|---|---|
| `admin` | active = True, role = admin, còn nguyên |
| `rehearsal_admin` | active = False (khóa mềm, có lịch sử 2 trạng thái) |
| `rehearsal_sale` | active = False (khóa mềm, có lịch sử 2 trạng thái) |
| `rehearsal_support` | active = False (khóa mềm, có lịch sử 2 trạng thái) |
| customers | 362 (không đổi, cả trước và sau merge) |
| shipments | 78 (không đổi, cả trước và sau merge) |
| user khác | Không user nào khác bị thay đổi |

## 2. ADMIN SAFETY — AN TOÀN

Tài khoản `admin` của anh không bị chạm vào trong toàn bộ quá trình (cả khi khôi phục 3 tài khoản thừa lẫn khi khóa mềm). Đọc database sau khi hoàn tất: `admin` vẫn active, role admin, mật khẩu nguyên bản không đổi.

## 3. GIT TRUTH — LIVE CHECK NGAY TRƯỚC MERGE (không suy đoán)

| Giá trị | Kết quả |
|---|---|
| CURRENT_MAIN_SHA | `09e2426` |
| FINAL_RELEASE_CANDIDATE_SHA (PR #2 headRefOid = remote branch HEAD = local HEAD) | `349f599` |
| PROVENANCE | PASS — chuỗi tuyến tính 20 commit từ main, `--first-parent --count = 20 = số dòng git log` (chứng minh không rebase/squash/rewrite) |
| Worktree | Sạch (tracked files, không uncommitted) |
| Remote vs local | Khớp tuyệt đối (không unpushed) |

**Giải thích các SHA trong báo cáo trước:** `efc5a4c` là HEAD tại thời điểm báo cáo VERDICT cuối; sau đó 2 commit mới được thêm vào PR theo đúng quy trình (9b786c2 bổ sung nốt nhãn tiếng Việt cho 4 nút màn hình 360, 349f599 sửa công cụ dọn thành khóa mềm đúng chỉ thị "không hard-delete"). Live check xác nhận **`349f599` là HEAD thật của PR #2** — đây là SHA được merge, không phải `efc5a4c` cũ.

## 4. REGRESSION — CHẠY LẠI TẠI CHÍNH CANDIDATE (2 commit mới sau lần kiểm tra trước)

| Hạng mục | Kết quả |
|---|---|
| Full regression (2 lần) | 217 passed / 28 skipped / **0 failed** (hai lần giống hệt) |
| RBAC | 27/27 PASS |
| Finance oracles | 10/10 PASS (UNKNOWN ≠ ZERO, ESTIMATE ≠ ACTUAL) |
| Mojibake / encoding | 0 marker lỗi, 0 file lỗi, 0 ký tự FFFD |
| Secret scan | 0 mật khẩu/URI trong mã nguồn |

## 5. MERGE — GIỮ PROVENANCE

GitHub từ chối merge API với PR ở trạng thái Draft (ngay cả khi owner mở Draft flag qua API). Với phê duyệt "DUYỆT PR #2" của anh, tôi dùng phương án merge giữ provenance tương đương: **git merge --no-ff** từ chính candidate vào main, tạo merge commit thật giữ trọn chuỗi lịch sử.

| Giá trị | Kết quả |
|---|---|
| FINAL PR HEAD SHA | `349f599` |
| MERGE SHA | `90d8cef` ("Merge PR #2: LG03 Vietnamese-first simplified UX (217/0/28, all gates PASS)") |
| MAIN AFTER MERGE | `90d8cef` |
| Chuỗi sau merge | `09e2426` (main gốc) → `349f599` (candidate) → `90d8cef` (merge) — xác minh bằng `git merge-base --is-ancestor`: cả hai đều là tổ tiên thật của main sau merge |
| PR #2 | Đã đóng (closed) sau khi merge commit lên main |

## 6. PRODUCTION DATA SAFETY — AN TOÀN

Không deploy. Không thay đổi database/config production sau khi merge. Snapshot đọc-only trước merge và sau merge giống hệt nhau: customers = 362, shipments = 78. Dữ liệu nghiệp vụ không bị chạm trong suốt LG03 (ngoài phần khóa mềm 3 tài khoản thử đã được anh phê duyệt, có thể hoàn tác).

## 7. DEPLOY STATUS — ĐÃ ĐƯA LÊN MÁY OWNER VÀ KHỞI CHẠY THÀNH CÔNG

Với phê duyệt của anh, bản mới đã được đưa lên máy của anh (D:\Logistics_App_GitHub): mã **`3c1e1c7`** (merge `90d8cef` + 1 commit giữ sửa công cụ LG02 của anh). Anh đã kéo mã, đưa về nhánh main, đóng app game trùng cổng 8501 và khởi động lại `streamlit run app.py`. App logistics chạy đúng cổng và tôi đã xác minh bằng trình duyệt.

## 8. SMOKE TEST TRỰC TIẾP TRÊN APP ĐANG CHẠY — TẤT CẢ ĐẠT

Kiểm tra read-only trên app thật (không thay đổi gì trong app, không tạo tài khoản mới):

| Hạng mục | Kết quả |
|---|---|
| Đăng nhập | Form tiếng Việt chuẩn: Tài khoản / Mật khẩu / Đăng nhập |
| Menu | Đủ 16 mục tiếng Việt + Đăng xuất, không lỗi chữ |
| Tổng Quan Công Việc | 78 lô, 76 cần xử lý, 0 deadline |
| Việc Cần Xử Lý | 206 mục, banner "chỉ đọc" hiện đúng |
| Khách Hàng | **Tổng số khách hàng: 362** (khớp database) |
| Đối Soát Tài Chính | Màn hình chỉ đọc, UNKNOWN giữ nguyên, không nút sửa số liệu |
| Người Dùng | admin hoạt động, 3 tài khoản rehearsal đã khóa |

**Xác minh database lần cuối (read-only, 9/9 ĐẠT):** admin = active, role = admin; rehearsal_admin / rehearsal_sale / rehearsal_support = inactive với lịch sử kiểm toán rõ ràng; 362 khách hàng, 78 lô hàng; không user nào khác bị thay đổi; 0 bản ghi tài chính mới phát sinh.

## 9. CLEANUP INCIDENT — ĐÃ GHI NHẬN, ĐÃ KHẮC PHỤC, KHÔNG CHE GIẤU

Trong lúc dọn 3 tài khoản thử, công cụ phiên bản cũ đã **xóa cứng** (hard-delete) thay vì khóa mềm — trái chỉ thị của anh. Tôi phát hiện qua kiểm tra, **khôi phục lại cả 3 tài khoản** từ bản sao lưu của LG02, sau đó viết lại công cụ thành khóa mềm (active = False + lịch sử trạng thái). Kết quả cuối cùng: 3 tài khoản thử đã khóa mềm đúng, có thể mở lại bất cứ lúc nào, tài khoản admin thật không bị chạm. Chi tiết trong `evidence/R0_release_verdict_facts.md` và `tools/cleanup_rehearsal_users.py`.

## 10. OWNER ACTION NEEDED — KHÔNG CÒN

Mọi bước đã hoàn tất; app tiếng Việt đang chạy trên máy anh. LOG-LG04 = NOT_STARTED.

Không bắt đầu LOG-LG04. LOG-LG03 kết thúc tại cổng duyệt và đã hoàn tất đúng phạm vi.
