"""Internal Telegram knowledge bot for Logistics staff.

Plain staff questions are routed to configured NotebookLM domain notebooks.
Explicit /law queries use the verified VNLAW API. NotebookLM is an operational
knowledge layer only; legal authority remains with VNLAW / official sources.
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

from core.notebooklm_telegram import (
    NotebookLMConfigError,
    NotebookLMServiceError,
    answer_notebook_question,
)
from core.vnlaw_telegram import (
    VNLAWConfigError,
    VNLAWServiceError,
    answer_vnlaw_question,
    is_allowed_telegram_user,
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

HELP_TEXT = """🧠 Trợ lý tra cứu nội bộ Trường Thành Logistics

Gửi câu hỏi bình thường để bot tự phân loại:
• HS / mã HS
• Hóa chất
• Bộ KH&CN
• Bộ TT&TT

Có thể ép đúng nhóm bằng:
/hs <câu hỏi>
/hoachat <câu hỏi>
/bkhcn <câu hỏi>
/btttt <câu hỏi>

Tra cứu pháp lý đã xác minh:
/law <câu hỏi>
/law YYYY-MM-DD <câu hỏi>

NotebookLM hỗ trợ tra cứu nghiệp vụ; kết luận pháp lý cần đối chiếu VNLAW/nguồn chính thức."""


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
            "⛔ Tài khoản Telegram này chưa được cấp quyền tra cứu nội bộ.",
        )
        return False

    @bot.message_handler(commands=["start", "help"])
    def show_help(message):
        if getattr(getattr(message, "chat", None), "type", None) != "private":
            return
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
            command = text.split(" ", 1)[0].split("@", 1)[0].casefold()
            if command in {"/law", "/vnlaw"}:
                answer = answer_vnlaw_question(text)
            else:
                answer = answer_notebook_question(text)
        except ValueError as exc:
            if str(exc) == "HELP":
                answer = HELP_TEXT
            else:
                answer = f"⚠️ {exc}"
        except NotebookLMConfigError:
            answer = (
                "⚠️ NotebookLM chưa được cấu hình đầy đủ trên máy chủ. "
                "Vui lòng báo Admin Logistics."
            )
        except NotebookLMServiceError:
            answer = (
                "⚠️ NotebookLM hiện không trả lời được. "
                "Bot không tự bịa câu trả lời thay cho notebook."
            )
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
            # Do not log staff questions, auth state, URLs, headers or raw
            # NotebookLM/VNLAW responses on an unexpected failure.
            print(f"Knowledge bot unexpected error: {type(exc).__name__}")
            answer = "⚠️ Có lỗi nội bộ khi tra cứu. Vui lòng thử lại sau."
        bot.reply_to(message, answer[:3900], disable_web_page_preview=True)

    return bot


def main() -> int:
    if not TELEGRAM_TOKEN:
        print("Telegram bot disabled: TELEGRAM_TOKEN is not configured.")
        return 0
    bot = create_bot(TELEGRAM_TOKEN)
    print("Bot Service is running: NotebookLM routing + VNLAW lookup enabled.")
    bot.infinity_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
