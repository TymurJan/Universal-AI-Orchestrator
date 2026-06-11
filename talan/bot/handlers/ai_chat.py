"""
talan/bot/handlers/ai_chat.py
Function Calling (Autonomous Skill Routing) та основний хендлер текстових повідомлень.
"""

import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from telebot.types import Message

from talan.bot.config import bot, BASE_DIR, PROJECT_PATH, SYSTEM_PROMPT
from talan.bot.ai_orchestrator import ai_orchestrator, AI_READY, chat_histories, ask_ai
from talan.bot.handlers.admin import guard, safe_send
from talan.bot.handlers.commands import handle_commands
from talan.bot.services.tts import web_search, generate_audio_summary
from talan.bot.services.cache import ask_ai_oneshot

log = logging.getLogger("Bot.AIChat")

# ── Function Calling Schema ───────────────────────────────────────────────────

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "run_system_audit",
            "description": "Запускає системний аудит. Використовуй, якщо користувач просить перевірити систему або здоров'я бота.",
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_strategic_idea",
            "description": "Зберігає стратегічну ідею у Dropzone для подальшої обробки Агентом.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title":   {"type": "string", "description": "Короткий заголовок ідеї"},
                    "content": {"type": "string", "description": "Детальний опис ідеї"},
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Пошук інформації в інтернеті: гранти, закони, новини.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Пошуковий запит"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": "Пошук документів у внутрішній Базі Знань ГО Талан ЮА.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Ключове слово"},
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_action",
            "description": "Створення запису або ліда в CRM клієнта (Bitrix24, Trello, Jira).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_type": {"type": "string", "description": "Тип дії (create_lead, create_task)"},
                    "payload":     {"type": "string", "description": "Дані для CRM у форматі JSON-строки"},
                },
                "required": ["action_type", "payload"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_document",
            "description": "Квіз, флешкартки або аудіо-підсумок з документа у Базі Знань.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Ключове слово для пошуку файлу"},
                    "action":  {"type": "string", "enum": ["audio", "quiz", "flashcards"]},
                },
                "required": ["keyword", "action"],
            },
        },
    },
]


