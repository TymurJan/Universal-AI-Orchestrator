"""
Universal AI Orchestrator — Web Scout Tool (AI-Розвідник v2.0)
Універсальний автономний моніторинг ресурсів з 3-шаровим конвеєром (LLM-Розвідник → Keyword → LLM-Аналітик).

Використання:
  python web_scout_tool.py watch --url "https://x.com" --directions "Ветеранські гранти,Соціальні проєкти" --filters "сума > 10K"
  python web_scout_tool.py scan --notify --token BOT_TOKEN --chat CHAT_ID
  python web_scout_tool.py discover --query "гранти для НГО Україна 2026" --directions "Гранти НГО"
  python web_scout_tool.py template --use grants-ngo
  python web_scout_tool.py list
  python web_scout_tool.py remove --name "USAID"
"""

import argparse
import hashlib
import json
import os
import sys
import difflib
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

try:
    import requests
except ImportError:
    print("❌ Помилка: requests не встановлено.")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Помилка: beautifulsoup4 не встановлено.")
    sys.exit(1)

from openai import OpenAI
import anthropic

# --- Шляхи та Ініціалізація ---
BASE_DIR = Path("d:\\ГО Талан UA\\Talan UA Antigravity manager\\.agents\\skills\\03-web-scout")
load_dotenv(Path("d:\\ГО Талан UA\\Talan UA Antigravity manager\\.env"))  # Завантажуємо загальний .env

SCOUT_DIR = BASE_DIR / "scout_cache"
CONFIG_FILE = SCOUT_DIR / "watchlist.json"
SNAPSHOTS_DIR = SCOUT_DIR / "snapshots"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = LOGS_DIR / "scout_reports"

# Налаштування логування
LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SCOUT_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOGS_DIR / "scout.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("WebScout")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TALAN_PARAMETERS = """ПАРАМЕТРИ МОНІТОРИНГУ ДЛЯ ГО "ТАЛАН ЮА":

Ключові слова (3 категорії):

КАТЕГОРІЯ 1 - "ASHRAM" (Реабілітація та підтримка):
- "гранти Україна соціальні проекти"
- "фінансування НГО ветерани"
- "підтримка реабілітаційні центри"
- "grants Ukraine veterans rehabilitation"
- "mental health PTSD veterans Ukraine"
- "реінтеграція ветеранів у цивільне життя"

КАТЕГОРІЯ 2 - "ХАБ ТА СОЦПІДПРИЄМНИЦТВО" (Спортивно-відпочинковий простір, бізнес ГО):
- "гранти соціальне підприємництво ветерани"
- "створення соціального бізнесу НГО"
- "інституційна підтримка розвиток ГО Україна"
- "grants NGO capacity building Ukraine"
- "veteran social enterprise funding"
- "гранти громадський простір хаб інфраструктура"
- "ІСАР Єднання розвиток спроможності ГО"

КАТЕГОРІЯ 3 - "КОМБО" (Комплексні проєкти):
- "соціальне підприємництво плюс реабілітація"
- "фінансування ветеранських просторів"
- "комплексна підтримка ветеранських ініціатив"

КАТЕГОРІЯ 4 - "СПРОМОЖНІСТЬ" (Розбудова ГО та інституційна підтримка):
- "гранти на організаційний розвиток ГО"
- "інституційна підтримка НГО Україна"
- "стратегічне планування гранти"
- "training for NGO staff grants"
- "institutional support civil society"
- "гранти на аудит та комунікації ГО"

ФІЛЬТРИ ДЛЯ ВІДБОРУ АГЕНТОМ:
- Для [ASHRAM] та [КОМБО]: Дедлайн ≥ 2 тижні | Сума від 150,000 грн | Тема: реабілітація, ПТСР, соціалізація.
- Для [ХАБ]: Дедлайн ≥ 3 тижні | Сума від $20,000 (або інституційні гранти від $10,000) | Тема: соціальне підприємництво, закупівля обладнання, фінансова стійкість ГО.
- Для [СПРОМОЖНІСТЬ]: Дедлайн ≥ 2 тижні | Сума від 50,000 грн | Тема: навчання команди, стратегія, оргрозвиток.

