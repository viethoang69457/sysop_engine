#!/usr/bin/env python3
import requests
import os
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path=env_path)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(message):
    """Gửi tin nhắn cảnh báo trực tiếp về Telegram"""
    print(f"\n[ALERT ENGINE TRIGGERED]:\n{message}\n")
    
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("[!] Telegram Token not configured.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"🚨 [SysOps Engine Alert] 🚨\n\n{message}",
        "parse_mode": "Markdown"
    }

    try:
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            print("[✓] Telegram alert sent successfully!")
        else:
            print(f"[!] Telegram API Error: {res.text}")
    except Exception as e:
        print(f"[!] Failed to send Telegram alert: {e}")

if __name__ == "__main__":
    send_alert("Test Alert System - Master Node Online!")
