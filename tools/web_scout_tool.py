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

# --- Шляхи та Ініціалізація ---
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")  # Завантажуємо .env проєкту

SCOUT_DIR = BASE_DIR / ".orchestrator" / "scout_cache"
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

# --- LLM Інтеграція (ROI / Direct API) ---
def call_llm(prompt: str, system_prompt: str = "Ти розумний AI-аналітик.") -> str:
    """Виклик LLM через існуючі API ключі. Пріоритет: OpenAI -> Anthropic."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if openai_key:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"OpenAI LLM помилка: {e}. Перехід на резервний варіант (Anthropic)...")
            
    if anthropic_key:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        data = {
            "model": "claude-3-haiku-20240307",
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.3
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            if resp.status_code != 200:
                logger.error(f"Anthropic error response: {resp.text}")
            resp.raise_for_status()
            return resp.json()["content"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Anthropic LLM помилка: {e}")
            
    logger.warning("Усі API LLM недоступні! LLM-аналіз пропущено.")
    return ""


def llm_analyze_changes(added_lines: list, directions: list, filters: str) -> dict:
    """Шар 3: LLM Аналітик. Оцінює релевантність змін та напрямок."""
    if not added_lines:
        return {"relevance_score": 0.0, "matching_directions": [], "summary": "Немає нових рядків"}
        
    text_to_analyze = "\\n".join(added_lines[:50]) # Беремо перші 50 рядків щоб не перевищити токени
    
    system = "Ти незалежний експерт з оцінки текстових даних. Аналізуй зміни сайту і повертай ВИКЛЮЧНО JSON без маркдаун блоків."
    prompt = f"""
    Оціни ці нові рядки з веб-сторінки на релевантність для наших цілей.
    
    Наші напрямки (Directions): {directions}
    Наші фільтри/Вимоги (Filters): {filters}
    
    Новий текст зі сторінки:
    {text_to_analyze}
    
    Поверни JSON такого формату:
    {{
       "relevance_score": 0.95, // від 0.0 до 1.0, наскільки це відповідає фільтрам/напрямкам
       "matching_directions": ["Назва напрямку з нашого списку"],
       "summary": "Короткий опис про що цей текст (1 речення)",
       "details": "Знайдені важливі дані (напр. сума, дати, назви) або null якщо нічого"
    }}
    Якщо інформація зовсім не релевантна (напр. загальні новини сайту, зміна меню) або relevance_score < 0.3 - повертай низький бал.
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
    
    return {"relevance_score": 0.5, "matching_directions": [], "summary": "LLM аналіз не вдався", "details": None}


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
    """Шари 2 та 3. Точний моніторинг змін (Keyword/Hash) та LLM-Аналіз (якщо є зміни)."""
    watchlist = load_watchlist()
    if not watchlist:
        logger.warning("Список моніторингу порожній.")
        return

    logger.info(f"Сканування {len(watchlist)} джерел розпочато...")
    alerts = []

    for entry in watchlist:
        url = entry["url"]
        site_id = entry["id"]
        
        new_text = fetch_page_text(url)
        if new_text.startswith("[ПОМИЛКА"):
            logger.error(f"[{entry['name']}] Помилка: {new_text[:50]}")
            continue

        snap_path = get_snapshot_path(site_id)
        old_text = snap_path.read_text(encoding="utf-8") if snap_path.exists() else ""
        
        # Шар 2: Швидке виявлення змін (безкоштовно)
        changes = detect_changes(old_text, new_text)
        
        if changes["type"] == "first_scan":
            logger.info(f"[{entry['name']}] Перший знімок збережено.")
        elif changes["type"] == "unchanged":
            logger.info(f"[{entry['name']}] Знайомих змін не виявлено.")
        else:
            # Шар 3: Зміни є. Передаємо в LLM-Аналітик
            logger.info(f"[{entry['name']}] Виявлено +{len(changes['added_lines'])} нових рядків. Передача в LLM-Аналітик...")
            
            analysis = llm_analyze_changes(changes["added_lines"], entry.get("directions", []), entry.get("filters", ""))
            score = analysis.get("relevance_score", 0.0)
            
            if score >= 0.5: # Мінімальний поріг релевантності
                logger.critical(f"🔔 АЛЕРТ! Знайдено релевантні зміни (Score: {score}) на {entry['name']}")
                alerts.append({
                    "entry": entry,
                    "analysis": analysis,
                    "preview": changes["added_lines"][:3]
                })
            else:
                logger.info(f"[{entry['name']}] Зміни відхилено LLM (Score: {score}). {analysis.get('summary', '')}")
                
        # Зберігаємо новий стан
        snap_path.write_text(new_text, encoding="utf-8")
        entry["last_scan"] = datetime.now().isoformat()

    save_watchlist(watchlist)

    # Сповіщення
    if alerts:
        report_path = generate_markdown_report(alerts)
        if args.notify and args.token and args.chat:
            send_telegram_alert(args.token, args.chat, alerts, report_path)


def cmd_template(args):
    """Шаблони для швидкого старту"""
    if args.use == "grants-ngo":
        templates = [
            {"name": "EU Funding & Tenders", "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/programmes/crea", "directions": "Гранти, Культура", "filters": "тільки ті, що діють в Україні"},
            {"name": "USAID Ukraine", "url": "https://www.usaid.gov/ukraine/partner-with-us", "directions": "Гранти, Співпраця", "filters": "соціальні та економічні"},
            {"name": "Український Ветеранський Фонд", "url": "https://veteranfund.com.ua/contests/", "directions": "Ветеранські гранти", "filters": "всі активні"}
        ]
        for t in templates:
            class DummyArgs:
                url = t["url"]
                name = t["name"]
                directions = t["directions"]
                filters = t["filters"]
            cmd_watch(DummyArgs())
        logger.info("Шаблон 'grants-ngo' розгорнуто!")
    else:
        logger.error("Невідомий шаблон.")


# --- Нотифікації ---
def generate_markdown_report(alerts: list) -> Path:
    """Генерує Markdown звіт зі знайденими структурованими даними."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"ALERT_{ts}.md"
    
    lines = [f"# 🔔 Звіт AI-Розвідника (Web Scout) — {datetime.now().strftime('%Y-%m-%d %H:%M')}\\n"]
    for a in alerts:
        score = a['analysis'].get('relevance_score', 0)
        dirs = ", ".join(a['analysis'].get('matching_directions', []))
        
        lines.append(f"## {a['entry']['name']} (Relevance: {score})")
        lines.append(f"**Напрямки:** {dirs}")
        lines.append(f"**URL:** {a['entry']['url']}")
        lines.append(f"**Опис:** {a['analysis'].get('summary', '')}")
        if a['analysis'].get('details'):
            lines.append(f"**Деталі:** {a['analysis'].get('details')}")
        lines.append(f"\\n**Фрагмент коду:**\\n```text\\n{'\\n'.join(a['preview'])}\\n```\\n")
        
    path.write_text("\\n".join(lines), encoding="utf-8")
    logger.info(f"Звіт збережено: {path}")
    return path


def send_telegram_alert(token: str, chat_id: str, alerts: list, report_path: Path):
    message_parts = ["🚨 <b>AI-РОЗВІДНИК: Важливі оновлення!</b>\n"]
    for a in alerts[:3]:
        score = int(a['analysis'].get('relevance_score', 0) * 100)
        message_parts.append(f"🔔 <b>{a['entry']['name']}</b> [Відповідність: {score}%]")
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
