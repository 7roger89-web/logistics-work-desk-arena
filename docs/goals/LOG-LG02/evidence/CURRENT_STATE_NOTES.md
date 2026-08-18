# TRẠNG THÁI CUỐI — 2026-08-18 (sau hotfix mojibake)

## NGUYÊN NHÂN GỐC của việc Owner vẫn thấy chữ lỗi
1. Máy Owner kéo branch `log-lg01-multi-user-internal-rc` (commit 1d48ddc) —
   bản hotfix của tôi nằm trên main (0d6ce55) nên pull không về được file sửa.
2. File `views/quotations.py`: TOÀN BỘ lịch sử git chứa mojibake (Owner push
   hỏng encoding từ đầu ở LG01) — không sửa được bằng git checkout.
3. `core/database.py`: dòng ConcurrentUpdateError mojibake trong R4 gate.
4. `views/web_app.py`: đã sửa trước đó (451 ký tự).

## SỬA XONG — VERIFIED
- Decoder THAM-LAM (greedy longest valid utf-8 group) với ARTIFACT_MAP
  cp1252 0x80-0x9F — xử lý được blob HỖN HỢP (char Việt sạch 0x80-0xFF +
  glyph mojibake). Test: /tmp/test_fix — 3 file fix, fffd=0, compileall pass,
  idempotent lần 2 (0 file).
- Branch rc đã được cập nhật: e8ee684 (merge main) + a77c675 (fix script)
  = remote HEAD rc hiện tại.
- main = 0d6ce55 (có hotfix).
- Script độc lập cho Owner: /home/ubuntu/fix_vietnamese.py (cũng push lên
  docs/goals/LOG-LG02/tools/fix_vietnamese.py trong branch rc).

## CÒN LẠI — GIAI ĐOẠN 3: gửi Owner
- Owner cần: git pull origin log-lg01-multi-user-internal-rc (sẽ lấy e8ee684+a77c675)
  rồi chạy `python docs\goals\LOG-LG02\tools\fix_vietnamese.py` trong repo,
  rồi `rd /s /q views\__pycache__` + `streamlit run web_app.py`.
- Đã gửi hướng dẫn 3 lệnh ở message trước; đang chờ Owner báo kết quả.
- App sandbox chạy trên 8501 (không ảnh hưởng máy Owner).
- Terminal outcome vẫn INTERNAL_RELEASE_VERIFIED (state.json đã commit).
