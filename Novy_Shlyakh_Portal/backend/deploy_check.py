"""
deploy_check.py — Автоматична передстартова перевірка порталу «Новий Шлях»
ГО Талан UA | Запускається ПЕРЕД кожним деплоєм або перезапуском сервера.

Перевіряє:
  1. Наявність FERNET_KEY у .env (захист документів спеціалістів)
  2. Валідність FERNET_KEY (Fernet може ініціалізуватись)
  3. Наявність усіх обов'язкових змінних середовища
  4. Доступність та цілісність файлу бази даних
  5. Наявність таблиць у БД (схема ініціалізована)
  6. Наявність шаблону договору зі спеціалістом

Повертає:
  Exit code 0 — все гаразд, деплой дозволений
  Exit code 1 — критична проблема, деплой ЗАБЛОКОВАНИЙ
"""

import os
import sys
import sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# Налаштування шляхів
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent
ENV_FILE    = BACKEND_DIR / ".env"
DB_FILE     = BACKEND_DIR / "data" / "novy_shlyakh.db"
CONTRACT_TEMPLATE = BACKEND_DIR.parent.parent / "talan" / "autobot" / "templates" / "contract_specialist.md"

REQUIRED_TABLES = ["specialists", "veterans", "intake_logs", "education"]
REQUIRED_ENV_VARS = ["BOT_TOKEN", "ADMIN_ID", "FERNET_KEY"]

# ---------------------------------------------------------------------------
# Кольорове виведення (ANSI)
# ---------------------------------------------------------------------------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg: str)   -> None: print(f"  {GREEN}✅ {msg}{RESET}")
def fail(msg: str) -> None: print(f"  {RED}❌ {msg}{RESET}")
def warn(msg: str) -> None: print(f"  {YELLOW}⚠️  {msg}{RESET}")
def head(msg: str) -> None: print(f"\n{BOLD}{msg}{RESET}")


# ---------------------------------------------------------------------------
# Допоміжна функція: завантаження .env без dotenv
# ---------------------------------------------------------------------------
def load_env_file(env_path: Path) -> dict:
    """Читає .env файл і повертає словник змінних (без зовнішніх залежностей)."""
    env_vars = {}
    if not env_path.exists():
        return env_vars
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip()
    return env_vars


# ---------------------------------------------------------------------------
# ПЕРЕВІРКА 1: Змінні середовища та .env
# ---------------------------------------------------------------------------
def check_env_vars() -> bool:
    head("[1/5] Перевірка змінних середовища (.env)")
    passed = True

    if not ENV_FILE.exists():
        fail(f"Файл .env не знайдено за шляхом: {ENV_FILE}")
        fail("Створіть .env на основі .env.example перед деплоєм!")
        return False

    ok(f".env файл знайдено: {ENV_FILE}")

    # Завантажуємо .env у os.environ для поточного процесу
    env_vars = load_env_file(ENV_FILE)
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value

    # Перевіряємо обов'язкові змінні
    for var in REQUIRED_ENV_VARS:
        value = os.environ.get(var, "")
        if not value:
            fail(f"Змінна {var} відсутня або порожня у .env!")
            passed = False
        elif var == "FERNET_KEY":
            ok(f"{var} = {value[:12]}... [приховано, {len(value)} символів]")
        else:
            ok(f"{var} встановлено")

    return passed


# ---------------------------------------------------------------------------
# ПЕРЕВІРКА 2: Валідність FERNET_KEY
# ---------------------------------------------------------------------------
def check_fernet_key() -> bool:
    head("[2/5] Валідація FERNET_KEY")

    fernet_key = os.environ.get("FERNET_KEY", "")
    if not fernet_key:
        fail("FERNET_KEY не встановлено — пропускаємо валідацію")
        return False

    try:
        from cryptography.fernet import Fernet
        fernet = Fernet(fernet_key.encode("utf-8"))

        # Тестове шифрування/розшифрування
        test_data = "deploy_check_test_2026"
        encrypted = fernet.encrypt(test_data.encode())
        decrypted = fernet.decrypt(encrypted).decode()

        if decrypted == test_data:
            ok("FERNET_KEY валідний — тестове шифрування/розшифрування пройшло успішно")
            return True
        else:
            fail("FERNET_KEY: результат розшифрування не співпав!")
            return False

    except Exception as e:
        fail(f"FERNET_KEY невалідний: {e}")
        fail("Згенеруйте новий ключ: python crypto_utils.py → generate_new_key()")
        return False


