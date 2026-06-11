"""
talan/bot/handlers/knowledge.py
Команди роботи з Knowledge Base: аудіо, квіз, флешкартки, записати, блокнот, kb.
"""

import logging

from telebot.types import Message

from talan.bot.config import bot, KB_PATH, PROTOCOL_PATH
from talan.bot.handlers.admin import guard, safe_send
from talan.bot.services.cache import ask_ai_oneshot
from talan.bot.services.tts import generate_audio_summary
from talan.autobot.kb_manager import NotebookManager

log = logging.getLogger("Bot.Knowledge")

kb_manager = NotebookManager(kb_path=KB_PATH, protocol_path=PROTOCOL_PATH)


def find_kb_file(keyword: str) -> list:
    return kb_manager.find_file(keyword)


def read_kb_file(path, max_chars: int = 6000) -> str:
    return kb_manager.read_file(path, max_chars)


# ── /аудіо ────────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["audio", "аудіо"])
@guard
def handle_audio(msg: Message) -> None:
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        safe_send(msg.chat.id,
            "ℹ️ Використання: `/аудіо <ключове слово>`\nНаприклад: `/аудіо Ашрам`")
        return

    keyword = args[1].strip()
    matches = find_kb_file(keyword)
    if not matches:
        safe_send(msg.chat.id,
            f"❌ Не знайдено документів за запитом «{keyword}». "
            "Спробуй /базазнань для перегляду доступних.")
        return

    target = matches[0]
    safe_send(msg.chat.id,
        f"🔊 Генерую аудіо-підсумок для: `{target.stem}`\n⏳ ~30 секунд...")

    content = read_kb_file(target, max_chars=8000)
    audio   = generate_audio_summary(content)

    if audio:
        bot.send_voice(msg.chat.id, audio, caption=f"🔊 Підсумок: {target.stem}")
        log.info(f"TTS sent: {target.name}")
    else:
        safe_send(msg.chat.id, "❌ Не вдалося згенерувати аудіо. Перевір квоту OpenAI.")


# ── /квіз ─────────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["quiz", "квіз"])
@guard
def handle_quiz(msg: Message) -> None:
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        safe_send(msg.chat.id,
            "ℹ️ Використання: `/квіз <ключове слово>`\nНаприклад: `/квіз безпека`")
        return

    keyword = args[1].strip()
    matches = find_kb_file(keyword)
    if not matches:
        safe_send(msg.chat.id, f"❌ Не знайдено документів за запитом «{keyword}».")
        return

    target = matches[0]
    safe_send(msg.chat.id, f"🧠 Генерую квіз по документу: `{target.stem}`...")

    content = read_kb_file(target, max_chars=8000)
    quiz = ask_ai_oneshot(
        "Ти — викладач. Створи квіз з 5 питань з 4 варіантами відповідей (A, B, C, D) "
        "на основі наданого тексту. Формат:\n\n"
        "❓ 1. [питання]\n   A) ...\n   B) ...\n   C) ...\n   D) ...\n"
        "✅ Відповідь: [літера]\n\n"
        "Відповідай українською. Питання різного рівня складності.",
        f"Документ «{target.stem}»:\n\n{content}",
        temperature=0.8,
        use_cache=True,
    )
    if quiz:
        safe_send(msg.chat.id, f"🧠 **Квіз: {target.stem}**\n\n{quiz}")
    else:
        safe_send(msg.chat.id, "❌ Не вдалося згенерувати квіз.")


# ── /флешкартки ───────────────────────────────────────────────────────────────

