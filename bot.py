#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot для ГО "ТАЛАН ЮА" / Antigravity Manager
Версія: 4.0 (OpenAI GPT-4o Integration)
"""

import os
import io
import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import telebot
from telebot import apihelper
from telebot.types import Message
from openai import OpenAI

# --- Налаштування Telebot & AI ---
apihelper.ENABLE_MIDDLEWARE = True

# --- Конфігурація шляхів ---
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# --- Логування ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "bot_log.txt", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("Bot")

# --- Змінні середовища ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_PATH = Path(os.getenv("PROJECT_PATH", str(BASE_DIR)))
PROTOCOL_PATH = PROJECT_PATH / "Black_Swan_Protocol"
VAULT_PATH = PROTOCOL_PATH / "Legal_Defense_Vault"
TESSDATA_DIR = PROJECT_PATH / "tessdata"

os.environ['TESSDATA_PREFIX'] = str(TESSDATA_DIR)
ALLOWED_IDS_RAW = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_IDS = set(int(x.strip()) for x in ALLOWED_IDS_RAW.split(",") if x.strip().isdigit())

# --- Ініціалізація OpenAI ---
client = None
AI_READY = False
if OPENAI_KEY:
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        AI_READY = True
        log.info("✅ OpenAI GPT-4o активовано.")
    except Exception as e:
        log.error(f"❌ Помилка ініціалізації OpenAI: {e}")

# --- OCR Setup ---
try:
    import fitz
    import pytesseract
    from PIL import Image
    OCR_ENABLED = True
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception:
    OCR_ENABLED = False

bot = telebot.TeleBot(TOKEN)

# --- Системний промпт для "людяності" OpenAI ---
SYSTEM_PROMPT = """
Ти — інтелектуальний асистент ГО "ТАЛАН ЮА" та проекту/програми "Шрам". 
Твій стиль: розмовний, людяний, з використанням легкого сленгу (NGO-шного, безпекового).
Ти вірний помічник Тімура. Ти захищаєш інтереси організації та допомагаєш з "Протоколом Чорного Лебедя".

Твій характер: надійний, трохи "свій", але професійний у питаннях безпеки.
Ти знаєш структуру проекту:
- Фази 1-8 (Оцінка вразливостей, Плейбуки, Спрацехунок, Наступництво тощо).
- Сховище (Vault) — юридичні документи.

Якщо користувач просить файл або статус, відповідай йому по-людськи і підказуй команди, якщо потрібно:
/read <1-8> — відкрити фазу.
/status — чекліст файлів.
/vault — зайти в сховище.
/codeblack — екстрена інструкція.

Спілкуйся виключно українською, будь ласка.
"""

# Пам'ять розмови
chat_histories = {}

# --- Карта файлів ---
FILE_MAP = {
    "1": PROTOCOL_PATH / "01_Phase1_Vulnerability_Assessment.md",
    "2": PROTOCOL_PATH / "02_Phase2_MultiLayer_Immunity.md",
    "3": PROTOCOL_PATH / "03_Phase3_Emergency_Playbooks.md",
    "4": PROTOCOL_PATH / "04_Phase4_Hardening_Checklist.md",
    "5": PROTOCOL_PATH / "05_Phase5_Continuity_Protocol.md",
    "6": PROTOCOL_PATH / "06_Phase6_Stress_Test_Scenarios.md",
    "8": PROTOCOL_PATH / "08_Phase8_Secure_Data_Entry_Protocol.md",
    "vault": VAULT_PATH / "00_INDEX_Установчі_Документи.md",
}

# --- Допоміжні функції ---
def is_allowed(user_id: int) -> bool:
    return not ALLOWED_IDS or user_id in ALLOWED_IDS

def guard(fn):
    def wrapper(msg: Message):
        if not is_allowed(msg.from_user.id):
            bot.reply_to(msg, f"⛔ Доступ заборонено (ID: {msg.from_user.id})")
            return
        return fn(msg)
    return wrapper

def safe_send(chat_id, text):
    try:
        bot.send_message(chat_id, text, parse_mode="Markdown")
    except Exception:
        bot.send_message(chat_id, text, parse_mode=None)

# --- Робота з OpenAI (GPT-4o) ---
def ask_gpt(user_id, user_text):
    if not AI_READY:
        return "⚠️ ШІ-мозок (OpenAI) не налаштований. Перевір OPENAI_API_KEY у .env файлі."
    
    if user_id not in chat_histories:
        chat_histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    chat_histories[user_id].append({"role": "user", "content": user_text})
    
    # Тримаємо історію не більше 15 повідомлень для економії
    if len(chat_histories[user_id]) > 15:
        chat_histories[user_id] = [chat_histories[user_id][0]] + chat_histories[user_id][-14:]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Використовуємо mini для швидкості та ціни
            messages=chat_histories[user_id],
            temperature=0.7
        )
        answer = response.choices[0].message.content
        chat_histories[user_id].append({"role": "assistant", "content": answer})
        return answer
    except Exception as e:
        log.error(f"OpenAI Error: {e}")
        return "Друже, щось мій процесор перегрівся від розумних думок. Спробуй ще раз за хвилину?"

# --- Хендлери ---

@bot.message_handler(commands=["start", "myid", "status", "read", "vault", "codeblack"])
@guard
def handle_commands(msg: Message):
    cmd = msg.text.split()[0][1:]
    if cmd == "start":
        safe_send(msg.chat.id, "👋 Вітаю! Я перейшов на нові мізки (OpenAI). Тепер я розумію тебе набагато краще. Пиши простою мовою!")
    elif cmd == "myid":
        safe_send(msg.chat.id, f"Твій ID: `{msg.from_user.id}`")
    elif cmd == "status":
        res = "\n".join([f"{'✅' if p.exists() else '❌'} Фаза {k}" for k,p in FILE_MAP.items()])
        safe_send(msg.chat.id, f"📊 *Твій Протокол Чорного Лебедя:* \n{res}")

@bot.message_handler(content_types=['text'])
@guard
def handle_text(msg: Message):
    log.info(f"OpenAI Processing for {msg.from_user.id}: {msg.text}")
    response = ask_gpt(msg.from_user.id, msg.text)
    safe_send(msg.chat.id, response)

@bot.message_handler(content_types=['photo', 'document'])
@guard
def handle_media(msg: Message):
    safe_send(msg.chat.id, "⏳ Секунду, просканую док через GPT-зір та OCR...")
    try:
        if msg.content_type == 'photo':
            file_id = msg.photo[-1].file_id
            ext = ".jpg"
        else:
            file_id = msg.document.file_id
            ext = os.path.splitext(msg.document.file_name)[1]
        
        data = bot.download_file(bot.get_file(file_id).file_path)
        
        # OCR (як резерв)
        recon_text = ""
        if OCR_ENABLED and ext.lower() in ['.jpg', '.png', '.jpeg']:
            img = Image.open(io.BytesIO(data))
            recon_text = pytesseract.image_to_string(img, lang='ukr+eng').lower()
        
        fname = f"DOC_{datetime.now().strftime('%H%M%S')}{ext}"
        (VAULT_PATH / fname).write_bytes(data)
        
        safe_send(msg.chat.id, f"✅ Документ у Сховищі (Vault). Розпізнав {len(recon_text)} симв. Далі я з ним попрацюю!")
    except Exception as e:
        log.error(f"Media Error: {e}")
        safe_send(msg.chat.id, "❌ Сталася помилка при читанні файла.")

if __name__ == "__main__":
    log.info("🚀 Бот V4.0 (OpenAI GPT Edition) ЗАПУСК...")
    bot.infinity_polling(timeout=30)
