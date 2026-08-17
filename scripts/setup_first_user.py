"""LOG-C15 — Bootstrap tài khoản Admin đầu tiên (CLI an toàn).

Chạy trực tiếp trên máy chủ (KHÔNG qua Streamlit):

    python scripts/setup_first_user.py

Quy tắc an toàn:
1. Chỉ tạo khi users collection TRỐNG — nếu đã có user nào đó, script dừng
   ngay (không đè tài khoản hiện có).
2. MẬT KHẨU KHÔNG ĐƯỢC TRUYỀN QUA ARGS/ENV: script tương tác nhập password
   tại terminal (getpass), không in ra màn hình, không lưu vào file.
3. Validation như UI: username 3-30 ký tự chữ thường an toàn; mật khẩu ≥8;
   mật khẩu xác nhận phải khớp.
4. Lưu bằng chính hàm persistence chuẩn của ứng dụng (core.database.save_user)
   — không tự viết query riêng.
5. Kết quả xác nhận: in username/role (KHÔNG in mật khẩu/hash).

Yêu cầu: MONGO_URI/database đã cấu hình trong .streamlit/secrets.toml
hoặc biến môi trường MONGO_URI/MONGODB_DATABASE.
"""
from __future__ import annotations

import getpass
import sys

sys.path.insert(0, ".")

from core.database import load_users, save_user
from core.users import UserError, build_user_document


def _prompt_until(message: str, predicate=None) -> str:
    while True:
        value = input(message).strip()
        if value and (predicate is None or predicate(value)):
            return value
        print("  Giá trị không hợp lệ, nhập lại.")


def _prompt_username() -> str:
    return _prompt_until(
        "Tên đăng nhập (3-30 ký tự, chữ thường, số, dấu chấm/gạch): ",
    )


def _prompt_password() -> tuple[str, str]:
    while True:
        password = getpass.getpass("Mật khẩu (≥8 ký tự, không hiển thị): ")
        confirm = getpass.getpass("Nhập lại mật khẩu: ")
        if len(password) < 8:
            print("  Mật khẩu cần ít nhất 8 ký tự.")
            continue
        if password != confirm:
            print("  Mật khẩu xác nhận không khớp.")
            continue
        return password, confirm


def main() -> int:
    print("LOG-C15 — Bootstrap tài khoản Admin đầu tiên")
    print("=" * 52)

    try:
        existing = load_users()
    except Exception as exc:  # noqa: BLE001
        print(f"LỖI: Không kết nối được database: {exc}")
        return 2

    if existing:
        print("NGỪNG: đã có tài khoản trong hệ thống — không tạo đè.")
        print(f"Hiện có {len(existing)} tài khoản. Dùng màn 'Tài khoản hệ thống'")
        print("trong UI (Admin) để tạo tài khoản mới hoặc reset mật khẩu.")
        return 3

    username = _prompt_username()
    display_name = _prompt_until("Tên hiển thị: ")
    email = input("Email (không bắt buộc): ").strip().lower()
    password, _confirm = _prompt_password()

    try:
        document = build_user_document(
            username=username,
            password=password,
            display_name=display_name,
            role="admin",
            email=email,
            created_by="cli-bootstrap",
        )
    except UserError as exc:
        print(f"LỖI: {exc}")
        return 4

    if not save_user(document):
        print("LỖI: Không lưu được tài khoản. Kiểm tra kết nối database.")
        return 5

    print(f"OK: Đã tạo tài khoản Admin '{document['username']}' (role: admin).")
    print("    Mật khẩu được lưu dạng hash — không thể xem lại.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
