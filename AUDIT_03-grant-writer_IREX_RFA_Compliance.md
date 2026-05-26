# 🔍 ДЕТАЛЬНИЙ АУДИТ СКІЛУ `.agents:03-grant-writer` vs IREX RFA (Регіональна координація)
**Дата аудиту:** 24 травня 2026 р.  
**Версія скілу:** SKILL.md + Talan_Grant_Methodology.md + generate_irex_docs.py  
**Предмет:** Заявка «Новий Шлях» (IREX конкурс на регіональну координацію ветеранів)

---

## 1️⃣ МЕТОДОЛОГІЯ "КРОК А + КРОК Б" — Перевірка застосування

### Крок А (Локальні примітки з форми IREX):
**Розташування:** template_dump.txt (витягнуто з форми шаблону)

#### Знайдені вимоги Крок А:
| Пункт | Вимога в формі | Скіл перевірив? |
|:---:|:---|:---|
| 2. Objectives | "SMART principles" + логічні зв'язки | ✅ Частково |
| 3. Target Audience | "Include information on... number of NGOs and other stakeholders" | ❌ Проминуто |
| 4. Partnerships | "Include... memorandums of understanding and letters of support" | ✅ Так |
| 9. Sustainability | "Without reliance on external funding" | ✅ Так |
| 10. Key Personnel | "Experience in similar projects" + CV | ❌ Відсутній |
| 11. Internal Management | "References from donor organizations" | ❌ Не було |
| 12. Potential Risks | "Both risks AND mitigation plans" | ✅ Так |
| 14. Monitoring Plan | "Quantitative AND qualitative indicators" | ✅ Так |

**Висновок Крок А:** Скіл витягнув ~60% локальних вимог. **Дефіцити:** CV персоналу, рекомендації від донорів, деталізація NGO кількості.

### Крок Б (Глобальні рекомендації з RFA документу):
**Розташування:** UKR RFA_UVRR_Regional_Coordination.docx (витягнуто в template_dump.txt)

#### КРИТИЧНІ вимоги Крок Б, які скіл мав застосувати:

| Пункт RFA | Опис | Застосовано в заявці? | Рівень виконання |
|:---:|:---|:---|:---|
| **P12 (Objectives)** | "SMART + Логічні зв'язки між цілями → результатами" | ✅ Так | 🟡 60% (SMART є, але логіка не явна) |
| **P14 (Target Audience)** | "Include information on... NGOs... that will participate" | ✅ Так | 🟡 50% (названо 5 ГО, але без конкретних чисел) |
| **P15 (Partnerships)** | "Describe sustainability of partnerships + govt engagement" | ✅ Частково | 🔴 40% (Меморандуми обіцяні, але не підписані) |
| **P23 (Activities Framework)** | "Outputs vs Outcomes (обов'язково розрізняти)" | ✅ Так | 🟢 85% |
| **P29 (Sustainability)** | "FORMALIZED in existing systems" + "Embedded in local governance" | ❌ **КРИТИЧНО ПРОПУЩЕНО** | 🔴 20% |
| **P48 (Key Personnel)** | "Provide experience in similar projects" + CV | ✅ Частково | 🟡 50% (Анна Сакун має CV, інші — шорт-ліст) |
| **P62 (Donor References)** | "References from donor organizations" | ❌ **КРИТИЧНО ПРОПУЩЕНО** | 🔴 0% |

**Висновок Крок Б:** Скіл пропустив **2 КРИТИЧНІ вимоги:**
1. **Sustainability formalization** — мав бути детальний план інтеграції у державні системи
2. **Donor references** — мали бути рекомендації від IREX/USAID партнерів

---

## 2️⃣ СПЕЦИФІЧНІ ВИМОГИ IREX за пунктам

### ✅ Пункт 3 (Objectives) — SMART-аналіз

**Скіл перевірив SMART?** Частково.

#### Твердження скілу (SKILL.md, рядок 45):
> "Глибокий аналіз тексту над кожним пунктом форми за SMART-методологією"

#### Реальні Objectives у заявці:

| Objective | S (Specific) | M (Measurable) | A (Achievable) | R (Relevant) | T (Time-bound) | SMART? |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| O1: 150+ фахівців | ✅ | ✅ | ✅ | ✅ | ✅ | 🟢 Так |
| O2: SQLite + AI модуль | ✅ | ⚠️ (дифузне) | ✅ | ✅ | ✅ | 🟡 Частково |
| O3: Intake-хаб (1-2 прийомів/день) | ✅ | ✅ | ⚠️ (реалістично?) | ✅ | ✅ | 🟡 Частково |
| O4: 5 координаційних заходів | ✅ | ✅ | ✅ | ✅ | ✅ | 🟢 Так |

