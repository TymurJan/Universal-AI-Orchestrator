import os
import json
import shutil
import hashlib
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Request
from pydantic import BaseModel
from typing import Optional

# Імітація майбутнього сервера для AI-Чату
# Цей файл є заготовкою (boilerplate) для розгортання RAG-системи.
# Потребує: pip install fastapi uvicorn openai

app = FastAPI(title="Novy Shlyakh AI Backend", version="1.0.0")

class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"

class ChatResponse(BaseModel):
    reply: str
    sources: list = []

# Завантаження бази спеціалістів при старті
SPECIALISTS_DB = []
try:
    with open('data/specialists.json', 'r', encoding='utf-8') as f:
        SPECIALISTS_DB = json.load(f)
except FileNotFoundError:
    print("WARNING: Database not found. Fallback mode.")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Головний ендпоінт для спілкування з чатом на сайті.
    Коли з'явиться фінансування, тут буде додано логіку:
    1. Перетворення req.message на вектор.
    2. Пошук у Pinecone/Supabase.
    3. Звернення до OpenAI API.
    """
    
    # ІМІТАЦІЯ ВІДПОВІДІ (Stub)
    user_msg = req.message.lower()
    
    # Демонстрація реакції на ключові слова
    if "убд" in user_msg or "закон" in user_msg:
        reply = "Згідно з чинним законодавством України (Закон про статус ветеранів), ви маєте право на пільги. Детальну консультацію може надати наш юрист."
        sources = ["Закон України № 3551-XII"]
    elif "бізнес" in user_msg or "грант" in user_msg:
        reply = "Ви можете податися на державну програму «Власна справа». Вам може допомогти наша бізнес-ментор Ганна Грант."
        sources = ["Постанова КМУ № 738", "Ганна Грант (Ментор)"]
    else:
        reply = "Я AI-координатор центру «Новий Шлях». Я можу допомогти знайти потрібного спеціаліста або дати довідку по законодавству. Чим можу бути корисним?"
        sources = []

    return ChatResponse(reply=reply, sources=sources)

# ─── Тексти угод (версія v1.0 від 2026-06-09) ─────────────────────────────
# При зміні тексту — змінювати CONSENT_VERSION!
CONSENT_VERSION = "v1.0"

CONSENT_PRIVACY_TEXT = """ПОЛІТИКА КОНФІДЕНЦІЙНОСТІ — ГО «ТАЛАН ЮА» / Проєкт «Новий Шлях»

1. Загальні положення
Ця Політика конфіденційності описує, як ГРОМАДСЬКА ОРГАНІЗАЦІЯ «ТАЛАН ЮА» збирає,
використовує та захищає персональні дані користувачів порталу «Новий Шлях».
Ми дотримуємося вимог Закону України «Про захист персональних даних» та принципів GDPR.

2. Які дані ми збираємо
- Для спеціалістів: ПІБ, номер телефону, спеціалізація, адреса кабінету, опис досвіду,
  фото профілю, копії документів про освіту (PDF).
- Для ветеранів: Ми не зберігаємо персональні дані ветеранів на Порталі без їхньої прямої згоди.

3. Мета обробки даних
Верифікація кваліфікації спеціаліста та забезпечення зв'язку з отримувачами допомоги.

4. Ваші права
Ви маєте право на доступ до своїх даних, їх зміну або видалення (Право на забуття).
Email для зв'язку: ngo.talan.ua@gmail.com"""

CONSENT_AGREEMENT_TEXT = """УГОДА ПРО СПІВПРАЦЮ — Проєкт підтримки ветеранів «Новий Шлях»

1. Предмет угоди
Спеціаліст погоджується розмістити свою анкету на порталі для надання послуг ветеранам
та їхнім родинам.

2. Фінансові умови та Статутна діяльність
- Спеціаліст погоджується нарахувати адміністративний внесок на статутну діяльність ГО
  від суми платних послуг, отриманих через Портал.
- Кошти спрямовуються на технічне обслуговування порталу та соціальні проєкти Організації.

3. Верифікація та Припинення
Спеціаліст погоджується надати документи для перевірки.
У разі видалення профілю угода припиняється негайно."""