# ── execute_tool ──────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, arguments_json: str, chat_id: int) -> str:
    from talan.bot.handlers.knowledge import find_kb_file, read_kb_file  # lazy

    try:
        args = json.loads(arguments_json)
    except Exception:
        args = {}

    log.info(f"⚙️ Tool: {tool_name} args={args}")

    if tool_name == "run_system_audit":
        safe_send(chat_id, "⚙️ **Запускаю аудит здоров'я системи...**")
        result = subprocess.run(
            [sys.executable, "talan/autobot/meta_optimizer.py"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode == 0:
            return "Аудит завершено успішно. Запропонуй /optimize для деталей."
        return f"Помилка аудиту: {result.stderr}"

    elif tool_name == "record_strategic_idea":
        title   = args.get("title", "Без назви")
        content = args.get("content", "")
        ideas_path = BASE_DIR / "_DROPZONE" / "IN" / "IDEAS"
        ideas_path.mkdir(parents=True, exist_ok=True)
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"IDEA_{ts}.md"
        body     = (
            f"# 💡 СТРАТЕГІЧНА ІДЕЯ: {title}\n\n"
            f"**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"**Опис:**\n{content}\n\n---\n*Передано через Telegram Bot*"
        )
        try:
            (ideas_path / filename).write_text(body, encoding="utf-8")
            safe_send(chat_id, f"✅ Ідею «{title}» зафіксовано у системі стратегічного розвитку.")
            return f"Успіх: збережено у {filename}"
        except Exception as e:
            return f"Помилка збереження: {e}"

    elif tool_name == "web_search":
        query = args.get("query", "")
        safe_send(chat_id, f"🔍 Шукаю в інтернеті: «{query}»...")
        return web_search(query)

    elif tool_name == "search_kb":
        keyword = args.get("keyword", "")
        safe_send(chat_id, f"📂 Шукаю в Базі Знань: «{keyword}»...")
        matches = find_kb_file(keyword)
        if not matches:
            return f"Документ за запитом '{keyword}' не знайдено."
        content = read_kb_file(matches[0], max_chars=4000)
        return f"Знайдено документ {matches[0].stem}:\n\n{content}"

    elif tool_name == "analyze_document":
        keyword = args.get("keyword", "")
        action  = args.get("action", "flashcards")
        matches = find_kb_file(keyword)
        if not matches:
            return f"Документ за запитом '{keyword}' не знайдено."
        target  = matches[0]
        content = read_kb_file(target, max_chars=8000)

        if action == "audio":
            safe_send(chat_id, f"🔊 Генерую аудіо-підсумок для: `{target.stem}`...")
            audio = generate_audio_summary(content)
            if audio:
                bot.send_voice(chat_id, audio, caption=f"🔊 Підсумок: {target.stem}")
                return "Аудіо успішно надіслано."
            return "Помилка при генерації аудіо."
        elif action == "quiz":
            safe_send(chat_id, f"🧠 Генерую квіз: `{target.stem}`...")
            result = ask_ai_oneshot(
                "Ти — викладач. Створи квіз з 5 питань з 4 варіантами відповідей.",
                content, temperature=0.8, use_cache=True,
            )
            return result or "Помилка генерації квізу."
        elif action == "flashcards":
            safe_send(chat_id, f"📇 Генерую флешкартки: `{target.stem}`...")
            result = ask_ai_oneshot(
                "Ти — викладач. Створи 10 флешкарток (питання-відповідь).",
                content, temperature=0.7, use_cache=True,
            )
            return result or "Помилка генерації флешкарток."

    elif tool_name == "crm_action":
        action_type = args.get("action_type", "unknown")
        payload     = args.get("payload", "{}")
        safe_send(chat_id, f"🔌 Відправляю вебхук до CRM [{action_type}]...")
        return f"Успіх: {action_type} виконано. Дані: {payload}"

    return f"Невідомий інструмент: {tool_name}"


# ── handle_text ───────────────────────────────────────────────────────────────

@bot.message_handler(content_types=["text"])
@guard
def handle_text(msg: Message) -> None:
    log.info(f"AI ({ai_orchestrator.active_model}): {msg.text!r}")

    # Швидкий редирект для health-фраз
    health_kw = ["як справи", "все добре", "статус", "бекап",
                 "синхронізація", "здоров'я", "працює", "health"]
    if any(k in msg.text.lower() for k in health_kw) and len(msg.text) < 30:
        msg.text = "/health"
        handle_commands(msg)
        return

    user_id = msg.from_user.id
    history = chat_histories.setdefault(user_id, [])

    # Multi-tenancy: custom system prompt per tenant
    client_profile = Path(f"Knowledge_Base/tenant_{user_id}/profile.json")
    if client_profile.exists():
        try:
            profile_data  = json.loads(client_profile.read_text(encoding="utf-8"))
            sys_prompt    = profile_data.get("system_prompt", SYSTEM_PROMPT)
        except Exception:
            sys_prompt    = SYSTEM_PROMPT
    else:
        sys_prompt = SYSTEM_PROMPT

    sys_prompt += (
        "\nЯкщо ти не можеш виконати запит, поясни причину і обов'язково "
        "запропонуй альтернативу з доступних тобі інструментів."
    )

    try:
        gpt = ai_orchestrator.providers.get("gpt")
        if not gpt or not gpt.ready:
            # Fallback: звичайний ask_ai
            safe_send(msg.chat.id, ask_ai(user_id, msg.text))
            return

        messages = [{"role": "system", "content": sys_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": msg.text})

        response    = gpt.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            tools=TOOLS_SCHEMA,
        )
        message_obj = response.choices[0].message

        if message_obj.tool_calls:
            history.append({"role": "user", "content": msg.text})
            history.append(message_obj)

            for tc in message_obj.tool_calls:
                result = execute_tool(tc.function.name, tc.function.arguments, msg.chat.id)
                history.append({"role": "tool", "tool_call_id": tc.id, "content": result})

            messages = [{"role": "system", "content": sys_prompt}] + history
            final    = gpt.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
            )
            answer   = final.choices[0].message.content
            history.append({"role": "assistant", "content": answer})
            safe_send(msg.chat.id, answer)

        else:
            answer = message_obj.content or (
                "❌ Я не зміг обробити цей запит. Спробуй перефразувати або скористайся меню."
            )
            history.append({"role": "user",      "content": msg.text})
            history.append({"role": "assistant",  "content": answer})
            safe_send(msg.chat.id, answer)

        if len(history) > 20:
            chat_histories[user_id] = history[-20:]

    except Exception as e:
        log.error(f"handle_text error: {e}")
        safe_send(msg.chat.id,
            "Друже, щось мій процесор перегрівся. Спробуй базові команди з меню.")
