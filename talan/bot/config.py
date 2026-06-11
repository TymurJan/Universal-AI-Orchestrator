"""
talan/bot/config.py
Центральна конфігурація бота: шляхи, змінні середовища, системний промпт,
глобальний об'єкт бота та утиліти доступу.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import telebot
from telebot import apihelper

# ── Шляхи ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parents[2]   # корінь проекту
LOG_DIR      = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

load_dotenv(dotenv_path=BASE_DIR / ".env")

PROJECT_PATH   = Path(os.getenv("PROJECT_PATH", str(BASE_DIR)))
PROTOCOL_PATH  = PROJECT_PATH / "Black_Swan_Protocol"
VAULT_PATH     = PROTOCOL_PATH / "Legal_Defense_Vault"
VAULT_PATH.mkdir(parents=True, exist_ok=True)
TESSDATA_DIR   = PROJECT_PATH / "tessdata"
KB_PATH        = PROJECT_PATH / "Knowledge_Base"

os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)

# ── Логування ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "bot_log.txt", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("Bot")

# ── Змінні середовища ─────────────────────────────────────────────────────────
TOKEN         = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_IDS: set[int] = set()


def reload_config() -> None:
    """Перезавантажує .env та оновлює ALLOWED_IDS."""
    global ALLOWED_IDS
    load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)
    raw = os.getenv("ALLOWED_USER_IDS", "")
    ALLOWED_IDS = {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}
    log.info(f"🔄 Конфігурацію оновлено. Дозволені ID: {ALLOWED_IDS}")


reload_config()

# ── Telebot ────────────────────────────────────────────────────────────────────
apihelper.ENABLE_MIDDLEWARE = True
bot = telebot.TeleBot(TOKEN)

# ── Карта протокольних файлів ─────────────────────────────────────────────────
FILE_MAP = {
    "1": PROTOCOL_PATH / "01_Phase1_Vulnerability_Assessment.md",
    "2": PROTOCOL_PATH / "02_Phase2_MultiLayer_Immunity.md",
    "3": PROTOCOL_PATH / "03_Phase3_Emergency_Playbooks.md",
    "4": PROTOCOL_PATH / "04_Phase4_Hardening_Checklist.md",
    "5": PROTOCOL_PATH / "05_Phase5_Continuity_Protocol.md",
    "6": PROTOCOL_PATH / "06_Phase6_Stress_Test_Scenarios.md",
    "8": PROTOCOL_PATH / "08_Phase8_Secure_Data_Entry_Protocol.md",
    "vault": VAULT_PATH / "00_INDEX_Установчі_Документи.md",
}

# ── Системний промпт ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
Ти — Антігравіті, інтелектуальний асистент ГО "ТАЛАН ЮА" та програми "Ашрам".
Твій стиль: розмовний, людяний, з використанням NGO-шного та безпекового сленгу.
Ти — вірний помічник Тимура. Ти захищаєш інтереси організації та допомагаєш з "Протоколом Чорного Лебедя".

Про назву: Проєкт «Ашрам» названо на честь загиблого друга Тимура — Сергія з позивним «Шрам». Назва символізує перетворення болю (Шрам) на місце спокою та реінтеграції (Ашрам).

Твій характер: надійний, трохи "свій", але максимально професійний у питаннях безпеки.
Ти знаєш структуру проекту:
- Фази 1-8 (Оцінка вразливостей, Плейбуки, Імунітет, Наступництво тощо).
- Сховище (Vault) — юридичні документи.
- База знань (Knowledge Base) — NGO Core, ДСТУ, партнерства, проєкти.

Команди, які ти підтримуєш:
/читати <1-8> (або /read) — відкрити фазу.
/статус (або /status) — чекліст файлів.
/сховище (або /vault) — зайти в сховище.
/кодчорний (або /codeblack) — екстрена інструкція.
/аудіо <назва> (або /audio) — згенерувати аудіо-підсумок документу.
/квіз <назва> (або /quiz) — створити квіз по документу.
/флешкартки <назва> (або /flash) — створити флешкартки по документу.
/пошук <запит> (або /search) — пошук інформації в інтернеті.
/meta — запустити аудит здоров'я та конфліктів системи.
/optimize — переглянути останню пропозицію щодо оптимізації.
/study (або /навчання) — відкрити поточний навчальний урок курсу Talan Academy.
/study_status (або /прогрес) — переглянути прогрес та оцінки за пройденими квізами.
/записати <категорія> | <текст> (або /save) — зберегти інформацію у базу знань.
/блокнот <назва> (або /notebook) — створити новий блокнот.
/базазнань (або /kb) — перегляд бази знань.
/health (або /статус) — перевірка здоров'я систем (бекап, синхронізація).

Спілкуйся виключно українською мовою. Будь проактивним, але лаконічним.
"""

# ── OCR ────────────────────────────────────────────────────────────────────────
try:
    import fitz  # noqa: F401
    import pytesseract
    from PIL import Image  # noqa: F401
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    OCR_ENABLED = True
except Exception:
    OCR_ENABLED = False