**Проблема:** O2 і O3 мають нечіткі метрики для IT та фізичної роботи.

---

### 🔴 Пункт 6 (Key Personnel) — CV ПРОМИНУТО

**Вимога RFA (P51-52):**
> "Provide information about the team that will implement the project"
> **Очікується:** Таблиця з посадами, назвами, досвідом, ролями, % навантаження

#### Що було в заявці (generate_irex_docs.py, рядки 316-336):

| Персона | CV наявне? | Роль | % |
|:---|:---:|:---|:---:|
| Тимур Шаповал (Project Lead) | ❌ Не повний | Голова правління | 50% |
| Анна Сакун (PR Lead) | ✅ Премія Гаврилишина | Комунікації | 50% |
| Фінансовий менеджер | ❌ "За шорт-листом" | Бухгалтерія | 30% |
| IT архітектор | ❌ "Штатний фахівець" | DevOps/AI | 50% |

**Дефіцит:** Відсутні докладні CV для 3 з 4 персон. **RFA вимагав** прикріпити CV як додаток.

---

### 🔴 Пункт 10 (Budget) — Narrative ВІДСУТНЯ

**Вимога IREX:** Детальний бюджетний narrative (не лише цифри в таблиці).

#### Що містить generate_irex_docs.py (рядки 516-572):
- ✅ Основна таблиця ($100,000 розбито на 6 категорій)
- ✅ Описи статей (текстові обґрунтування)
- ❌ **Відсутня:** Детальна розшифровка "кількість × ціна = сума" з посиланнями на ринкові ціни

**Приклад дефіциту:**
```
Заявка: "PR та Поліграфія: $15,000"
Ринкова ціна повинна була: 
  - 100 плакатів А3 (300 гр/м2) = ~$1,500
  - 1,000 буклетів = ~$3,000
  - 5 павуків = ~$2,500
  - SMM-реклама = $7,000
  = $14,000 ✅ (близько)
```

**Проблема:** У заявці НЕ БУЛИ вказані посилання на конкретні товари/цени.

---

### 🔴 Пункт 4 (Partnerships) — Partner Letters

**Вимога RFA (P16, P27):**
> "Indicate any existing memorandums of understanding and/or letters of support attached"
> Мінімум: 7-10 Partner Letters

#### Що було згенеровано (generate_irex_docs.py, рядки 475-511):

```python
partners = [
    "02_Letter_of_Support_Cherkasy_City_Council",
    "03_Letter_of_Support_DF_Cherkasy_TG",
    "04_Letter_of_Support_NGO_Cherkasy_City_Institute",
    "05_Letter_of_Support_NGO_Horizon_of_Change",
    "06_Letter_of_Support_Veteran_Pro"
]
```

**Кількість:** 5 листів (з 7-10 мінімуму).

**Статус листів:** ❌ **Шаблони, не підписані** (placeholder: "ІМ'Я ПРІЗВИЩЕ")

---

## 3️⃣ НЕДОЛІКИ В IREX ЗАЯВЦІ (Що скіл пропустив?)

### 🔴 КРИТИЧНІ (Red Flags, які скіл МУСИВ попередити):

| Недолік | Розташування | Скіл попередив? | Вплив |
|:---|:---|:---:|:---|
| **Risk Assessment неповна** | Пункт 12 (Potential Risks) | ❌ Ні | 🔴 Критично |
| **M&E Framework відсутня** | Пункт 14 (Monitoring Plan) | ⚠️ Частково | 🔴 Критично |
| **CV персоналу не приєднані** | Пункт 10 | ❌ Ні | 🟡 Важливо |
| **Partner Letters не підписані** | Додатки | ❌ Ні | 🟡 Важливо |
| **Бюджетні references відсутні** | Пункт 10 Budget | ❌ Ні | 🟡 Важливо |
| **Donor references нема** | Пункт 11 | ❌ Ні | 🟡 Важливо |

#### Деталь 1: Risk Assessment — ЩО ПРОПУЩЕНО?

**RFA вимагає (P74):** Risks + Mitigation Plans

**У заявці (generate_irex_docs.py, рядки 350-364) є 3 ризики:**
1. ✅ Ескалація військових дій (HIGH)
2. ✅ Низька активність фахівців (MEDIUM)
3. ✅ Скептицизм ветеранів (MEDIUM)

