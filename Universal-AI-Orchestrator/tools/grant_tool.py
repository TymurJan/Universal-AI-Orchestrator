"""
Universal AI Orchestrator — Grant Application Tool
Автоматична підготовка структури грантових заявок.

Використання:
  python grant_tool.py create --project "Центр реінтеграції" --donor "USAID" --goal "Реінтеграція 200 ветеранів" --budget 150000 --currency USD --duration 12
  python grant_tool.py list
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
GRANTS_DIR = BASE_DIR / ".orchestrator" / "grant_applications"

# Словник відомих донорів з профільними налаштуваннями.
# Якщо донор не в списку — використовується шаблон "Generic" і назва донора зберігається як є.
KNOWN_DONORS = {
    # ── МІЖНАРОДНІ ОРГАНІЗАЦІЇ ────────────────────────────────────────────
    "USAID": {
        "style": "Results-Oriented (Focusing on clearly measurable outcomes)",
        "lang": "EN",
        "budget_note": "Indirect costs typically capped at 20% of total budget. NICRA required for US universities.",
        "priority_sections": ["Problem Statement", "Theory of Change", "M&E Plan", "Sustainability"],
        "tip": "Use active voice, avoid jargon. Include baseline data.",
    },
    "EU": {
        "style": "Logical Framework (LogFrame / Intervention Logic)",
        "lang": "EN/UK",
        "budget_note": "Co-financing (10-20% min) required. No profit allowed. VAT usually ineligible.",
        "priority_sections": ["Context Analysis", "LogFrame Matrix", "Budget Breakdown", "Risk Matrix", "Visibility Plan"],
        "tip": "LogFrame is mandatory. Every output must link to an outcome and impact.",
    },
    "UN Women": {
        "style": "Gender-Transformative Approach",
        "lang": "EN",
        "budget_note": "Gender-sensitive budgeting required. Disaggregate all data by gender.",
        "priority_sections": ["Gender Analysis", "Theory of Change", "Capacity Building", "M&E"],
        "tip": "Explicitly address gender equality and women's empowerment in every section.",
    },
    "UNICEF": {
        "style": "Child-Rights Based Approach",
        "lang": "EN",
        "budget_note": "Focus on children 0-18. Indirect costs usually 7-13%.",
        "priority_sections": ["Situation Analysis", "Programme Logic", "Safeguarding Plan", "Implementation Plan", "Budget"],
        "tip": "Must address child protection / do-no-harm principles explicitly.",
    },
    "UNHCR": {
        "style": "Humanitarian Response",
        "lang": "EN",
        "budget_note": "Typically project-based, fast-turnaround funding. Joint projects preferred.",
        "priority_sections": ["Needs Assessment", "Target Population", "Protection Concerns", "Activity Plan", "Budget"],
        "tip": "Use humanitarian cluster language. Emphasize speed of response.",
    },
    "WHO": {
        "style": "Health Systems Strengthening",
        "lang": "EN",
        "budget_note": "Focus on public health outcomes. Evidence-based interventions only.",
        "priority_sections": ["Health Needs Assessment", "Theory of Change", "Service Delivery Model", "Monitoring"],
        "tip": "Cite WHO guidelines and global health targets (SDG 3).",
    },
    "UNDP": {
        "style": "Human Development / SDG-Aligned",
        "lang": "EN",
        "budget_note": "SDG alignment is required. Include GHG/environmental impact where applicable.",
        "priority_sections": ["SDG Mapping", "Problem Analysis", "Stakeholder Engagement", "Results Framework"],
        "tip": "Link every objective to at least one Sustainable Development Goal.",
    },
    "GIZ": {
        "style": "German Development Cooperation (Capacity Development)",
        "lang": "DE/EN",
        "budget_note": "BMZ rules apply. Co-financing or in-kind contributions often expected.",
        "priority_sections": ["Systemic Analysis", "Capacity Development Plan", "Results Chain", "Budget"],
        "tip": "Strong emphasis on long-term systemic change and local ownership.",
    },
    "World Bank": {
        "style": "Evidence-Based Development Finance",
        "lang": "EN",
        "budget_note": "Procurement rules are strict. Environmental and Social Framework (ESF) compliance required.",
        "priority_sections": ["Problem Identification", "Institutional Analysis", "Financial Plan", "ESF Assessment"],
        "tip": "Use economic analysis (cost-benefit). Environmental safeguards are non-negotiable.",
    },
    "EBRD": {
        "style": "Transition Impact Assessment",
        "lang": "EN",
        "budget_note": "Focus on private sector development. Blended finance structures accepted.",
        "priority_sections": ["Market Analysis", "Transition Impact", "Financial Projections", "Environmental Policy"],
        "tip": "Show economic transition contribution — competition, integration, governance.",
    },
    "IFC": {
        "style": "Private Sector Development",
        "lang": "EN",
        "budget_note": "ROI and financial sustainability are key criteria. No full grants — blended instruments.",
        "priority_sections": ["Market Gap", "Business Model", "Development Impact", "Financial Plan"],
        "tip": "Must show commercial viability alongside development impact.",
    },
    # ── ДВОСТОРОННІ ДОНОРИ ────────────────────────────────────────────────
    "SIDA": {
        "style": "Swedish Development Aid (Rights-Based)",
        "lang": "EN/SV",
        "budget_note": "Human rights-based approach mandatory. Anti-corruption clause required.",
        "priority_sections": ["Rights Analysis", "Target Groups", "Change Theory", "Budget & Audit Plan"],
        "tip": "Address the four human rights principles: participation, non-discrimination, accountability, transparency.",
    },
    "DFID / FCDO": {
        "style": "UK Aid — Value for Money",
        "lang": "EN",
        "budget_note": "Economy, Efficiency, Effectiveness (3 E's) must be demonstrated.",
        "priority_sections": ["Problem Statement", "Theory of Change", "VfM Analysis", "Risk Register"],
        "tip": "Explicitly address 'Value for Money' with cost-per-beneficiary calculations.",
    },
    "AFD": {
        "style": "French Development Agency — Climate & Inequality Focus",
        "lang": "FR/EN",
        "budget_note": "Climate co-benefits must be quantified. Gender marker required.",
        "priority_sections": ["Context & Needs", "Climate Assessment", "Logical Framework", "Budget"],
        "tip": "Link to Paris Agreement goals. Use AFD gender and climate markers.",
    },
    # ── КОРПОРАТИВНІ ФОНДИ ───────────────────────────────────────────────
    "МХП": {
        "style": "Корпоративна соціальна відповідальність (КСВ)",
        "lang": "UK",
        "budget_note": "Акцент на локальній громаді та вимірюваних соціальних метриках.",
        "priority_sections": ["Проблематика", "Бенефіціари", "Партнери", "Бюджет", "КСВ-вплив"],
        "tip": "Покажіть прямий зв'язок з діяльністю компанії та сталим розвитком регіону.",
    },
    "Укрпошта / Нова пошта": {
        "style": "Корпоративний фонд / Соціальний проєкт",
        "lang": "UK",
        "budget_note": "Акцент на масштабуванні через логістичну мережу компанії.",
        "priority_sections": ["Соціальна проблема", "Рішення", "Партнерство", "Бюджет"],
        "tip": "Покажіть як мережа компанії допомагає масштабувати ефект.",
    },
    "ДТЕК": {
        "style": "Корпоративний фонд — Енергетика та Громади",
        "lang": "UK",
        "budget_note": "Пріоритет — проєкти в регіонах присутності компанії.",
        "priority_sections": ["Громада та потреба", "Енергоефективність", "Бюджет", "Сталість"],
        "tip": "Покажіть зв'язок з енергетичними або екологічними пріоритетами ДТЕК.",
    },
    # ── УКРАЇНСЬКІ ІНФРАСТРУКТУРНІ ДОНОРИ / ПЛАТФОРМИ ────────────────────
    "ISAR Єднання": {
        "style": "Розвиток громадянського суспільства (Civil Society Development)",
        "lang": "UK",
        "budget_note": (
            "Непрямі витрати — до 15%. Власний внесок заохочується, але не обов'язковий. "
            "ISAR зазвичай вимагає детальний бюджет по статтях і банківські реквізити організації."
        ),
        "priority_sections": [
            "Проблема та потреба громади",
            "Мета, завдання та очікувані результати",
            "Цільова група (кількість прямих та непрямих бенефіціарів)",
            "Спроможність організації (досвід, команда)",
            "Партнерства та мережі",
            "План реалізації (місяць за місяцем)",
            "Бюджет (детально по статтях)",
            "Стійкість після завершення фінансування",
        ],
        "tip": (
            "ISAR Єднання фінансує НКО, що зміцнюють демократію, участь громадян та підзвітність влади. "
            "Обов'язково вкажіть: 1) скільки людей ПРЯМО отримають послугу (реальна цифра, не перебільшення); "
            "2) як проєкт пов'язаний з адвокацією, доступом до інформації або діалогом з владою; "
            "3) як організація підтримуватиме результат після завершення гранту (без нового фінансування). "
            "ТАБУ: грантові кошти не можна витрачати на ремонт, будівництво та придбання нерухомості."
        ),
    },

    # ── Резерв ───────────────────────────────────────────────────────────
    "Generic": {
        "style": "Стандартний міжнародний проєктний цикл",
        "lang": "UK/EN",
        "budget_note": "Перевірте специфічні вимоги до бюджету у положенні донора.",
        "priority_sections": ["Актуальність проблеми", "Мета та завдання", "План реалізації", "Бюджет", "Стійкість"],
        "tip": "Уточніть вимоги донора і адаптуйте шаблон відповідно.",
    },
}

def ensure_dirs():
    GRANTS_DIR.mkdir(parents=True, exist_ok=True)


def get_donor_profile(donor_name: str) -> dict:
    """Повертає профіль відомого донора або Generic з назвою кастомного."""
    for key in KNOWN_DONORS:
        if key.lower() == donor_name.lower():
            return KNOWN_DONORS[key]
    return KNOWN_DONORS["Generic"]


def generate_grant(args):
    donor = get_donor_profile(args.donor)
    grant_id = f"GRANT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    today = datetime.now().strftime("%d.%m.%Y")
    budget_per_month = args.budget / args.duration if args.duration > 0 else args.budget

    sections_list = "\n".join([f"- [ ] **{s}**" for s in donor["priority_sections"]])
    tip_block = f"\n> 💡 **Порада для цього донора:** {donor['tip']}" if donor.get("tip") else ""

    content = f"""# ГРАНТОВА ЗАЯВКА: {args.project}
