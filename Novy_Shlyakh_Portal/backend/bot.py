import os
import re
import json
import asyncio
import logging
import tempfile
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, ReplyKeyboardRemove, MenuButtonWebApp, MenuButtonDefault
from dotenv import load_dotenv

# Завантаження налаштувань
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = os.getenv("ADMIN_ID", "YOUR_TELEGRAM_ID")
PORTAL_URL = os.getenv("PORTAL_URL", "https://talan.ua/novy-shlyakh") # Посилання на сайт

# Налаштування логування
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

from aiogram import BaseMiddleware
import time

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit=1.0):
        self.limit = limit
        self.users = {}

    async def __call__(self, handler, event, data):
        if not hasattr(event, "from_user") or not event.from_user:
            return await handler(event, data)
        
        user_id = event.from_user.id
        now = time.time()
        if user_id in self.users:
            if now - self.users[user_id] < self.limit:
                # Spam detected (Double Front Door effect)
                return
        self.users[user_id] = now
        return await handler(event, data)

dp.message.middleware(ThrottlingMiddleware())


# Шлях до бази даних
JSON_PATH = "data/specialists.json"

# Підключаємо менеджер бази даних
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    import db_manager
except ImportError:
    from . import db_manager

# СТАНИ FSM (Для реєстрації спеціаліста)
class Registration(StatesGroup):
    name = State()
    category = State()
    address = State()
    phone = State()
    bio = State()
    discount = State()
    photo = State()
    document = State()
    
    # States for the portal transition (optional, kept for logic)
    portal_redirect = State()
    
    # Стан для редагування
    edit_field = State()
    edit_value = State()

class AIMatchmaking(StatesGroup):
    waiting_for_query = State()

# СТАНИ ДЛЯ ВІДГУКІВ
class Feedback(StatesGroup):
    waiting_for_spec = State()
    rating_quality = State()
    rating_ethics = State()
    rating_honesty = State()
    comment = State()

# СТАНИ ДЛЯ ФІНАНСІВ
class Financial(StatesGroup):
    reporting_amount = State()
    uploading_receipt = State()

# --- ДОПОМІЖНІ ФУНКЦІЇ ---

db_lock = asyncio.Lock()