**Пропущені ризики, які мав включити скіл:**
- ❌ **Технічні ризики:** Видалення даних, DDoS-атаки, заморозка Telegram API
- ❌ **Фінансові ризики:** Валютні коливання (USD), затримка платежів
- ❌ **Управлінські ризики:** Плинність персоналу, конфлікти в координаційній раді
- ❌ **Законодавчі ризики:** Зміни в законодавстві про захист персональних даних (GDPR)

#### Деталь 2: M&E Framework — ЩО ТОЧНО ПРОПУЩЕНО?

**RFA вимагає (P82):** Таблиця з:
- Quantitative indicators (output level)
- Qualitative indicators (outcome level)
- **Long-term impact indicators** (після завершення проєкту)
- Методи збору даних

**У заявці (generate_irex_docs.py, рядки 377-423) є таблиця Monitoring Plan, але:**

| Елемент | Наявне? | Якість |
|:---|:---:|:---|
| Output indicators (к-сть верифікованих фахівців) | ✅ | 🟢 Хороша |
| Outcome indicators (% активних спеціалістів) | ✅ | 🟢 Хороша |
| **Impact indicators** | ❌ | 🔴 ВІДСУТНІ |
| Data collection methods | ⚠️ | 🟡 Базові (бази даних + логи) |
| **Qualitative validation** | ❌ | 🔴 ВІДСУТНЯ |

**Приклад впущеного Impact indicator:**
```
Impact (12+ місяців після проєкту):
- % координаційних механізмів, які залишилися активними без гранту
- Кількість нових ветеранів, залучених після завершення фінансування
- Коефіцієнт інституціоналізації (чи платформа була інтегрована в ОТГ системи)
```

---

## 4️⃣ COMPLIANCE MAPPING (Таблиця відповідності)

**Формат:** Пункт заявки → Вимога RFA → Виконано → Якість

| # | Пункт | Вимога IREX | У заявці | Скіл перевірив? | % Виконання |
|:---:|:---:|:---|:---:|:---:|:---:|
| **1** | Summary (до 400 слів) | Короткий опис проєкту | 📄 370 слів | ✅ | 90% |
| **2** | Objectives & Outcomes | SMART + Логічні зв'язки | ✅ 4 ObjectivesOUTPUT-OUTCOME таблиця | ⚠️ | 70% |
| **3** | Target Audience | NGO кількість + статистика | ✅ 2,500+ ветеранів, 15+ ГО | ✅ | 75% |
| **4** | Partnerships | MoUs + Letters of Support | ✅ 5 листів (шаблон) | ⚠️ | 50% |
| **5** | Coordination Mechanism | Мандат, роль, структура, sustainability | ✅ Детально описано | ✅ | 85% |
| **6** | Activities & Outputs | Детальна матриця активностей | ✅ Таблиця з 2 завданнями | ✅ | 80% |
| **7** | Implementation Timeline | Ганта-диаграма помісячно | ✅ Теоретично (шаблон IREX) | ⚠️ | 60% |
| **8** | Organization Experience | Досвід (3 роки),협ordination examples | ✅ Військова логістика | ⚠️ | 65% |
| **9** | Sustainability | Формалізація + Інституціоналізація | ⚠️ Планується, не гарантовано | ⚠️ | 55% |
| **10** | Key Personnel | CV + Досвід + Ролі + % навантаження | ✅ Таблиця, але CV не приєднані | ❌ | 50% |
| **11** | Internal Management | Donor references + Experience з грантами | ⚠️ Є опис процедур, но references нема | ❌ | 60% |
| **12** | Potential Risks | Risks + Mitigation | ✅ 3 ризики | ⚠️ | 60% |
| **13** | Communication & Outreach | Channels + Goals | ✅ 3 рішення | ✅ | 80% |
| **14** | Monitoring Plan | Output + Outcome + методи | ✅ Таблиця, але не full M&E | ⚠️ | 65% |
| **15** | Budget | Детальне обґрунтування + references | ✅ Таблиця, але no market links | ❌ | 60% |

**ЗАГАЛЬНА ОЦІНКА COMPLIANCE:** 67% (ЗАДОВІЛЬНО, але з КРИТИЧНИМИ ДЕФІЦИТАМИ)

---

## 5️⃣ ДЕФІЦИТИ СКІЛУ `.agents:03-grant-writer`

### 🔴 БАЗОВІ ДЕФІЦИТИ:

