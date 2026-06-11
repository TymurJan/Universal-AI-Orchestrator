"""
talan/bot/handlers/admin.py
Утиліти безпеки (guard, safe_send) та хендлер Inline Keyboard callbacks
(wf_home / wf_back / wf_cmd_*).
"""

import logging
from functools import wraps

from telebot.types import Message, CallbackQuery

from talan.bot.config import bot, ALLOWED_IDS
from talan.bot.services.workflow import run_workflow, user_workflow_stack

log = logging.getLogger("Bot.Admin")


# ── Безпека ───────────────────────────────────────────────────────────────────

def is_allowed(user_id: int) -> bool:
    return not ALLOWED_IDS or user_id in ALLOWED_IDS


def guard(fn):
    """Декоратор: перевіряє, чи користувач є у білому списку."""
    @wraps(fn)
    def wrapper(msg: Message):
        if not is_allowed(msg.from_user.id):
            bot.reply_to(msg, f"⛔ Доступ заборонено (ID: {msg.from_user.id})")
            return
        return fn(msg)
    return wrapper


def safe_send(chat_id: int, text: str) -> None:
    """Відправляє повідомлення з Markdown; fallback на plain text при помилці."""
    try:
        bot.send_message(chat_id, text, parse_mode="Markdown")
    except Exception:
        bot.send_message(chat_id, text, parse_mode=None)


# ── Workflow callbacks ────────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda call: call.data.startswith("wf_"))
def handle_workflow_callbacks(call: CallbackQuery) -> None:
    chat_id = call.message.chat.id
    data    = call.data

    if data == "wf_home":
        user_workflow_stack[chat_id] = []
        run_workflow(chat_id, "menu")

    elif data == "wf_back":
        stack = user_workflow_stack.get(chat_id, [])
        if len(stack) > 1:
            stack.pop()
            prev = stack.pop()
            run_workflow(chat_id, prev)
        else:
            run_workflow(chat_id, "menu")

    elif data.startswith("wf_cmd_"):
        # Емулюємо текстову команду
        from talan.bot.handlers.commands import handle_commands  # lazy — уникаємо кола
        cmd_name = data.replace("wf_cmd_", "")
        call.message.text = f"/{cmd_name}"
        handle_commands(call.message)

    bot.answer_callback_query(call.id)
