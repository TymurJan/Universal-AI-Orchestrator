"""
talan/bot/handlers/study.py
Хендлер навчального курсу Talan Academy: теорія, інтерактивні квізи та прогрес.
"""

import os
import json
import logging
from pathlib import Path
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from talan.bot.config import bot, BASE_DIR
from talan.bot.handlers.admin import guard, safe_send, is_allowed

log = logging.getLogger("Bot.Study")

ACADEMY_DIR = BASE_DIR / "Talan_Academy"
PROGRESS_FILE = ACADEMY_DIR / "progress.json"

# Активні сесії тестування: {user_id: {"lesson_id": str, "question_idx": int, "score": int, "questions": list}}
active_quizzes = {}


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            log.error(f"Error reading progress file: {e}")
    return {}


def save_progress(progress: dict) -> None:
    ACADEMY_DIR.mkdir(parents=True, exist_ok=True)
    try:
        PROGRESS_FILE.write_text(json.dumps(progress, indent=4, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log.error(f"Error saving progress file: {e}")


def get_user_progress(user_id: int) -> dict:
    progress = load_progress()
    user_str = str(user_id)
    if user_str not in progress:
        progress[user_str] = {
            "current_module": 1,
            "current_lesson": 1,
            "completed_lessons": [],
            "scores": {}
        }
        save_progress(progress)
    return progress[user_str]


def update_user_progress(user_id: int, current_module: int, current_lesson: int, completed_lesson: str = None, score: int = None) -> None:
    progress = load_progress()
    user_str = str(user_id)
    if user_str not in progress:
        progress[user_str] = {
            "current_module": 1,
            "current_lesson": 1,
            "completed_lessons": [],
            "scores": {}
        }
    
    progress[user_str]["current_module"] = current_module
    progress[user_str]["current_lesson"] = current_lesson
    
    if completed_lesson:
        if completed_lesson not in progress[user_str]["completed_lessons"]:
            progress[user_str]["completed_lessons"].append(completed_lesson)
            
    if completed_lesson and score is not None:
        progress[user_str]["scores"][completed_lesson] = score
        
    save_progress(progress)


# ── Команди ───────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["study", "навчання"])
@guard
def handle_study(msg: Message) -> None:
    user_id = msg.from_user.id
    user_progress = get_user_progress(user_id)
    
    current_lesson = user_progress.get("current_lesson", 1)
    
    # Зчитуємо файл уроку динамічно за префіксом номера уроку
    lessons_dir = ACADEMY_DIR / "lessons"
    lesson_file = None
    if lessons_dir.exists():
        for f in lessons_dir.iterdir():
            if f.is_file() and f.name.startswith(f"lesson_{current_lesson}_") and f.name.endswith(".md"):
                lesson_file = f
                break

    if not lesson_file or not lesson_file.exists():
        safe_send(msg.chat.id, "📚 **Вітаємо у Talan Academy!**\n\nВи пройшли всі доступні уроки. Нові матеріали з'являться згодом.")
        return
        
    try:
        content = lesson_file.read_text(encoding="utf-8")
    except Exception as e:
        safe_send(msg.chat.id, f"❌ Помилка завантаження уроку: {e}")
        return
        
    # Відправляємо теорію уроку
    safe_send(msg.chat.id, content)
    
    # Додаємо кнопки взаємодії
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📝 Пройти квіз", callback_data=f"study_quiz_start_{current_lesson}"),
        InlineKeyboardButton("📊 Мій прогрес", callback_data="study_progress_status")
    )
    bot.send_message(msg.chat.id, "📖 **Дії для поточного уроку:**", reply_markup=markup)


@bot.message_handler(commands=["study_status", "прогрес"])
@guard
def handle_study_status(msg: Message) -> None:
    _send_progress_status(msg.chat.id, msg.from_user.id)


def _send_progress_status(chat_id: int, user_id: int) -> None:
    user_progress = get_user_progress(user_id)
    completed = user_progress.get("completed_lessons", [])
    scores = user_progress.get("scores", {})
    
    status_text = (
        "📊 **Talan Academy — Мій прогрес:**\n\n"
        f"👤 Учень: `ID {user_id}`\n"
        f"📂 Поточний модуль: `{user_progress.get('current_module', 1)}`\n"
        f"📖 Наступний урок: `{user_progress.get('current_lesson', 1)}`\n\n"
        "📜 **Пройдені уроки:**\n"
    )
    
    if not completed:
        status_text += "└ *Ви ще не завершили жодного уроку.*\n"
    else:
        for idx, lesson in enumerate(completed, 1):
            score = scores.get(lesson, "—")
            status_text += f"{idx}. Урок `{lesson}` (Оцінка: `{score}%`)\n"
            
    safe_send(chat_id, status_text)


# ── Обробка Callbacks ─────────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda call: call.data.startswith("study_"))
def handle_study_callbacks(call: CallbackQuery) -> None:
    user_id = call.from_user.id
    if not is_allowed(user_id):
        bot.answer_callback_query(call.id, "⛔ Доступ заборонено", show_alert=True)
        return
        
    chat_id = call.message.chat.id
    data = call.data
    
    if data == "study_progress_status":
        bot.answer_callback_query(call.id)
        _send_progress_status(chat_id, user_id)
        
    elif data.startswith("study_quiz_start_"):
        lesson_id_str = data.replace("study_quiz_start_", "")
        bot.answer_callback_query(call.id)
        _start_quiz(chat_id, user_id, lesson_id_str)
        
    elif data.startswith("study_quiz_ans_"):
        # Формат: study_quiz_ans_{ans_idx}_{q_idx}
        parts = data.split("_")
        ans_idx = int(parts[3])
        q_idx = int(parts[4])
        bot.answer_callback_query(call.id)
        
        # Видаляємо кнопки, щоб користувач не міг клікнути повторно
        try:
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        except Exception:
            pass
            
        _process_quiz_answer(chat_id, user_id, q_idx, ans_idx)


def _start_quiz(chat_id: int, user_id: int, lesson_id_str: str) -> None:
    # Динамічний пошук файлу тесту за префіксом номера уроку
    quizzes_dir = ACADEMY_DIR / "quizzes"
    quiz_file = None
    if quizzes_dir.exists():
        for f in quizzes_dir.iterdir():
            if f.is_file() and f.name.startswith(f"quiz_{lesson_id_str}_") and f.name.endswith(".json"):
                quiz_file = f
                break

    if not quiz_file or not quiz_file.exists():
        safe_send(chat_id, f"❌ Файл тесту для уроку {lesson_id_str} не знайдено.")
        return
        
    try:
        questions = json.loads(quiz_file.read_text(encoding="utf-8"))
    except Exception as e:
        safe_send(chat_id, f"❌ Помилка завантаження тесту: {e}")
        return
        
    active_quizzes[user_id] = {
        "lesson_id": lesson_id_str,
        "question_idx": 0,
        "score": 0,
        "questions": questions
    }
    
    safe_send(chat_id, f"📝 **Починаємо тест до Уроку {lesson_id_str}!**\nВсього питань: `{len(questions)}`..")
    _send_next_quiz_question(chat_id, user_id)


def _send_next_quiz_question(chat_id: int, user_id: int) -> None:
    session = active_quizzes.get(user_id)
    if not session:
        return
        
    q_idx = session["question_idx"]
    questions = session["questions"]
    
    if q_idx >= len(questions):
        _finish_quiz(chat_id, user_id)
        return
        
    q = questions[q_idx]
    text = f"❓ **Питання {q_idx + 1}/{len(questions)}:**\n\n{q['question']}"
    
    markup = InlineKeyboardMarkup()
    for idx, opt in enumerate(q["options"]):
        markup.row(InlineKeyboardButton(opt, callback_data=f"study_quiz_ans_{idx}_{q_idx}"))
        
    bot.send_message(chat_id, text, reply_markup=markup)


def _process_quiz_answer(chat_id: int, user_id: int, q_idx: int, ans_idx: int) -> None:
    session = active_quizzes.get(user_id)
    if not session:
        return
        
    if q_idx != session["question_idx"]:
        return
        
    questions = session["questions"]
    q = questions[q_idx]
    
    correct_idx = q["answer_idx"]
    if ans_idx == correct_idx:
        session["score"] += 1
        bot.send_message(chat_id, "✅ **Правильно!**")
    else:
        correct_text = q["options"][correct_idx]
        bot.send_message(chat_id, f"❌ **Неправильно.**\nПравильна відповідь: *{correct_text}*")
        
    session["question_idx"] += 1
    _send_next_quiz_question(chat_id, user_id)


def _finish_quiz(chat_id: int, user_id: int) -> None:
    session = active_quizzes.pop(user_id, None)
    if not session:
        return
        
    score = session["score"]
    total = len(session["questions"])
    percentage = int((score / total) * 100)
    lesson_id = session["lesson_id"]
    
    text = (
        f"🏁 **Тест завершено!**\n\n"
        f"Правильних відповідей: `{score}/{total}` (`{percentage}%`)\n"
    )
    
    if percentage >= 75:
        text += "🎉 **Вітаємо! Тест успішно складено.** Урок розблоковано та зараховано!"
        completed_key = f"lesson_{lesson_id}"
        
        # Оскільки уроків поки тільки 1, залишаємо lesson=1, але завершеним.
        update_user_progress(user_id, current_module=1, current_lesson=1, completed_lesson=completed_key, score=percentage)
    else:
        text += "😢 **Тест не складено (мінімум 75%).** Спробуйте ще раз, ввівши команду `/study`."
        
    safe_send(chat_id, text)
