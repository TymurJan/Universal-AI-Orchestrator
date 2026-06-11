"""
talan/bot/handlers/commands.py
Основні команди бота: start, status, vault, codeblack, model, reload,
grant_scan, grant_status, meta, optimize, fulfill та навігація (menu/home/back).
"""

import os
import sys
import json
import time
import hashlib
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from telebot.types import Message

from talan.bot.config import bot, BASE_DIR, PROJECT_PATH, FILE_MAP, reload_config
from talan.bot.ai_orchestrator import ai_orchestrator
from talan.bot.handlers.admin import guard, safe_send
from talan.bot.services.workflow import run_workflow, user_workflow_stack
from talan.autobot.backup_manager import sync_env_to_external

log = logging.getLogger("Bot.Commands")


# ── Головна диспетчерська команда ─────────────────────────────────────────────

@bot.message_handler(commands=[
    "start", "старт", "myid", "айді", "status", "статус",
    "read", "читати", "vault", "сховище", "codeblack", "кодчорний",
    "reload", "health", "menu", "onboarding", "back", "home",
    "grant_scan", "grant_status", "model",
])
@guard
def handle_commands(msg: Message) -> None:
    log.info(f"Command: {msg.text!r} from {msg.from_user.id}")
    text = msg.text.lower()

    # ── health / status ────────────────────────────────────────────────────────
    if "health" in text or ("status" in text and "grant" not in text) or "статус" in text:
        _handle_health(msg)
        return

    # ── reload ────────────────────────────────────────────────────────────────
    if "reload" in text:
        reload_config()
        sync_env_to_external()
        safe_send(msg.chat.id, "✅ Конфігурацію оновлено та синхронізовано на Диск E!")
        return

    # ── навігація ─────────────────────────────────────────────────────────────
    if any(x in text for x in ["start", "старт", "onboarding"]):
        run_workflow(msg.chat.id, "onboarding")
    elif "menu" in text:
        run_workflow(msg.chat.id, "menu")
    elif "home" in text:
        user_workflow_stack[msg.chat.id] = []
        run_workflow(msg.chat.id, "menu")
    elif "back" in text:
        stack = user_workflow_stack.get(msg.chat.id, [])
        if len(stack) > 1:
            stack.pop()
            prev = stack.pop()
            run_workflow(msg.chat.id, prev)
        else:
            safe_send(msg.chat.id, "⏪ Ви вже на самому початку.")
            run_workflow(msg.chat.id, "menu")

    # ── myid ──────────────────────────────────────────────────────────────────
    elif any(x in text for x in ["myid", "айді"]):
        safe_send(msg.chat.id, f"Твій ID: `{msg.from_user.id}`")

    # ── vault ─────────────────────────────────────────────────────────────────
    elif any(x in text for x in ["vault", "сховище"]):
        path = FILE_MAP["vault"]
        if path.exists():
            safe_send(msg.chat.id,
                f"📦 **Входимо у Сховище (Vault).** Ось індекс документів:\n\n"
                f"{path.read_text(encoding='utf-8')[:3000]}")
        else:
            safe_send(msg.chat.id, "❌ Індекс сховища не знайдено.")

    # ── codeblack ─────────────────────────────────────────────────────────────
    elif any(x in text for x in ["codeblack", "кодчорний"]):
        safe_send(msg.chat.id,
            "⚠️ **АКТИВОВАНО КОД ЧОРНИЙ!** Не панікуй. "
            "Дотримуйся інструкцій з Фази 3. Всі порти та доступи будуть обмежені.")

    # ── grant_scan ────────────────────────────────────────────────────────────
    elif "grant_scan" in text:
        safe_send(msg.chat.id,
            "🔎 **Запускаю розвідувальний дрон Web Scout..**\n"
            "Я перевірю всі джерела на наявність нових грантів.")
        try:
            scout = PROJECT_PATH / ".agents" / "skills" / "03-web-scout" / "web_scout_tool_talan.py"
            subprocess.Popen([sys.executable, str(scout), "scan", "--notify"])
        except Exception as e:
            safe_send(msg.chat.id, f"❌ Помилка запуску розвідника: {e}")

    # ── grant_status ──────────────────────────────────────────────────────────
    elif "grant_status" in text:
        config_path = (PROJECT_PATH / ".agents" / "skills" / "03-web-scout"
                       / "scout_cache" / "watchlist.json")
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding="utf-8"))
            resp = f"🛡 **Стан моніторингу грантів:**\n\nМоніториться джерел: `{len(data)}`\n"
            for item in data[:5]:
                resp += f"└ {item['name']}: `{item.get('last_scan', 'ніколи')[:16]}`\n"
            safe_send(msg.chat.id, resp)
        else:
            safe_send(msg.chat.id, "ℹ️ Список моніторингу порожній.")

    # ── model ─────────────────────────────────────────────────────────────────
    elif "model" in text:
        args = msg.text.split()
        if len(args) < 2:
            cur = ai_orchestrator.active_model
            safe_send(msg.chat.id,
                f"🤖 **Поточна модель:** `{cur.upper()}`\n\n"
                "Щоб змінити:\n`/model gpt` — GPT-4o-mini\n`/model claude` — Claude 3.5 Sonnet\n`/model gemini` — Gemini 1.5 Flash")
            return
        target = args[1].lower()
        if ai_orchestrator.switch_model(target):
            safe_send(msg.chat.id, f"✅ **Модель змінено на {target.upper()}!**")
        else:
            safe_send(msg.chat.id, f"❌ Не вдалося активувати `{target}`. Перевір ключі або назву.")


