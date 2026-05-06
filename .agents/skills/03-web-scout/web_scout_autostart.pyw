"""
Web Scout Autostart — Запускається при вході в Windows.
Логіка: чекає 15 хв → перевіряє, чи вже сканував сьогодні → якщо ні, запускає scan з Telegram-нотифікацією.
Файл .pyw = без чорного вікна консолі у фоні.
"""
import subprocess
import sys
import time
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
import os

# Завантажуємо змінні середовища
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SCOUT_DIR = Path(__file__).parent / "scout_cache"
FLAG_FILE = SCOUT_DIR / "last_scan_date.txt"
DISCOVERY_FLAG = SCOUT_DIR / "last_discovery_date.txt"
SCRIPT = Path(__file__).parent / "web_scout_tool_talan.py"

SCOUT_DIR.mkdir(parents=True, exist_ok=True)

def already_ran_today(flag_path: Path) -> bool:
    """Перевіряє, чи дія вже була сьогодні."""
    if flag_path.exists():
        last_date = flag_path.read_text(encoding="utf-8").strip()
        return last_date == str(date.today())
    return False

def mark_done(flag_path: Path):
    """Записує сьогоднішню дату як прапорець."""
    flag_path.write_text(str(date.today()), encoding="utf-8")

if __name__ == "__main__":
    # Якщо вже сканував сьогодні — виходимо тихо
    if already_ran_today(FLAG_FILE):
        sys.exit(0)

    # Чекаємо 15 хвилин (900 секунд), щоб інтернет встиг підключитися
    time.sleep(900)

    # Перевіряємо ще раз
    if already_ran_today(FLAG_FILE):
        sys.exit(0)

    # ЛОГІКА DISCOVERY: Щопонеділка шукаємо нові сайти через LLM
    is_monday = date.today().weekday() == 0
    if is_monday and not already_ran_today(DISCOVERY_FLAG):
        discovery_query = "найкращі офіційні джерела грантів 2026 для ветеранів, реабілітації ПТСР та соціального підприємництва в Україні"
        try:
            subprocess.run(
                [sys.executable, str(SCRIPT), "discover", "--query", discovery_query],
                cwd=str(PROJECT_ROOT),
                timeout=120
            )
            mark_done(DISCOVERY_FLAG)
        except Exception:
            pass

    # Збираємо аргументи для запуску SCAN
    token = os.environ.get("GRANT_SEEKER_BOT_TOKEN", "")
    chat = os.environ.get("GRANT_SEEKER_CHAT_ID", "")

    cmd = [sys.executable, str(SCRIPT), "scan", "--notify"]
    if token:
        cmd += ["--token", token]
    if chat:
        cmd += ["--chat", chat]

    # Запускаємо сканування
    try:
        subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            timeout=300
        )
        mark_done(FLAG_FILE)
    except Exception:
        pass