ПРАВИЛА ТЕГУВАННЯ:
- [ASHRAM] - реабілітація, ментальне здоров'я.
- [ХАБ] - грант на створення соцпідприємства, закупівлю обладнання або ремонт бази/простору.
- [СПРОМОЖНІСТЬ] - оргрозвиток, стратегія, навчання, інституційна підтримка.
- [КОМБО] - якщо грант покриває декілька категорій одночасно.
- [ТЕРМІНВО] - червоний прапорець, якщо залишилося менше 2 тижнів.
"""


# --- LLM Інтеграція (Multi-Model Orchestrator) ---
def call_llm(prompt: str, system_prompt: str = "Ти розумний AI-аналітик.") -> str:
    """Виклик LLM через офіційні клієнти. Пріоритет: OpenAI -> Anthropic."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Спроба 1: OpenAI (GPT-4o-mini) - дешево та швидко
    if openai_key and "sk-" in openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                timeout=30
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"⚠️ OpenAI (Scout) не доступний: {e}. Пробую Claude...")
            
    # Спроба 2: Anthropic (Claude 3.5 Sonnet) - якісно та надійно
    if anthropic_key and "sk-ant" in anthropic_key:
        try:
            client = anthropic.Anthropic(api_key=anthropic_key)
            resp = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                timeout=30
            )
            return resp.content[0].text.strip()
        except Exception as e:
            logger.error(f"❌ Anthropic (Scout) помилка: {e}")
            
    logger.warning("🚫 Платні моделі недоступні. Використовую Fallback-аналіз.")
    return ""


def llm_analyze_changes(added_lines: list, directions: list, filters: str) -> dict:
    """Шар 3: LLM Аналітик. Оцінює релевантність змін та напрямок."""
    if not added_lines:
        return {"relevance_score": 0.0, "matching_directions": [], "summary": "Немає нових рядків"}
        
    text_to_analyze = "\\n".join(added_lines[:50]) # Беремо перші 50 рядків щоб не перевищити токени
    
    system = f"Ти незалежний експерт з оцінки грантів. Твій контекст:\n{TALAN_PARAMETERS}\n\nАналізуй зміни сайту і повертай ВИКЛЮЧНО JSON без маркдаун блоків."
    prompt = f"""
    Оціни ці нові рядки з веб-сторінки на релевантність для наших цілей (ГО Талан ЮА).
    
    Наші напрямки (Directions/Уточнення для цього сайту): {directions}
    Наші фільтри/Вимоги (Filters): {filters}
    
    Новий текст зі сторінки:
    {text_to_analyze}
    
    Поверни JSON такого формату:
    {{
       "relevance_score": 0.95, // від 0.0 до 1.0
       "category": "[ASHRAM], [ХАБ] або [КОМБО]", // Визнач за правилами тегування. Якщо не підходить, тоді null.
       "urgent": true/false, // true, якщо підпадає під тег [ТЕРМІНВО]
       "summary": "Назва гранту та коротко про що він",
       "reasoning": "Чому підходить для ГО 'Талан ЮА' та як краще подавати заявку", // Важливий аналіз
       "deadline": "DD.MM.YYYY або 'Не вказано'",
       "amount": "$XXX,XXX або 'Не вказано'"
    }}
    Якщо інформація зовсім не релевантна (новини сайту, зміна меню, не грант) або relevance_score < 0.5 - повертай низький бал.
    """
    
    result_str = call_llm(prompt, system)
    if result_str:
        try:
            # Очищення можливого маркдауну ```json ... ```
            clean_str = result_str.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_str)
            return data
        except json.JSONDecodeError:
            logger.error(f"Помилка парсингу JSON від LLM: {result_str}")
    
    # --- FALLBACK: Аналіз на ключових словах, якщо LLM недоступний ---
    logger.warning("LLM недоступний. Використовую fallback-аналіз на ключових словах.")
    return keyword_fallback_analyze(added_lines, directions)


