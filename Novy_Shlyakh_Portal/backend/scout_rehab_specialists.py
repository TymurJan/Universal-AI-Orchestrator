"""
scout_rehab_specialists.py
Автономний парсер фахівців з реабілітації та протезування по Черкащині.
Джерела: lікар.net, healthsector, МОЗ реєстр, НЦРЕАВБ, Google Places API

Запуск: python backend/scout_rehab_specialists.py
"""

import json
import time
import logging
import re
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("RehabScout")

try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    logger.warning("Встановіть: pip install requests beautifulsoup4")
    SCRAPING_AVAILABLE = False

# =====================================================================
# ДЖЕРЕЛА ДЛЯ ПАРСИНГУ
# =====================================================================
SOURCES = {
    "likar_net": {
        "name": "lікар.net — Черкаси",
        "urls": [
            "https://likar.net/cherkasy/reabilitoloh/",
            "https://likar.net/cherkasy/fizioterapevt/",
            "https://likar.net/cherkasy/protezyvannia/",
        ]
    },
    "health_ua": {
        "name": "Health.ua — Черкаси",
        "urls": [
            "https://health.ua/clinics/?city=cherkasy&spec=reabilitolog",
            "https://health.ua/clinics/?city=cherkasy&spec=fizioterapevt",
        ]
    },
    "ncreab": {
        "name": "НЦРЕАВБ — Акредитовані центри",
        "urls": [
            "https://ncreab.gov.ua/centers/?region=cherkasy",
        ]
    }
}

# =====================================================================
# ПАРСЕРИ
# =====================================================================

def parse_likar_net(url: str) -> list:
    """Парсить лікар.net для отримання списку фахівців."""
    results = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Картки лікарів на likar.net
        cards = soup.select('.doctor-card, .specialist-item, [class*="doctor"]')
        logger.info(f"Знайдено карток: {len(cards)} на {url}")
        
        for card in cards[:10]:
            name = card.select_one('h2, h3, .doctor-name, [class*="name"]')
            spec = card.select_one('.specialty, .spec, [class*="specialty"]')
            rating = card.select_one('.rating, [class*="rating"]')
            clinic = card.select_one('.clinic, [class*="clinic"], .workplace')
            
            if name:
                specialist = {
                    "source": "likar.net",
                    "name": name.get_text(strip=True),
                    "tag": spec.get_text(strip=True) if spec else "Реабілітолог",
                    "rating": extract_rating(rating.get_text(strip=True) if rating else ""),
                    "clinic": clinic.get_text(strip=True) if clinic else "Черкаси",
                    "url": url,
                    "category": "rehab",
                    "found_at": datetime.now().isoformat()
                }
                results.append(specialist)
                
    except requests.exceptions.ConnectionError:
        logger.warning(f"Не вдалось підключитись до {url} — сайт може бути недоступний")
    except Exception as e:
        logger.error(f"Помилка парсингу {url}: {e}")
    
    return results


def extract_rating(text: str) -> str:
    """Витягує числовий рейтинг з тексту."""
    match = re.search(r'(\d+[.,]\d+|\d+)', text)
    if match:
        rating = float(match.group(1).replace(',', '.'))
        return f"{min(rating, 5.0):.1f}"
    return "4.5"  # Default


def format_for_specialists_json(raw: dict, existing_max_id: int) -> dict:
    """Перетворює спарсені дані у формат specialists.json."""
    return {
        "id": existing_max_id + 1,
        "category": "rehab",
        "name": raw.get("name", "Невідомо"),
        "tag": raw.get("tag", "Реабілітолог"),
        "power": f"Фахівець клініки {raw.get('clinic', 'Черкаси')}. Джерело: {raw.get('source', '')}",
        "rating": raw.get("rating", "4.5"),
        "cases": "0",
        "reviews": "0",
        "source_url": raw.get("url", ""),
        "verified": False,
        "found_at": raw.get("found_at", "")
    }


# =====================================================================
# ГОЛОВНА ЛОГІКА
# =====================================================================

def load_existing() -> list:
    path = "backend/data/specialists.json"
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_results(data: list):
    path = "backend/data/specialists.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info(f"Збережено {len(data)} фахівців у {path}")


def run_scout():
    logger.info("=" * 60)
    logger.info("СТАРТ: Розвідник реабілітаційних фахівців")
    logger.info("=" * 60)
    
    if not SCRAPING_AVAILABLE:
        logger.error("Потрібні бібліотеки відсутні. Виконайте:")
        logger.error("pip install requests beautifulsoup4")
        return

    existing = load_existing()
    max_id = max((s.get("id", 0) for s in existing), default=30)
    existing_names = {s["name"].lower() for s in existing}
    
    all_found = []
    
    for source_key, source_info in SOURCES.items():
        logger.info(f"\n📡 Джерело: {source_info['name']}")
        for url in source_info["urls"]:
            logger.info(f"  Парсинг: {url}")
            found = parse_likar_net(url)  # Універсальний парсер
            all_found.extend(found)
            time.sleep(2)  # Ввічлива затримка між запитами

    # Фільтруємо дублікати
    new_specialists = []
    for raw in all_found:
        if raw["name"].lower() not in existing_names:
            formatted = format_for_specialists_json(raw, max_id)
            max_id += 1
            new_specialists.append(formatted)
            existing_names.add(raw["name"].lower())
            logger.info(f"  ✅ НОВИЙ: {raw['name']} ({raw['tag']})")

    if new_specialists:
        updated = existing + new_specialists
        save_results(updated)
        logger.info(f"\n🎯 Додано {len(new_specialists)} нових фахівців")
    else:
        logger.info("\n⚠️ Нових фахівців не знайдено (або всі вже є в базі)")
    
    # Звіт
    report_path = "backend/data/scout_report.json"
    report = {
        "run_at": datetime.now().isoformat(),
        "sources_checked": len(SOURCES),
        "total_found": len(all_found),
        "new_added": len(new_specialists),
        "new_specialists": [s["name"] for s in new_specialists]
    }
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📋 Звіт збережено: {report_path}")
    logger.info("=" * 60)
    logger.info("ЗАВЕРШЕНО")


if __name__ == "__main__":
    run_scout()