async def load_db_async():
    """Завантажує спеціалістів з SQL бази."""
    async with db_lock:
        try:
            return db_manager.get_specialists()
        except Exception as e:
            logging.error(f"SQL Load Error: {e}. Falling back to JSON.")
            try:
                with open(JSON_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []

async def save_db_async(data):
    """Синхронізує дані (SQL вже оновився через db_manager, тут робимо JSON бекап)."""
    async with db_lock:
        try:
            db_manager.sync_to_json()
        except Exception as e:
            logging.error(f"Sync to JSON error: {e}")


def validate_text(text, min_words=1, min_len=2, allow_latin=False):
    # Видаляємо зайві пробіли
    text = text.strip()
    
    # Перевірка на мову (тільки українська + спецсимволи)
    if not allow_latin:
        if re.search(r'[a-zA-Z]', text):
            return False, "❌ Будь ласка, використовуйте лише українську мову (латиниця заборонена)."
    
    # Перевірка на російські літери
    if re.search(r'[ыэъЫЭЪ]', text):
        return False, "❌ Будь ласка, використовуйте лише українську мову (російські літери заборонені)."
        
    # Перевірка на безглузді повтори літер (напр. 'ааааа')
    if re.search(r'(.)\1{3,}', text):
        return False, "❌ Текст містить занадто багато повторюваних символів. Напишіть змістовно."
        
    words = text.split()
    if len(words) < min_words:
        return False, f"❌ Будь ласка, введіть принаймні {min_words} слова."
        
    if len(text) < min_len:
        return False, f"❌ Текст занадто короткий (мінімум {min_len} симв.)."
        
    # Перевірка на повтори слів (напр. 'апро апро апро')
    if len(words) > 2:
        unique_words = set(w.lower() for w in words)
        if len(unique_words) / len(words) < 0.4:
            return False, "❌ Ваша відповідь містить занадто багато однакових слів. Будь ласка, опишіть детальніше."
            
    # Перевірка на "клавіатурне сміття" (машинг)
    vowels = "аеєиіїоуюя"
    consonants = "бвгґджзйклмнпрстфхцчшщ"
    
    for word in words:
        if len(word) > 5:
            word_lower = word.lower()
            # Шукаємо 5+ приголосних підряд (типу 'йцукен')
            consonant_streak = 0
            for char in word_lower:
                if char in consonants:
                    consonant_streak += 1
                    if consonant_streak >= 5:
                        return False, f"❌ Слово '{word}' схоже на випадковий набір літер. Будь ласка, пишіть зрозуміло."
                else:
                    consonant_streak = 0
            
            # Перевірка балансу голосних (в українській мові зазвичай 30-50% голосних)
            v_count = sum(1 for char in word_lower if char in vowels)
            if v_count == 0 or (v_count / len(word) < 0.15):
                return False, f"❌ Слово '{word}' містить занадто мало голосних. Це не схоже на українське слово."

    return True, ""

# --- ГОРОВНЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logging.info(f"DEBUG: /start command received from {message.from_user.id}")
    # Обробка параметрів старту (наприклад, ?start=login з сайту)
    args = message.text.split()
    is_login_redirect = len(args) > 1 and args[1] == "login"
    
    db = await load_db_async()
    # Перевіряємо, чи є цей користувач серед спеціалістів (шукаємо tg_id або префікс в id)
    user_id_str = str(message.from_user.id)
    is_specialist = any(
        str(s.get("tg_id")) == user_id_str or 
        str(s.get("id", "")).startswith(f"user_{user_id_str}") 
        for s in db
    )
    
    kb = [[KeyboardButton(text="🎖️ Я Ветеран / Родина")]]
    
    if is_specialist:
        kb.append([KeyboardButton(text="👤 Мій Кабінет")])
    else:
        kb.append([KeyboardButton(text="💼 Я Спеціаліст (Реєстрація)")])
        
    import time
    timestamp = int(time.time())
    kb.append([KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v={timestamp}"))])
    
    if str(message.from_user.id).strip() == str(ADMIN_ID).strip():
        kb.append([KeyboardButton(text="🛡️ Адмін-панель")])
        
    reply_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    welcome_text = "Вітаємо у координаційному центрі **'Новий Шлях'**!\n\nЦей бот допоможе вам знайти фахівця або долучитися до нашої мережі підтримки."
    if is_login_redirect:
        welcome_text = "🔐 **Ви успішно авторизувалися через портал!**\n\nВаше меню керування активоване нижче 👇"
        # Примусове оновлення UI: видаляємо і повертаємо клавіатуру
        tmp = await message.answer("Оновлення інтерфейсу...", reply_markup=ReplyKeyboardRemove())
        await tmp.delete()

    await message.answer(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

@dp.message(F.text == "🌐 Перейти на Портал")
async def portal_redirect(message: types.Message):
    kb = [[InlineKeyboardButton(text="🚀 Відкрити Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]]
    await message.answer(
        "Натисніть кнопку нижче, щоб перейти до ветеранського порталу. \n\n"
        "На комп'ютері він відкриється у браузері, на телефоні — у Telegram. 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# --- ШЛЯХ ВЕТЕРАНА ---
@dp.message(F.text == "🎖️ Я Ветеран / Родина")
async def veteran_menu(message: types.Message, state: FSMContext = None):
    # Якщо state не передано, спробуємо отримати його (для виклику з інших функцій)
    if state is None:
        state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
        
    kb = [
        [InlineKeyboardButton(text="🤖 Підібрати спеціаліста (AI)", callback_data="ai_matchmaking")],
        [InlineKeyboardButton(text="⚖️ Юрист", callback_data="find_legal")],
        [InlineKeyboardButton(text="🧠 Психолог", callback_data="find_psychology")],
        [InlineKeyboardButton(text="🦾 Реабілітація", callback_data="find_rehab")],
        [InlineKeyboardButton(text="💼 Кар'єра", callback_data="find_career")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    
    # Створюємо нижню клавіатуру для навігації
    nav_kb = [
        [KeyboardButton(text="⬅️ Повернутися до вибору ролі")],
        [KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]
    ]
    nav_markup = ReplyKeyboardMarkup(keyboard=nav_kb, resize_keyboard=True)
    
    # Зберігаємо ID повідомлення з меню, щоб видалити його потім
    msg = await message.answer("Яка допомога вам потрібна зараз?", reply_markup=markup)
    await state.update_data(last_menu_id=msg.message_id)
    await message.answer("Ви можете повернутися або перейти на портал кнопками внизу 👇", reply_markup=nav_markup)

@dp.message(F.text == "⬅️ Повернутися до вибору ролі")
async def back_to_main_msg(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    
    # Спроба видалити останнє Inline-меню, якщо воно є
    data = await state.get_data()
    last_menu_id = data.get("last_menu_id")
    if last_menu_id:
        try:
            await bot.delete_message(message.chat.id, last_menu_id)
        except Exception:
            pass
            
    await state.clear()
    await cmd_start(message)

@dp.callback_query(F.data == "to_main_menu")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete() # Видаляємо старе меню
    # Викликаємо головне меню з відновленням ReplyKeyboardMarkup
    await cmd_start(callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith("find_"))
async def show_specialists(callback: types.CallbackQuery):
    await callback.message.delete() # Видаляємо меню вибору, щоб не захаращувати чат
    category = callback.data.split("_")[1]
    
    # Миттєво оновлюємо клавіатуру (прибираємо кнопку порталу)
    nav_kb = [[KeyboardButton(text="⬅️ Повернутися до вибору послуг")]]
    nav_markup = ReplyKeyboardMarkup(keyboard=nav_kb, resize_keyboard=True)
    await callback.message.answer("Завантажую список фахівців... 🔎", reply_markup=nav_markup)
    
    db = await load_db_async()
    # Показуємо тільки верифікованих
    specialists = [s for s in db if s.get("category") == category and s.get("status") == "verified"]
    
    if not specialists:
        await callback.message.answer(
            "Наразі у цій категорії немає активних фахівців. Ми працюємо над розширенням мережі!"
        )
        return

    def get_cat_name(cat):
        names = {"legal": "Юрист", "psychology": "Психолог", "rehab": "Реабілітолог", "career": "Кар'єра/Бізнес"}
        return names.get(cat, cat)

    for s in specialists:
        text = (
            f"👤 **{s.get('name', 'Без імені')}**\n"
            f"🎓 {get_cat_name(s.get('category'))}\n"
            f"📍 {s.get('address', 'Черкаси')}\n"
            f"🎁 Пільги: {s.get('discount', 'Уточнюйте')}\n\n"
            f"📝 {s.get('bio', '')}"
        )
        
        await callback.message.answer(
            text, 
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📞 Отримати контакти", callback_data=f"contact_{s['id']}")]]),
            parse_mode="Markdown"
        )
    
    await callback.answer()

@dp.callback_query(F.data.startswith("contact_"))
async def handle_contact_request(callback: types.CallbackQuery):
    spec_id = callback.data.replace("contact_", "")
    db = await load_db_async()
    spec = next((s for s in db if str(s.get("id")) == str(spec_id) or s.get("tg_id") == spec_id), None)
    
    if spec:
        # --- ДИСПЕТЧЕРСЬКА ЛОГІКА (SQL Logging) ---
        try:
            # Зберігаємо факт звернення в SQL
            db_manager.log_intake(callback.from_user.id, spec.get('id'))
            logging.info(f"✅ Intake logged for veteran {callback.from_user.id} to spec {spec.get('id')}")
        except Exception as e:
            logging.error(f"Intake logging error: {e}")

        # Надсилаємо контакти користувачу
        contact_text = f"📞 Телефон: `{spec.get('phone', 'Не вказано')}`"
        if spec.get('username'):
            contact_text += f"\n✈️ Telegram: @{spec['username']}"
        
        await callback.message.answer(f"✅ Контакти спеціаліста {spec.get('name', '')}:\n\n{contact_text}", parse_mode="Markdown")
        
        # Попередження про зворотний зв'язок
        await callback.message.answer(
            "⏳ **За 48 годин** ми надішлемо вам коротке опитування, щоб дізнатися, чи була ця допомога корисною. \n"
            "Це допомагає нам покращувати сервіс для ветеранів. Дякуємо!",
            parse_mode="Markdown"
        )
        
        # Сповіщаємо спеціаліста
        if spec.get('tg_id'):
            try:
                await bot.send_message(
                    spec['tg_id'],
                    f"🔔 До ваших контактів щойно звернувся користувач через портал 'Новий Шлях'!\n"
                    f"Будьте готові до дзвінка або повідомлення. Дякуємо за вашу працю! 🫡"
                )
            except Exception:
                pass
    
    await callback.answer("Контакти отримано та зафіксовано в системі!")

@dp.message(F.text == "⬅️ Повернутися до вибору послуг")
async def back_to_vet_menu_msg(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    await veteran_menu(message, state)

# --- ШЛЯХ СПЕЦІАЛІСТА (FSM) ---
@dp.message(F.text == "💼 Я Спеціаліст (Реєстрація)")
async def spec_reg_start(message: types.Message, state: FSMContext):
    await state.set_state(Registration.name)
    kb = [
        [KeyboardButton(text="❌ Скасувати реєстрацію")],
        [KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]
    ]
    msg = await message.answer(
        "Розпочнемо реєстрацію. Як вас звати? (Введіть ПІБ та посаду)", 
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
    await state.update_data(last_prompt_id=msg.message_id)

@dp.message(F.text == "❌ Скасувати реєстрацію")
async def cancel_reg(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    await state.clear()
    await cmd_start(message)

@dp.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    is_valid, error_msg = validate_text(message.text, min_words=2, min_len=5)
    if not is_valid:
        await message.answer(error_msg)
        return
    await state.update_data(name=message.text)
    kb = [
        [InlineKeyboardButton(text="Юрист", callback_data="cat_legal")],
        [InlineKeyboardButton(text="Психолог", callback_data="cat_psychology")],
        [InlineKeyboardButton(text="Реабілітолог", callback_data="cat_rehab")],
        [InlineKeyboardButton(text="Кар'єра/Бізнес", callback_data="cat_career")]
    ]
    await state.set_state(Registration.category)
    
    nav_kb = [
        [KeyboardButton(text="⬅️ Назад до імені")],
        [KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]
    ]
    await message.answer("Оберіть вашу категорію:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    msg = await message.answer("Ви можете повернутися або перейти на портал 👇", reply_markup=ReplyKeyboardMarkup(keyboard=nav_kb, resize_keyboard=True))
    await state.update_data(last_prompt_id=msg.message_id)

@dp.message(Registration.category, F.text == "⬅️ Назад до імені")
async def back_to_name(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    
    data = await state.get_data()
    last_id = data.get("last_prompt_id")
    if last_id:
        try:
            await bot.delete_message(message.chat.id, last_id)
        except:
            pass
            
    await state.set_state(Registration.name)
    kb = [
        [KeyboardButton(text="❌ Скасувати реєстрацію")],
        [KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]
    ]
    msg = await message.answer(
        "Повертаємось. Як вас звати? (Введіть ПІБ та посаду)", 
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
    await state.update_data(last_prompt_id=msg.message_id)

@dp.callback_query(F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.split("_")[1]
    await state.update_data(category=cat)
    await state.set_state(Registration.phone)
    
    kb = [
        [KeyboardButton(text="📱 Поділитися моїм номером", request_contact=True)],
        [KeyboardButton(text="⬅️ Назад до категорії")],
        [KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]
    ]
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await callback.message.answer("📞 Будь ласка, поділіться своїм номером телефону для верифікації:", reply_markup=markup)
    await callback.answer()

@dp.message(Registration.address, F.text == "⬅️ Назад до категорії")
async def back_to_cat(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    
    data = await state.get_data()
    last_id = data.get("last_prompt_id")
    if last_id:
        try:
            await bot.delete_message(message.chat.id, last_id)
        except:
            pass
            
    await state.set_state(Registration.category)
    # Відправляємо вибір категорії ще раз
    kb = [
        [InlineKeyboardButton(text="Юрист", callback_data="cat_legal")],
        [InlineKeyboardButton(text="Психолог", callback_data="cat_psychology")],
        [InlineKeyboardButton(text="Реабілітолог", callback_data="cat_rehab")],
        [InlineKeyboardButton(text="Кар'єра/Бізнес", callback_data="cat_career")]
    ]
    await message.answer("Оберіть вашу категорію:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    nav_kb = [[KeyboardButton(text="⬅️ Назад до імені")], [KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]]
    msg = await message.answer("Ви можете повернутися або перейти на портал 👇", reply_markup=ReplyKeyboardMarkup(keyboard=nav_kb, resize_keyboard=True))
    await state.update_data(last_prompt_id=msg.message_id)

@dp.callback_query(F.data == "reg_back_cat")
async def reg_back_cat(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # Імітуємо повідомлення з ім'ям щоб викликати вибір категорії
    msg = types.Message(message_id=0, date=None, chat=callback.message.chat, from_user=callback.from_user, text=data.get('name'))
    await process_name(msg, state)
    await callback.message.delete()
    await callback.answer()

@dp.message(Registration.address)
async def process_address(message: types.Message, state: FSMContext):
    is_valid, error_msg = validate_text(message.text, min_words=1, min_len=5)
    if not is_valid:
        await message.answer(error_msg)
        return
    await state.update_data(address=message.text)
    await state.set_state(Registration.phone)
    kb = [
        [KeyboardButton(text="📱 Поділитися моїм номером", request_contact=True)],
        [KeyboardButton(text="⬅️ Назад до адреси")],
        [KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]
    ]
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("📞 Будь ласка, поділіться своїм номером телефону для верифікації:", reply_markup=markup)

@dp.message(Registration.phone, F.text == "⬅️ Назад до адреси")
async def reg_back_address(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    
    data = await state.get_data()
    last_id = data.get("last_prompt_id")
    if last_id:
        try:
            await bot.delete_message(message.chat.id, last_id)
        except:
            pass
            
    await state.set_state(Registration.address)
    nav_kb = [[KeyboardButton(text="⬅️ Назад до категорії")], [KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]]
    msg = await message.answer("Повертаємось. Введіть адресу вашого кабінету ще раз:", reply_markup=ReplyKeyboardMarkup(keyboard=nav_kb, resize_keyboard=True))
    await state.update_data(last_prompt_id=msg.message_id)

@dp.message(Registration.phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("❌ З метою безпеки ви можете зареєструвати лише свій власний номер телефону. Будь ласка, скористайтеся системною кнопкою.")
        return
    phone = contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    
    data = await state.get_data()
    data['phone'] = phone
    
    # Формуємо посилання на портал з даними (базове кодування)
    import urllib.parse
    params = {
        "name": data.get("name"),
        "cat": data.get("category"),
        "phone": phone,
        "tg_id": message.from_user.id
    }
    query = urllib.parse.urlencode(params)
    reg_url = f"{PORTAL_URL}#registration?{query}"
    
    kb = [[InlineKeyboardButton(text="🚀 Завершити реєстрацію на порталі", web_app=WebAppInfo(url=reg_url))]]
    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    
    await message.answer(
        "✅ Основну інформацію отримано!\n\n"
        "Тепер, будь ласка, перейдіть на наш портал для завершення реєстрації. \n"
        "Там ви зможете:\n"
        "1. Завантажити документи та фото.\n"
        "2. Ознайомитися з Політикою конфіденційності.\n"
        "3. Підписати угоду про співпрацю.\n\n"
        "Це необхідно для верифікації вашого профілю.",
        reply_markup=markup
    )
    await state.clear()

@dp.message(Registration.bio, F.text == "⬅️ Назад до телефону")
async def back_to_phone(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
        
    data = await state.get_data()
    last_id = data.get("last_prompt_id")
    if last_id:
        try:
            await bot.delete_message(message.chat.id, last_id)
        except:
            pass
            
    await state.set_state(Registration.phone)
    kb = [
        [KeyboardButton(text="📱 Поділитися моїм номером", request_contact=True)],
        [KeyboardButton(text="⬅️ Назад до адреси")],
        [KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]
    ]
    msg = await message.answer("Повертаємось. Поділіться номером телефону:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.update_data(last_prompt_id=msg.message_id)

@dp.callback_query(F.data == "reg_back_phone")
async def reg_back_phone(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Registration.phone)
    kb = [[KeyboardButton(text="📱 Поділитися моїм номером", request_contact=True)]]
    await callback.message.answer("Повертаємось. Поділіться номером телефону:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await callback.message.delete()
    await callback.answer()

@dp.message(Registration.phone)
async def process_phone_invalid(message: types.Message):
    await message.answer("❌ Будь ласка, скористайтеся кнопкою '📱 Поділитися моїм номером' внизу екрану для верифікації вашого контакту.")

@dp.message(Registration.bio)
async def process_bio(message: types.Message, state: FSMContext):
    is_valid, error_msg = validate_text(message.text, min_words=5, min_len=30)
    if not is_valid:
        await message.answer(error_msg + "\n\n(Розкажіть про ваш досвід детальніше — мінімум 5 слів та 30 символів)")
        return
    await state.update_data(bio=message.text)
    await state.set_state(Registration.discount)
    kb = [
        [KeyboardButton(text="⬅️ Назад до опису")],
        [KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]
    ]
    await message.answer(
        "🎁 Які пільгові умови ви надаєте ветеранам? (напр. 'Перша консультація безкоштовно'):", 
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )

@dp.message(Registration.discount, F.text == "⬅️ Назад до опису")
async def back_to_bio(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
        
    data = await state.get_data()
    last_id = data.get("last_prompt_id")
    if last_id:
        try:
            await bot.delete_message(message.chat.id, last_id)
        except:
            pass
            
    await state.set_state(Registration.bio)
    nav_kb = [[KeyboardButton(text="⬅️ Назад до телефону")], [KeyboardButton(text="🌐 Перейти на Портал", web_app=WebAppInfo(url=f"{PORTAL_URL}?v=24"))]]
    msg = await message.answer("Повертаємось. Опишіть ваш досвід ще раз:", reply_markup=ReplyKeyboardMarkup(keyboard=nav_kb, resize_keyboard=True))
    await state.update_data(last_prompt_id=msg.message_id)

@dp.message(Registration.discount)
async def process_discount(message: types.Message, state: FSMContext):
    is_valid, error_msg = validate_text(message.text, min_words=1, min_len=3)
    if not is_valid:
        await message.answer(error_msg)
        return
    import time
    data = await state.get_data()
    data['discount'] = message.text
    data['status'] = 'pending'
    data['id'] = f"user_{message.from_user.id}_{int(time.time())}"
    data['tg_id'] = message.from_user.id
    data['username'] = message.from_user.username
    
    # Зберігаємо в SQL базу через db_manager
    try:
        db_manager.add_specialist(data)
        logging.info(f"✅ New specialist added to SQL: {data['name']}")
    except Exception as e:
        logging.error(f"SQL Add Error: {e}")
        # Fallback to JSON if SQL fails
        db = await load_db_async()
        db.append(data)
        async with db_lock:
             with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
    
    await state.clear()
    await message.answer("Дякуємо! Ваша заявка надіслана на модерацію. Ми повідомимо вас, коли ваш профіль стане активним.")
    
    # Сповіщення адміну
    if ADMIN_ID:
        kb = [
            [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"approve_{data['id']}")],
            [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_{data['id']}")]
        ]
        await bot.send_message(
            ADMIN_ID, 
            f"🆕 **Нова заявка спеціаліста!**\n\n"
            f"👤 {data['name']}\n"
            f"🗂 Категорія: {data['category']}\n"
            f"📍 {data['address']}\n"
            f"📞 {data['phone']}\n"
            f"🎁 {data['discount']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode="Markdown"
        )

# --- АДМІН-ЛОГІКА ---
@dp.callback_query(F.data.startswith("approve_"))
async def approve_specialist(callback: types.CallbackQuery):
    spec_id = callback.data.replace("approve_", "")
    
    # Оновлюємо статус в SQL
    db_manager.update_specialist_status(spec_id, 'verified')
    
    await callback.message.edit_text(callback.message.text + "\n\n✅ **СХВАЛЕНО** (Очікуємо фото та документи від спеціаліста)")
    
    # Отримуємо ID спеціаліста
    user_id = int(spec_id.replace("user_", "").split("_")[0])
    
    # Налаштовуємо стан для спеціаліста, щоб він міг завантажити фото
    state_spec = dp.fsm.resolve_context(bot, message_thread_id=None, chat_id=user_id, user_id=user_id)
    await state_spec.set_state(Registration.photo)
    await state_spec.update_data(spec_db_id=spec_id)
    
    try:
        await bot.send_message(
            user_id, 
            "🎉 Ваш профіль попередньо схвалено!\n\n"
            "📸 Тепер, будь ласка, надішліть ваше **фото** для профілю на порталі."
        )
    except Exception:
        pass
    await callback.answer()

@dp.message(Registration.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    
    data = await state.get_data()
    spec_id = data.get("spec_db_id", f"user_{message.from_user.id}")
    
    photo_path = f"media/photos/{spec_id}.jpg"
    
    # Переконуємось, що папка для фото існує
    os.makedirs(os.path.dirname(photo_path), exist_ok=True)
    
    await bot.download_file(file_info.file_path, photo_path)
    
    try:
        # Оновлюємо шлях у SQLite базі
        db_manager.update_specialist_documents(spec_id, {
            "photo_path": photo_path
        })
        logging.info(f"✅ Photo path for specialist {spec_id} updated in SQL.")
    except Exception as e:
        logging.error(f"❌ Error updating photo path in SQL: {e}")
    
    await state.set_state(Registration.document)
    await message.answer(
        "✅ Фото збережено!\n\n"
        "📄 Останній крок: надішліть ваш **диплом або ліцензію у форматі PDF** для внутрішньої перевірки."
    )

@dp.message(Registration.document, F.document)
async def process_document(message: types.Message, state: FSMContext):
    if not message.document.file_name.lower().endswith('.pdf'):
        await message.answer("❌ Будь ласка, надішліть файл саме у форматі **PDF**.")
        return
        
    doc = message.document
    file_info = await bot.get_file(doc.file_id)
    
    data = await state.get_data()
    spec_id = data.get("spec_db_id", f"user_{message.from_user.id}")
    
    doc_path = f"media/documents/{spec_id}.pdf"
    
    # Переконуємось, що папка для документів існує
    os.makedirs(os.path.dirname(doc_path), exist_ok=True)
    
    await bot.download_file(file_info.file_path, doc_path)
    
    try:
        # 1. Зчитуємо та шифруємо вміст файлу
        import crypto_utils
        with open(doc_path, "rb") as f:
            file_bytes = f.read()
            
        encrypted_bytes = crypto_utils.encrypt_file(file_bytes)
        enc_doc_path = doc_path + ".enc"
        
        with open(enc_doc_path, "wb") as f:
            f.write(encrypted_bytes)
            
        # Видаляємо оригінальний нешифрований файл з диску
        if os.path.exists(doc_path):
            os.remove(doc_path)
            
        # 2. Оновлюємо інформацію в SQLite базі (це автоматично оновить JSON бекап)
        db_manager.update_specialist_documents(spec_id, {
            "document_path": enc_doc_path,
            "doc_diploma_enc": enc_doc_path,
            "status": "verified"
        })
        logging.info(f"✅ Document for specialist {spec_id} encrypted and saved to SQL.")
    except Exception as e:
        logging.error(f"❌ Error encrypting/saving specialist document: {e}")
        # Якщо виникла помилка, все ж спробуємо оновити статус
        db_manager.update_specialist_status(spec_id, 'verified')
    
    await state.clear()
    await message.answer(
        "🎊 Вітаємо! Всі дані отримано. Ваш профіль тепер повністю активовано та додано на портал.\n\n"
        "Дякуємо за вашу службу та підтримку ветеранів!"
    )
    
    # Також робимо фінальну синхронізацію з GitHub
    import subprocess
    try:
        subprocess.run(
            'Copy-Item -Path "data/specialists.json" -Destination "../../Novy-Shlyakh-Portal-Repo/backend/data/" -Force ; cd "../../Novy-Shlyakh-Portal-Repo" ; git add . ; git commit -m "Final activation: Specialist docs uploaded" ; git push origin main',
            shell=True, check=False, executable="powershell.exe"
        )
    except Exception:
        pass

@dp.callback_query(F.data.startswith("reject_"))
async def reject_specialist(callback: types.CallbackQuery):
    spec_id = callback.data.replace("reject_", "")
    db = await load_db_async()
    
    # Видаляємо з бази
    new_db = [s for s in db if s.get("id") != spec_id]
    await save_db_async(new_db)
    
    await callback.message.edit_text(callback.message.text + "\n\n❌ **ВІДХИЛЕНО** (Заявку видалено)")
    
    # Повідомлення користувачу
    user_id = spec_id.replace("user_", "").split("_")[0]
    try:
        await bot.send_message(user_id, "⚠️ На жаль, ваш профіль не пройшов модерацію. Перевірте правильність заповнення даних та спробуйте ще раз.")
    except Exception:
        pass
    await callback.answer()

# --- ОСОБИСТИЙ КАБІНЕТ СПЕЦІАЛІСТА ---
@dp.message(F.text == "👤 Мій Кабінет")
async def show_cabinet(message: types.Message, user_id=None):
    db = await load_db_async()
    # Якщо user_id не передано (це пряме повідомлення), беремо його з message.from_user.id
    # Якщо передано (це callback), використовуємо переданий ID
    user_id_str = str(user_id if user_id else message.from_user.id)
    
    spec = next((
        s for s in db 
        if str(s.get("tg_id")) == user_id_str or 
        s.get("id", "").startswith(f"user_{user_id_str}")
    ), None)
    
    if not spec:
        await message.answer(f"Ваш профіль не знайдено (ID: {user_id_str}). Спробуйте зареєструватися.")
        return
        
    status_emoji = "✅" if spec.get("status") == "verified" else "⏳"
    status_text = "Верифіковано" if spec.get("status") == "verified" else "На модерації"
    
    text = (
        f"👤 **Ваш Профіль**\n\n"
        f"Статус: {status_emoji} {status_text}\n"
        f"ПІБ: {spec.get('name')}\n"
        f"Категорія: {spec.get('category')}\n"
        f"Адреса: {spec.get('address')}\n"
        f"Телефон: {spec.get('phone')}\n\n"
        "Ви можете оновити дані або видалити профіль."
    )
    
    kb = [
        [InlineKeyboardButton(text="💰 Звітувати про оплату (25%)", callback_data="report_payment")],
        [InlineKeyboardButton(text="📝 Редагувати анкету", callback_data="edit_profile")],
        [InlineKeyboardButton(text="❌ Видалити профіль", callback_data="delete_profile_confirm")]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data == "delete_profile_confirm")
async def delete_profile_confirm(callback: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="✅ Так, видалити", callback_data="delete_profile_final")],
        [InlineKeyboardButton(text="🔙 Скасувати", callback_data="to_cabinet")]
    ]
    await callback.message.edit_text("⚠️ Ви впевнені, що хочете видалити свій профіль? Цю дію неможливо скасувати.", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data == "delete_profile_final")
async def delete_profile_final(callback: types.CallbackQuery):
    db = await load_db_async()
    new_db = [s for s in db if str(s.get("tg_id")) != str(callback.from_user.id)]
    await save_db_async(new_db)
    await callback.message.edit_text("✅ Ваш профіль успішно видалено. Дякуємо за співпрацю!")
    await callback.answer()

@dp.callback_query(F.data == "to_cabinet")
async def to_cabinet(callback: types.CallbackQuery):
    await callback.message.delete()
    await show_cabinet(callback.message, user_id=callback.from_user.id)
    await callback.answer()

@dp.callback_query(F.data == "edit_profile")
async def edit_profile_menu(callback: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="👤 Змінити ПІБ", callback_data="edit_name")],
        [InlineKeyboardButton(text="📍 Змінити адресу", callback_data="edit_address")],
        [InlineKeyboardButton(text="📝 Оновити біо", callback_data="edit_bio")],
        [InlineKeyboardButton(text="🎁 Змінити пільги", callback_data="edit_discount")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="to_cabinet")]
    ]
    await callback.message.edit_text("Оберіть, що ви хочете змінити:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await callback.answer()

@dp.callback_query(F.data.startswith("edit_"))
async def start_edit_field(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.replace("edit_", "")
    await state.update_data(editing_field=field)
    await state.set_state(Registration.edit_value)
    
    # Отримуємо поточне значення з бази
    db = await load_db_async()
    user_id_str = str(callback.from_user.id)
    spec = next((s for s in db if str(s.get("tg_id")) == user_id_str or s.get("id", "").startswith(f"user_{user_id_str}")), {})
    current_value = spec.get(field, "не вказано")
    
    prompts = {
        "name": "Ваше поточне ПІБ",
        "address": "Ваша поточна адреса",
        "bio": "Ваш поточний опис",
        "discount": "Ваші поточні пільги"
    }
    
    field_label = prompts.get(field, "Поточне значення")
    text = f"📝 **{field_label}**: \n`{current_value}`\n\nВведіть нове значення або натисніть 'Скасувати' 👇"
    
    kb = [[InlineKeyboardButton(text="🔙 Скасувати", callback_data="edit_profile")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    await callback.answer()

@dp.message(Registration.edit_value)
async def process_edit_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("editing_field")
    new_value = message.text
    
    # Валідація
    is_valid, error_msg = validate_text(new_value)
    if not is_valid:
        await message.answer(error_msg)
        return
        
    db = await load_db_async()
    user_id_str = str(message.from_user.id)
    for s in db:
        if str(s.get("tg_id")) == user_id_str or s.get("id", "").startswith(f"user_{user_id_str}"):
            s[field] = new_value
            s["status"] = "pending" # Відправляємо на повторну модерацію
            break
    await save_db_async(db)
    
    await state.clear()
    await message.answer("✅ Дані оновлено! Ваша анкета відправлена на повторну модерацію.")
    await show_cabinet(message, user_id=message.from_user.id)
    
    # Сповіщення адміну з кнопками
    spec_id = None
    for s in db:
        if str(s.get("tg_id")) == user_id_str or s.get("id", "").startswith(f"user_{user_id_str}"):
            spec_id = s.get("id")
            break
            
    kb = [
        [InlineKeyboardButton(text="✅ Схвалити зміни", callback_data=f"approve_{spec_id}")],
        [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_{spec_id}")],
        [InlineKeyboardButton(text="💬 Зв'язатися", url=f"tg://user?id={message.from_user.id}")]
    ]
    
    await bot.send_message(
        ADMIN_ID, 
        f"🔔 **Спеціаліст оновив дані!**\n\n"
        f"👤 Фахівець: {message.from_user.full_name}\n"
        f"📝 Поле: `{field}`\n"
        f"🆕 Нове значення: {new_value}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="Markdown"
    )

@dp.message(F.text == "🛡️ Адмін-панель")
async def show_admin_panel(message: types.Message):
    if str(message.from_user.id).strip() != str(ADMIN_ID).strip():
        return
        
    db = await load_db_async()
    total = len(db)
    verified = len([s for s in db if s.get("status") == "verified"])
    pending = len([s for s in db if s.get("status") == "pending"])
    
    # Статистика кліків
    clicks = 0
    try:
        with open("data/stats.json", "r", encoding="utf-8") as f:
            stats = json.load(f)
            clicks = len(stats)
    except Exception:
        pass
        
    text = (
        "📊 **Статистика Порталу**\n\n"
        f"👥 Усього спеціалістів: {total}\n"
        f"✅ Верифіковано: {verified}\n"
        f"⏳ Очікують перевірки: {pending}\n"
        f"📞 Запитів на контакти: {clicks}\n\n"
        "Оберіть дію нижче 👇"
    )
    
    kb = [
        [InlineKeyboardButton(text="📑 База спеціалістів", callback_data="admin_export")],
        [InlineKeyboardButton(text="⏳ Переглянути чергу", callback_data="admin_queue")],
        [InlineKeyboardButton(text="📈 Детальна статистика", callback_data="admin_stats")]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data == "admin_export")
async def admin_export(callback: types.CallbackQuery):
    if str(callback.from_user.id).strip() != str(ADMIN_ID).strip(): return
    
    import pandas as pd
    from aiogram.types import FSInputFile
    
    db = await load_db_async()
    if not db:
        await callback.answer("База порожня!", show_alert=True)
        return
        
    # Створюємо DataFrame та перейменовуємо колонки
    df = pd.DataFrame(db)
    
    # Обираємо та перейменовуємо важливі колонки
    cols_map = {
        "name": "ПІБ",
        "category": "Категорія",
        "address": "Адреса",
        "phone": "Телефон",
        "bio": "Біографія",
        "discount": "Знижки/Пільги",
        "status": "Статус"
    }
    
    df = df[list(cols_map.keys())].rename(columns=cols_map)
    
    # Зберігаємо в Excel
    excel_path = "data/specialists_export.xlsx"
    df.to_excel(excel_path, index=False)
    
    file = FSInputFile(excel_path)
    await callback.message.answer_document(file, caption="Актуальна база спеціалістів (Excel) 📊")
    await callback.answer()

@dp.callback_query(F.data == "admin_queue")
async def admin_queue(callback: types.CallbackQuery):
    if str(callback.from_user.id) != ADMIN_ID: return
    db = await load_db_async()
    pending = [s for s in db if s.get("status") == "pending"]
    
    if not pending:
        await callback.answer("Черга порожня! 🎉", show_alert=True)
        return
        
    await callback.message.answer(f"🔎 Знайдено {len(pending)} нових заявок:")
    for s in pending:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"approve_{s['id']}")],
            [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_{s['id']}")]
        ])
        await callback.message.answer(
            f"👤 {s['name']}\n🎓 {s['category']}\n📍 {s['address']}", 
            reply_markup=markup
        )
    await callback.answer()

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if str(callback.from_user.id).strip() != str(ADMIN_ID).strip(): return
    
    db = await load_db_async()
    
    # 1. Розподіл за категоріями
    cat_counts = {}
    for s in db:
        cat = s.get("category", "інше")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        
    def get_cat_name(cat):
        names = {"legal": "⚖️ Юрист", "psychology": "🧠 Психолог", "rehab": "🦾 Реабілітація", "career": "💼 Кар'єра"}
        return names.get(cat, cat)
        
    cat_text = "\n".join([f"{get_cat_name(c)}: {count}" for c, count in cat_counts.items()])
    
    # 2. Популярність (з логів)
    click_stats = {}
    total_clicks = 0
    try:
        with open("data/stats.json", "r", encoding="utf-8") as f:
            stats = json.load(f)
            total_clicks = len(stats)
            for entry in stats:
                cat = entry.get("category", "інше")
                click_stats[cat] = click_stats.get(cat, 0) + 1
    except Exception:
        pass
        
    popular_text = "Даних про запити поки немає ⏳"
    if click_stats:
        popular_text = "\n".join([f"{get_cat_name(c)}: {count} запитів" for c, count in click_stats.items()])

    text = (
        "📈 **Детальна Аналітика Порталу**\n\n"
        "👥 **Мережа фахівців:**\n"
        f"{cat_text}\n\n"
        "🔥 **Популярність категорій:**\n"
        f"{popular_text}\n\n"
        f"🚀 **Загальна кількість звернень:** {total_clicks}\n\n"
        "Ці дані допоможуть вам планувати розвиток мережі! 🫡"
    )
    
    kb = [[InlineKeyboardButton(text="🔙 Назад до панелі", callback_data="to_admin_panel")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data == "to_admin_panel")
async def to_admin_panel(callback: types.CallbackQuery):
    await callback.message.delete()
    await show_admin_panel(callback.message)
    await callback.answer()

# ЗАПУСК
async def main():
    # Очищуємо системні команди
    await bot.delete_my_commands()
    
    # Скидаємо кнопку меню до стандартної
    await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
    
    await dp.start_polling(bot)

@dp.message(Command("admin"))
async def cmd_admin_direct(message: types.Message):
    await show_admin_panel(message)

@dp.message(Command("cabinet"))
async def cmd_cabinet_direct(message: types.Message):
    await show_cabinet(message)

# --- ЛОГІКА ВІДГУКІВ (Feedback Loop) ---

@dp.message(Command("feedback"))
async def start_feedback(message: types.Message, state: FSMContext):
    """Початок опитування ветерана"""
    await message.answer(
        "🎖 Вітаємо! Нам важливо знати вашу думку про роботу наших спеціалістів.\n"
        "Будь ласка, оберіть фахівця, з яким ви спілкувалися, або введіть його ім'я:"
    )
    await state.set_state(Feedback.waiting_for_spec)

@dp.message(Feedback.waiting_for_spec)
async def process_feedback_spec(message: types.Message, state: FSMContext):
    await state.update_data(spec_name=message.text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐", callback_data="rate_1"),
         InlineKeyboardButton(text="⭐⭐", callback_data="rate_2"),
         InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate_3"),
         InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate_4"),
         InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate_5")]
    ])
    
    await message.answer(
        f"1/3. **Якість допомоги**: Чи була консультація корисною?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(Feedback.rating_quality)

@dp.callback_query(Feedback.rating_quality)
async def process_quality(callback: types.CallbackQuery, state: FSMContext):
    rating = callback.data.split("_")[1]
    await state.update_data(quality=rating)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👍 Добре", callback_data="eth_good"),
         InlineKeyboardButton(text="😐 Нейтрально", callback_data="eth_neut"),
         InlineKeyboardButton(text="👎 Погано", callback_data="eth_bad")]
    ])
    
    await callback.message.edit_text(
        f"2/3. **Відношення та Етика**: Наскільки комфортним було спілкування?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(Feedback.rating_ethics)

@dp.callback_query(Feedback.rating_ethics)
async def process_ethics(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(ethics=callback.data)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Так, все чесно", callback_data="hon_yes"),
         InlineKeyboardButton(text="❌ Ні, умови змінилися", callback_data="hon_no")]
    ])
    
    await callback.message.edit_text(
        f"3/3. **Чесність**: Чи відповідали умови та ціна обіцяним на порталі?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(Feedback.rating_honesty)

@dp.callback_query(Feedback.rating_honesty)
async def process_honesty(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(honesty=callback.data)
    await callback.message.edit_text("Дякуємо за ваш відгук! Ваша оцінка допоможе іншим ветеранам обрати найкращого спеціаліста. 🇺🇦")
    
    data = await state.get_data()
    logging.info(f"FEEDBACK RECEIVED: {data}")
    # Тут логіка збереження відгуку в БД та перерахунку рейтингу
    await state.clear()
# --- ФІНАНСОВА ЗВІТНІСТЬ (25% Внесок) ---

@dp.callback_query(F.data == "report_payment")
async def start_report_payment(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📊 **Звіт про оплату**\n\n"
        "Будь ласка, вкажіть загальну суму, яку ви отримали від клієнта (у гривнях).\n"
        "Система автоматично розрахує 25% внеску на статутну діяльність ГО.",
        parse_mode="Markdown"
    )
    await state.set_state(Financial.reporting_amount)
    await callback.answer()

@dp.message(Financial.reporting_amount)
async def process_payment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        contribution = amount * 0.25
        await state.update_data(amount=amount, contribution=contribution)
        
        text = (
            f"✅ **Розрахунок завершено**\n\n"
            f"Сума оплати: {amount} грн\n"
            f"Внесок ГО (25%): **{contribution:.2f} грн**\n\n"
            f"Будь ласка, перерахуйте внесок за реквізитами ГО:\n"
            f"`IBAN: UA000000000000000000000000` (Приклад)\n\n"
            f"Після оплати надішліть **скріншот квитанції** сюди 👇"
        )
        await message.answer(text, parse_mode="Markdown")
        await state.set_state(Financial.uploading_receipt)
    except ValueError:
        await message.answer("❌ Будь ласка, введіть число (наприклад, 1000).")

@dp.message(Financial.uploading_receipt, F.photo)
async def process_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount")
    contribution = data.get("contribution")
    
    # Зберігаємо квитанцію (логіка аналогічна документам)
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    receipt_path = f"media/receipts/{message.from_user.id}_{int(time.time())}.jpg"
    if not os.path.exists("media/receipts"): os.makedirs("media/receipts")
    await bot.download_file(file_info.file_path, receipt_path)
    
    # Логуємо фінансову операцію
    log_entry = {
        "timestamp": int(time.time()),
        "user_id": message.from_user.id,
        "amount": amount,
        "contribution": contribution,
        "receipt": receipt_path,
        "status": "pending_verification"
    }
    
    finance_path = "data/finance.json"
    try:
        if not os.path.exists("data"): os.makedirs("data")
        if not os.path.exists(finance_path):
            with open(finance_path, "w", encoding="utf-8") as f:
                json.dump([], f)
        
        with open(finance_path, "r+", encoding="utf-8") as f:
            records = json.load(f)
            records.append(log_entry)
            f.seek(0)
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    await message.answer(
        "🙏 **Дякуємо за внесок!**\n\n"
        "Ваша підтримка допомагає нам розвивати портал та допомагати іншим ветеранам.\n"
        "Квитанція надіслана на модерацію. Ваш рейтинг активності буде підвищено! 🚀",
        parse_mode="Markdown"
    )
    await state.clear()


import asyncio

async def schedule_followup(user_id, specialist_name):
    # Mocking a 3-day follow-up with a 10-second delay for testing
    await asyncio.sleep(10)
    try:
        await bot.send_message(
            user_id, 
            f"🤖 Привіт! Минуло 3 дні після вашого метчу зі спеціалістом ({specialist_name}).\n\nЯк ваше самопочуття? Чи вдалося вирішити вашу проблему? Напишіть мені, якщо потрібна додаткова підтримка."
        )
    except Exception as e:
        logging.error(f"Followup failed: {e}")

# ══════════════════════════════════════════
# AI MATCHMAKING — Powered by OpenAI GPT-4o
# ══════════════════════════════════════════

CAT_LABELS = {
    "legal":      "⚖️ Юрист",
    "psychology": "🧠 Психолог",
    "rehab":      "🦾 Реабілітолог",
    "career":     "💼 Кар'єра / Бізнес",
}

async def transcribe_voice(file_path: str) -> str:
    """Транскрибує голосове повідомлення через OpenAI Whisper."""
    try:
        from openai import AsyncOpenAI
        oai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(file_path, "rb") as audio_file:
            result = await oai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="uk"
            )
        return result.text
    except Exception as e:
        logging.error(f"Whisper transcription error: {e}")
        return ""

async def ai_analyze_request(query: str, specialists: list) -> dict:
    """
    Надсилає запит ветерана до GPT-4o.
    Повертає JSON:
    {
        "categories": ["psychology", "legal"],   // відсортовані за релевантністю
        "summary": "Коротко: ветеран має ...",    // що GPT зрозумів
        "matches": [
            {"id": "...", "score": 92, "reason": "..."},
            ...
        ]
    }
    """
    try:
        from openai import AsyncOpenAI
        oai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Формуємо каталог спеціалістів для GPT
        spec_catalog = json.dumps(
            [
                {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "category": s.get("category"),
                    "role": s.get("role", ""),
                    "bio": (s.get("bio") or "")[:200],  # обрізаємо для токен-ефективності
                    "address": s.get("address", ""),
                    "discount": s.get("discount", ""),
                }
                for s in specialists
            ],
            ensure_ascii=False
        )

        system_prompt = (
            "Ти — розумний AI-диспетчер ветеранського порталу 'Новий Шлях' (Черкаси, Україна).\n"
            "Твоя задача: проаналізувати запит ветерана і підібрати 1-2 найкращих спеціалістів із наданого каталогу.\n"
            "Категорії: legal (юридична), psychology (психологічна), rehab (реабілітаційна), career (кар'єра/бізнес).\n"
            "ВАЖЛИВО: відповідай ТІЛЬКИ валідним JSON без markdown-блоків, без пояснень поза JSON.\n"
            "Формат відповіді:\n"
            "{\"summary\": \"Коротко (1 речення) що потрібно ветерану\","
            "\"categories\": [\"назва_категорії\"],"
            "\"matches\": [{\"id\": \"id спеца\", \"score\": 0-100, \"reason\": \"пояснення чому саме він підходить (1-2 речення)\"}]}"
        )

        user_prompt = (
            f"Запит ветерана:\n\"{query}\"\n\n"
            f"Каталог верифікованих спеціалістів:\n{spec_catalog}"
        )

        response = await oai.chat.completions.create(
            model="gpt-4o-mini",  # оптимальний баланс ціна/якість
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=600,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        return json.loads(raw)

    except Exception as e:
        logging.error(f"AI matchmaking error: {e}")
        return {}


@dp.callback_query(F.data == "ai_matchmaking")
async def start_ai_matchmaking(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    kb = [[KeyboardButton(text="❌ Скасувати пошук")]]
    await callback.message.answer(
        "🤖 **Розумний підбір (AI)**\n\n"
        "Опишіть своїми словами, яка допомога вам потрібна.\n\n"
        "_Наприклад:_\n"
        "• «Маю проблеми зі сном і тривогу після служби»\n"
        "• «Потрібно оскаржити статус інваліда у суді»\n"
        "• «Хочу відкрити власний бізнес, не знаю з чого почати»\n\n"
        "Також можна надіслати 🎙️ **голосове повідомлення**.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
    await state.set_state(AIMatchmaking.waiting_for_query)
    await callback.answer()


@dp.message(AIMatchmaking.waiting_for_query, F.text == "❌ Скасувати пошук")
async def cancel_ai_matchmaking(message: types.Message, state: FSMContext):
    await state.clear()
    await cmd_start(message)


@dp.message(AIMatchmaking.waiting_for_query)
async def process_ai_query(message: types.Message, state: FSMContext):
    query_text = ""

    # ── Голосове повідомлення → Whisper ──
    if message.voice:
        processing_msg = await message.answer("🎙️ Розпізнаю голосове повідомлення...")
        try:
            file_info = await bot.get_file(message.voice.file_id)
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
                tmp_path = tmp.name
            await bot.download_file(file_info.file_path, tmp_path)
            query_text = await transcribe_voice(tmp_path)
            os.unlink(tmp_path)

            if not query_text:
                await processing_msg.delete()
                await message.answer(
                    "❌ Не вдалося розпізнати голос. Будь ласка, напишіть текстом."
                )
                return
            await processing_msg.edit_text(f"✅ *Розпізнано:* _{query_text}_", parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Voice download error: {e}")
            await processing_msg.delete()
            await message.answer("❌ Помилка обробки голосу. Напишіть текстом.")
            return
    elif message.text:
        query_text = message.text
    else:
        await message.answer("Будь ласка, надішліть текст або голосове повідомлення.")
        return

    # ── Завантажуємо тільки верифікованих спеціалістів ──
    db = await load_db_async()
    verified_specs = [s for s in db if s.get("status") == "verified"]

    if not verified_specs:
        await message.answer(
            "😔 На жаль, наразі в базі немає верифікованих спеціалістів.\n"
            "Ми активно поповнюємо мережу — спробуйте пізніше!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🎖️ Я Ветеран / Родина")]],
                resize_keyboard=True
            )
        )
        await state.clear()
        return

    # ── GPT-4o аналізує запит ──
    thinking_msg = await message.answer(
        "🧠 *ШІ аналізує ваш запит...*\n"
        "_Це займе кілька секунд_",
        parse_mode="Markdown"
    )

    ai_result = await ai_analyze_request(query_text, verified_specs)

    await thinking_msg.delete()

    if not ai_result or not ai_result.get("matches"):
        # Fallback: показуємо список категорій
        await message.answer(
            "🔍 ШІ не зміг автоматично підібрати — оберіть категорію вручну:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚖️ Юрист",     callback_data="find_legal")],
                [InlineKeyboardButton(text="🧠 Психолог",  callback_data="find_psychology")],
                [InlineKeyboardButton(text="🦾 Реабілітація", callback_data="find_rehab")],
                [InlineKeyboardButton(text="💼 Кар'єра",   callback_data="find_career")],
            ])
        )
        await state.clear()
        return

    summary = ai_result.get("summary", "")
    matches = ai_result.get("matches", [])[:2]  # максимум 2 результати

    # ── Формуємо відповідь ──
    header = (
        "🎯 **Підбір завершено!**\n\n"
        f"📋 *ШІ зрозумів:* {summary}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(header, parse_mode="Markdown")

    # Формуємо словник спеців за ID для швидкого пошуку
    specs_by_id = {str(s.get("id")): s for s in verified_specs}

    for i, match in enumerate(matches, 1):
        spec = specs_by_id.get(str(match.get("id")))
        if not spec:
            continue

        score = match.get("score", 0)
        reason = match.get("reason", "")
        cat_label = CAT_LABELS.get(spec.get("category", ""), "🔷 Спеціаліст")

        # Індикатор відповідності
        bar_filled = int(score / 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)

        card = (
            f"**{i}. {spec.get('name', 'Без імені')}**\n"
            f"{cat_label}\n"
            f"📊 Відповідність: `{bar}` {score}%\n"
            f"📍 {spec.get('address', 'Черкаси')}\n"
            f"🎁 Пільги: {spec.get('discount', 'Уточнюйте')}\n\n"
            f"💡 _{reason}_"
        )

        kb = [[
            InlineKeyboardButton(
                text="📞 Отримати контакти",
                callback_data=f"contact_{spec['id']}"
            )
        ]]
        await message.answer(
            card,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )

    # ── Повертаємо звичайну клавіатуру ──
    nav_kb = [
        [KeyboardButton(text="🔄 Новий пошук")],
        [KeyboardButton(text="⬅️ Повернутися до вибору ролі")],
    ]
    await message.answer(
        "⏱️ *ШІ-протокол турботи активовано:* через 3 дні я запитаю, чи вдалося вирішити питання.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard=nav_kb, resize_keyboard=True)
    )

    # ── Follow-up через 3 дні (259200 сек) ──
    spec_name = specs_by_id.get(str(matches[0].get("id")), {}).get("name", "спеціаліста") if matches else "спеціаліста"
    asyncio.create_task(schedule_followup(message.from_user.id, spec_name))

    await state.clear()


@dp.message(F.text == "🔄 Новий пошук")
async def new_ai_search(message: types.Message, state: FSMContext):
    """Повторний AI-пошук без повернення в головне меню."""
    kb = [[KeyboardButton(text="❌ Скасувати пошук")]]
    await message.answer(
        "🤖 Опишіть нову ситуацію або проблему:",
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
    await state.set_state(AIMatchmaking.waiting_for_query)


# ══════════════════════════════════════════
# ЗАПУСК (має бути в самому кінці файлу!)
# ══════════════════════════════════════════
if __name__ == "__main__":
    asyncio.run(main())
