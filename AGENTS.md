# AGENTS.md — luật làm việc cho executor trong repo này

## 1. Đọc gì trước
Đọc `docs/DONE.md` và `docs/PROCESS.md` trước khi làm bất cứ gì.

## 2. Một phiên một ticket
Chỉ nhận việc phục vụ trực tiếp 1 trong 5 điều kiện của `docs/DONE.md`.
Việc khác: đóng issue, không làm.

## 3. Nhánh
Một task một nhánh, tên `task/<số-issue>-<mô-tả>`. Gộp xong xoá nhánh.
Không đẩy thẳng `main`. Mục tiêu dưới 20 nhánh mở.

## 4. Bằng chứng
Lời tự khai không tính. Phải có output lệnh, ảnh chụp, hoặc số đo.
Kết luận cuối task chỉ một trong ba: XONG / CHƯA XONG / HỎNG.

## 5. Trước khi mở PR
Chạy theo thứ tự, hỏng việc nào thì dừng việc đó:
`ruff check .` ; `python scripts/check_router.py` ;
`python -m pytest tests -q --continue-on-collection-errors`.
`tests/BASELINE_FAILED.txt` là nợ cũ — chỉ chịu trách nhiệm lỗi MỚI.

## 6. Cấm
Không deploy production khi chưa có lệnh Owner. Không chạm `logistics_db`.
Không in URI/khóa/mật khẩu. Không thêm thư viện khi thư viện hiện có làm
được. Không đổi stack.

## 7. Database
Đọc README.md mục 7 trước khi làm bất cứ gì liên quan database.

## 8. Chống over engineering
Trước khi viết code mới, trả lời câu: "Không bị over engineering chứ?"
Nếu có đường đơn giản hơn thì chọn đường đó.
