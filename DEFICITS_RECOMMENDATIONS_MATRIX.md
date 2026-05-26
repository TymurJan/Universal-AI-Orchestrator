# 📊 МАТРИЦЯ ДЕФІЦИТІВ / РЕКОМЕНДАЦІЙ

## Таблиця 1: CRITICAL DEFICITS (Яка проблема буде при подачі заявки)

| №  | Дефіцит | Де виявлено | Вплив на IREX | Терміновість | Розв'язання |
|:--:|:--------|:-----------|:-------------|:------------|:-----------|
| **D1** | **Крок Б не реалізований** (Скіл не парсить RFA документи) | generate_irex_docs.py не читає template_dump.txt вимоги | 🔴 **КРИТИЧНО** — IREX очікує явного посилання на RFA пункти в заявці | 🚨 ASAP | Додати `parse_rfa_requirements()` функцію |
| **D2** | **Impact Indicators missing** (M&E Framework неповна) | Line 377-423 (Monitoring Plan) — тільки Output/Outcome | 🔴 **КРИТИЧНО** — RFA прямо вимагає long-term indicators (12+ міс) | 🚨 ASAP | Додати impact_indicators section в M&E template |
| **D3** | **CV персоналу не приєднані** (Шорт-листи замість документів) | Line 328-330: "За шорт-листом ГО" | 🔴 **КРИТИЧНО** — RFA вимагає CV як обов'язковий додаток | 🚨 До 31.05 | Зібрати CV від Шапovala, Фін.менеджера, IT архітектора |
| **D4** | **Partner Letters не підписані** (Template з placeholder) | Line 478-510: "ІМ'Я ПРІЗВИЩЕ" в усіх листах | 🔴 **КРИТИЧНО** — IREX перевіряє підписи (МП) | 🚨 До 31.05 | Отримати реальні підписи від 5 партнерів |
| **D5** | **Donor References absent** (0 letters) | SKILL.md line 58 — перелік ресурсів не включає donation-reference workflow | 🟡 **ВАЖЛИВО** — RFA line P62 вимагає 2-3 reference letters | ⚠️ До 31.05 | Попросити referencias від USAID Ukraine / IREX antiga partners |
| **D6** | **Red Flag system missing** (Нема попередження) | Весь SKILL.md — нема автоматичної перевірки compliance | 🟡 **ВАЖЛИВО** — Ризик пропустити critical issues | ⚠️ До 01.06 | Додати compliance_checker() з emoji-rated deficits |

---

## Таблиця 2: COMPLIANCE GAPS (Що конкретно не відповідає IREX)

| RFA Пункт | Вимога | Заявка містить | Статус | Red Flag |
|:----------|:-------|:-------------|:-------|:---------|
| **P.2** (Objectives) | SMART + явні логічні зв'язки | SMART є, логіка прихована | 🟡 70% | ⚠️ Об'єктивність 2 & 3 нечітка |
| **P.3** (Target Audience) | Кількість NGOs + статистика | 15+ ГО названо, але без detail | 🟡 60% | ⚠️ Варто була б таблиця: ГО → Region → Role |
| **P.4** (Partnerships) | Existing MoUs + Letters | 5 листів-шаблонів + обіцяні MoUs | 🔴 40% | 🚨 **Листи не підписані** |
| **P.6** (Key Personnel) | CV + Experience + Role + % | 1/4 CV (Сакун), інші — шорт-ліст | 🔴 25% | 🚨 **CV не приєднані** |
| **P.8** (Experience) | 3 роки + Coordination examples | Військова логістика (не coordination) | 🟡 50% | ⚠️ Мав бути focus на협ordination projects |
| **P.9** (Sustainability) | Formalized + Embedded в системи | Обіцяна формалізація, але не гарантована | 🟡 55% | ⚠️ **Нема MoU schedule** |
| **P.10** (Budget) | Narrative + Market references | Таблиця без посилань | 🟡 60% | ⚠️ Де поділяння на товари? |
| **P.11** (Internal Mgmt) | Donor references + Audit history | Описано процедури, нема referencias | 🟡 60% | 🚨 **0 referencias** |
| **P.12** (Risks) | Risks + Mitigation | 3 ризики + Mitigation | 🟡 60% | ⚠️ **Пропущені:** Tech, Finance, Legal risks |
| **P.14** (M&E) | Output + Outcome + Impact | Output + Outcome, НЕ Impact | 🟡 65% | 🚨 **Impact indicators absent** |