def _generate_consent_doc(
    name: str,
    tg_id: str,
    phone: str,
    category: str,
    address: str,
    ip_address: str,
    consent_at: str,
    tariff_plan: str,
    contract_end_date: Optional[str] = None,
    court_cases: int = 0,
    team_work: int = 0,
    avg_service_price: Optional[str] = None,
) -> str:
    """
    Генерує текст Consent Receipt (підтвердження згоди) за стандартом GDPR.
    Повертає рядок Markdown для збереження у файл.
    """
    
    # 1. Формуємо фінансові умови та тарифний опис відповідно до обраного плану (3 Зони)
    financial_terms = ""
    
    # Зона 1 — Приватні фахівці (сесійна модель)
    if tariff_plan == "grant_standard":
        end_date_str = contract_end_date if contract_end_date else "протягом 12 місяців з моменту підписання"
        financial_terms = f"""### ТАРИФНИЙ ПЛАН: «Грантовий» — Зона 1 (Етап 1: Грантовий період)
- **Фіксована плата**: $0 / місяць
- **Комісія платформи**: 0%
- **Знижка ветерану**: 10% (обов'язкова знижка з власного тарифу фахівця)
- **Опис**: Участь у платформі безкоштовна. Фахівець будує репутацію без жодних фінансових відрахувань.
- **Дата закінчення договору**: {end_date_str}"""

    elif tariff_plan == "zone1_stable":
        financial_terms = """### ТАРИФНИЙ ПЛАН: «Стабільний» — Зона 1 (Етап 2: Перехід / Постійна співпраця)
- **Фіксована плата**: $30 / місяць (перехідний, місяці 13–24), $50 / місяць (постійний, місяць 25+)
- **Комісія з сесій через портал**: 5%
- **Знижка ветерану**: 10% (обов'язкова умова)
- **Точка беззбитковості**: ~6 сесій/міс (перехідний) / ~10 сесій/міс (постійний)
- **Порядок оплати**: Фіксована частина сплачується до 5-го числа кожного місяця.
- **Повернення коштів**: Фіксована частина за поточний місяць поверненню не підлягає."""

    elif tariff_plan == "zone1_flexible":
        financial_terms = """### ТАРИФНИЙ ПЛАН: «Гнучкий» — Зона 1 (Етап 2: Перехід / Постійна співпраця)
- **Фіксована плата**: $0 / місяць
- **Комісія з сесій через портал**: 10% (перехідний), 15% (постійний, місяць 25+)
- **Знижка ветерану**: 10% (обов'язкова умова)
- **Точка беззбитковості**: відсутня (комісія нараховується лише з фактичних транзакцій)
- **Порядок оплати**: Якщо сесій немає — платіж відсутній. Підходить для фахівців із змінним навантаженням.
- **Мінімальний платіж**: $0"""

    # Зона 2 — Юристи, адвокати, протезисти (фіксована підписка)
    elif tariff_plan == "zone2a_consultant":
        financial_terms = """### ТАРИФНИЙ ПЛАН: «Зона 2а: Юрист-консультант»
- **Грантовий етап (місяці 1–12)**: $0 / місяць, 0% комісія
- **Перехідний етап (місяці 13–24)**: $50 / місяць + 5% комісія
- **Постійна співпраця (місяць 25+)**: $100 / місяць + 5% комісія
- **Знижка ветерану**: 10% (обов'язкова умова)
- **Порядок оплати**: Фіксована частина сплачується до 5-го числа кожного місяця.
- **Повернення коштів**: При достроковому розірванні фіксована частина поточного місяця поверненню не підлягає."""

    elif tariff_plan == "zone2b_practitioner":
        financial_terms = """### ТАРИФНИЙ ПЛАН: «Зона 2б: Адвокат-практик (судовий супровід)»
- **Грантовий етап (місяці 1–12)**: $0 / місяць, 0% комісія
- **Перехідний етап (місяці 13–24)**: $50 / місяць
- **Постійна співпраця (місяць 25+)**: $100 / місяць
- **Комісія з справ**: 0% (фіксована підписка без % від виграшу)
- **Знижка ветерану**: 10% рекомендована (для судового супроводу — на розсуд адвоката)
- **Порядок оплати**: Фіксована частина сплачується до 5-го числа кожного місяця.
- **Повернення коштів**: Фіксована частина за поточний місяць поверненню не підлягає."""

    elif tariff_plan == "zone2c_bureau":
        financial_terms = """### ТАРИФНИЙ ПЛАН: «Зона 2в: Адвокатське бюро / Протезний центр»
- **Грантовий етап (місяці 1–12)**: $0 / місяць
- **Перехідний етап (місяці 13–24)**: $100 / місяць
- **Постійна співпраця (місяць 25+)**: $150 / місяць
- **Комісія з сесій через портал**: 0%
- **Знижка ветерану**: Надається на власний розсуд установи.
- **Опис**: Розширений профіль установи: логотип, команда, перелік послуг, скарговий механізм.
- **Порядок оплати**: Фіксована частина сплачується до 5-го числа кожного місяця.
- **Мінімальний платіж**: $0 (грант) / $100 (перехід) / $150 (постійно)"""

    # Зона 3 — Реабілітаційні центри, клініки, центри (установи)
    elif tariff_plan in ("zone3_bureau", "zone3_state"):
        financial_terms = """### ТАРИФНИЙ ПЛАН: «Зона 3: Реабілітаційний центр / Клініка / Центр»
- **Грантовий етап (місяці 1–12)**: $0 / місяць
- **Перехідний етап (місяці 13–24)**: $100 / місяць
- **Постійна співпраця (місяць 25+)**: $150 / місяць
- **Комісія**: 0%
- **Опис**: Інституційний профіль з розширеним описом, командою та скарговим механізмом.
- **Порядок оплати**: До 5-го числа кожного місяця."""

    # Зона 4 — ГО та благодійні фонди
    elif tariff_plan == "zone4_ngo":
        financial_terms = """### ТАРИФНИЙ ПЛАН: «Зона 4: Громадська організація / Благодійний фонд»
- **Фіксована плата**: $0 (безкоштовно після верифікації Координаційною Радою)
- **Комісія платформи**: 0%
- **Умова доступу**: Рішення Координаційної Ради ГО «Талан ЮА» + надання статутних документів.
- **Опис**: Безкоштовний партнерський профіль для підтримки ветеранської екосистеми."""

    # Зона 5 — Державні структури
    elif tariff_plan == "zone5_state":
        financial_terms = """### ТАРИФНИЙ ПЛАН: «Зона 5: Державна структура / ОМС / ЦНАП»
- **Фіксована плата**: $0 (безкоштовно за рішенням Ради)
- **Комісія платформи**: 0%
- **Знижка ветерану**: Не застосовується (послуги надаються в межах держфінансування)
- **Опис**: Інформаційний профіль установи (ТЦК, ЦНАП, соцслужби тощо) за рішенням Координаційної Ради."""

    else:
        financial_terms = "### ТАРИФНИЙ ПЛАН: Невизначений\nУмови згідно з регламентом платформи."

    # 2. Намагаємося завантажити шаблон договору
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(os.path.dirname(backend_dir), "talan", "autobot", "templates", "contract_specialist.md")
    
    agreement_text = ""
    if os.path.exists(template_path):
        try:
            with open(template_path, "r", encoding="utf-8") as tf:
                agreement_text = tf.read()
            # Заміна плейсхолдерів
            end_date_str = contract_end_date if contract_end_date else "протягом 12 місяців з моменту підписання (або до зміни етапу)"
            agreement_text = agreement_text.replace("[ДАТА_ЗАВЕРШЕННЯ]", end_date_str)
            agreement_text = agreement_text.replace("[ФІНАНСОВІ_УМОВИ]", financial_terms)
        except Exception as te:
            agreement_text = f"Помилка завантаження шаблону договору: {te}"
    
    # Якщо шаблон порожній — використовуємо fallback
    if not agreement_text:
        agreement_text = f"Угода про співпрацю для тарифного плану {tariff_plan}.\n\n{financial_terms}"

    # Хеш тексту угод — дозволяє довести, що саме цей текст підписали
    privacy_hash = hashlib.sha256(CONSENT_PRIVACY_TEXT.encode()).hexdigest()[:16]
    agreement_hash = hashlib.sha256(agreement_text.encode()).hexdigest()[:16]

    return f"""# ПІДТВЕРДЖЕННЯ ЗГОДИ (Consent Receipt)
## Портал «Новий Шлях» | ГО «ТАЛАН ЮА»

---

## ДАНІ ПІДПИСАНТА

| Поле              | Значення                          |
|-------------------|-----------------------------------|
| ПІБ               | {name}                            |
| Telegram ID       | {tg_id}                           |
| Телефон           | {phone}                           |
| Категорія         | {category}                        |
| Адреса / Онлайн   | {address}                         |

## ФАКТ ПІДПИСАННЯ

| Поле              | Значення                          |
|-------------------|-----------------------------------|
| Дата та час (UTC) | {consent_at}                      |
| IP-адреса         | {ip_address}                      |
| Версія документів | {CONSENT_VERSION}                 |
| Метод підтвердження | Checkbox (WebApp Telegram)      |
| Тарифний план     | {tariff_plan}                     |
| Дата закінчення   | {contract_end_date or "Не вказано"} |

## ДОКУМЕНТИ, З ЯКИМИ ПОГОДИВСЯ СПЕЦІАЛІСТ

### [✓] 1. Політика конфіденційності (SHA-256: {privacy_hash}...)

{CONSENT_PRIVACY_TEXT}

---

### [✓] 2. Угода про співпрацю (SHA-256: {agreement_hash}...)

{agreement_text}

---

*Цей документ згенеровано автоматично системою порталу «Новий Шлях».*
*Зберігається як юридичний доказ згоди відповідно до ст. 7 Регламенту ЄС 2016/679 (GDPR)*
*та Закону України «Про захист персональних даних» № 2297-VI.*
""", agreement_text


