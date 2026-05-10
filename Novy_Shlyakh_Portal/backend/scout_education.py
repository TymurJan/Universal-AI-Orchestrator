# backend/scout_education.py
"""
AUTONOMOUS EDUCATION SCOUT v1.0
Призначення: Автоматичний моніторинг сайтів ДСЗ, грантових порталів та ВНЗ.
"""

import json
import time
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EducationScout")

# Ресурси для моніторингу
TARGET_URLS = [
    "https://www.dcz.gov.ua/storinka/vauchery",
    "https://mate.academy/ua/for-veterans",
    "https://ukraine.iom.int/uk/news",
    "https://minvet.gov.ua/osvita"
]

def scout_for_updates():
    """
    Імітація автономного веб-кроулінгу.
    В реальності тут буде використання BeautifulSoup4 або Selenium.
    """
    logger.info("Початок сеансу моніторингу освітніх ресурсів...")
    
    # Імітація знаходження нової програми
    found_programs = [
        {
            "id": int(time.time()),
            "category": "grants",
            "institution": "USAID",
            "title": "Програма підтримки підприємництва для ветеранів",
            "desc": "Гранти на бізнес-освіту та запуск власної справи. Обсяг до 250 000 грн.",
            "price": "Грант",
            "link": "https://usaid.gov.ua",
            "deadline": "30.06.2026"
        }
    ]
    
    time.sleep(2)
    logger.info(f"Знайдено нових програм: {len(found_programs)}")
    
    # Оновлення локальної бази
    try:
        with open('backend/data/education.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Додаємо лише унікальні
        current_titles = [item['title'] for item in data]
        for p in found_programs:
            if p['title'] not in current_titles:
                data.append(p)
                logger.info(f"Додано нову програму: {p['title']}")

        with open('backend/data/education.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        logger.error(f"Помилка оновлення бази: {e}")

if __name__ == "__main__":
    while True:
        scout_for_updates()
        # Моніторинг раз на 24 години
        logger.info("Очікування наступного циклу моніторингу...")
        time.sleep(86400)
