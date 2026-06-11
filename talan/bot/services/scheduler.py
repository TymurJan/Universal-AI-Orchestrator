"""
talan/bot/services/scheduler.py
Фонові потоки: singleton-перевірка, env-вочер, планувальник задач.
"""

import os
import sys
import time
import json
import logging
import subprocess
import threading
from datetime import datetime
from pathlib import Path

import psutil

from talan.bot.config import BASE_DIR, PROJECT_PATH
from talan.autobot.backup_manager import sync_env_to_external

log = logging.getLogger("Bot.Scheduler")


def check_single_instance() -> None:
    """Перевіряє, чи не запущений вже інший екземпляр бота через PID-файл."""
    pid_file  = BASE_DIR / "bot.pid"
    current   = os.getpid()

    if pid_file.exists():
        try:
            old_pid = int(pid_file.read_text().strip())
            if psutil.pid_exists(old_pid):
                proc = psutil.Process(old_pid)
                if "python" in proc.name().lower():
                    log.warning(f"⚠️ Вже запущено екземпляр бота (PID: {old_pid}). Вихід.")
                    sys.exit(0)
        except Exception as e:
            log.error(f"Помилка перевірки PID: {e}")

    pid_file.write_text(str(current))
    log.info(f"📍 PID зафіксовано: {current}")


def env_watcher() -> None:
    """
    Фоновий потік: моніторить зміни у .env та миттєво синхронізує їх на Диск E.
    Перевірка кожні 5 секунд.
    """
    env_file   = BASE_DIR / ".env"
    last_mtime = env_file.stat().st_mtime if env_file.exists() else 0
    log.info("👀 Моніторинг змін .env активовано.")

    while True:
        try:
            if env_file.exists():
                mtime = env_file.stat().st_mtime
                if mtime > last_mtime:
                    log.info("📝 Зміну в .env виявлено. Синхронізація на Диск Е.")
                    sync_env_to_external()
                    last_mtime = mtime
        except Exception as e:
            log.error(f"env_watcher error: {e}")
        time.sleep(5)


def run_scheduler() -> None:
    """
    Фоновий планувальник:
    - KB-синхронізація кожні 4 години о 5-й хвилині
    - Розвідка грантів щодня о 09:00
    Перевірка кожні 30 секунд.
    """
    log.info("⏳ Фоновий планувальник запущено.")

    while True:
        try:
            now = datetime.now()

            # KB-синхронізація (кожні 4 год о :05)
            if now.hour % 4 == 0 and now.minute == 5:
                log.info(f"⏰ Планова синхронізація KB ({now.hour}:05).")
                subprocess.run([sys.executable, "talan/autobot/kb_sync.py"])
                time.sleep(60)

            # Ранкова розвідка грантів о 09:00
            if now.hour == 9 and now.minute == 0:
                log.info("⏰ Ранкова розвідка грантів (09:00).")
                scout = PROJECT_PATH / ".agents" / "skills" / "03-web-scout" / "web_scout_tool_talan.py"
                subprocess.Popen([sys.executable, str(scout), "scan", "--notify"])
                time.sleep(60)

        except Exception as e:
            log.error(f"❌ Помилка планувальника: {e}")

        time.sleep(30)


def run_watchdog() -> None:
    """
    Фоновий потік: періодично запускає мета-оптимізатор та перевіряє status.json.
    Надсилає сповіщення адміністраторам при виявленні помилок.
    Запуск при старті, а потім кожні 12 годин.
    """
    log.info("🛡️ Watchdog-моніторинг активовано.")
    from talan.bot.config import bot, ALLOWED_IDS
    
    first_run = True
    while True:
        try:
            # Чекаємо 30 секунд при першому запуску, щоб бот встиг повністю піднятися
            if first_run:
                time.sleep(30)
                first_run = False
            else:
                time.sleep(12 * 3600)  # Кожні 12 годин
            
            log.info("🛡️ Watchdog: Запуск планової перевірки здоров'я.")
            
            # 1. Запуск мета-оптимізатора
            subprocess.run([sys.executable, "talan/autobot/meta_optimizer.py"])
            
            # 2. Аналіз пропозицій
            rec_dir = BASE_DIR / ".agents" / "recommendations"
            proposals = sorted(rec_dir.glob("orchestrator_proposal_*.json"), key=os.path.getmtime)
            
            issues = []
            if proposals:
                try:
                    data = json.loads(proposals[-1].read_text(encoding="utf-8"))
                    for item in data:
                        if item.get("severity") == "high":
                            issues.append(f"⚠️ [Conflict Guard] {item['topic']}: {item['recommendation']}")
                except Exception as ex:
                    log.error(f"Watchdog error reading proposals: {ex}")
            
            # 3. Аналіз status.json
            status_file = BASE_DIR / "logs" / "status.json"
            if status_file.exists():
                try:
                    status_data = json.loads(status_file.read_text(encoding="utf-8"))
                    for service, info in status_data.items():
                        if info.get("status") == "error":
                            issues.append(f"❌ [Service Status] {service.upper()} error: {info.get('details')}")
                except Exception as ex:
                    log.error(f"Watchdog error reading status: {ex}")
            
            # 4. Надсилання сповіщень
            if issues and ALLOWED_IDS:
                msg = "🚨 <b>Watchdog Alert: Виявлено проблеми зі стабільністю!</b>\n\n"
                
                def escape_html(text: str) -> str:
                    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
                escaped_issues = [escape_html(issue) for issue in issues]
                msg += "\n".join(escaped_issues)
                msg += "\n\n💡 Використай команду /status або /meta для детального аудиту."
                
                for admin_id in ALLOWED_IDS:
                    try:
                        bot.send_message(admin_id, msg, parse_mode="HTML")
                        log.info(f"📨 Watchdog Alert надіслано адміністратору {admin_id}")
                    except Exception as ex:
                        log.error(f"Failed to send watchdog alert to {admin_id}: {ex}")
            else:
                log.info("✅ Watchdog: Системи стабільні. Проблем не виявлено.")
                
        except Exception as e:
            log.error(f"Watchdog main loop error: {e}")


def start_background_threads() -> None:
    """Запускає всі фонові потоки."""
    threading.Thread(target=run_scheduler, daemon=True, name="Scheduler").start()
    threading.Thread(target=env_watcher,   daemon=True, name="EnvWatcher").start()
    threading.Thread(target=run_watchdog,  daemon=True, name="Watchdog").start()
    log.info("🧵 Фонові потоки запущено (з Watchdog).")