---

## Таблиця 3: ACTIONABLE FIXES (Як виправити для наступної заявки)

| Fix ID | Назва | Де змінити | Що додати | Дедлайн | Пріоритет |
|:----:|:------|:----------|:---------|:--------|:---------|
| **F1** | RFA Parser | `.agents:03-grant-writer/SKILL.md` | Нова функція: `extract_rfa_requirements(docx_path)` → JSON структура | +1 тиждень | 🔴 CRÍTICO |
| **F2** | Compliance Checker | `generate_irex_docs.py` | Функція `validate_compliance(proposal, rfa_json)` → 🟢🟡🔴 scoring | +1 тиждень | 🔴 CRÍTICO |
| **F3** | Impact Indicators | `Talan_Grant_Methodology.md` | Додати section: "Урок 9: Вимірювання 12+ місяці impact" | +2 тижні | 🔴 CRÍTICO |
| **F4** | CV Manager | `generate_irex_docs.py` | Function: `collect_cv_files()` + validation schema | +3 тижні | 🟡 ВАЖЛИВО |
| **F5** | Partner Tracker | `generate_irex_docs.py` | Dashboard для відслідкування підписів partner letters | +2 тижні | 🟡 ВАЖЛИВО |
| **F6** | Budget Validator | `generate_irex_docs.py` | Integration з Google Shopping / Prom.ua для ціни | +4 тижні | 🟡 ВАЖЛИВО |
| **F7** | Donor Reference | Новий workflow | Email template для запиту referencias + tracker | +1 тиждень | 🟡 ВАЖЛИВО |
| **F8** | Red Flag Report | `generate_irex_docs.py` | Final output: `COMPLIANCE_REPORT.txt` з 🚨 warnings | +1 тиждень | 🟡 ВАЖЛИВО |

---

## Таблиця 4: SCORE CARD

### 4.1 Оцінка по методологіі Таланa

| Компонента методології | Скіл реалізував? | Якість | Коментар |
|:---|:---:|:---:|:---|
| **Урок 1:** Емпатія в рамках бюрократії | ✅ | 🟢 90% | Хороша емоційна розповідь про платформу |
| **Урок 2:** Подвійна лупа (Форма + Рекомендації) | ⚠️ | 🟡 40% | Крок А є, Крок Б ВІДСУТНЯ |
| **Урок 3:** Ефект метелика (Логіко-фінансовий ланцюг) | ⚠️ | 🟡 60% | Бюджет витягнутий із плану, але без детальної верифікації |
| **Урок 4:** Незмінність шаблону | ✅ | 🟢 95% | Шаблон IREX збережено повністю |
| **Урок 5:** КСВ інтеграція | ❌ | 🔴 20% | Бізнес-партнери не залучені (тільки ГО) |
| **Урок 6:** Співфінансування | ⚠️ | 🟡 50% | 100% від IREX, мав бути місцевий внесок |
| **Урок 7:** Стратегія диверсифікації | ❌ | 🔴 10% | Повна залежність від одного гранту |
| **Урок 8:** Масштабування і сталість | ✅ | 🟢 75% | Sustainability plan є, але не формалізована |

### 4.2 Оцінка по IREX вимогам

| Категорія | Скорінг |
|:---|:---:|
| **Структура заявки** | 85% ✅ |
| **Логіка проблема→рішення** | 80% ✅ |
| **SMART Objectives** | 70% 🟡 |
| **Target Audience** | 75% 🟡 |
| **Partnerships & Sustainability** | 55% 🔴 |
| **Key Personnel** | 50% 🔴 |
| **Budget Narrative** | 60% 🟡 |
| **Risk & M&E** | 65% 🟡 |
| **Compliance with RFA** | 67% 🟡 |
| **INTERNAL MANAGEMENT** | 60% 🟡 |
| **ЗАГАЛЬНА ОЦІНКА** | **67%** 🟡 |

