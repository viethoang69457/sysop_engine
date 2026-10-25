#!/usr/bin/env python3
import requests

TELEGRAM_BOT_TOKEN = "8178006927:AAGoY-NM1ZCp7jz-5aeCp6j6IOBlJ3c3hio"
TELEGRAM_CHAT_ID = "5711698626"

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
