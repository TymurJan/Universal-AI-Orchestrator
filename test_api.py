import os
from dotenv import load_dotenv
import telebot

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

try:
    me = bot.get_me()
    print(f"✅ Підключено до Telegram!")
    print(f"Бот: @{me.username} (ID: {me.id})")
    
    updates = bot.get_updates()
    print(f"📦 Кількість очікуючих оновлень: {len(updates)}")
    for u in updates:
        if u.message:
            print(f"📩 Отримано повідомлення від ID {u.message.from_user.id}: {u.message.text}")
except Exception as e:
    print(f"❌ Помилка підключення: {e}")