@bot.message_handler(commands=["flash", "флешкартки"])
@guard
def handle_flashcards(msg: Message) -> None:
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        safe_send(msg.chat.id,
            "ℹ️ Використання: `/флешкартки <ключове слово>`\nНаприклад: `/флешкартки ДСТУ`")
        return

    keyword = args[1].strip()
    matches = find_kb_file(keyword)
    if not matches:
        safe_send(msg.chat.id, f"❌ Не знайдено документів за запитом «{keyword}».")
        return

    target = matches[0]
    safe_send(msg.chat.id, f"📇 Генерую флешкартки по документу: `{target.stem}`...")

    content = read_kb_file(target, max_chars=8000)
    cards = ask_ai_oneshot(
        "Ти — викладач. Створи 10 флешкарток (питання-відповідь) на основі тексту. "
        "Формат кожної картки:\n\n"
        "📌 **Картка 1**\n❓ [питання]\n💡 [коротка відповідь]\n\n"
        "Відповідай українською.",
        f"Документ «{target.stem}»:\n\n{content}",
        temperature=0.7,
        use_cache=True,
    )
    if cards:
        safe_send(msg.chat.id, f"📇 **Флешкартки: {target.stem}**\n\n{cards}")
    else:
        safe_send(msg.chat.id, "❌ Не вдалося згенерувати флешкартки.")


# ── /пошук ────────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["search", "пошук"])
@guard
def handle_search(msg: Message) -> None:
    from talan.bot.services.tts import web_search  # lazy — уникаємо кола з tts

    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        safe_send(msg.chat.id,
            "ℹ️ Використання: `/пошук <запит>`\nНаприклад: `/пошук гранти для NGO 2026`")
        return

    query = args[1].strip()
    safe_send(msg.chat.id, f"🔍 Шукаю в інтернеті: «{query}»...")
    result = web_search(query)
    safe_send(msg.chat.id, f"🔍 **Результати пошуку:**\n\n{result[:3500]}")


# ── /записати ─────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["save", "записати"])
@guard
def handle_save(msg: Message) -> None:
    args = msg.text.split(maxsplit=1)
    if len(args) < 2 or "|" not in args[1]:
        safe_send(msg.chat.id,
            "ℹ️ Використання: `/записати <категорія> | <текст>`\n"
            "Наприклад: `/записати Ашрам | Зустріч з волонтерами підтвердила потребу у 3 локаціях`")
        return

    parts    = args[1].split("|", 1)
    category = parts[0].strip()
    raw_text = parts[1].strip()

    # Форматуємо запис через AI (виправлено: ask_gpt_oneshot → ask_ai_oneshot)
    formatted = ask_ai_oneshot(
        "Ти — редактор. Очисти та відформатуй наступний текст як структурований запис "
        "для бази знань NGO. Додай маркери та чітку структуру. Не додавай вигаданої інформації. "
        "Відповідай українською.",
        raw_text,
    ) or raw_text

    result = kb_manager.save_note(category, raw_text, formatted)
    if result.get("created_new_category"):
        log.info(f"Нова категорія KB: {result['cat_dir_name']}")

    safe_send(msg.chat.id,
        f"✅ Записано у базу знань!\n"
        f"📂 Категорія: `{result['cat_dir_name']}`\n"
        f"📄 Файл: `{result['file_name']}`")
    log.info(f"KB Save: {result['cat_dir_name']}/{result['file_name']} ({len(raw_text)} chars)")


# ── /блокнот ──────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["notebook", "блокнот"])
@guard
def handle_notebook(msg: Message) -> None:
    from talan.bot.config import PROJECT_PATH  # lazy

    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        safe_send(msg.chat.id,
            "ℹ️ Використання: `/блокнот <назва теми>`\n"
            "Наприклад: `/блокнот Партнерство з Червоним Хрестом`")
        return

    topic = args[1].strip()
    safe_send(msg.chat.id, f"📒 Створюю блокнот: «{topic}»...")

    structure = ask_ai_oneshot(
        "Ти — менеджер-проєктів NGO. Створи шаблон блокноту для нової теми. "
        "Формат markdown. Включи розділи: Мета, Контекст, Ключові факти, "
        "Контакти, Наступні кроки, Нотатки. Заповни заголовки, тіло залиш порожнім з підказками. "
        "Відповідай українською.",
        f"Тема блокноту: {topic}",
        temperature=0.6,
    )

    result = kb_manager.create_notebook(topic, structure, PROJECT_PATH)
    safe_send(msg.chat.id, result["message"])
    log.info(f"Notebook created: {result['path']}")


# ── /базазнань ────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["kb", "базазнань"])
@guard
def handle_kb_list(msg: Message) -> None:
    tree_text = kb_manager.get_kb_tree()
    safe_send(msg.chat.id, tree_text)
