"""
Universal AI Orchestrator — Market Analyzer Tool (TAM, SAM, SOM)
Інструмент для автоматичного розрахунку обсягу ринку та генерації стратегічних звітів.

Використання:
  python market_analyzer_tool.py analyze --industry "SaaS CRM" --region "Європа" --total_clients 50000 --avg_check 1200 --sam_percent 20 --som_percent 5
  python market_analyzer_tool.py list
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# --- Шляхи ---
BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / ".orchestrator" / "market_reports"

def ensure_dirs():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def generate_report(industry, region, total_clients, avg_check, sam_percent, som_percent):
    """Генерує математичний розрахунок воронки ринку."""
    
    # 1. Total Addressable Market (Загальний ринок)
    tam_clients = int(total_clients)
    tam_revenue = tam_clients * avg_check
    
    # 2. Serviceable Available Market (Доступний ринок)
    sam_clients = int(tam_clients * (sam_percent / 100))
    sam_revenue = sam_clients * avg_check
    
    # 3. Serviceable Obtainable Market (Досяжний ринок / Мета)
    som_clients = int(sam_clients * (som_percent / 100))
    som_revenue = som_clients * avg_check
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_id = f"market_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Дані для JSON
    data = {
        "id": report_id,
        "timestamp": timestamp,
        "input": {
            "industry": industry,
            "region": region,
            "total_clients_estimate": total_clients,
            "avg_check_usd": avg_check,
            "sam_penetration_percent": sam_percent,
            "som_conversion_percent": som_percent
        },
        "analysis": {
            "TAM": {"clients": tam_clients, "revenue_usd": tam_revenue},
            "SAM": {"clients": sam_clients, "revenue_usd": sam_revenue},
            "SOM": {"clients": som_clients, "revenue_usd": som_revenue}
        }
    }
    
    # Формування Markdown звіту
    md_content = f"""# Аналіз Ринку: {industry} ({region})
**Дата генерації:** {timestamp}
**ID звіту:** `{report_id}`

## Вхідні Параметри
- **Оціночна кількість клієнтів у світі/регіоні:** {total_clients:,}
- **Середній чек (ARPU / LTV):** ${avg_check:,}
- **Коефіцієнт звуження (SAM):** {sam_percent}% (Цільовий сегмент, який продукт реально може покрити)
- **Конверсійна мета (SOM):** {som_percent}% (Частка, яку планується захопити в короткостроковій перспективі)

---

## 📊 Результати розрахунку (Воронка Ринків)

### 🌍 1. TAM (Total Addressable Market)
*Скільки грошей у всій ніші загалом, якщо продати всім.*
- **Потенційні клієнти:** {tam_clients:,}
- **Обсяг ринку:** **${tam_revenue:,.2f}**

### 🎯 2. SAM (Serviceable Available Market)
*Обсяг доступний саме нашій бізнес-моделі (з урахуванням географії, мови, специфіки).*
- **Цільові клієнти:** {sam_clients:,}
- **Обсяг ринку:** **${sam_revenue:,.2f}**

### 🚀 3. SOM (Serviceable Obtainable Market)
*Наш реальний план продажів / захоплення частки ринку на поточних ресурсах.*
- **Реальні клієнти (мета):** {som_clients:,}
- **Прогнозований дохід:** **${som_revenue:,.2f}**

---
*Звіт автоматично згенеровано модулем Universal AI Orchestrator (Strategy Core).*
"""
    
    ensure_dirs()
    
    # Збереження файлів
    json_path = REPORTS_DIR / f"{report_id}.json"
    md_path = REPORTS_DIR / f"{report_id}.md"
    
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(md_content, encoding="utf-8")
    
    return report_id, md_path, md_content

def cmd_analyze(args):
    """Запуск аналізу через CLI."""
    print(f"📊 Market Analyzer: Починаю розрахунок для '{args.industry}'...\n")
    
    report_id, md_path, md_content = generate_report(
        industry=args.industry,
        region=args.region,
        total_clients=args.total_clients,
        avg_check=args.avg_check,
        sam_percent=args.sam_percent,
        som_percent=args.som_percent
    )
    print(md_content)
    print(f"\n✅ Звіт успішно збережено:")
    print(f"   -> {md_path}")
    print(f"   -> {md_path.with_suffix('.json')}")

def cmd_list(args):
    """Список всіх згенерованих звітів."""
    ensure_dirs()
    reports = list(REPORTS_DIR.glob("*.json"))
    
    if not reports:
        print("📋 Жодного звіту ще не створено.")
        return
        
    print(f"📋 Знайдено звітів: {len(reports)}\n")
    for r in sorted(reports, reverse=True):
        try:
            data = json.loads(r.read_text(encoding="utf-8"))
            dt = data.get("timestamp", "Unknown Date")
            ind = data.get("input", {}).get("industry", "Unknown")
            print(f"- [{dt}] {r.stem} | Індустрія: {ind}")
        except Exception as e:
            print(f"- [ПОМИЛКА ЧИТАННЯ] {r.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Universal AI Orchestrator: Market Analyzer (TAM, SAM, SOM)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Команди")

    # analyze
    analyze_p = subparsers.add_parser("analyze", help="Провести розрахунок TAM/SAM/SOM")
    analyze_p.add_argument("--industry", required=True, type=str, help="Назва індустрії (напр. 'Cafe CRM')")
    analyze_p.add_argument("--region", required=True, type=str, help="Регіон або країна")
    analyze_p.add_argument("--total_clients", required=True, type=int, help="Загальна к-ть клієнтів (TAM size)")
    analyze_p.add_argument("--avg_check", required=True, type=float, help="Середній чек клієнта в $ (LTV/ARPU)")
    analyze_p.add_argument("--sam_percent", type=float, default=20.0, help="Відсоток ринку для SAM (default: 20)")
    analyze_p.add_argument("--som_percent", type=float, default=5.0, help="Відсоток SAM для SOM (default: 5)")

    # list
    list_p = subparsers.add_parser("list", help="Переглянути історію звітів")

    args = parser.parse_args()

    if args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()