**ID:** `{grant_id}`  |  **Дата:** {today}  |  **Донор:** {args.donor}

---

## 📋 АНОТАЦІЯ ТА МЕТОДОЛОГІЯ (Universal AI Orchestrator)

**Організація-заявник:** ________________________________  
**Назва проєкту:** {args.project}  
**Загальний бюджет:** {args.budget:,.2f} {args.currency}  
**Тривалість реалізації:** {args.duration} місяців  
**Бюджет на місяць:** ~{budget_per_month:,.2f} {args.currency}

> ⚠️ **КРИТИЧНІ ПРАВИЛА ГЛИБОКОГО АНАЛІЗУ (Базується на курсі "Від фінансування до реалізації"):**
> 1. **Емпатія в рамках бюрократії:** Транслюйте глибокий емоційний вплив ("щоб донор ЗАХОТІВ стати причетним"). Використовувати суху грантову мову зі статистикою і сильними ціннісними маркерами.
> 2. **Подвійна лупа (Аналіз нотаток):** Аналізуйте і поглиблюйте кожну нотатку форми за схемою SMART та документом "Рекомендаціями щодо заповнення".
> 3. **Ефект метелика (Цілі -> Бюджет):** Логіка йде від Анотації -> Плану -> Бюджету. План і Ризики генерують УСІ неявні витрати (доставка, адмінка, буфер). У коментарях детально описується все необхідне з точними цінами і гіперпосиланнями.
> 4. **Незмінність шаблону:** Оригінальна форма донора є священною. Суворо заборонено змінювати структуру, розмітку чи видаляти нотатки донора — текст пишеться під ними.
> 5. **Інтеграція КСВ:** Залучайте бізнес до партнерства, показуючи їхні вигоди через вплив проєкту на громаду.
> 6. **Фінансова стійкість:** Завжди вказуйте фінансову участь організації (власні кошти або місцевий бюджет) у статтях. Це доводить вашу спроможність.
> 7. **Стратегія диверсифікації:** Прописуйте альтернативні джерела ресурсів (ярмарки, донейти), щоб довести незалежність від одного 1 гранту.
> 8. **Стратегія масштабування:** Аналітика інформаційного супроводу та сталості проєкту виводиться безпосередньо з логіки Бюджету та Мети, паралельно синхронізуючись із Планом публікацій.

