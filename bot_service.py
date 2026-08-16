import telebot
import json
import google.generativeai as genai
import os
import sys
from datetime import datetime
from functools import lru_cache  # For cache

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.database import load_shipments_flat
except ImportError:
    load_shipments_flat = lambda: {}

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@lru_cache(maxsize=1, typed=True)  # Cache with TTL via timed refresh if needed
def fetch_clean_data():
    data_dict = load_shipments_flat()
    if not data_dict: return None
    
    clean_list = []
    for sid, r in data_dict.items():
        try:
            details = r.get('details', {})
            if not isinstance(details, dict): continue

            client_name = r.get('customer', 'N/A')
            s0 = details.get('0.0', {})
            s34 = details.get('3.4', {})
            
            status = s0.get('st', 'unknown')
            created_at = s0.get('created_at', '')
            
            month = "N/A"
            if created_at:
                try:
                    dt = datetime.strptime(str(created_at)[:10], "%Y-%m-%d")
                    month = dt.strftime("Tháng %m/%Y")
                except: pass

            rev = float(s34.get('out', 0))
            cost = float(s34.get('in', 0))
            comm = float(s34.get('commission', {}).get('total', 0))
            profit = rev - cost - comm
            
            clean_list.append({
                "Mã": sid,
                "Khách": client_name,
                "Ngày tạo": created_at,
                "Tháng": month,
                "Trạng thái": status,
                "Doanh thu": rev,
                "Lợi nhuận": profit
            })
        except Exception as inner_e:
            print(f"Lỗi dòng {sid}: {inner_e}")
            continue
        
    return clean_list

# (Giữ nguyên phần còn lại, nhưng gọi fetch_clean_data() sẽ cache)

if __name__ == "__main__":
    print("Bot Service is running...")
    bot.infinity_polling()