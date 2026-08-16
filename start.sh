#!/bin/bash

# Chạy Bot Telegram ngầm
python bot_service.py &

# Chạy Web App chính (Sửa app.py thành main.py)
streamlit run web_app.py --server.port $PORT --server.address 0.0.0.0