def keyword_fallback_analyze(added_lines: list, directions: list) -> dict:
    """Спрощений аналіз без LLM: шукає ключові слова з TALAN_PARAMETERS у тексті."""
    text = " ".join(added_lines).lower()
    
    ashram_keywords = ["грант", "реабілітац", "ветеран", "птср", "ptsd", "mental health", "реінтеграц", "соціальн"]
    hub_keywords = ["підприємництв", "capacity building", "інституцій", "спроможн", "обладнання", "ремонт", "хаб", "enterprise"]
    cap_keywords = ["оргрозвиток", "стратегічне", "навчання", "audit", "management", "civil society", "спроможність"]
    
    ashram_hits = sum(1 for kw in ashram_keywords if kw in text)
    hub_hits = sum(1 for kw in hub_keywords if kw in text)
    cap_hits = sum(1 for kw in cap_keywords if kw in text)
    total_hits = ashram_hits + hub_hits + cap_hits
    
    if total_hits == 0:
        return {"relevance_score": 0.1, "category": None, "urgent": False,
                "summary": "Зміни не містять ключових слів", "reasoning": None,
                "deadline": "Не вказано", "amount": "Не вказано"}
    
    # Визначаємо переможця
    hits = {"[ASHRAM]": ashram_hits, "[ХАБ]": hub_hits, "[СПРОМОЖНІСТЬ]": cap_hits}
    category = max(hits, key=hits.get)
    if list(hits.values()).count(hits[category]) > 1:
        category = "[КОМБО]"

    
    score = min(0.5 + total_hits * 0.1, 0.9)
    preview = " ".join(added_lines[:3])[:200]
    
    return {
        "relevance_score": score,
        "category": category,
        "urgent": False,
        "summary": f"[Keyword Fallback] Знайдено {total_hits} ключових слів у нових рядках",
        "reasoning": f"⚠️ LLM був недоступний, аналіз зроблено на ключових словах. Фрагмент: {preview}...",
        "deadline": "Не вказано",
        "amount": "Не вказано"
    }


def llm_discover(query: str) -> list:
    """Шар 1: LLM Розвідник. Шукає нові URL базуючись на параметричних знаннях LLM."""
    logger.info(f"Звертаюсь до бази знань LLM для запиту: {query}")
    
    system = "Ти експертний дослідник грантів та веб-сайтів. Повертай ВИКЛЮЧНО JSON без маркдаун блоків."
    prompt = f"""
    Мені потрібні найкращі 3-5 офіційних посилань (сайти донорів, портали, агрегатори) для моніторингу за темою: '{query}'.
    Поверни JSON масив об'єктів з полями 'url' та 'name'.
    Приклад: [{{\\"url\\": \\"https://gurt.org.ua/news/grants/\\", \\"name\\": \\"ГУРТ - Гранти\\"}}]
    """
    
    try:
        res_str = call_llm(prompt, system)
        if res_str:
            clean_str = res_str.replace("```json", "").replace("```", "").strip()
            # Безпечно шукаємо масив
            start = clean_str.find("[")
            end = clean_str.rfind("]")
            if start != -1 and end != -1:
                return json.loads(clean_str[start:end+1])
        return []
    except Exception as e:
        logger.error(f"Помилка розвідки: {e}")
        return []


# --- Базові функції ---
def load_watchlist() -> list:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return []


def save_watchlist(watchlist: list):
    CONFIG_FILE.write_text(json.dumps(watchlist, ensure_ascii=False, indent=2), encoding="utf-8")