**ВИСНОВОК:** Заявка де**ЦЕ ЗАДОВІЛЬНО, але ДАЛЕКО ВІД EXCELLENCE**. Ризик на 2-3 раунді відбору.

---

## Таблиця 5: UNIVERSAL ALGORITHM vs DONOR-SPECIFIC

| Аспект | Універсально | Специфічно для IREX | Специфічно для USAID | Специфічно для Велика Справа |
|:---|:---:|:---|:---|:---|
| **Problem Statement** | ✅ (Generic) | + SMART + 3 ризики | + Baseline data + Geo-targeting | + KPI monitoring |
| **Objectives** | ✅ (SMART) | 4 Objectives | 3-5 Objectives | 2-3 Key Results |
| **Budget** | ✅ (Categories) | Статті + Narrative | Spreadsheet + Quarters | Quarterly forecasts |
| **Timeline** | ✅ (Gantt-like) | 12 місяців | 24-36 місяців | 6-12 місяців |
| **Monitoring** | ✅ (Output+Outcome) | + Long-term | + Quarterly reports | + Monthly dashboards |
| **Risks** | ✅ (Basic table) | 3-5 risks | 5-10 risks | Regulatory + Market |
| **CV requirement** | ✅ (Table) | CV attached | CV + Security clearance | CV + References |
| **Partner Letters** | ✅ (Template) | 5-10 letters | 15+ MOUs | LOI від business |

**Висновок:** Скіл універсален на 60%, але **специфікацію потрібно розширювати вручну** для кожного донора.

---

## 🎯 FINAL RECOMMENDATION (ДЛЯ МЕНЕДЖМЕНТУ)

### ПЕРЕД ПОДАЧЕЮ IREX (31.05.2026):

**MUST-HAVE (обов'язково):**
- [ ] Зібрати CV від Шапова + Фін.менеджера + IT архітектора (F4)
- [ ] Отримати підписи партнерів на 5 листах підтримки (D4)
- [ ] Додати 2-3 reference letters від попередніх донорів (D5)
- [ ] Розширити Risk Assessment (+ Technical, Finance, Legal) (D2)
- [ ] Додати 3-4 Impact indicators в M&E (D2)

**NICE-TO-HAVE (якщо є час):**
- [ ] Додати ринкові посилання в бюджет (F6)
- [ ] Отримати MoU від мінімум 1 партнера (Departament соцполітики) (D6)
- [ ] Розширити Target Audience таблицю (P.3)

### ПІСЛЯ IREX (для наступних грантів):

**Терміновість 1 місяць:**
- Реалізувати F1 (RFA Parser)
- Реалізувати F2 (Compliance Checker)
- Реалізувати F7 (Donor Reference workflow)

**Терміновість 2-3 місяці:**
- Реалізувати F3 (Impact Indicators methodology)
- Реалізувати F4 (CV Manager)
- Реалізувати F5 (Partner Tracker)

**Терміновість 4+ місяці:**
- Розширити для USAID + EU
- Додати multilingual support
- Benchmarking analytics

---

## 📞 КЛЮЧОВІ КОНТАКТИ ДЛЯ ВИПРАВЛЕННЯ

| Особа | Обов'язок | Термін |
|:---|:---|:---|
| **Тимур Шаповал** | Зібрати CV + Letter від IREX antiga projects | До 28.05 |
| **Анна Сакун** | Підписати листи партнерів | До 29.05 |
| **Фінансовий менеджер** | Додати ринкові посилання в бюджет | До 29.05 |
| **IT архітектор** | CV + технічні деталі масштабування | До 28.05 |
| **`.agents:03-grant-writer` скіл** | Додати RFA Parser + Compliance Checker | До 31.05 |

---

**Дата звіту:** 24 травня 2026 р.  
**Статус IREX заявки:** ⚠️ INCOMPLETE (Потребує виправлень)  
**Вірогідність успіху (сьогодні):** 35-40% (LOW)  
**Вірогідність успіху (після fixes):** 65-75% (MODERATE)
