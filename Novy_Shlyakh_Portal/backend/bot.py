import os
import json
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# Завантаження налаштувань
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = os.getenv("ADMIN_ID", "YOUR_TELEGRAM_ID") # Для модерації

# Налаштування логування
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Шлях до бази даних
DB_PATH = "data/specialists.json"

# СТАНИ FSM (Для реєстрації спеціаліста)
class Registration(StatesGroup):
    name = State()
    category = State()
    address = State()
    phone = State()
    bio = State()
    discount = State()

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
def load_db():
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- ГОРОВНЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [KeyboardButton(text="🎖️ Я Ветеран / Родина")],
        [KeyboardButton(text="💼 Я Спеціаліст (Реєстрація)")]
    ]
    if str(message.from_user.id) == ADMIN_ID:
        kb.append([KeyboardButton(text="🛡️ Адмін-панель")])
        
    reply_markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
        "Вітаємо у координаційному центрі **'Новий Шлях'**!\n\n"
        "Цей бот допоможе вам знайти фахівця або долучитися до нашої мережі підтримки.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# --- ШЛЯХ ВЕТЕРАНА ---
@dp.message(F.text == "🎖️ Я Ветеран / Родина")
async def veteran_menu(message: types.Message):
    kb = [
        [InlineKeyboardButton(text="⚖️ Юрист", callback_data="find_legal")],
        [InlineKeyboardButton(text="🧠 Психолог", callback_data="find_psychology")],
        [InlineKeyboardButton(text="🦾 Реабілітація", callback_data="find_rehab")],
        [InlineKeyboardButton(text="💼 Кар'єра", callback_data="find_career")],
        [InlineKeyboardButton(text="🌐 Перейти на Портал", url="https://novyshlyakh.ua")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer("Яка допомога вам потрібна зараз?", reply_markup=markup)

@dp.callback_query(F.data.startswith("find_"))
async def show_specialists(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    db = load_db()
    # Показуємо тільки верифікованих
    filtered = [s for s in db if s.get("category") == category and s.get("status") == "verified"]
    
    if not filtered:
        await callback.message.answer("Наразі у цій категорії немає верифікованих фахівців у вашому регіоні. Ми працюємо над цим!")
        return

    for spec in filtered:
        text = (
            f"👤 **{spec['name']}**\n"
            f"🎓 {spec['role']}\n"
            f"📍 {spec['address']}\n"
            f"🎁 {spec['discount']}\n\n"
            f"📝 {spec['bio']}"
        )
        kb = [[InlineKeyboardButton(text="📞 Зателефонувати", url=f"tel:{spec['phone']}")]]
        markup = InlineKeyboardMarkup(inline_keyboard=kb)
        await callback.message.answer(text, reply_markup=markup, parse_mode="Markdown")
    
    await callback.answer()

# --- ШЛЯХ СПЕЦІАЛІСТА (FSM) ---
@dp.message(F.text == "💼 Я Спеціаліст (Реєстрація)")
async def spec_reg_start(message: types.Message, state: FSMContext):
    await state.set_state(Registration.name)
    await message.answer("Розпочнемо реєстрацію. Як вас звати? (Введіть ПІБ та посаду)")

@dp.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = [
        [InlineKeyboardButton(text="Юрист", callback_data="cat_legal")],
        [InlineKeyboardButton(text="Психолог", callback_data="cat_psychology")],
        [InlineKeyboardButton(text="Реабілітолог", callback_data="cat_rehab")],
        [InlineKeyboardButton(text="Кар'єра/Бізнес", callback_data="cat_career")]
    ]
    await state.set_state(Registration.category)
    await message.answer("Оберіть вашу категоріy:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.split("_")[1]
    await state.update_data(category=cat)
    await state.set_state(Registration.address)
    await callback.message.answer("Введіть адресу вашого кабінету у Черкасах (або 'Онлайн'):")
    await callback.answer()

@dp.message(Registration.address)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(Registration.phone)
    await message.answer("Введіть ваш контактний номер телефону (у форматі +380...):")

@dp.message(Registration.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(Registration.bio)
    await message.answer("Коротко опишіть ваш досвід роботи з ветеранами:")

@dp.message(Registration.bio)
async def process_bio(message: types.Message, state: FSMContext):
    await state.update_data(bio=message.text)
    await state.set_state(Registration.discount)
    await message.answer("Які пільгові умови ви надаєте ветеранам? (напр. 'Перша консультація безкоштовно'):")

@dp.message(Registration.discount)
async def process_discount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data['discount'] = message.text
    data['status'] = 'pending'
    data['id'] = f"user_{message.from_user.id}"
    
    # Зберігаємо в базу як 'pending'
    db = load_db()
    db.append(data)
    save_db(db)
    
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
    spec_id = callback.data.split("_")[1]
    db = load_db()
    for spec in db:
        if spec.get("id") == spec_id:
            spec["status"] = "verified"
            # Спроба додати координати за замовчуванням (Черкаси центр), якщо їх немає
            if "coordinates" not in spec:
                spec["coordinates"] = [49.4444, 32.0597]
            break
    save_db(db)
    
    await callback.message.edit_text(callback.message.text + "\n\n✅ **СХВАЛЕНО**")
    # Повідомлення користувачу
    user_id = spec_id.split("_")[1]
    try:
        await bot.send_message(user_id, "🎉 Вітаємо! Ваш профіль пройшов модерацію та тепер доступний ветеранам Черкащини.")
    except Exception:
        pass
    await callback.answer()

# ЗАПУСК
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
