import os
import json
import time
import asyncio
import logging
from aiogram import Bot
from dotenv import load_dotenv

# Налаштування логування
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("Scheduler")

# Завантаження налаштувань
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
STATS_PATH = "data/stats.json"

bot = Bot(token=API_TOKEN)

async def check_and_send_feedback():
    """Перевіряє статистику та надсилає запити на відгук через 48 годин"""
    if not os.path.exists(STATS_PATH):
        log.info("📊 База статистики порожня.")
        return

    try:
        with open(STATS_PATH, "r", encoding="utf-8") as f:
            stats = json.load(f)
    except Exception as e:
        log.error(f"❌ Помилка читання бази: {e}")
        return

    current_time = int(time.time())
    delay = 48 * 3600  # 48 годин у секундах
    
    # Для тестування можна змінити delay на 60 секунд
    # delay = 60 

    updated = False
    for entry in stats:
        # Умова: пройшло 48 годин ТА фідбек ще не надсилався
        if not entry.get("feedback_sent") and (current_time - entry["timestamp"]) >= delay:
            user_id = entry["user_id"]
            spec_name = entry.get("spec_name", "спеціаліста")
            
            try:
                log.info(f"🚀 Надсилаю запит на відгук користувачу {user_id}...")
                await bot.send_message(
                    user_id,
                    f"🎖 **Контроль якості проекту 'Новий Шлях'**\n\n"
                    f"Минуло два дні з моменту, як ви отримали контакти {spec_name}.\n"
                    f"Будь ласка, знайдіть 1 хвилину, щоб оцінити роботу фахівця. \n"
                    f"Ваш відгук допоможе нам підтримувати чесність та якість допомоги іншим ветеранам.\n\n"
                    f"Для початку оцінки натисніть 👉 /feedback",
                    parse_mode="Markdown"
                )
                entry["feedback_sent"] = True
                updated = True
                # Невелика затримка, щоб не спамити API
                await asyncio.sleep(0.5)
            except Exception as e:
                log.error(f"⚠️ Не вдалося надіслати повідомлення {user_id}: {e}")

    if updated:
        try:
            with open(STATS_PATH, "w", encoding="utf-8") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            log.info("✅ Базу статистики оновлено.")
        except Exception as e:
            log.error(f"❌ Помилка запису бази: {e}")

async def main():
    log.info("🤖 Планувальник відгуків запущено...")
    while True:
        await check_and_send_feedback()
        # Перевірка щогодини (3600 сек)
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("🛑 Планувальник зупинено.")
