"""
Universal AI Orchestrator — Legal Document Tool
Автоматична генерація бізнес-документів (договори, акти, накази, NDA).

Використання:
  python legal_tool.py generate --type contract --party1 "ТОВ Альфа" --party2 "ФОП Іваненко" --subject "Надання послуг з розробки ПЗ" --amount 50000 --currency UAH
  python legal_tool.py generate --type act --party1 "ТОВ Альфа" --party2 "ФОП Іваненко" --subject "Приймання-передача роботи" --amount 15000 --currency UAH
  python legal_tool.py generate --type nda --party1 "ТОВ Альфа" --party2 "ПП Бета"
  python legal_tool.py list
"""

import argparse
import json
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / ".orchestrator" / "legal_docs"

TEMPLATES = {
    "contract": {
        "title": "ДОГОВІР ПРО НАДАННЯ ПОСЛУГ",
        "requires_amount": True,
    },
    "act": {
        "title": "АКТ ПРИЙМАННЯ-ПЕРЕДАЧІ ПОСЛУГ",
        "requires_amount": True,
    },
    "nda": {
        "title": "УГОДА ПРО НЕРОЗГОЛОШЕННЯ (NDA)",
        "requires_amount": False,
    },
    "order": {
        "title": "НАКАЗ",
        "requires_amount": False,
    },
}

def ensure_dirs():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

def generate_contract(args) -> str:
    today = date.today().strftime("%d.%m.%Y")
    doc_id = f"DOC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    title = TEMPLATES[args.type]["title"]

    amount_section = ""
    if TEMPLATES[args.type]["requires_amount"] and hasattr(args, "amount") and args.amount:
        currency = getattr(args, "currency", "UAH")
        amount_section = f"""
## 3. ВАРТІСТЬ ПОСЛУГ ТА ПОРЯДОК РОЗРАХУНКІВ

3.1. Загальна вартість послуг за цим Договором складає **{args.amount:,.2f} {currency}** (у тому числі ПДВ за ставкою, передбаченою чинним законодавством, або без ПДВ — відповідно до статусу Виконавця).

3.2. Оплата здійснюється шляхом банківського переказу на розрахунковий рахунок Виконавця протягом 5 (п'яти) банківських днів після підписання Акту приймання-передачі.
"""

    doc_content = f"""# {title}
**Документ № {doc_id}**
м. _____________                                                          «{today}»

---

## СТОРОНИ

**ЗАМОВНИК:** {args.party1}
в особі __________________________________, що діє на підставі __________________________________.

**ВИКОНАВЕЦЬ:** {args.party2}
в особі __________________________________, що діє на підставі __________________________________.

Разом іменуються «Сторони», а кожна окремо — «Сторона».

---

## 1. ПРЕДМЕТ ДОГОВОРУ

1.1. Виконавець зобов'язується надати Замовнику послуги з: **{args.subject}**

1.2. Замовник зобов'язується прийняти та оплатити надані послуги на умовах цього Договору.

1.3. Строк надання послуг: з «____» ____________ 20__ р. по «____» ____________ 20__ р.

---

## 2. ПРАВА ТА ОБОВ'ЯЗКИ СТОРІН

2.1. **Виконавець зобов'язаний:**
- Надати послуги якісно, в обумовлені строки та у повному обсязі.
- Своєчасно інформувати Замовника про обставини, які можуть вплинути на якість або строки надання послуг.

2.2. **Замовник зобов'язаний:**
- Своєчасно надати Виконавцю всі необхідні матеріали та інформацію.
- Прийняти та оплатити надані послуги відповідно до умов цього Договору.
{amount_section}
## 4. ВІДПОВІДАЛЬНІСТЬ СТОРІН

4.1. За невиконання або неналежне виконання умов цього Договору Сторони несуть відповідальність відповідно до чинного законодавства України.

4.2. Жодна із Сторін не несе відповідальності за невиконання своїх зобов'язань, якщо таке невиконання є наслідком форс-мажорних обставин.

---

## 5. КОНФІДЕНЦІЙНІСТЬ

5.1. Умови цього Договору є конфіденційними. Сторони зобов'язуються не розголошувати їх третім особам без письмової згоди іншої Сторони.

---

## 6. СТРОК ДІЇ ДОГОВОРУ

6.1. Цей Договір набирає чинності з моменту підписання обома Сторонами і діє до повного виконання Сторонами своїх зобов'язань.

---

## ПІДПИСИ СТОРІН

*Документ є чернеткою. Перевірте з юридичним відділом перед підписанням.*

| ЗАМОВНИК | ВИКОНАВЕЦЬ |
|:---|---:|
| {args.party1} | {args.party2} |
| __________________________ | __________________________ |
| (підпис, П.І.Б.)                 | (підпис, П.І.Б.)                 |
| «____» ____________ 20__ р. | «____» ____________ 20__ р. |

---
*⚠️ Чернетка згенерована автоматично модулем Universal AI Orchestrator (Legal Tool). Документ № {doc_id}*
"""
    return doc_content, doc_id