> **Мета одним реченням / Pitch:** {args.goal}

---

## 🎯 СТИЛЬ ЗАЯВКИ ДЛЯ ЦЬОГО ДОНОРА

- **Стиль:** {donor["style"]}
- **Мова подачі:** {donor["lang"]}
- **Бюджетна примітка:** {donor["budget_note"]}{tip_block}

---

## ✅ ОБОВ'ЯЗКОВІ РОЗДІЛИ (Checklist)
{sections_list}

---

## 1. АКТУАЛЬНІСТЬ ПРОБЛЕМИ (Evidence-based)

> *(Заповніть: статистику, локальний контекст, докази проблеми — обов'язково з посиланнями на офіційні джерела. Тут формується «емоційний гачок» але на базі фактів.)*

**Проблема:**
[...вставте опис проблеми...]

**Кількісні показники:**
- Кількість людей, яких стосується: ____________
- Джерело даних: ____________
- Тенденція (зростає / стабільна / зменшується): ____________

---

## 2. МЕТА ТА ЗАВДАННЯ (Action-oriented)

**Загальна мета проєкту:**
> {args.goal}

**Завдання (SMART - Конкретні, вимірювані, досяжні):**
1. [Дієслово доконаного виду] __________________________________
2. [Дієслово доконаного виду] __________________________________
3. [Дієслово доконаного виду] __________________________________

**Очікувані результати:**
- **Кількісні:** [Точні метрики] ____________
- **Якісні:** [Зміни у стані бенефіціарів] ____________

---

## 3. ЦІЛЬОВА АУДИТОРІЯ

| Категорія | Кількість (прямі) | Кількість (непрямі) |
|---|---|---|
| Основна група | ______ | ______ |
| Вторинна група | ______ | ______ |

---

## 4. ПЛАН РЕАЛІЗАЦІЇ (Календарний графік)

| Місяць | Активність (Діяльність) | Відповідальна особа | Результат |
|---|---|---|---|
| 1-2 | Підготовка (Закупівлі, набір персоналу, домовленості) | | |
| 3-6 | Основний етап впровадження | | |
| 7-{args.duration} | Масштабування, фіналізація, передача досвіду | | |

---

## 5. БЮДЖЕТ (З тотальним обґрунтуванням «під ключ»)

| Стаття витрат | Опис («під ключ»), ТХ / Гіперпосилання | Кількість | Ціна | Сума ({args.currency}) | Обґрунтування / Роль |
|---|---|---|---|---|---|
| 1. Обладнання | [Точні ТХ, посилання на постачальника] | | | | [Чому це критично] |
| 2. Послуги | [Опис + посилання] | | | | |
| 3. Адміндіяльність | [Бухгалтерія, логістика] | | | | |
| 4. Медіа / Промо | [Опис стратегічної кампанії] | | | | [Як це посилить імпакт] |
| **ВСЬОГО (Грант)** | | | | **{args.budget:,.2f}** | |
| **Співфінансування** | [Опис власного внеску / ресурсів] | | | | Партнерська база |

---

## 6. МАТРИЦЯ РИЗИКІВ (Синхронізована з Бюджетом)

| Ризик | Імовірність | Вплив | Стратегія мінімізації (Забезпечена ресурсами) |
|---|---|---|---|
| Логістичний / Операційний | Середня | Високий | Резерв в бюджеті, гарантійні договори постачальників |
| Затримка фінансування | Середня | Високий | Використання власного оборотного капіталу / партнерських ресурсів |
| Форс-мажор / Безпека | Низька | Високий | Гнучкий графік, віддалені формати, релокація |

---

## 7. СТІЙКІСТЬ ПІСЛЯ ЗАВЕРШЕННЯ ГРАНТУ (Sustainability)

> *(Опишіть: 1. Фінансову стійкість (знайдені інші донори або монетизація). 2. Інституційну стійкість (передача на баланс держави/громади). 3. Як проєкт продовжить роботу після завершення фінансування від {args.donor})*

---

*⚠️ Чернетка згенерована автоматично (Universal AI Orchestrator — Grant Tool v2.1). ID: {grant_id}*
*Впроваджено Універсальну Грантову Методологію. Перевірте з керівником перед подачею.*
"""
    return content, grant_id


def cmd_create(args):
    ensure_dirs()
    print(f"\n📄 Grant Tool: Генерую заявку для '{args.donor}'...")
    content, grant_id = generate_grant(args)

    md_path = GRANTS_DIR / f"{grant_id}.md"
    md_path.write_text(content, encoding="utf-8")

    meta = {
        "id": grant_id,
        "project": args.project,
        "donor": args.donor,
        "goal": args.goal,
        "budget": args.budget,
        "currency": args.currency,
        "duration_months": args.duration,
        "created": datetime.now().isoformat(),
        "status": "draft"
    }
    json_path = GRANTS_DIR / f"{grant_id}.json"
    json_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(content)
    print(f"\n✅ Заявку збережено:")
    print(f"   -> {md_path}")
    print(f"   -> {json_path}")


def cmd_list(args):
    ensure_dirs()
    grants = list(GRANTS_DIR.glob("*.json"))
    if not grants:
        print("📋 Жодної заявки не створено.")
        return
    print(f"\n📋 Грантові заявки ({len(grants)}):\n")
    for g in sorted(grants, reverse=True):
        try:
            meta = json.loads(g.read_text(encoding="utf-8"))
            print(f"  [{meta['created'][:10]}] {meta['id']}")
            print(f"     Проєкт: {meta['project']} | Донор: {meta['donor']}")
            print(f"     Бюджет: {meta['budget']:,.0f} {meta['currency']} | {meta['duration_months']} міс.")
            print()
        except Exception:
            print(f"  [ПОМИЛКА] {g.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Universal AI Orchestrator: Grant Application Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subs = parser.add_subparsers(dest="command")

    create = subs.add_parser("create", help="Створити грантову заявку")
    create.add_argument("--project", required=True, help="Назва проєкту")
    create.add_argument("--donor", required=True,
                        help="Назва донора. Підтримуються: " + ", ".join(KNOWN_DONORS.keys()) +
                             ". Або введіть будь-яку іншу назву — буде використано Universal шаблон.")
    create.add_argument("--goal", required=True, help="Мета проєкту одним реченням")
    create.add_argument("--budget", type=float, required=True, help="Загальний бюджет заявки")
    create.add_argument("--currency", default="USD",
                        help="Валюта (USD, EUR, UAH, GBP, CHF або будь-яка інша). Default: USD")
    create.add_argument("--duration", type=int, default=12, help="Тривалість у місяцях (default: 12)")

    subs.add_parser("list", help="Переглянути всі заявки")

    args = parser.parse_args()
    if args.command == "create":
        cmd_create(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()
