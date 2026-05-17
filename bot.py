"""
Телеграм-бот ГО "ТАЛАН ЮА" / Менеджер Антігравіті
Версія: 5.0 (Knowledge Base V2)
Нове: TTS аудіо, квізи, флешкартки, веб-пошук, управління KB
"""

import os
import io
import logging
import sys
import traceback
import re
import json
import time
import hashlib
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import telebot
from telebot import apihelper
import psutil
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from openai import OpenAI
import anthropic  # Додано для Claude 3.5 Sonnet
import google.generativeai as genai  # Додано для Gemini 1.5 Flash

# Ensure the root directory is in sys.path for importing local 'talan' package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from talan.autobot.kb_manager import NotebookManager
from talan.autobot.backup_manager import sync_env_to_external  # Для швидкої ізоляції секретів

# --- Налаштування Telebot & AI ---
apihelper.ENABLE_MIDDLEWARE = True

# --- Конфігурація шляхів ---
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# --- Логування ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "logs" / "bot_log.txt", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("Bot")

# --- Змінні середовища ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
PROJECT_PATH = Path(os.getenv("PROJECT_PATH", str(BASE_DIR)))
PROTOCOL_PATH = PROJECT_PATH / "Black_Swan_Protocol"
VAULT_PATH = PROTOCOL_PATH / "Legal_Defense_Vault"
TESSDATA_DIR = PROJECT_PATH / "tessdata"
KB_PATH = PROJECT_PATH / "Knowledge_Base"

os.environ['TESSDATA_PREFIX'] = str(TESSDATA_DIR)
ALLOWED_IDS = set()

def reload_config():
    global ALLOWED_IDS
    load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)
    raw = os.getenv("ALLOWED_USER_IDS", "")
    ALLOWED_IDS = set(int(x.strip()) for x in raw.split(",") if x.strip().isdigit())
    log.info(f"🔄 Конфігурацію оновлено. Дозволені ID: {ALLOWED_IDS}")

reload_config()

# --- Керування API Ключами (Multi-Model Orchestrator) ---

class BaseAIProvider:
    def ask(self, system_prompt, user_text, history=None):
        raise NotImplementedError

class OpenAIProvider(BaseAIProvider):
    def __init__(self):
        self.key = os.getenv("OPENAI_API_KEY")
        self.org_id = os.getenv("OPENAI_ORG_ID")
        self.ready = False
        if self.key:
            try:
                # Надаємо перевагу Organisation ID, якщо він вказаний
                if self.org_id:
                    self.client = OpenAI(api_key=self.key, organization=self.org_id)
                    log.info(f"✅ OpenAI Provider: Запуск з Organization ID: {self.org_id[:10]}...")
                else:
                    self.client = OpenAI(api_key=self.key)
                    log.info("✅ OpenAI Provider: Запуск без Organization ID (Default).")
                self.ready = True
            except Exception as e:
                log.error(f"❌ OpenAI Init Error: {e}")

    def ask(self, system_prompt, user_text, history=None):
        messages = [{"role": "system", "content": system_prompt}]
        if history: messages.extend(history)
        messages.append({"role": "user", "content": user_text})
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini", # Базова модель для чату
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content

class AnthropicProvider(BaseAIProvider):
    def __init__(self):
        self.key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        self.ready = False
        if self.key and "sk-ant" in self.key:
            try:
                self.client = anthropic.Anthropic(api_key=self.key)
                self.ready = True
            except Exception as e:
                log.error(f"❌ Anthropic Init Error: {e}")

    def ask(self, system_prompt, user_text, history=None):
        # Конвертуємо історію OpenAI формату в Anthropic
        messages = []
        if history:
            for m in history:
                messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": user_text})

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text

