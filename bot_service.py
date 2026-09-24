"""Internal Telegram bot service for Logistics staff.

The first production capability is read-only VNLAW lookup. The bot never owns
legal truth: it forwards one staff question to the configured VNLAW verified
query API and returns only the authority groups/provenance VNLAW supplied.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from functools import lru_cache

import telebot

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.database import load_shipments_flat
except ImportError:
    load_shipments_flat = lambda: {}

from core.vnlaw_telegram import (
    HELP_TEXT,
    VNLAWConfigError,
    VNLAWServiceError,
    answer_vnlaw_question,
    is_allowed_telegram_user,
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")


@lru_cache(maxsize=1, typed=True)
def fetch_clean_data():
    """Existing shipment projection retained for later staff-bot capabilities."""
    data_dict = load_shipments_flat()
    if not data_dict:
        return None

    clean_list = []
    for sid, row in data_dict.items():
        try:
            details = row.get("details", {})
            if not isinstance(details, dict):
                continue

            client_name = row.get("customer", "N/A")
            s0 = details.get("0.0", {})
            s34 = details.get("3.4", {})
            status = s0.get("st", "unknown")
            created_at = s0.get("created_at", "")

            month = "N/A"
            if created_at:
                try:
                    dt = datetime.strptime(str(created_at)[:10], "%Y-%m-%d")
                    month = dt.strftime("Tháng %m/%Y")
                except (TypeError, ValueError):
                    pass

            rev = float(s34.get("out", 0))
            cost = float(s34.get("in", 0))
            comm = float(s34.get("commission", {}).get("total", 0))
            clean_list.append(
                {
                    "Mã": sid,
                    "Khách": client_name,
                    "Ngày tạo": created_at,
                    "Tháng": month,
                    "Trạng thái": status,
                    "Doanh thu": rev,
                    "Lợi nhuận": rev - cost - comm,
                }
            )
        except (AttributeError, TypeError, ValueError) as exc:
            print(f"Lỗi dòng {sid}: {exc}")
            continue
    return clean_list


def create_bot(token: str) -> telebot.TeleBot:
    bot = telebot.TeleBot(token)

    def _authorized(message) -> bool:
        user = getattr(message, "from_user", None)
        user_id = getattr(user, "id", None)
        if is_allowed_telegram_user(user_id):
            return True
        bot.reply_to(
            message,
            "⛔ Tài khoản Telegram này chưa được cấp quyền tra cứu VNLAW nội bộ.",
        )
        return False

    @bot.message_handler(commands=["start", "help"])
    def show_help(message):
        if not _authorized(message):
            return
        bot.reply_to(message, HELP_TEXT, disable_web_page_preview=True)

    @bot.message_handler(
        func=lambda message: getattr(
            getattr(message, "chat", None), "type", None
        ) == "private",
        content_types=["text"],
    )
    def answer_private_text(message):
        if not _authorized(message):
            return
        text = (getattr(message, "text", None) or "").strip()
        if not text:
            return
        try:
            bot.send_chat_action(message.chat.id, "typing")
            answer = answer_vnlaw_question(text)
        except ValueError as exc:
            if str(exc) == "HELP":
                answer = HELP_TEXT
            else:
                answer = f"⚠️ {exc}"
        except VNLAWConfigError:
            answer = (
                "⚠️ Kênh VNLAW chưa được cấu hình trên máy chủ. "
                "Vui lòng báo Admin Logistics."
            )
        except VNLAWServiceError:
            answer = (
                "⚠️ VNLAW hiện chưa trả được kết quả xác minh. "
                "Bot không tự suy đoán thay cho nguồn pháp lý."
            )
        except Exception as exc:
            print(f"VNLAW bot unexpected error: {type(exc).__name__}: {exc}")
            answer = "⚠️ Có lỗi nội bộ khi tra cứu VNLAW. Vui lòng thử lại sau."
        bot.reply_to(message, answer, disable_web_page_preview=True)

    return bot


def main() -> int:
    if not TELEGRAM_TOKEN:
        print("Telegram bot disabled: TELEGRAM_TOKEN is not configured.")
        return 0
    bot = create_bot(TELEGRAM_TOKEN)
    print("Bot Service is running: VNLAW verified lookup enabled.")
    bot.infinity_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
