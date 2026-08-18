# Mojibake UI giai quyet tren may Owner — 2026-08-18

## Ket qua xac nhan cuoi cung (Owner xac nhan truc tiep)
- Owner dang nhap thanh cong: username `admin`, mat khau dat rieng.
- UI chu tieng Viet CHUAN tren may Owner (sidebar: Tao Lo Moi,
  Khach Hang... khong con mojibake). Owner: "vao khong bi loi chu nua".

## Goc loi cuoi cung
1. File source tren GitHub da sach tu truoc (commits 0d6ce55 main,
   a77c675/4633711 rc: fix mojibake web_app.py, quotations.py, database.py).
2. Tren may Owner, process Streamlit CU dang giu cong 8501 tu truoc khi
   sua source van tiep tuc phuc vu UI mojibake (module cache trong RAM).
   Kiem tra bang netstat + taskkill (PID 5008, 11876 da bi kill).
3. Sau khi kill process cu + xoa __pycache__ + chay lai `python -m
   streamlit run app.py`, UI sach. Mot process chay tren cong moi 8601
   tu dau da hien UI sach + man hinh dang nhap (dieu nay chung minh
   source tren disk da dung).
4. Cong cu cuoi duoc them: `docs/goals/LOG-LG02/tools/reset_admin.py`
   (dat lai mat khau admin khong can UI, mat khau nhap an toan qua
   bien moi truong), da test thanh cong tren production DB va da push
   len main (merge 4194f4e) + rc (4633711).

## Bai hoc
- Khi source da sach ma UI van loi: nghi process Streamlit cu van song.
  Luon kill process dang giu port truoc khi chuan doan cache.
- Luon test tren cong moi chua tung dung de loai tru process cu.
- `python -m streamlit run` dam bao dung Python interpreter hien tai.