| Дефіцит | Опис | Рівень | Рішення |
|:---|:---|:---:|:---|
| **Крок Б не реалізований** | Скіл не читає RFA документи + не витягує глобальні вимоги | 🔴 CRÍTICO | Додати парс RFA documento у скіл |
| **CV Management не вбудований** | Скіл не перевіряє наявність CV | 🔴 CRÍTICO | Створити модуль CV validation |
| **Impact Indicators missing** | Скіл генерує Output/Outcome, але не Impact | 🟡 ВАЖЛИВО | Додати long-term indicators logic |
| **Budget narrative не автоматизована** | Скіл не генерує посилання на конкретні товари | 🟡 ВАЖЛИВО | Додати market research module |
| **Donor References check** | Скіл не запитує reference letters | 🟡 ВАЖЛИВО | Додати donor validation workflow |
| **Red Flag system відсутня** | Скіл не видає попередження про критичні недоліки | 🔴 CRÍTICO | Додати automated compliance checker |

### 🟡 ПРОЦЕСНІ ДЕФІЦИТИ:

1. **Partner Letters Template** — скіл генерує шаблони, але:
   - ❌ Не запитує реальні підписи (placeholder: "ІМ'Я ПРІЗВИЩЕ")
   - ❌ Не перевіряє наявність MoUs від партнерів
   - ⚠️ Не напоумінає про дедлайн збору листів

2. **Timeline validation** — скіл не перевіряє реалістичність терміну:
   - ✅ Вказано 12 місяців реалізації
   - ❌ Але чи розумно це для 150+ фахівців + IT-розробки + 5 заходів?

3. **Budget-to-Activity mapping** — скіл не перевіряє логічні зв'язки:
   - `$20,000 на IT` ← чи достатньо для SQLite + AI модуля + GDPR?
   - `$15,000 на офлайн хаб` ← включає оренду за 12 місяців?

---

## 6️⃣ ЯК СКІЛ ЗАСТОСОВУВАТИМЕ ЦЕ ДЛЯ ІНШИХ ДОНОРІВ?

### Універсальний алгоритм vs IREX-специфіка:

**Скіл ЗНАЄ про універсальність (SKILL.md, рядок 30):**
> "Агент НЕ прив'язаний до конкретного проєкту чи донора — він знає методологію та адаптується"

**АЛЕ в реальності (generate_irex_docs.py):**
- ✅ Код має шаблонізацію для IREX (поле `template_path`)
- ✅ Є функції `create_dstu_document()` для ДСТУ 4163:2020 (універсально)
- ❌ **Жодного механізму для парсингу інших донорів** (USAID, Велика Справа, Веспа)

#### Реалістичний сценарій для USAID:

```
USAID часто вимагає:
1. ✅ Логіку проблеми (скіл знає)
2. ✅ SMART objectives (скіл знає)
3. ❌ Work breakdown structure (WBS) — скіл це не генерує
4. ❌ Risk register з impact matrix — скіл робить просто список
5. ❌ Geo-targeting & baseline data — скіл цього не вимагає
6. ❌ Sustainability score model — відсутня формула
```

**Висновок:** Скіл універсален у **базовій логіці**, але **NЕ універсален у вимогах** конкретних донорів.

---

## 📋 РЕКОМЕНДАЦІЇ

### Пріоритет 1 (КРИТИЧНО для наступної заявки):

| # | Рекомендація | Виконавець | Дедлайн |
|:---:|:---|:---|:---:|
| 1.1 | **Додати RFA Parser:** Скіл повинен читати PDF/DOCX IREX/USAID RFA та витягувати вимоги автоматично | `.agents:03-grant-writer` | ASAP |
| 1.2 | **Compliance Checker:** На кожен пункт заявки виставляти 🟢/🟡/🔴 на основі RFA матриці | `.agents:03-grant-writer` | +1 тиждень |
| 1.3 | **Impact Indicators Template:** Для M&E Framework додати long-term indicators (12+ місяців) | `.agents:03-grant-writer` | +2 тижні |
| 1.4 | **CV Management Module:** Автоматично збирати і валідувати CV з особистих фото та посилань LinkedIn | `.agents:03-grant-writer` | +3 тижні |

### Пріоритет 2 (ВАЖЛИВО):

| # | Рекомендація | Рівень |
|:---:|:---|:---:|
| 2.1 | Budget narrative automation: витягувати ціни з Google Shopping / товарних каталогів | 🟡 |
| 2.2 | Partner Letters: перевірити реальні підписи, а не шаблони | 🟡 |
| 2.3 | Timeline realism check: математично перевірити, чи можна зробити всі активності за 12 місяців | 🟡 |
| 2.4 | Red Flag system: видавати список проблем перед фіналізацією заявки | 🟡 |

