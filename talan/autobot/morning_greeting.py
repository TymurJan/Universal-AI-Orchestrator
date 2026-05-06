import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("ALLOWED_USER_IDS").split(",")[0]

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

print("⏰ Будильник встановлено на 09:00...")

while True:
    now = datetime.now()
    if now.hour == 9 and now.minute == 0:
        print("🔔 ЧАС ПРИЙШОВ! Відправляю привітання...")
        send_msg("☀️ **Доброго ранку, Тимуре!**\n\nЯ прокинувся. OpenAI прогрівся. Вся система ГО «Талан ЮА» готова до роботи. З 9-ю ранку вашого нового року! 🚀")
        break
    time.sleep(30) # Перевіряємо кожні 30 сек