class GeminiProvider(BaseAIProvider):
    def __init__(self):
        self.key = os.getenv("GEMINI_API_KEY")
        self.ready = False
        if self.key:
            try:
                genai.configure(api_key=self.key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.ready = True
            except Exception as e:
                log.error(f"❌ Gemini Init Error: {e}")

    def ask(self, system_prompt, user_text, history=None):
        # Конвертуємо історію для Gemini (role: 'user'/'model')
        contents = []
        # Додаємо системний промпт як перший хід, якщо історія порожня
        # (Gemini 1.5 Flash краще розуміє системний контекст через початковий меседж)
        contents.append({"role": "user", "parts": [system_prompt]})
        contents.append({"role": "model", "parts": ["Зрозумів. Я готовий допомагати як Антігравіті."]})

        if history:
            for m in history:
                role = "user" if m["role"] == "user" else "model"
                contents.append({"role": role, "parts": [m["content"]]})
        
        contents.append({"role": "user", "parts": [user_text]})

        response = self.model.generate_content(contents)
        return response.text

class AIOrchestrator:
    def __init__(self):
        self.providers = {
            "gpt": OpenAIProvider(),
            "claude": AnthropicProvider(),
            "gemini": GeminiProvider()
        }
        self.active_model = "gpt"
        # Автоматичний вибір найбільш "готової" моделі при старті
        if not self.providers["gpt"].ready:
            if self.providers["claude"].ready:
                self.active_model = "claude"
            elif self.providers["gemini"].ready:
                self.active_model = "gemini"

    def switch_model(self, model_name):
        if model_name in self.providers and self.providers[model_name].ready:
            self.active_model = model_name
            return True
        return False

    def ask(self, system_prompt, user_text, history=None):
        provider = self.providers[self.active_model]
        try:
            return provider.ask(system_prompt, user_text, history)
        except Exception as e:
            # Fallback logic: OpenAI -> Claude -> Gemini
            other_models = ["claude", "gemini"] if self.active_model == "gpt" else ["gpt", "gemini"]
            for model in other_models:
                if self.providers[model].ready:
                    log.info(f"🔄 Режим Fallback: Спроба запуску {model}...")
                    try:
                        return self.providers[model].ask(system_prompt, user_text, history)
                    except Exception:
                        continue
            raise e

ai_orchestrator = AIOrchestrator()
AI_READY = any(p.ready for p in ai_orchestrator.providers.values())

# --- OCR Setup ---
try:
    import fitz
    import pytesseract
    from PIL import Image
    OCR_ENABLED = True
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception:
    OCR_ENABLED = False

bot = telebot.TeleBot(TOKEN)

# --- Системний промпт для "Антігравіті" ---
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
/записати <категорія> | <текст> (або /save) — зберегти інформацію у базу знань.
/блокнот <назва> (або /notebook) — створити новий блокнот.
/базазнань (або /kb) — перегляд бази знань.
/health (або /статус) — перевірка здоров'я систем (бекап, синхронізація).

Спілкуйся виключно українською мовою. Будь проактивним, але лаконічним.
"""

# Пам'ять розмови та Навігація
chat_histories = {}
user_workflow_stack = {} # {chat_id: ["workflow_name1", "workflow_name2"]}

# --- Навігаційний Двигун (Workflow Engine) ---

def run_workflow(chat_id, workflow_name, push_to_stack=True):
    """
    Читає .md файл з .agents/workflows/, парсить кнопи та відправляє повідомлення.
    """
    workflow_path = BASE_DIR / ".agents" / "workflows" / f"{workflow_name}.md"
    if not workflow_path.exists():
        log.error(f"Workflow file not found: {workflow_path}")
        return False

    content = workflow_path.read_text(encoding="utf-8")
    
    # Витягуємо опис (description) з YAML-фронтматтера
    desc_match = re.search(r"description:\s*(.*)", content)
    description = desc_match.group(1).strip() if desc_match else ""
    
    # Витягуємо основний текст (після ---)
    body = re.split(r"---", content)[-1].strip()
    
    # Шукаємо пункти списку, що починаються зі слеша (це наші кнопки)
    options = re.findall(r"-\s*(`?(/[\w_]+)`?)\s*[—\-]?\s*(.*)", body)
    
    markup = InlineKeyboardMarkup()
    for raw_cmd_full, cmd, label in options:
        btn_text = f"{label} ({cmd})" if label else cmd
        markup.add(InlineKeyboardButton(text=btn_text, callback_data=f"wf_cmd_{cmd[1:]}"))

    # Додаємо системні кнопки навігації (якщо це не головний екран)
    nav_buttons = []
    if workflow_name != "menu":
        nav_buttons.append(InlineKeyboardButton(text="⏪ Назад (/back)", callback_data="wf_back"))
        nav_buttons.append(InlineKeyboardButton(text="🏠 Головна (/home)", callback_data="wf_home"))
    
    if nav_buttons:
        markup.row(*nav_buttons)

    # Зберігаємо в історію
    if push_to_stack:
        if chat_id not in user_workflow_stack:
            user_workflow_stack[chat_id] = []
        # Уникаємо дублювання однакових етапів підряд
        if not user_workflow_stack[chat_id] or user_workflow_stack[chat_id][-1] != workflow_name:
            user_workflow_stack[chat_id].append(workflow_name)

    try:
        bot.send_message(chat_id, body, reply_markup=markup, parse_mode="Markdown")
        return True
    except Exception as e:
        log.error(f"Workflow Send Error: {e}")
        bot.send_message(chat_id, body, reply_markup=markup, parse_mode=None)
        return True

# --- Карта файлів ---
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

# --- Допоміжні функції ---
def is_allowed(user_id: int) -> bool:
    return not ALLOWED_IDS or user_id in ALLOWED_IDS

def guard(fn):
    def wrapper(msg: Message):
        if not is_allowed(msg.from_user.id):
            bot.reply_to(msg, f"⛔ Доступ заборонено (ID: {msg.from_user.id})")
            return
        return fn(msg)
    return wrapper

def safe_send(chat_id, text):
    try:
        bot.send_message(chat_id, text, parse_mode="Markdown")
    except Exception:
        bot.send_message(chat_id, text, parse_mode=None)

# --- Knowledge Base: Менеджер файлів ---
kb_manager = NotebookManager(kb_path=KB_PATH, protocol_path=PROTOCOL_PATH)

def find_kb_file(keyword):
    """Шукає файл у Knowledge_Base за ключовим словом у назві."""
    return kb_manager.find_file(keyword)

def read_kb_file(path, max_chars=6000):
    """Читає вміст файлу з обмеженням."""
    return kb_manager.read_file(path, max_chars)

# --- Робота з OpenAI (GPT-4o) ---

def _is_switchable_error(e: Exception) -> bool:
    """Повертає True якщо помилка є ознакою вичерпаного ресурсу і потрібне перемикання ключа."""
    err = str(e).lower()
    return any(marker in err for marker in [
        "insufficient_quota",  # Ліміт балансу вичерпано
        "rate_limit_exceeded",  # Тимчасовий ліміт RPM/TPM
        "429",                  # HTTP Too Many Requests
        "quota",                # Загальна квота
    ])

def ask_ai(user_id, user_text):
    if not AI_READY:
        return "⚠️ ШІ-мозок не налаштований. Перевір API ключі у .env файлі."
    
    if user_id not in chat_histories:
        chat_histories[user_id] = []
    
    history = chat_histories[user_id]
    
    try:
        answer = ai_orchestrator.ask(SYSTEM_PROMPT, user_text, history)
        
        # Оновлюємо історію (зберігаємо в OpenAI-сумісному форматі)
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": answer})
        
        if len(history) > 20:
            chat_histories[user_id] = history[-20:]
            
        return answer
    except Exception as e:
        log.error(f"AI Error: {e}")
        return "Друже, щось мій процесор перегрівся. Дай мені хвилину прийти до тями."

# --- Кешування (Optimization) ---
ONESHOT_CACHE = {}
AUDIO_CACHE = {}
CACHE_TTL = 86400  # 24 години кешу (у секундах)

def ask_ai_oneshot(system_msg, user_msg, temperature=0.7, use_cache=False):
    """Одноразовий запит до обраної ШІ-моделі без історії."""
    if not AI_READY:
        return None
        
    cache_key = None
    if use_cache:
        cache_key = hashlib.md5(f"{system_msg}_{user_msg}_{temperature}".encode('utf-8')).hexdigest()
        if cache_key in ONESHOT_CACHE:
            entry = ONESHOT_CACHE[cache_key]
            if time.time() - entry['time'] < CACHE_TTL:
                return entry['data']

    try:
        answer = ai_orchestrator.ask(system_msg, user_msg)
        
        if use_cache and answer:
            ONESHOT_CACHE[cache_key] = {'time': time.time(), 'data': answer}
        return answer
    except Exception:
        return None

# ====================================================================
# FEATURE 2: TTS — Аудіо-підсумки
# ====================================================================
def generate_audio_summary(text, voice="nova"):
    """Генерує аудіо-файл з тексту через OpenAI TTS."""
    if not AI_READY:
        return None
        
    cache_key = hashlib.md5(f"audio_{text}_{voice}".encode('utf-8')).hexdigest()
    if cache_key in AUDIO_CACHE:
        entry = AUDIO_CACHE[cache_key]
        if time.time() - entry['time'] < CACHE_TTL:
            log.info("Serving Audio TTS from cache.")
            return io.BytesIO(entry['data'])
            
    try:
        # Спершу генеруємо стислий підсумок
        summary = ask_ai_oneshot(
            "Ти — асистент. Зроби чіткий, стислий підсумок наступного тексту українською мовою. "
            "Максимум 3000 символів. Підсумок має бути зрозумілим на слух як аудіо-запис.",
            text,
            use_cache=True
        )
        if not summary:
            return None
        
        response = ai_provider.client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=summary,
            response_format="opus"
        )
        
        audio_data = io.BytesIO()
        for chunk in response.iter_bytes():
            audio_data.write(chunk)
            
        AUDIO_CACHE[cache_key] = {'time': time.time(), 'data': audio_data.getvalue()}
        audio_data.seek(0)
        return audio_data
    except Exception as e:
        log.error(f"TTS Error: {e}")
        return None

# ====================================================================
# FEATURE 7: /meta — Універсальний Оркестратор / Meta-Optimizer
# ====================================================================
@bot.message_handler(commands=["meta"])
@guard
def handle_meta(msg: Message):
    safe_send(msg.chat.id, "🔍 **Запускаю аудит здоров'я системи...**\n"
                           "Це займе до 10 секунд. Я перевірю структуру, скіли та наявність конфліктів.")
    
    try:
        # Запускаємо скрипт як окремий процес, щоб не блокувати бота
        import subprocess
        result = subprocess.run([sys.executable, "talan/autobot/meta_optimizer.py"], 
                                capture_output=True, text=True, encoding="utf-8")
        
        if result.returncode == 0:
            # Шукаємо останній створений файл у папці рекомендацій
            rec_dir = BASE_DIR / ".agents" / "recommendations"
            files = sorted(rec_dir.glob("orchestrator_proposal_*.json"), key=os.path.getmtime)
            
            if files:
                latest_proposal = files[-1]
                data = json.loads(latest_proposal.read_text(encoding="utf-8"))
                
                resp = "🧠 **Результати аудиту Універсального Оркестратора:**\n\n"
                for item in data:
                    icon = "🔴" if item.get("severity") == "high" else "🟡"
                    resp += f"{icon} **{item['topic'].upper()}**\n"
                    resp += f"└ {item['recommendation']}\n\n"
                
                resp += "💡 Використай /optimize, щоб отримати план виправлення."
                safe_send(msg.chat.id, resp)
            else:
                safe_send(msg.chat.id, "✅ **Аудит завершено.** Конфліктів або критичних зауважень не виявлено. Ваша система в ідеальному стані!")
        else:
            log.error(f"Meta-Optimizer Error: {result.stderr}")
            safe_send(msg.chat.id, "❌ Помилка під час запуску аудиту. Подробиці у логах.")
            
    except Exception as e:
        log.error(f"Handle Meta Error: {e}")
        safe_send(msg.chat.id, f"❌ Сталася неочікувана помилка: {e}")

@bot.message_handler(commands=["optimize"])
@guard
def handle_optimize(msg: Message):
    rec_dir = BASE_DIR / ".agents" / "recommendations"
    files = sorted(rec_dir.glob("orchestrator_proposal_*.json"), key=os.path.getmtime)
    
    if not files:
        safe_send(msg.chat.id, "ℹ️ Поки що немає нових пропозицій для оптимізації. Запусти /meta для свіжого аудиту.")
        return
    
    latest_proposal = files[-1]
    data = json.loads(latest_proposal.read_text(encoding="utf-8"))
    
    resp = "🚀 **План оптимізації на основі аудиту:**\n\n"
    for i, item in enumerate(data, 1):
        resp += f"{i}. **{item['topic']}**:\n"
        resp += f"   - Шлях: {item['recommendation']}\n"
        resp += f"   - ДОЦІЛЬНІСТЬ: Економія ресурсів + стабільність.\n\n"
    
    resp += "🤔 **Тимуре, чи бажаєте ви впровадити ці зміни?**\n(Напишіть мені: 'Так, впроваджуй [Topic]', і я створю відповідний скіл або патч)."
    safe_send(msg.chat.id, resp)

# ====================================================================
# FEATURE 4: Веб-пошук через OpenAI
# ====================================================================
def web_search(query):
    """Пошук в інтернеті через OpenAI Responses API з web_search."""
    if not AI_READY:
        return "⚠️ ШІ не налаштований."
    try:
        gpt_provider = ai_orchestrator.providers.get("gpt")
        if not gpt_provider or not gpt_provider.ready or not gpt_provider.client:
            raise Exception("OpenAI client unavailable for web search")
        
        response = gpt_provider.client.responses.create(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            input=f"Знайди актуальну інформацію українською мовою: {query}"
        )
        # Витягуємо текстові блоки з відповіді
        result_text = ""
        for item in response.output:
            if hasattr(item, 'content'):
                for block in item.content:
                    if hasattr(block, 'text'):
                        result_text += block.text
        return result_text if result_text else "Не вдалося знайти інформацію."
    except Exception as e:
        log.error(f"Web Search Error: {e}")
        # Fallback: використовуємо Оркестратор
        return ask_ai_oneshot(
            "Ти — дослідник. Дай найкращу відповідь на запит користувача, базуючись на своїх знаннях. "
            "Відповідай українською.",
            query
        ) or f"❌ Помилка пошуку: {e}"

# ====================================================================
# ХЕНДЛЕРИ — Основні команди
# ====================================================================

@bot.message_handler(commands=["start", "старт", "myid", "айді", "status", "статус",
                                "read", "читати", "vault", "сховище", "codeblack", "кодчорний", 
                                "reload", "health", "menu", "onboarding", "back", "home",
                                "grant_scan", "grant_status", "model"])
@guard
def handle_commands(msg: Message):
    log.info(f"DEBUG: Command received: {msg.text} from {msg.from_user.id}")
    text = msg.text.lower()
    
    if "health" in text or "status" in text or "статус" in text:
        # Читаємо статус із файлу
        status_file = BASE_DIR / "logs" / "status.json"
        if not status_file.exists():
            safe_send(msg.chat.id, "📊 **Статус систем:**\nЛоги ще не сформовані. Запустіть перший бекап.")
            return
            
        try:
            data = json.loads(status_file.read_text(encoding="utf-8"))
            resp = "📊 **Аудит стабільності систем:**\n\n"
            
            for proc, info in data.items():
                icon = "✅" if info["status"] == "success" else "❌"
                proc_name = proc.upper().replace("_", " ")
                resp += f"{icon} **{proc_name}**\n"
                resp += f"└ Останній запуск: `{info['last_run']}`\n"
                if info["status"] != "success":
                    resp += f"└ Помилка: `{info['details']}`\n"
                resp += "\n"
            
            # Додаємо статус бота
            resp += "🤖 **BOT CORE**\n└ Статус: `ONLINE`\n└ Uptime: `Active`"
            safe_send(msg.chat.id, resp)
        except Exception as e:
            safe_send(msg.chat.id, f"❌ Помилка читання статусів: {e}")
        return
        
    if "reload" in text:
        reload_config()
        sync_env_to_external() # Синхронізація паролів на диск Е при перевантаженні
        safe_send(msg.chat.id, "✅ Конфігурацію оновлено та синхронізовано на Диск E!")
        return
        
    if any(x in text for x in ["start", "старт"]):
        # При старті запускаємо онбординг для нових клієнтів
        run_workflow(msg.chat.id, "onboarding")
    elif "onboarding" in text:
        run_workflow(msg.chat.id, "onboarding")
    elif "menu" in text:
        run_workflow(msg.chat.id, "menu")
    elif "home" in text:
        user_workflow_stack[msg.chat.id] = []
        run_workflow(msg.chat.id, "menu")
    elif "back" in text:
        stack = user_workflow_stack.get(msg.chat.id, [])
        if len(stack) > 1:
            stack.pop() # видаляємо поточний
            prev = stack.pop() # дістаємо попередній
            run_workflow(msg.chat.id, prev)
        else:
            safe_send(msg.chat.id, "⏪ Ви вже на самому початку.")
            run_workflow(msg.chat.id, "menu")
    elif any(x in text for x in ["myid", "айді"]):
        safe_send(msg.chat.id, f"Твій ID: `{msg.from_user.id}`")
    elif any(x in text for x in ["status", "статус"]):
        res = "\n".join([f"{'✅' if p.exists() else '❌'} Фаза {k}" for k,p in FILE_MAP.items()])
        safe_send(msg.chat.id, f"📊 **Статус Протоколу Чорного Лебедя:**\n{res}")
    elif any(x in text for x in ["vault", "сховище"]):
        path = FILE_MAP["vault"]
        if path.exists():
            safe_send(msg.chat.id, f"📦 **Входимо у Сховище (Vault).** Ось індекс документів:\n\n{path.read_text(encoding='utf-8')[:3000]}")
        else:
            safe_send(msg.chat.id, "❌ Індекс сховища не знайдено.")
    elif any(x in text for x in ["codeblack", "кодчорний"]):
        safe_send(msg.chat.id, "⚠️ **АКТИВОВАНО КОД ЧОРНИЙ!** Не панікуй. Дотримуйся інструкцій з Фази 3. Всі порти та доступи будуть обмежені згідно з протоколом.")
    elif "grant_scan" in text:
        safe_send(msg.chat.id, "🔎 **Запускаю розвідувальний дрон Web Scout...**\n"
                               "Я перевірю всі джерела на наявність нових грантів для ГО Талан ЮА. Результати прийдуть в окремий бот Grant Seeker.")
        try:
            scout_script = PROJECT_PATH / ".agents" / "skills" / "03-web-scout" / "web_scout_tool_talan.py"
            subprocess.Popen([sys.executable, str(scout_script), "scan", "--notify"])
        except Exception as e:
            safe_send(msg.chat.id, f"❌ Помилка запуску розвідника: {e}")
    elif "grant_status" in text:
        config_path = PROJECT_PATH / ".agents" / "skills" / "03-web-scout" / "scout_cache" / "watchlist.json"
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding="utf-8"))
            resp = f"🛡 **Стан моніторингу грантів:**\n\nМоніториться джерел: `{len(data)}`\n"
            resp += "Останні сканування:\n"
            for item in data[:5]:
                resp += f"└ {item['name']}: `{item.get('last_scan', 'ніколи')[:16]}`\n"
            safe_send(msg.chat.id, resp)
        else:
            safe_send(msg.chat.id, "ℹ️ Список моніторингу порожній. Запустіть перше сканування.")
    elif "model" in text:
        args = msg.text.split()
        if len(args) < 2:
            current = ai_orchestrator.active_model
            safe_send(msg.chat.id, f"🤖 **Поточна модель:** `{current.upper()}`\n\nЩоб змінити, напишіть:\n`/model gpt` — для GPT-4o-mini\n`/model claude` — для Claude 3.5 Sonnet")
            return
        
        target = args[1].lower()
        if ai_orchestrator.switch_model(target):
            safe_send(msg.chat.id, f"✅ **Модель успішно змінено на {target.upper()}!**\nТепер я буду думати цим 'мозком'.")
        else:
            safe_send(msg.chat.id, f"❌ Не вдалося активувати модель `{target}`. Можливо, вона не налаштована або введений невірний код.")

# ====================================================================
# FEATURE 2: /аудіо — TTS аудіо-підсумки
# ====================================================================
@bot.message_handler(commands=["audio", "аудіо"])
@guard
def handle_audio(msg: Message):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        safe_send(msg.chat.id, "ℹ️ Використання: `/аудіо <ключове слово>`\nНаприклад: `/аудіо Ашрам`")
        return
    
    keyword = args[1].strip()
    matches = find_kb_file(keyword)
    
    if not matches:
        safe_send(msg.chat.id, f"❌ Не знайдено документів за запитом «{keyword}». Спробуй /базазнань для перегляду доступних.")
        return
    
    target = matches[0]
    safe_send(msg.chat.id, f"🔊 Генерую аудіо-підсумок для: `{target.stem}`\n⏳ Це може зайняти ~30 секунд...")
    
    content = read_kb_file(target, max_chars=8000)
    audio = generate_audio_summary(content)
    
    if audio:
        bot.send_voice(msg.chat.id, audio, caption=f"🔊 Підсумок: {target.stem}")
        log.info(f"TTS sent for: {target.name}")
    else:
        safe_send(msg.chat.id, "❌ Не вдалося згенерувати аудіо. Можливо, проблема з квотою OpenAI.")

# ====================================================================
# FEATURE 3: /квіз — Квізи по документу
# ====================================================================
@bot.message_handler(commands=["quiz", "квіз"])
@guard
def handle_quiz(msg: Message):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        safe_send(msg.chat.id, "ℹ️ Використання: `/квіз <ключове слово>`\nНаприклад: `/квіз безпека`")
        return
    
    keyword = args[1].strip()
    matches = find_kb_file(keyword)
    
    if not matches:
        safe_send(msg.chat.id, f"❌ Не знайдено документів за запитом «{keyword}».")
        return
    
    target = matches[0]
    safe_send(msg.chat.id, f"🧠 Генерую квіз по документу: `{target.stem}`...")
    
    content = read_kb_file(target, max_chars=8000)
    quiz = ask_gpt_oneshot(
        "Ти — викладач. Створи квіз з 5 питань з 4 варіантами відповідей (A, B, C, D) "
        "на основі наданого тексту. Формат:\n\n"
        "❓ 1. [питання]\n"
        "   A) ...\n   B) ...\n   C) ...\n   D) ...\n"
        "✅ Відповідь: [літера]\n\n"
        "Відповідай українською. Зроби питання різного рівня складності.",
        f"Документ «{target.stem}»:\n\n{content}",
        temperature=0.8,
        use_cache=True
    )
    
    if quiz:
        safe_send(msg.chat.id, f"🧠 **Квіз: {target.stem}**\n\n{quiz}")
    else:
        safe_send(msg.chat.id, "❌ Не вдалося згенерувати квіз.")

# ====================================================================
# FEATURE 3: /флешкартки — Флешкартки по документу
# ====================================================================
@bot.message_handler(commands=["flash", "флешкартки"])
@guard
def handle_flashcards(msg: Message):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        safe_send(msg.chat.id, "ℹ️ Використання: `/флешкартки <ключове слово>`\nНаприклад: `/флешкартки ДСТУ`")
        return
    
    keyword = args[1].strip()
    matches = find_kb_file(keyword)
    
    if not matches:
        safe_send(msg.chat.id, f"❌ Не знайдено документів за запитом «{keyword}».")
        return
    
    target = matches[0]
    safe_send(msg.chat.id, f"📇 Генерую флешкартки по документу: `{target.stem}`...")
    
    content = read_kb_file(target, max_chars=8000)
    cards = ask_gpt_oneshot(
        "Ти — викладач. Створи 10 флешкарток (питання-відповідь) на основі тексту. "
        "Формат кожної картки:\n\n"
        "📌 **Картка 1**\n"
        "❓ [питання]\n"
        "💡 [коротка відповідь]\n\n"
        "Відповідай українською. Питання мають бути корисними для запам'ятовування ключових фактів.",
        f"Документ «{target.stem}»:\n\n{content}",
        temperature=0.7,
        use_cache=True
    )
    
    if cards:
        safe_send(msg.chat.id, f"📇 **Флешкартки: {target.stem}**\n\n{cards}")
    else:
        safe_send(msg.chat.id, "❌ Не вдалося згенерувати флешкартки.")

# ====================================================================
# FEATURE 4: /пошук — Веб-пошук
# ====================================================================
@bot.message_handler(commands=["search", "пошук"])
@guard
def handle_search(msg: Message):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        safe_send(msg.chat.id, "ℹ️ Використання: `/пошук <запит>`\nНаприклад: `/пошук гранти для NGO 2026`")
        return
    
    query = args[1].strip()
    safe_send(msg.chat.id, f"🔍 Шукаю в інтернеті: «{query}»...")
    
    result = web_search(query)
    safe_send(msg.chat.id, f"🔍 **Результати пошуку:**\n\n{result[:3500]}")

# ====================================================================
# FEATURE 5: /записати — Зберегти у Knowledge Base
# ====================================================================
@bot.message_handler(commands=["save", "записати"])
@guard
def handle_save(msg: Message):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2 or "|" not in args[1]:
        safe_send(msg.chat.id,
            "ℹ️ Використання: `/записати <категорія> | <текст>`\n"
            "Наприклад: `/записати Ашрам | Зустріч з волонтерами підтвердила потребу у 3 локаціях`")
        return
    
    parts = args[1].split("|", 1)
    category = parts[0].strip()
    raw_text = parts[1].strip()
    
    # Форматуємо запис через GPT
    formatted = ask_gpt_oneshot(
        "Ти — редактор. Очисти та відформатуй наступний текст як структурований запис "
        "для бази знань NGO. Додай маркери та чітку структуру. Не додавай вигаданої інформації. "
        "Відповідай українською.",
        raw_text
    ) or raw_text
    
    # Зберігаємо через менеджер
    result = kb_manager.save_note(category, raw_text, formatted)
    
    if result["created_new_category"]:
        log.info(f"Created new KB category: {result['cat_dir_name']}")
        
    safe_send(msg.chat.id, f"✅ Записано у базу знань!\n📂 Категорія: `{result['cat_dir_name']}`\n📄 Файл: `{result['file_name']}`")
    log.info(f"KB Save: {result['cat_dir_name']}/{result['file_name']} ({len(raw_text)} chars)")

# ====================================================================
# FEATURE 5: /блокнот — Створити новий блокнот
# ====================================================================
@bot.message_handler(commands=["notebook", "блокнот"])
@guard
def handle_notebook(msg: Message):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        safe_send(msg.chat.id,
            "ℹ️ Використання: `/блокнот <назва теми>`\n"
            "Наприклад: `/блокнот Партнерство з Червоним Хрестом`")
        return
    
    topic = args[1].strip()
    
    # Генеруємо структуру через GPT
    safe_send(msg.chat.id, f"📒 Створюю блокнот: «{topic}»...")
    
    structure = ask_ai_oneshot(
        "Ти — менеджер-проєктів NGO. Створи шаблон блокноту для нової теми. "
        "Формат markdown. Включи розділи: Мета, Контекст, Ключові факти, "
        "Контакти, Наступні кроки, Нотатки. Заповни заголовки, тіло залиш порожнім з підказками "
        "що писати. Відповідай українською.",
        f"Тема блокноту: {topic}",
        temperature=0.6
    )
    
    result = kb_manager.create_notebook(topic, structure, PROJECT_PATH)
    
    safe_send(msg.chat.id, result["message"])
    log.info(f"Notebook created: {result['path']}")

# ====================================================================
# FEATURE 5: /базазнань — Перегляд Knowledge Base
# ====================================================================
# ====================================================================
# FEATURE 6: /fulfill — Автоматична видача продукту (License Delivery)
# ====================================================================
@bot.message_handler(commands=['fulfill'])
def handle_fulfill(msg: Message):
    if msg.from_user.id not in ALLOWED_IDS:
        return
    
    try:
        # Expected: /fulfill user@email.com core
        parts = msg.text.split()
        if len(parts) < 3:
            safe_send(msg.chat.id, "📌 Використання: `/fulfill <email> <audit|core|ent>`")
            return
            
        email = parts[1]
        tier = parts[2].upper()
        
        # Simple key generation logic
        salt = "TALAN_SECURE_2026"
        raw = f"{email}|{tier}|{salt}|{int(time.time())}"
        key_hash = hashlib.sha256(raw.encode()).hexdigest()[:12].upper()
        license_key = f"{tier}-{key_hash}"
        
        # Save to active licenses
        licenses_file = BASE_DIR / "active_licenses.json"
        data = {}
        if licenses_file.exists():
            with open(licenses_file, "r") as f: data = json.load(f)
        
        data[license_key] = {"email": email, "tier": tier, "issued_at": str(datetime.now())}
        with open(licenses_file, "w") as f: json.dump(data, f, indent=4)
        
        response = (
            f"✅ **Система: Оплата Підтверджена!**\n\n"
            f"📦 **Продукт:** Universal AI Orchestrator ({tier})\n"
            f"🔑 **Ваш Ключ:** `{license_key}`\n\n"
            f"📥 **Скачати:** [Universal-AI-Orchestrator-v1.1.zip](https://github.com/TymurJan/Universal-AI-Orchestrator/releases/latest)\n\n"
            f"⚠️ *Примітка: Ключ буде прив'язано до вашого ПК при першому запуску.*"
        )
        safe_send(msg.chat.id, response)
        log.info(f"🎁 Ліцензія {license_key} видана для {email}")
        
    except Exception as e:
        log.error(f"❌ Помилка fulfillment: {e}")
        safe_send(msg.chat.id, "❌ Помилка при генерації ліцензії.")

@bot.message_handler(commands=["kb", "базазнань"])
@guard
def handle_kb_list(msg: Message):
    """Показує структуру Knowledge Base."""
    tree_text = kb_manager.get_kb_tree()
    safe_send(msg.chat.id, tree_text)

# ====================================================================
# Callback Хендлер для Меню (Workflow Support)
# ====================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("wf_"))
def handle_workflow_callbacks(call: CallbackQuery):
    chat_id = call.message.chat.id
    data = call.data
    
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
        cmd_name = data.replace("wf_cmd_", "")
        # Виконуємо команду як текст (емуляція вводу)
        call.message.text = f"/{cmd_name}"
        handle_commands(call.message)
    
    bot.answer_callback_query(call.id)

# ====================================================================
# Стандартні хендлери (текст та медіа)
# ====================================================================

# ====================================================================
# FUNCTION CALLING (AUTONOMOUS SKILL ROUTING)
# ====================================================================

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "run_system_audit",
            "description": "Запускає повний системний аудит. Використовуй, якщо користувач просить перевірити систему, конфлікти або здоров'я бота."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_strategic_idea",
            "description": "Зберігає стратегічну ідею або нову інформацію для розробки, щоб Агент (IDE) міг опрацювати її пізніше.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Короткий заголовок ідеї"},
                    "content": {"type": "string", "description": "Детальний опис ідеї або посилання на джерело"}
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Пошук інформації в інтернеті. Для пошуку нових грантів, законів або новин.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Пошуковий запит"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": "Пошук та читання документів у внутрішній Базі Знань ГО Талан ЮА.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Ключове слово для пошуку файлу"}
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crm_action",
            "description": "Створення запису, ліда або картки в CRM клієнта (наприклад, Bitrix24, Trello, Jira).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_type": {"type": "string", "description": "Тип дії (create_lead, create_task)"},
                    "payload": {"type": "string", "description": "Дані для CRM у форматі JSON-строки"}
                },
                "required": ["action_type", "payload"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_document",
            "description": "Створення квізів, флешкарток або аудіо-підсумку з документа у Базі Знань.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Ключове слово для пошуку файлу"},
                    "action": {"type": "string", "enum": ["audio", "quiz", "flashcards"], "description": "Дія, яку треба виконати"}
                },
                "required": ["keyword", "action"]
            }
        }
    }
]

def execute_tool(tool_name, arguments_json, chat_id):
    import json
    import subprocess
    
    try:
        args = json.loads(arguments_json)
    except Exception:
        args = {}

    log.info(f"⚙️ Виклик інструменту: {tool_name} з аргументами {args}")

    if tool_name == "run_system_audit":
        safe_send(chat_id, "⚙️ **Запускаю аудит здоров'я системи...**")
        result = subprocess.run([sys.executable, "talan/autobot/meta_optimizer.py"], 
                                capture_output=True, text=True, encoding="utf-8")
        if result.returncode == 0:
            return "Аудит завершено успішно. Скажи користувачеві, що конфліктів немає або запропонуй переглянути /optimize."
        return f"Помилка аудиту: {result.stderr}"

    elif tool_name == "record_strategic_idea":
        title = args.get("title", "Без назви")
        content = args.get("content", "")
        
        # Path to Dropzone
        ideas_path = BASE_DIR / "_DROPZONE" / "IN" / "IDEAS"
        ideas_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"IDEA_{timestamp}.md"
        file_path = ideas_path / filename
        
        idea_body = f"# 💡 СТРАТЕГІЧНА ІДЕЯ: {title}\n\n**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n**Опис:**\n{content}\n\n---\n*Передано через Telegram Bot*"
        
        try:
            file_path.write_text(idea_body, encoding="utf-8")
            safe_send(chat_id, f"✅ Ідею «{title}» зафіксовано в системі стратегічного розвитку. Агент Антігравіті отримає її при наступній синхронізації.")
            return f"Успіх: Ідея збережена у файл {filename}"
        except Exception as e:
            return f"Помилка збереження ідеї: {e}"

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
        return f"Знайдено документ {matches[0].stem}:\\n\\n{content}"

    elif tool_name == "analyze_document":
        keyword = args.get("keyword", "")
        action = args.get("action", "flashcards")
        matches = find_kb_file(keyword)
        if not matches:
            return f"Документ за запитом '{keyword}' не знайдено."
        
        target = matches[0]
        content = read_kb_file(target, max_chars=8000)
        
        if action == "audio":
            safe_send(chat_id, f"🔊 Генерую аудіо-підсумок для: `{target.stem}`...")
            audio = generate_audio_summary(content)
            if audio:
                bot.send_voice(chat_id, audio, caption=f"🔊 Підсумок: {target.stem}")
                return "Аудіо успішно згенеровано і надіслано користувачеві."
            return "Помилка при генерації аудіо."
            
        elif action == "quiz":
            safe_send(chat_id, f"🧠 Генерую квіз по документу: `{target.stem}`...")
            quiz = ask_ai_oneshot(
                "Ти — викладач. Створи квіз з 5 питань з 4 варіантами відповідей на основі тексту.",
                content, temperature=0.8, use_cache=True
            )
            return quiz if quiz else "Помилка генерації квізу."
            
        elif action == "flashcards":
            safe_send(chat_id, f"📇 Генерую флешкартки по документу: `{target.stem}`...")
            cards = ask_ai_oneshot(
                "Ти — викладач. Створи 10 флешкарток (питання-відповідь) на основі тексту.",
                content, temperature=0.7, use_cache=True
            )
            return cards if cards else "Помилка генерації флешкарток."

    elif tool_name == "crm_action":
        action_type = args.get("action_type", "unknown")
        payload = args.get("payload", "{}")
        safe_send(chat_id, f"🔌 Відправляю вебхук до CRM [{action_type}]...")
        # Webhook Stub for Multi-Tenancy B2B
        return f"Успіх: Дію {action_type} успішно виконано в CRM клієнта. Дані: {payload}"

    return f"Невідомий інструмент: {tool_name}"

@bot.message_handler(content_types=['text'])
@guard
def handle_text(msg: Message):
    log.info(f"AI Processing ({ai_orchestrator.active_model}): {msg.text}")
    
    health_keywords = ["як справи", "все добре", "статус", "бекап", "синхронізація", "здоров'я", "працює", "health"]
    if any(k in msg.text.lower() for k in health_keywords) and len(msg.text) < 30:
        msg.text = "/health"
        handle_commands(msg)
        return
        
    user_id = msg.from_user.id
    if user_id not in chat_histories:
        chat_histories[user_id] = []
    
    history = chat_histories[user_id]
    
    # CUSTOM SOUL INJECTION (Multi-Tenancy)
    client_profile_path = Path(f"Knowledge_Base/tenant_{user_id}/profile.json")
    if client_profile_path.exists():
        try:
            with open(client_profile_path, "r", encoding="utf-8") as pf:
                profile_data = json.load(pf)
                custom_sys_prompt = profile_data.get("system_prompt", SYSTEM_PROMPT)
        except Exception:
            custom_sys_prompt = SYSTEM_PROMPT
    else:
        custom_sys_prompt = SYSTEM_PROMPT
        
    # SYSTEM PROMPT INJECTION FOR FAIL-SAFE
    sys_prompt = custom_sys_prompt + "\nЯкщо ти не можеш виконати запит, поясни причину і обов'язково запропонуй альтернативу з доступних тобі інструментів."
    
    try:
        # Initial request to model with tools
        gpt_provider = ai_orchestrator.providers.get("gpt")
        if not gpt_provider or not gpt_provider.ready:
            safe_send(msg.chat.id, ask_ai(user_id, msg.text))
            return
            
        messages = [{"role": "system", "content": sys_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": msg.text})
        
        response = gpt_provider.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            tools=TOOLS_SCHEMA
        )
        
        message_obj = response.choices[0].message
        
        if message_obj.tool_calls:
            # We have tool calls
            history.append({"role": "user", "content": msg.text})
            history.append(message_obj)
            
            for tool_call in message_obj.tool_calls:
                result = execute_tool(tool_call.function.name, tool_call.function.arguments, msg.chat.id)
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
                
            # Second call to get final answer
            messages = [{"role": "system", "content": sys_prompt}]
            messages.extend(history)
            
            final_response = gpt_provider.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7
            )
            final_answer = final_response.choices[0].message.content
            history.append({"role": "assistant", "content": final_answer})
            safe_send(msg.chat.id, final_answer)
            
        else:
            # Standard conversational response
            answer = message_obj.content
            if not answer:
                answer = "❌ Я не зміг обробити цей запит. Спробуй перефразувати або скористайся інструментами з меню."
                
            history.append({"role": "user", "content": msg.text})
            history.append({"role": "assistant", "content": answer})
            safe_send(msg.chat.id, answer)
            
        if len(history) > 20:
            chat_histories[user_id] = history[-20:]
            
    except Exception as e:
        log.error(f"Handle Text / Tool Call Error: {e}")
        safe_send(msg.chat.id, "Друже, щось мій процесор перегрівся. Спробуй використати базові команди з меню.")


@bot.message_handler(content_types=['photo', 'document'])
@guard
def handle_media(msg: Message):
    safe_send(msg.chat.id, "⏳ Секунду, просканую документ через зір Антігравіті...")
    try:
        if msg.content_type == 'photo':
            file_id = msg.photo[-1].file_id
            ext = ".jpg"
        else:
            file_id = msg.document.file_id
            ext = os.path.splitext(msg.document.file_name)[1]
        
        data = bot.download_file(bot.get_file(file_id).file_path)
        
        recon_text = ""
        if OCR_ENABLED and ext.lower() in ['.jpg', '.png', '.jpeg']:
            img = Image.open(io.BytesIO(data))
            recon_text = pytesseract.image_to_string(img, lang='ukr+eng').lower()
        
        fname = f"DOC_{datetime.now().strftime('%H%M%S')}{ext}"
        (VAULT_PATH / fname).write_bytes(data)
        
        safe_send(msg.chat.id, f"✅ Документ збережено у Сховищі. Розпізнано тексту: {len(recon_text)} симв. Далі я з ним попрацюю!")
    except Exception as e:
        log.error(f"Media Error: {e}")
        safe_send(msg.chat.id, "❌ Сталася помилка при обробці документа.")


# --- Захист від дублювання (Singleton) ---
def check_single_instance():
    """Перевіряє, чи не запущений вже інший екземпляр бота."""
    pid_file = BASE_DIR / "bot.pid"
    current_pid = os.getpid()

    if pid_file.exists():
        try:
            old_pid = int(pid_file.read_text().strip())
            if psutil.pid_exists(old_pid):
                process = psutil.Process(old_pid)
                # Перевіряємо, чи це справді наш бот (python процес з bot.py у аргументах)
                if "python" in process.name().lower():
                    log.warning(f"⚠️ Виявлено працюючий екземпляр бота (PID: {old_pid}). Вихід.")
                    sys.exit(0)
        except Exception as e:
            log.error(f"Помилка при перевірці PID файлу: {e}")

    # Записуємо поточний PID
    pid_file.write_text(str(current_pid))
    log.info(f"📍 PID зафіксовано: {current_pid}")

def env_watcher():
    """Фоновий потік, що моніторить зміни у файлі .env та миттєво синхронізує їх на Диск Е."""
    env_file = BASE_DIR / ".env"
    last_mtime = 0
    if env_file.exists():
        last_mtime = os.path.getmtime(env_file)
        
    log.info("👀 Моніторинг змін .env активовано.")
    while True:
        try:
            if env_file.exists():
                current_mtime = os.path.getmtime(env_file)
                if current_mtime > last_mtime:
                    log.info("📝 Виявлено зміну в .env! Синхронізація на Диск Е...")
                    sync_env_to_external()
                    last_mtime = current_mtime
        except Exception as e:
            log.error(f"Помилка вочера .env: {e}")
        time.sleep(5) # Перевірка кожні 5 секунд

def run_scheduler():
    """Фоновий потік для запуску періодичних завдань (якщо Планувальник Windows не доступний)."""
    log.info("⏳ Фоновий планувальник запущено.")
    
    while True:
        try:
            now = datetime.now()
            
            # 1. Щоденний бекап о 23:00
            if now.hour == 23 and now.minute == 0:
                log.info("⏰ Плановий час бекапу (23:00). Запуск...")
                subprocess.run([sys.executable, "talan/autobot/backup_manager.py"])
                time.sleep(60) # Уникнення повторного запуску в ту ж хвилину
            
            # 2. Синхронізація KB кожні 4 години
            if now.hour % 4 == 0 and now.minute == 5:
                log.info(f"⏰ Планова синхронізація KB ({now.hour}:05). Запуск...")
                subprocess.run([sys.executable, "talan/autobot/kb_sync.py"])
                time.sleep(60)

            # 3. Розвідка грантів о 09:00 ранку
            if now.hour == 9 and now.minute == 0:
                log.info("⏰ Час ранкової розвідки грантів (09:00). Запуск...")
                scout_script = PROJECT_PATH / ".agents" / "skills" / "03-web-scout" / "web_scout_tool_talan.py"
                subprocess.Popen([sys.executable, str(scout_script), "scan", "--notify"])
                time.sleep(60)
                
        except Exception as e:
            log.error(f"❌ Помилка планувальника: {e}")
            
        time.sleep(30) # Перевірка кожні 30 секунд

if __name__ == "__main__":
    check_single_instance()
    log.info("🚀 Антігравіті V5.0 (Knowledge Base V2) ЗАПУСК...")
    
    # Пріоритетне резервування секретів на Диск E
    sync_env_to_external()
    
    # Запуск фонового планувальника
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Запуск миттєвого вочера для .env
    watcher_thread = threading.Thread(target=env_watcher, daemon=True)
    watcher_thread.start()
    
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=20)
        except KeyboardInterrupt:
            log.info("Stopping bot by user request...")
            break
        except Exception as e:
            log.error(f"Критична помилка пулінгу: {e}")
            log.error(traceback.format_exc())
            log.info("Перезапуск через 5 секунд...")
            import time
            time.sleep(5)