def cmd_generate(args):
    ensure_dirs()
    if args.type not in TEMPLATES:
        print(f"❌ Невідомий тип документу: '{args.type}'. Доступні: {', '.join(TEMPLATES.keys())}")
        return

    print(f"\n⚖️ Legal Tool: Генерую '{TEMPLATES[args.type]['title']}'...")
    content, doc_id = generate_contract(args)

    md_path = DOCS_DIR / f"{doc_id}.md"
    md_path.write_text(content, encoding="utf-8")

    meta = {
        "id": doc_id,
        "type": args.type,
        "title": TEMPLATES[args.type]["title"],
        "party1": args.party1,
        "party2": args.party2,
        "subject": args.subject if hasattr(args, "subject") and args.subject else "",
        "amount": args.amount if hasattr(args, "amount") and args.amount else 0,
        "currency": args.currency if hasattr(args, "currency") and args.currency else "UAH",
        "created": datetime.now().isoformat(),
        "status": "draft"
    }
    json_path = DOCS_DIR / f"{doc_id}.json"
    json_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(content)
    print(f"\n✅ Документ збережено:")
    print(f"   -> {md_path}")
    print(f"   -> {json_path}")
    print(f"\n⚠️  Нагадування: Це чернетка. Перед підписанням перевірте з юридичною службою.")

def cmd_list(args):
    ensure_dirs()
    docs = list(DOCS_DIR.glob("*.json"))
    if not docs:
        print("📋 Жодного документу не створено.")
        return
    print(f"\n📋 Юридичні документи ({len(docs)}):\n")
    for d in sorted(docs, reverse=True):
        try:
            meta = json.loads(d.read_text(encoding="utf-8"))
            print(f"  [{meta['created'][:10]}] {meta['id']} | {meta['title']}")
            print(f"     {meta['party1']} ↔ {meta['party2']}")
            if meta.get("amount"):
                print(f"     Сума: {meta['amount']:,.2f} {meta['currency']}")
            print()
        except Exception:
            print(f"  [ПОМИЛКА ЧИТАННЯ] {d.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Universal AI Orchestrator: Legal Document Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subs = parser.add_subparsers(dest="command")

    gen = subs.add_parser("generate", help="Згенерувати документ")
    gen.add_argument("--type", required=True, choices=list(TEMPLATES.keys()), help="Тип документу")
    gen.add_argument("--party1", required=True, help="Сторона 1 (Замовник / Компанія)")
    gen.add_argument("--party2", required=True, help="Сторона 2 (Виконавець / Партнер)")
    gen.add_argument("--subject", default="", help="Предмет договору/акту")
    gen.add_argument("--amount", type=float, default=0, help="Сума (якщо є)")
    gen.add_argument("--currency", default="UAH", choices=["UAH", "USD", "EUR"], help="Валюта")

    subs.add_parser("list", help="Переглянути всі документи")

    args = parser.parse_args()
    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()