@app.post("/api/register-specialist")
async def register_specialist(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    bio: str = Form(...),
    tg_id: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    document: UploadFile = File(...),
    kep_file: Optional[UploadFile] = File(None),
    kep_password: Optional[str] = Form(None),
    
    # Нові тарифні та анкетні поля
    court_cases: Optional[int] = Form(0),
    team_work: Optional[int] = Form(0),
    avg_service_price: Optional[str] = Form(None),
    tariff_plan: Optional[str] = Form("grant_standard"),
    contract_end_date: Optional[str] = Form(None),
):
    """
    Ендпоінт для фінальної реєстрації спеціаліста (Крок 2).

    Створює per-specialist папку, зберігає файли та генерує
    Consent Receipt (підтвердження згоди) відповідно до GDPR / ЗУ «Про захист ПД».
    """
    try:
        # 1. Визначаємо унікальний ідентифікатор спеціаліста
        spec_id = tg_id or f"anon_{abs(hash(phone))}"

        # 2. Створюємо per-specialist папку
        spec_dir = os.path.join("uploads", "specialists", spec_id)
        os.makedirs(spec_dir, exist_ok=True)

        # 3. Зберігаємо фото
        photo_ext = os.path.splitext(photo.filename or "photo.jpg")[1] or ".jpg"
        photo_path = os.path.join(spec_dir, f"photo{photo_ext}")
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        # 4. Зберігаємо диплом / ліцензію
        doc_ext = os.path.splitext(document.filename or "document.pdf")[1] or ".pdf"
        doc_path = os.path.join(spec_dir, f"diploma{doc_ext}")
        with open(doc_path, "wb") as buffer:
            shutil.copyfileobj(document.file, buffer)

        # 5. Розраховуємо параметри тарифу
        tariff_stage = "stage_1"
        tariff_fixed_fee = 0.0
        tariff_commission_pct = 0.0
        
        if tariff_plan == "grant_standard":
            tariff_stage = "stage_1"
            tariff_fixed_fee = 0.0
            tariff_commission_pct = 0.0
        elif tariff_plan == "zone1_flexible":
            tariff_stage = "stage_3"
            tariff_fixed_fee = 0.0
            tariff_commission_pct = 10.0
        elif tariff_plan == "zone2a_consultant":
            tariff_stage = "stage_3"
            tariff_fixed_fee = 60.0
            tariff_commission_pct = 5.0
        elif tariff_plan == "zone2b_practitioner":
            tariff_stage = "stage_3"
            tariff_fixed_fee = 60.0
            tariff_commission_pct = 0.0
        elif tariff_plan == "zone2c_bureau":
            tariff_stage = "stage_3"
            tariff_fixed_fee = 100.0
            tariff_commission_pct = 0.0
        elif tariff_plan == "zone3_state":
            tariff_stage = "stage_3"
            tariff_fixed_fee = 0.0
            tariff_commission_pct = 0.0

        # 6. Генеруємо Consent Receipt і зберігаємо в папку спеціаліста
        consent_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        consent_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ip_address = request.client.host if request.client else "unknown"

        consent_text, agreement_text = _generate_consent_doc(
            name=name,
            tg_id=spec_id,
            phone=phone,
            category=category,
            address=address,
            ip_address=ip_address,
            consent_at=consent_at,
            tariff_plan=tariff_plan,
            contract_end_date=contract_end_date,
            court_cases=court_cases,
            team_work=team_work,
            avg_service_price=avg_service_price,
        )
        consent_filename = f"consent_{consent_date}.md"
        consent_path = os.path.join(spec_dir, consent_filename)
        with open(consent_path, "w", encoding="utf-8") as f:
            f.write(consent_text)

        # 7. (Опційно) КЕП-підпис consent-документа
        kep_signature_path = None
        kep_signed = False
        if kep_file and kep_file.filename:
            try:
                import sys
                sys.path.insert(0, os.path.dirname(__file__))
                from kep_signer import sign_consent_document
                kep_bytes = await kep_file.read()
                kep_pwd = kep_password or ""
                kep_signature_path = sign_consent_document(
                    consent_file_path=consent_path,
                    p12_bytes=kep_bytes,
                    password=kep_pwd,
                )
                kep_signed = True
            except Exception as kep_err:
                kep_signature_path = None

        # 8. Зберігаємо в SQLite через db_manager
        try:
            import sys
            sys.path.insert(0, os.path.dirname(__file__))
            import db_manager
            db_manager.add_specialist({
                "name": name,
                "category": category,
                "role": category,
                "phone": phone,
                "address": address,
                "bio": bio,
                "tg_id": spec_id,
                "status": "pending",
                "photo_path": photo_path,
                "document_path": doc_path,
                "consent_doc_path": consent_path,
                "consent_at": consent_at,
                "kep_signature_path": kep_signature_path,
            })
        except Exception as db_err:
            print(f"\u26a0\ufe0f DB warning (non-critical): {db_err}")

        # 8. JSON-бекап (сумісність зі старим фронтендом)
        db_path = os.path.join("data", "specialists.json")
        os.makedirs("data", exist_ok=True)
        current_db = []
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                current_db = json.load(f)

        current_db.append({
            "id": spec_id,
            "name": name,
            "category": category,
            "phone": phone,
            "address": address,
            "bio": bio,
            "photo_url": photo_path,
            "doc_url": doc_path,
            "consent_doc": consent_path,
            "consent_at": consent_at,
            "kep_signed": kep_signed,
            "status": "pending",
            "rating": "5.0",
            "reviews": []
        })
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(current_db, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "message": "Заявка прийнята на модерацію",
            "specialist_folder": spec_dir,
            "consent_doc": consent_path,
            "kep_signed": kep_signed,
            "kep_signature": kep_signature_path,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "Novy Shlyakh AI Ready"}

if __name__ == "__main__":
    import uvicorn
    # Запуск: python server.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
