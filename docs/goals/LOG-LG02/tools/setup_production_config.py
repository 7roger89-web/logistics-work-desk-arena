"""One-command helper: tao .streamlit/secrets.toml chuan cho production cutover.

Doc file secrets.toml CU dang hoat dong cua Owner (chua key Gemini/Telegram
that), them/cap nhat phan [mongo] voi production URI va bat [auth].required.
Khong dong vao bat ky du lieu database nao. Luu ban sao an toan truoc.

Cach dung (Windows cmd, trong thu muc repo):
  python docs\goals\LOG-LG02\tools\setup_production_config.py

Script hoi 2 thu:
  1. URI ket noi Atlas (copy tu Cloud Atlas > Connect > Connect your application,
     thay <db_password> bang mat khau that).
  2. Xac nhan ghi de bang token "CONFIG CONFIRM".
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
STREAMLIT_DIR = REPO / ".streamlit"
SECRETS = STREAMLIT_DIR / "secrets.toml"

PROD_URI_PREFIX = "mongodb+srv://"
PROD_DB = "logistics_db"


def ask(question: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{question}{suffix}: ").strip()
    return raw or (default or "")


def main() -> None:
    print("=== LOG-LG02 Production Config Setup ===")

    # 1. Keep a safe copy of whatever is currently there.
    if SECRETS.exists():
        backup = REPO / f"backups/secrets_before_cutover_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.toml"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SECRETS, backup)
        print(f"Da sao luu file cu thanh: {backup}")
    else:
        print("CANH BAO: khong tim thay .streamlit/secrets.toml hien tai.")
        print("App chua tung chay o che do da cau hinh? Tiep tuc se tao file moi.")

    # 2. Collect the production URI.
    uri = ask(
        "URI ket noi Atlas Cluster0 (mongdbsrv://admin:matkhau@cluster0...)\n"
        "Lay tu Atlas > Connect > Connect your application, thay <db_password>",
    )
    if not uri.startswith(PROD_URI_PREFIX):
        print(f"LOI: URI phai bat dau bang {PROD_URI_PREFIX}")
        sys.exit(1)
    if "<db_password>" in uri or "<db_username>" in uri:
        print("LOI: URI chua placeholder <db_password>/<db_username>. Thay bang thong tin that.")
        sys.exit(1)

    # 3. Preserve real gemini/telegram values from the old file when possible.
    old = ""
    if SECRETS.exists():
        old = SECRETS.read_text(encoding="utf-8")

    def old_value(section: str, key: str, default: str = '""') -> str:
        import re

        for line in old.splitlines():
            m = re.match(rf'^\s*{re.escape(key)}\s*=\s*(.*)$', line)
            if m:
                return m.group(1).strip()
        return default

    gemini_key = old_value("gemini", "api_key")
    telegram_token = old_value("telegram", "token")
    telegram_chat_id = old_value("telegram", "chat_id")

    # 4. Compose the canonical secrets file (plain ASCII-safe content).
    new_content = (
        '[mongo]\n'
        f'uri = "{uri}"\n'
        f'database = "{PROD_DB}"\n'
        'allowed_databases = ["logistics_db", "logistics_workdesk_logc14", "logistics_workdesk_LG01_E2E"]\n'
        "release_mode = true\n"
        "\n"
        '[env]\n'
        'identity = "PROD_INTERNAL"\n'
        "\n"
        "[auth]\n"
        "required = true\n"
        "\n"
        "[gemini]\n"
        f"api_key = {gemini_key}\n"
        "\n"
        "[telegram]\n"
        f"token = {telegram_token}\n"
        f"chat_id = {telegram_chat_id}\n"
    )

    # 5. Validate TOML before writing.
    try:
        import toml  # noqa: PLC0415

        toml.loads(new_content)
        parsed = toml.loads(new_content)
    except ImportError:
        print("Thieu goi toml: dang python -m pip install toml")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"LOI TOML: {exc}")
        sys.exit(1)

    assert parsed["mongo"]["uri"] == uri
    assert parsed["mongo"]["database"] == PROD_DB
    assert "logistics_db" in parsed["mongo"]["allowed_databases"]
    assert parsed["mongo"]["release_mode"] is True
    assert parsed["auth"]["required"] is True

    print("\nNoi dung se ghi:")
    print(new_content)

    # 6. Confirm.
    token = ask('Nhap "CONFIG CONFIRM" de ghi de secrets.toml')
    if token != "CONFIG CONFIRM":
        print("Da huy. Khong gi duoc ghi.")
        sys.exit(0)

    STREAMLIT_DIR.mkdir(parents=True, exist_ok=True)
    SECRETS.write_text(new_content, encoding="utf-8")
    print("DA GHI: .streamlit/secrets.toml (UTF-8, dinh dang chuan).")
    print("\nBuoc tiep theo: trong cmd, nhan Ctrl+C de dung app cu, roi chay lai:")
    print("  streamlit run web_app.py")
    print("Mo trinh duyet tai http://localhost:8501 - form tao Admin se hien.")


if __name__ == "__main__":
    main()