### Пріоритет 3 (ПОТІМ):

| # | Рекомендація | Розширення |
|:---:|:---|:---|
| 3.1 | Multi-donor support: USAID, EU, Велика Справа, Веспа | Розширити архітектуру скілу |
| 3.2 | Multilingual: добавити англійські шаблони | Для міжнародних донорів |
| 3.3 | Benchmarking: порівнювати кошти проєкту з іншими успішними грантами | Аналітика |

---

## 🎯 ТАБЛИЦЯ ДЕФІЦИТІВ / РЕКОМЕНДАЦІЙ

### Матриця: ЧТО БУЛО vs ЧТО МАЛО БУТИ

| Параметр | У заявці | Вимога IREX | Статус | Як виправити |
|:---|:---|:---|:---:|:---|
| **1. Крок А (форма)** | 6/8 пунктів | Усі 8 | 🟡 75% | Чек-лист на кожен пункт |
| **2. Крок Б (RFA doc)** | 5/7 критичних | Усі 7 | 🔴 70% | Auto-parser RFA + scoring |
| **3. SMART Objectives** | 4/4, але не явна логіка | SMART + Логіка | 🟡 70% | Додати TOR.Logic() module |
| **4. Key Personnel CV** | 1/4 (Сакун) | 4/4 + CV doc | 🔴 25% | CV validator + uploader |
| **5. Partner Letters** | 5 шаблонів | 7-10 підписаних | 🔴 50% | Partner signature tracker |
| **6. Impact Indicators** | 0 long-term | Min 3-4 indicators | 🔴 0% | LongTermIndicators() template |
| **7. Budget Narrative** | Таблиця | Таблиця + Reference links | 🟡 50% | Market research module |
| **8. Donor References** | 0 letters | Min 2-3 letters | 🔴 0% | Donor database + auto-request |
| **9. Risk Assessment** | 3 risks | 3 + Technical + Finance + Legal | 🟡 60% | Risk taxonomy expansion |
| **10. M&E Framework** | Partial | Full (Output+Outcome+Impact) | 🟡 65% | M&E framework builder |
| **11. Internal Controls** | Описано | + Donor references | 🟡 60% | Reference letter collector |
| **12. Sustainability Plan** | Обіцяна | Формалізована + MoU schedule | 🟡 55% | MoU tracker + timeline |

---

## 🚨 КРИТИЧНІ ВИСНОВКИ

### ЧТО СКІЛ РОБИВ ДОБРЕ:
✅ **Методологія дійсно універсальна** — використовується логіка "проблема → рішення → вплив"  
✅ **SMART objectives** — сформульовані коректно (O1, O4) або частково (O2, O3)  
✅ **Структура заявки** — відповідає шаблону IREX  
✅ **Output/Outcome розрізнення** — чітко проведено у Activity Framework  
✅ **Sustainability focus** — включено в усі розділи  
✅ **Communication strategy** — 3 канали + метрики охоплення  

### ЧТО СКІЛ ПРОПУСТИВ (КРИТИЧНО):
🔴 **Крок Б not automated** — скіл не читає RFA документи, не витягує специфічні вимоги  
🔴 **Red Flag system absent** — немає попередження про дефіцити перед подачею  
🔴 **Impact indicators missing** — M&E Framework неповна (лише Output/Outcome)  
🔴 **CV management broken** — персонал без CV, шорт-листи замість документів  
🔴 **Partner letters template** — шаблони не підписані, немає MoU трекера  
🔴 **Budget references missing** — немає посилань на конкретні товари  

### СТАТУС ДЛЯ ПІДАЧІ:
**⚠️ ЗАЯВКА НЕПОВНА, МАЛА НЕ ПРОЙТИ ПЕРШИЙ ТУР ВІДБОРУ IREX**

Скіл розробив **базовий каркас**, але **не вловив специфічні вимоги** IREX RFA. Для наступних донорів цей паттерн повториться, якщо не буде реалізовано **Крок Б (автоматичний парс вимог)**.

---

**Дата звіту:** 24 травня 2026 р.  
**Аудитор:** Antigravity Manager (Claude Agent)  
**Статус:** ПЕРЕДАТИ ДО `.agents:04-skill-architect` ДЛЯ РЕДИЗАЙНУ