def url_to_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def fetch_page_text(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, verify=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\\n".join(lines)
    except Exception as e:
        return f"[ПОМИЛКА ЗАВАНТАЖЕННЯ] {e}"


def get_snapshot_path(site_id: str) -> Path:
    return SNAPSHOTS_DIR / f"{site_id}.txt"


def detect_changes(old_text: str, new_text: str) -> dict:
    if not old_text:
        return {"type": "first_scan", "added_lines": []}
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))
    added = [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")]
    return {
        "type": "changed" if added else "unchanged",
        "added_lines": added
    }


# --- Команди ---
def cmd_watch(args):
    """Шар 2 (Налаштування). Додає об'єкт в Watchlist з напрямками і фільтрами."""
    watchlist = load_watchlist()
    dirs = [d.strip() for d in args.directions.split(",")] if args.directions else []
    
    entry = {
        "id": url_to_id(args.url),
        "name": args.name or args.url[:50],
        "url": args.url,
        "directions": dirs,
        "filters": args.filters or "Будь-які зміни",
        "added": datetime.now().isoformat(),
        "last_status": None
    }
    
    existing = [i for i, e in enumerate(watchlist) if e["url"] == args.url]
    if existing:
        watchlist[existing[0]] = entry
        logger.info(f"🔄 Оновлено: {entry['name']}")
    else:
        watchlist.append(entry)
        logger.info(f"✅ Додано до списку моніторингу: {entry['name']}")
        
    save_watchlist(watchlist)
    
    # Перший знімок
    logger.info("📸 Створюю початковий знімок сторінки...")
    text = fetch_page_text(args.url)
    if not text.startswith("[ПОМИЛКА"):
        get_snapshot_path(entry["id"]).write_text(text, encoding="utf-8")


def cmd_discover(args):
    """Шар 1. Знаходить і автоматично додає нові джерела (Discover)."""
    logger.info(f"🕵️ LLM-Розвідник починає пошук: '{args.query}'")
    results = llm_discover(args.query)
    if not results:
        logger.error("Розвідник не знайшов релевантних результатів.")
        return
        
    for res in results:
        args.url = res.get("url")
        args.name = res.get("name")
        cmd_watch(args)
    logger.info("🕵️ Пошук завершено. Джерела додані.")


def cmd_scan(args):
    """Шари 2 та 3. Точний моніторинг змін (Keyword/Hash) та LLM-Аналіз.
    --full: завантажити все поточне і зробити повний звіт (не тільки зміни).
    """
    watchlist = load_watchlist()
    if not watchlist:
        logger.warning("Список моніторингу порожній.")
        return

    logger.info(f"Сканування {len(watchlist)} джерел розпочато... (Full mode: {getattr(args, 'full', False)})")
    alerts = []
    is_full_mode = getattr(args, 'full', False)

    for entry in watchlist:
        url = entry["url"]
        site_id = entry["id"]
        
        new_text = fetch_page_text(url)
        if new_text.startswith("[ПОМИЛКА"):
            logger.error(f"[{entry['name']}] Помилка: {new_text[:50]}")
            continue

        snap_path = get_snapshot_path(site_id)
        old_text = snap_path.read_text(encoding="utf-8") if snap_path.exists() else ""
        
        # Визначаємо, що саме аналізувати
        if is_full_mode:
            # У повному режимі аналізуємо весь актуальний текст сторінки
            text_lines = new_text.split("\n")
            analysis = llm_analyze_changes(text_lines, entry.get("directions", []), entry.get("filters", ""))
            score = analysis.get("relevance_score", 0.0)
            
            if score >= 0.5:
                alerts.append({"entry": entry, "analysis": analysis, "preview": text_lines[:3]})
        else:
            # Тільки зміни
            changes = detect_changes(old_text, new_text)
            
            if changes["type"] == "first_scan":
                logger.info(f"[{entry['name']}] Перший знімок збережено. Для отримання звіту по всіх діючих грантах використайте --full")
            elif changes["type"] == "unchanged":
                logger.info(f"[{entry['name']}] Знайомих змін не виявлено.")
            else:
                logger.info(f"[{entry['name']}] Виявлено +{len(changes['added_lines'])} нових рядків.")
                analysis = llm_analyze_changes(changes["added_lines"], entry.get("directions", []), entry.get("filters", ""))
                if analysis.get("relevance_score", 0.0) >= 0.5:
                    alerts.append({"entry": entry, "analysis": analysis, "preview": changes["added_lines"][:3]})
                
        # Зберігаємо новий стан
        snap_path.write_text(new_text, encoding="utf-8")
        entry["last_scan"] = datetime.now().isoformat()

    save_watchlist(watchlist)

    # Сповіщення — ЗАВЖДИ (звіт + Telegram)
    if alerts:
        report_path = generate_markdown_report(alerts)
        
        # Тільки новий бот Grant Seeker
        targets = [
            (os.environ.get('GRANT_SEEKER_BOT_TOKEN', ''), os.environ.get('GRANT_SEEKER_CHAT_ID', ''))
        ]
        
        # Якщо в CLI передані конкретні токени — ставимо їх у пріоритет
        cli_token = getattr(args, 'token', None)
        cli_chat = getattr(args, 'chat', None)
        if cli_token and cli_chat:
            targets.insert(0, (cli_token, cli_chat))
            
        notified = False
        for tok, cht in targets:
            if tok and cht:
                send_telegram_alert(tok, cht, alerts, report_path)
                notified = True
        
        if not notified:
            logger.warning("Telegram токени не знайдено ні в CLI, ні в .env. Звіт збережено локально.")
    else:
        logger.info("✅ Сканування завершено. Нових релевантних грантів не знайдено.")


def cmd_template(args):
    """Шаблони для швидкого старту"""
    if args.use == "grants-ngo":
        templates = [
            {"name": "EU Funding & Tenders", "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-search", "directions": "Всі категорії", "filters": "дія в Україні"},
            {"name": "Work with USAID", "url": "https://www.workwithusaid.gov/solicitations", "directions": "ASHRAM, КОМБО", "filters": "соціальні, ветеранські"},
            {"name": "ІСАР Єднання", "url": "https://ednannia.ua/grants", "directions": "ХАБ, СПРОМОЖНІСТЬ", "filters": "розвиток спроможності, оргрозвиток"},
            {"name": "Український Ветеранський Фонд", "url": "https://veteranfund.com.ua/contests/", "directions": "Всі категорії", "filters": "всі активні"},
            {"name": "Міжнародний фонд Відродження", "url": "https://www.irf.ua/competitions/", "directions": "Всі категорії", "filters": "розвиток ГО"},
            {"name": "Дія.Бізнес Гранти", "url": "https://business.diia.gov.ua/cases/granti", "directions": "ХАБ (соцпідприємство)", "filters": "мікрогранти, єРобота"},
            {"name": "Pact Ukraine Opportunities", "url": "https://www.pactworld.org/solicitations", "directions": "СПРОМОЖНІСТЬ", "filters": "партнерство, гранти"},
            {"name": "Zagoriy Foundation", "url": "https://zagoriy.foundation/grants/", "directions": "СПРОМОЖНІСТЬ", "filters": "культура, меценатство, оргрозвиток"},
            {"name": "МХП Громаді", "url": "https://mhpgromadi.org.ua/hranty/potochni-hranty/", "directions": "ASHRAM, ХАБ", "filters": "розвиток громад, реабілітація"}
        ]

        for t in templates:
            class DummyArgs:
                url = t["url"]
                name = t["name"]
                directions = t["directions"]
                filters = t["filters"]
            cmd_watch(DummyArgs())
        logger.info("Шаблон 'grants-ngo' розгорнуто з правильними джерелами!")
    else:
        logger.error("Невідомий шаблон.")


# --- Нотифікації ---
def generate_markdown_report(alerts: list) -> Path:
    """Генерує Markdown звіт зі структурою, замовленою користувачем."""
    ts = datetime.now().strftime("%Y-%m-%d")
    file_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"NEW_GRANTS_{file_ts}.md"
    
    categories = {
        "[ASHRAM]": {"title": "## [ASHRAM] Проєкти з реабілітації", "items": []},
        "[ХАБ]": {"title": "## [ХАБ] Соціальне підприємництво та база ГО", "items": []},
        "[СПРОМОЖНІСТЬ]": {"title": "## [СПРОМОЖНІСТЬ] Розбудова та інституційна підтримка", "items": []},
        "[КОМБО]": {"title": "## [КОМБО] Комплексні проєкти", "items": []},
        "ІНШЕ": {"title": "## Інші знайдені можливості", "items": []}
    }


    best_strategic_advice = ""
    max_score = 0

    for a in alerts:
        analysis = a['analysis']
        cat = analysis.get('category', 'ІНШЕ')
        if cat not in categories:
            cat = "ІНШЕ"
            
        urgent_flag = " 🔥 **[ТЕРМІНВО]**" if analysis.get('urgent') else ""
        
        item_md = f"1. **{analysis.get('summary', a['entry']['name'])}**{urgent_flag}\n"
        item_md += f"   - 📅 **Дедлайн:** {analysis.get('deadline', 'Не вказано')}\n"
        item_md += f"   - 💰 **Сума:** {analysis.get('amount', 'Не вказано')}\n"
        item_md += f"   - 🔗 **Джерело:** [{a['entry']['name']}]({a['entry']['url']})\n"
        item_md += f"   - 🧠 **Висновки AI:** {analysis.get('reasoning', 'Без додаткового аналізу')}\n"
        
        categories[cat]["items"].append(item_md)
        
        score = analysis.get('relevance_score', 0)
        if score > max_score and analysis.get('reasoning'):
            max_score = score
            best_strategic_advice = analysis.get('reasoning')

    lines = [f"# 🎯 Розвідка грантів - {ts}\n"]
    
    for cat_data in categories.values():
        if cat_data["items"]:
            lines.append(cat_data["title"])
            lines.extend(cat_data["items"])
            lines.append("")

    lines.append("---")
    lines.append(f"💡 **Стратегічна порада Web Scout:**\n{best_strategic_advice if best_strategic_advice else 'Рекомендую переглянути список вище та визначити пріоритети для ГО Талан ЮА.'}")
    
    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Звіт збережено: {path}")
    return path


def send_telegram_alert(token: str, chat_id: str, alerts: list, report_path: Path):
    message_parts = ["🚨 <b>AI-РОЗВІДНИК: Важливі оновлення!</b>\n"]
    for a in alerts[:3]:
        score = int(a['analysis'].get('relevance_score', 0) * 100)
        category = a['analysis'].get('category', 'ІНШЕ')
        message_parts.append(f"🔔 <b>{category} {a['entry']['name']}</b> [Відповідність: {score}%]")
        message_parts.append(f"🌐 {a['entry']['url']}")
        message_parts.append(f"💡 {a['analysis'].get('summary', '')}\n")

    message_parts.append(f"📄 <i>Повний звіт: {report_path.name}</i>")
    text = "\n".join(message_parts)

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("Telegram-сповіщення відправлено успішно.")
        else:
            logger.error(f"Помилка Telegram: {resp.text}")
    except Exception as e:
        logger.error(f"Помилка відправки Telegram: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Універсальний AI-Розвідник v2.0")
    subparsers = parser.add_subparsers(dest="command")

    # watch
    watch_p = subparsers.add_parser("watch")
    watch_p.add_argument("--url", required=True)
    watch_p.add_argument("--directions", type=str, default="", help="Напр. 'IT Тендери,Нерухомість'")
    watch_p.add_argument("--filters", type=str, default="", help="Напр. 'дедлайн не менше тижня'")
    watch_p.add_argument("--name", type=str, default="")

    # discover
    discover_p = subparsers.add_parser("discover")
    discover_p.add_argument("--query", required=True, help="Запит для розвідника")
    discover_p.add_argument("--directions", type=str, default="Нове Джерело")
    discover_p.add_argument("--filters", type=str, default="Релевантне")

    # scan
    scan_p = subparsers.add_parser("scan")
    scan_p.add_argument("--notify", action="store_true")
    scan_p.add_argument("--token", type=str)
    scan_p.add_argument("--chat", type=str)
    scan_p.add_argument("--full", action="store_true", help="Повний звіт")


    # template
    templ_p = subparsers.add_parser("template")
    templ_p.add_argument("--use", required=True)

    # list & remove
    subparsers.add_parser("list")
    rem_p = subparsers.add_parser("remove")
    rem_p.add_argument("--name", required=True)

    args = parser.parse_args()

    if args.command == "watch":
        cmd_watch(args)
    elif args.command == "discover":
        cmd_discover(args)
    elif args.command == "scan":
        cmd_scan(args)
    elif args.command == "template":
        cmd_template(args)
    elif args.command == "list":
        wl = load_watchlist()
        for i, e in enumerate(wl):
            print(f"[{i}] {e['name']} - {e['url']} (Напрямки: {', '.join(e.get('directions',[]))})")
    elif args.command == "remove":
        wl = load_watchlist()
        original = len(wl)
        wl = [e for e in wl if e["name"] != args.name and e["url"] != args.name]
        save_watchlist(wl)
        print(f"Видалено джерел: {original - len(wl)}")
    else:
        parser.print_help()
