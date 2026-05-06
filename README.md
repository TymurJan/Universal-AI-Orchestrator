# Talan UA — Antigravity Manager

**Telegram-бот та система автоматизації для ГО "Талан ЮА"**

Проект є основою цифрової інфраструктури організації: управління Knowledge Base, кризові протоколи, автоматизація документообігу та Telegram-інтерфейс для щоденної роботи.

---

## Структура проекту

```
Talan UA Antigravity manager/
│
├── bot.py                      # Основний Telegram-бот (OpenAI + KB + команди)
├── _start_bot.bat              # Запуск бота у фоні
│
├── talan/                      # Базова папка пакетів
│   └── autobot/                # Автоматизація
│       ├── kb_sync.py          # Синхронізація Knowledge Base з Google Drive
│       ├── doc_engine.py       # Генерація документів із шаблону
│       ├── sheet_monitor.py    # Моніторинг відповідей Google Sheets
│       ├── create_task.ps1     # Реєстрація задачі у Планувальнику Windows
│       ├── remove_task.ps1     # Видалення задачі з Планувальника
│       ├── install_service.bat # Встановлення бота як Windows-сервіс
│       ├── uninstall_service.bat # Видалення сервісу
│       ├── run_bot_silent.vbs  # Тихий запуск (без консолі)
│       └── stop_bot.bat        # Зупинка бота
│
├── Knowledge_Base/             # База знань ГО (структурована)
│   ├── 00_NGO_Core/            # Установчі документи, статут
│   ├── 01_Standards_Legal/     # Стандарти та правові норми
│   ├── 02_Service_Activity_Partnerships/  # Сервісна діяльність
│   ├── 03_Major_Projects/      # Ключові проекти (Ашрам та ін.)
│   └── 99_Drive_Sync/          # Авто-синхронізація з Google Drive
│
├── Black_Swan_Protocol/        # Протоколи кризового реагування
│   ├── 01_Phase1_Vulnerability_Assessment.md
│   ├── 02_Phase2_MultiLayer_Immunity.md
│   ├── 03_Phase3_Emergency_Playbooks.md
│   ├── 04_Phase4_Hardening_Checklist.md
│   ├── 05_Phase5_Continuity_Protocol.md
│   ├── 06_Phase6_Stress_Test_Scenarios.md
│   ├── 08_Phase8_Secure_Data_Entry_Protocol.md
│   ├── 01_NGO_Internal/        # Внутрішні процедури ГО
│   ├── 02_Project_Ashram/       # Проект «Ашрам»
│   └── 03_Service_Activity/    # Сервісна діяльність
│
├── logs/                       # Логи (bot_log.txt, kb_sync_log.txt)
├── tessdata/                   # Дані OCR (Tesseract)
├── gemini/                     # Інструкції для Gemini CLI агента
│
├── .agent/skills/              # Скіли Antigravity агента
│   ├── my-skill/SKILL.md       # Базовий скіл: правила + профіль
│   └── kb-search/SKILL.md      # Скіл: пошук у Knowledge Base
│
├── .agents/workflows/          # Регламенти та сценарії
│   ├── talanregulations.md     # Основний регламент взаємодії
│   ├── start_bot.md            # Запуск/зупинка бота
│   └── black_swan_alert.md     # Активація кризового протоколу
│
├── .env                        # Змінні середовища (не в git)
├── pyproject.toml              # Залежності проекту
└── requirements.txt            # pip-залежності
```

---

## Швидкий старт

```powershell
# 1. Встановити залежності
pip install -r requirements.txt

# 2. Налаштувати .env (TELEGRAM_TOKEN, OPENAI_API_KEY, тощо)
copy .env.example .env

# 3. Запустити бота
.\_start_bot.bat
```

---

## Команди бота (Telegram)

| Команда | Опис |
|---|---|
| `/kb` | Показати Knowledge Base |
| `/записати категорія \| текст` | Додати запис до KB |
| `/аудіо назва` | Аудіо-підсумок документа (TTS) |
| `/квіз назва` | Квіз по документу |
| `/флешкартки назва` | Флешкартки по документу |
| `/пошук запит` | Веб-пошук через OpenAI |

---

## Кодове слово

**«Штучна душа»** — маркер довіри та неперервності контексту з AI-агентом.

---

*ГО "Талан ЮА" — Проект «Ашрам» — Antigravity AI Manager*