# ── /meta ─────────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["meta"])
@guard
def handle_meta(msg: Message) -> None:
    safe_send(msg.chat.id,
        "🔍 **Запускаю аудит здоров'я системи..**\n"
        "Це займе до 10 секунд.")
    try:
        result = subprocess.run(
            [sys.executable, "talan/autobot/meta_optimizer.py"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode == 0:
            rec_dir = BASE_DIR / ".agents" / "recommendations"
            files   = sorted(rec_dir.glob("orchestrator_proposal_*.json"), key=os.path.getmtime)
            if files:
                data = json.loads(files[-1].read_text(encoding="utf-8"))
                resp = "🧠 **Результати аудиту Оркестратора:**\n\n"
                for item in data:
                    icon  = "🔴" if item.get("severity") == "high" else "🟡"
                    resp += f"{icon} **{item['topic'].upper()}**\n└ {item['recommendation']}\n\n"
                resp += "💡 Використай /optimize для плану виправлення."
                safe_send(msg.chat.id, resp)
            else:
                safe_send(msg.chat.id, "✅ **Аудит завершено.** Конфліктів не виявлено.")
        else:
            log.error(f"Meta-Optimizer Error: {result.stderr}")
            safe_send(msg.chat.id, "❌ Помилка під час запуску аудиту. Деталі у логах.")
    except Exception as e:
        log.error(f"handle_meta error: {e}")
        safe_send(msg.chat.id, f"❌ Неочікувана помилка: {e}")


# ── /optimize ─────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["optimize"])
@guard
def handle_optimize(msg: Message) -> None:
    rec_dir = BASE_DIR / ".agents" / "recommendations"
    files   = sorted(rec_dir.glob("orchestrator_proposal_*.json"), key=os.path.getmtime)
    if not files:
        safe_send(msg.chat.id,
            "ℹ️ Немає нових пропозицій. Запусти /meta для свіжого аудиту.")
        return

    data = json.loads(files[-1].read_text(encoding="utf-8"))
    resp = "🚀 **План оптимізації:**\n\n"
    for i, item in enumerate(data, 1):
        resp += f"{i}. **{item['topic']}**:\n"
        resp += f"   - {item['recommendation']}\n"
        resp += f"   - ДОЦІЛЬНІСТЬ: Економія ресурсів + стабільність.\n\n"
    resp += "🤔 **Впровадити зміни?** Напишіть: 'Так, впроваджуй [назву теми, наприклад: architecture]'"
    safe_send(msg.chat.id, resp)


# ── /fulfill ─────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["fulfill"])
def handle_fulfill(msg: Message) -> None:
    from talan.bot.config import ALLOWED_IDS
    if msg.from_user.id not in ALLOWED_IDS:
        return

    try:
        parts = msg.text.split()
        if len(parts) < 3:
            safe_send(msg.chat.id, "📌 Використання: `/fulfill <email> <audit|core|ent>`")
            return

        email = parts[1]
        tier  = parts[2].upper()
        salt  = "TALAN_SECURE_2026"
        raw   = f"{email}|{tier}|{salt}|{int(time.time())}"
        key   = f"{tier}-{hashlib.sha256(raw.encode()).hexdigest()[:12].upper()}"

        licenses_file = BASE_DIR / "active_licenses.json"
        data = {}
        if licenses_file.exists():
            data = json.loads(licenses_file.read_text(encoding="utf-8"))
        data[key] = {"email": email, "tier": tier, "issued_at": str(datetime.now())}
        licenses_file.write_text(json.dumps(data, indent=4), encoding="utf-8")

        safe_send(msg.chat.id,
            f"✅ **Система: Оплата Підтверджена!**\n\n"
            f"📦 **Продукт:** Universal AI Orchestrator ({tier})\n"
            f"🔑 **Ваш Ключ:** `{key}`\n\n"
            f"📥 **Скачати:** [Universal-AI-Orchestrator-v1.1.zip]"
            f"(https://github.com/TymurJan/Universal-AI-Orchestrator/releases/latest)\n\n"
            f"⚠️ *Ключ прив'язується до ПК при першому запуску.*")
        log.info(f"🎁 Ліцензія {key} видана для {email}")

    except Exception as e:
        log.error(f"handle_fulfill error: {e}")
        safe_send(msg.chat.id, "❌ Помилка при генерації ліцензії.")


# ── Допоміжна: health ─────────────────────────────────────────────────────────

def _handle_health(msg: Message) -> None:
    status_file = BASE_DIR / "logs" / "status.json"
    if not status_file.exists():
        safe_send(msg.chat.id,
            "📊 **Статус систем:**\nЛоги ще не сформовані. Запустіть перший бекап.")
        return
    try:
        data = json.loads(status_file.read_text(encoding="utf-8"))
        resp = "📊 **Аудит стабільності систем:**\n\n"
        for proc, info in data.items():
            icon = "✅" if info["status"] == "success" else "❌"
            name = proc.upper().replace("_", " ")
            resp += f"{icon} **{name}**\n└ Останній запуск: `{info['last_run']}`\n"
            if info["status"] != "success":
                resp += f"└ Помилка: `{info['details']}`\n"
            resp += "\n"
        resp += "🤖 **BOT CORE**\n└ Статус: `ONLINE`\n└ Uptime: `Active`"
        safe_send(msg.chat.id, resp)
    except Exception as e:
        safe_send(msg.chat.id, f"❌ Помилка читання статусів: {e}")
