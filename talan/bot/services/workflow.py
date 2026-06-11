"""
talan/bot/services/workflow.py
Навігаційний двигун: читає .md workflow-файли, парсить кнопки,
відправляє повідомлення через бота та веде стек навігації.
"""

import re
import logging
from pathlib import Path

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from talan.bot.config import bot, BASE_DIR

log = logging.getLogger("Bot.Workflow")

# {chat_id: ["workflow1", "workflow2", ...]}
user_workflow_stack: dict[int, list[str]] = {}


def run_workflow(chat_id: int, workflow_name: str, push_to_stack: bool = True) -> bool:
    """
    Читає .md файл з .agents/workflows/, парсить кнопки та відправляє повідомлення.
    Повертає True при успіху, False якщо файл не знайдено.
    """
    workflow_path: Path = BASE_DIR / ".agents" / "workflows" / f"{workflow_name}.md"
    if not workflow_path.exists():
        log.error(f"Workflow file not found: {workflow_path}")
        return False

    content = workflow_path.read_text(encoding="utf-8")

    # Основний текст (після YAML-фронтматтеру)
    body = re.split(r"---", content)[-1].strip()

    # Кнопки — рядки зі слешем
    options = re.findall(r"-\s*(`?(/[\w_]+)`?)\s*[—\-]?\s*(.*)", body)

    markup = InlineKeyboardMarkup()
    for _raw, cmd, label in options:
        btn_text = f"{label} ({cmd})" if label else cmd
        markup.add(InlineKeyboardButton(text=btn_text, callback_data=f"wf_cmd_{cmd[1:]}"))

    if workflow_name != "menu":
        markup.row(
            InlineKeyboardButton(text="⏪ Назад (/back)", callback_data="wf_back"),
            InlineKeyboardButton(text="🏠 Головна (/home)", callback_data="wf_home"),
        )

    if push_to_stack:
        stack = user_workflow_stack.setdefault(chat_id, [])
        if not stack or stack[-1] != workflow_name:
            stack.append(workflow_name)

    try:
        bot.send_message(chat_id, body, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"Workflow Markdown error ({e}), retrying without parse_mode.")
        bot.send_message(chat_id, body, reply_markup=markup, parse_mode=None)

    return True
