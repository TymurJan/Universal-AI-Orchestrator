import os
import sys
import shutil
import logging
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# --- Path Configuration ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# --- Logging ---
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "backup_log.txt", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("Backup")

# --- Environment Variables ---
EXTERNAL_SYNC_PATH = Path(os.getenv("EXTERNAL_SYNC_PATH", "E:/BACKUP"))
STATUS_FILE = BASE_DIR / "logs" / "status.json"

# --- Filtering Settings (what NOT to backup) ---
EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "logs", ".gemini", "gemini"}


def sync_env_to_external():
    """Знаходить всі .env файли в проекті та копіює їх на зовнішній диск E:."""
    log.info("🔍 Пошук всіх .env файлів для резервного копіювання на E:")

    count = 0
    try:
        if not EXTERNAL_SYNC_PATH.exists():
            EXTERNAL_SYNC_PATH.mkdir(parents=True, exist_ok=True)

        env_backup_root = EXTERNAL_SYNC_PATH / "ENV_BACKUP"
        env_backup_root.mkdir(exist_ok=True)

        for root, dirs, files in os.walk(BASE_DIR):
            # Пропускаємо приховані та виключені директорії
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in EXCLUDE_DIRS]

            if ".env" in files:
                source = Path(root) / ".env"
                rel_path = source.relative_to(BASE_DIR).parent
                if str(rel_path) == ".":
                    dest_folder = env_backup_root / "ROOT"
                else:
                    safe_folder = str(rel_path).replace(os.sep, "_")
                    dest_folder = env_backup_root / safe_folder

                dest_folder.mkdir(parents=True, exist_ok=True)
                dest_file = dest_folder / ".env"

                shutil.copy2(source, dest_file)
                log.info(f"🔄 Скопійовано: {source.relative_to(BASE_DIR)} -> {dest_file}")
                count += 1

        log.info(f"✅ Всього .env файлів скопійовано на E:: {count}")
        return True, f"{count} .env файлів скопійовано на E:"
    except Exception as e:
        log.error(f"❌ Помилка під час копіювання .env на E:: {e}")
        return False, str(e)


def update_status(process_name, status, details=None):
    """Оновлює статус в центральному JSON файлі."""
    data = {}
    if STATUS_FILE.exists():
        try:
            data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    data[process_name] = {
        "last_run": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "status": status,
        "details": details or ""
    }

    try:
        STATUS_FILE.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log.error(f"❌ Не вдалося оновити status.json: {e}")


def run_backup():
    """Основна функція резервного копіювання.
    
    Виконує тільки одну дію: копіює всі .env файли на зовнішній диск E:.
    Google Drive та будь-який хмарний бекап — відключені.
    service_account.json зберігається на диску для ручних операцій за запитом.
    """
    log.info("=" * 60)
    log.info(f"🏁 РЕЗЕРВНЕ КОПІЮВАННЯ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    success, details = sync_env_to_external()

    if success:
        update_status("backup", "success", details)
        log.info("✅ Резервне копіювання завершено успішно.")
    else:
        update_status("backup", "error", details)
        log.error("❌ Резервне копіювання завершено з помилкою.")


if __name__ == "__main__":
    run_backup()
