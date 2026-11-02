# PROCESS — quy trình làm việc

Áp dụng cho mọi việc trong repo này. Năm bước, ba cổng. Cổng không qua thì dừng.

| Bước | Ai | Ra cái gì | Cổng |
|---|---|---|---|
| 1 Hỏi cho rõ | ChatGPT | Trang mô tả + mục KHÔNG LÀM | Owner đọc, thấy đúng ý |
| 2 Chia nhỏ | ChatGPT | Tối đa 3 ticket | Mỗi ticket làm được trong 1 phiên |
| 3 Thi công | Codex / arena | Code + test + PR nháp | CI xanh, không lỗi mới |
| 4 Soát | Codex | Danh sách lỗi | Không còn mục đỏ |
| 5 Ghi lại | ChatGPT | 5 dòng vào docs/NEXT.md | Phiên sau đọc là hiểu |

## Bước 1 — Hỏi cho rõ

```
/grill-me

Việc: <một câu>
Đọc docs/DONE.md để biết cái gì thuộc phạm vi xong.
Hỏi tôi từng câu một, tối đa 15 câu, về: đúng ý chưa, không làm gì,
lấy gì làm bằng chứng, hỏng thì lùi thế nào.
Xong thì viết một trang mô tả, cuối trang có mục "KHÔNG LÀM".
```

Không viết code ở bước này.

## Bước 2 — Chia nhỏ

```
/to-tickets
Chia trang mô tả trên thành tối đa 3 việc, mỗi việc làm được trong một
phiên. Ghi rõ thứ tự và việc nào chặn việc nào.
```

Mỗi ticket phải có đủ: việc duy nhất, bằng chứng sẽ lấy, không làm gì.

## Bước 3 — Thi công

Một phiên làm đúng một ticket.

```
Việc duy nhất: <dán đúng một dòng ticket>

BƯỚC 0: in git remote -v, nhánh hiện tại, git ls-files AGENTS.md.
Sai repo thì dừng.
Đọc AGENTS.md và docs/PROCESS.md. Tạo nhánh task/<số>-<mô-tả>.
Làm đúng việc này, không mở rộng.
Trước khi mở PR: ruff check ., scripts/check_router.py, pytest.
PR nháp. Kết luận XONG / CHƯA XONG / HỎNG.
```

## Bước 4 — Soát

```
/code-review
Soát diff so với main. Chỉ báo lỗi, không sửa.
```

Có mục đỏ thì quay lại bước 3.

## Bước 5 — Ghi lại

```
/handoff
Ghi 5 dòng vào docs/NEXT.md mục LỊCH SỬ: ngày, việc, kết quả,
cái gì còn lại, nhánh nào đang mở.
```

## Bỏ bước khi nào
Sửa một chữ trong tài liệu: bỏ bước 1, 2, 4. Sửa CSS, màu, khoảng cách: bỏ
bước 1, 2. Đụng tiền, chứng từ pháp lý, danh tính database: không bỏ bước nào.
