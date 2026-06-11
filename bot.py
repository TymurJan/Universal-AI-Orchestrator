"""
bot.py — Точка входу Антігравіті V5.0
Реєструє всі модулі та запускає infinity_polling.
"""

import sys
import traceback
import time
from pathlib import Path

# ── Додаємо корінь проекту до sys.path ──────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ── Ядро: конфіг та об'єкт бота ─────────────────────────────────────────────
from talan.bot.config import bot, log

# ── Сервіси (side-effects при імпорті не потрібні) ───────────────────────────
import talan.bot.services.workflow   # noqa: F401
import talan.bot.services.cache      # noqa: F401
import talan.bot.services.tts        # noqa: F401

# ── Хендлери (реєстрація через @bot.message_handler) ─────────────────────────
import talan.bot.handlers.admin      # noqa: F401  ← callbacks wf_*
import talan.bot.handlers.commands   # noqa: F401  ← /start, /status, /meta …
import talan.bot.handlers.knowledge  # noqa: F401  ← /quiz, /audio, /save …
import talan.bot.handlers.media      # noqa: F401  ← photo / document
import talan.bot.handlers.study      # noqa: F401  ← study / quiz
import talan.bot.handlers.ai_chat    # noqa: F401  ← text (повинен бути останнім!)

# ── Фонові потоки ─────────────────────────────────────────────────────────────
from talan.bot.services.scheduler import (
    check_single_instance,
    start_background_threads,
)
from talan.autobot.backup_manager import sync_env_to_external


def main() -> None:
    check_single_instance()
    log.info("🚀 Антігравіті V5.0 (Knowledge Base V2) ЗАПУСК..")

    sync_env_to_external()
    start_background_threads()

    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=20)
        except KeyboardInterrupt:
            log.info("Зупинка бота за запитом користувача.")
            break
        except Exception as e:
            log.error(f"Критична помилка пулінгу: {e}")
            log.error(traceback.format_exc())
            log.info("Перезапуск через 5 секунд..")
            time.sleep(5)


if __name__ == "__main__":
    main()