# ---------------------------------------------------------------------------
# ПЕРЕВІРКА 3: База даних
# ---------------------------------------------------------------------------
def check_database() -> bool:
    head("[3/5] Перевірка бази даних SQLite")
    passed = True

    if not DB_FILE.exists():
        warn(f"БД не знайдено: {DB_FILE}")
        warn("Запустіть python database.py для ініціалізації схеми")
        warn("Це нормально для першого деплою — БД буде створена автоматично")
        return True  # Не критично для першого старту

    ok(f"Файл БД знайдено: {DB_FILE} ({DB_FILE.stat().st_size} байт)")

    try:
        conn = sqlite3.connect(str(DB_FILE))
        cursor = conn.cursor()

        # Перевіряємо наявність таблиць
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        for table in REQUIRED_TABLES:
            if table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                ok(f"Таблиця '{table}' існує ({count} записів)")
            else:
                warn(f"Таблиця '{table}' відсутня — буде створена при першому запуску")

        conn.close()

    except Exception as e:
        fail(f"Помилка читання БД: {e}")
        passed = False

    return passed


# ---------------------------------------------------------------------------
# ПЕРЕВІРКА 4: Шаблон договору зі спеціалістом
# ---------------------------------------------------------------------------
def check_specialist_contract() -> bool:
    head("[4/5] Перевірка шаблону договору зі спеціалістом")

    if CONTRACT_TEMPLATE.exists():
        ok(f"Шаблон договору знайдено: {CONTRACT_TEMPLATE.name}")
        return True
    else:
        warn(f"Шаблон договору відсутній: {CONTRACT_TEMPLATE}")
        warn("Рекомендовано створити contract_specialist.md перед першою реєстрацією")
        warn("Спеціаліст має підписати згоду на обробку даних та публікацію контактів")
        return True  # Попередження, не блокування


# ---------------------------------------------------------------------------
# ПЕРЕВІРКА 5: Модуль crypto_utils
# ---------------------------------------------------------------------------
def check_crypto_module() -> bool:
    head("[5/5] Перевірка модуля шифрування")

    crypto_file = BACKEND_DIR / "crypto_utils.py"
    if not crypto_file.exists():
        fail(f"crypto_utils.py не знайдено: {crypto_file}")
        return False

    ok(f"crypto_utils.py знайдено ({crypto_file.stat().st_size} байт)")

    try:
        # Додаємо директорію до sys.path для імпорту
        sys.path.insert(0, str(BACKEND_DIR))
        import crypto_utils  # noqa: F401
        ok("Модуль crypto_utils імпортовано успішно")
        return True
    except Exception as e:
        fail(f"Помилка імпорту crypto_utils: {e}")
        return False


# ---------------------------------------------------------------------------
# ГОЛОВНА ФУНКЦІЯ
# ---------------------------------------------------------------------------
def main() -> int:
    print(f"\n{'='*60}")
    print(f"  {BOLD}Передстартова перевірка — Портал «Новий Шлях»{RESET}")
    print(f"  ГО Талан UA | deploy_check.py")
    print(f"{'='*60}")

    results = {
        "env_vars":   check_env_vars(),
        "fernet":     check_fernet_key(),
        "database":   check_database(),
        "contract":   check_specialist_contract(),
        "crypto_mod": check_crypto_module(),
    }

    # Критичні перевірки (блокують деплой)
    critical = ["env_vars", "fernet", "crypto_mod"]
    critical_failed = [k for k in critical if not results[k]]

    print(f"\n{'='*60}")
    print(f"  {BOLD}ПІДСУМОК{RESET}")
    print(f"{'='*60}")

    all_passed = all(results.values())
    critical_ok = len(critical_failed) == 0

    for check, passed in results.items():
        status = f"{GREEN}OK{RESET}" if passed else f"{RED}FAIL{RESET}"
        label = f"[КРИТИЧНО]" if check in critical else "[ПОПЕРЕДЖЕННЯ]"
        print(f"  {status}  {label} {check}")

    print(f"{'='*60}")

    if critical_ok:
        print(f"\n  {GREEN}{BOLD}✅ ДЕПЛОЙ ДОЗВОЛЕНО{RESET}")
        if not all_passed:
            print(f"  {YELLOW}Є попередження — перевірте їх перед першою реєстрацією{RESET}")
        return 0
    else:
        print(f"\n  {RED}{BOLD}❌ ДЕПЛОЙ ЗАБЛОКОВАНО{RESET}")
        print(f"  Усуньте критичні помилки: {', '.join(critical_failed)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
