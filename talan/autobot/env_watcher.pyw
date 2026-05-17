"""
ENV Watcher — Автоматична синхронізація .env → E:\.env при будь-якій зміні.
Працює тихо у фоні (.pyw = без вікна консолі).
Запускається через Task Scheduler при вході в систему.
"""
import time
import shutil
import hashlib
from pathlib import Path
from datetime import datetime

SOURCE = Path(r"d:\ГО Талан UA\Talan UA Antigravity manager\.env")
DESTINATION = Path(r"E:\.env")
LOG_FILE = SOURCE.parent / "logs" / "env_sync.log"
CHECK_INTERVAL = 5  # секунд між перевірками


def log(msg: str):
    """Записує повідомлення в лог."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")


def file_hash(path: Path) -> str:
    """Обчислює MD5 хеш файлу."""
    if not path.exists():
        return ""
    return hashlib.md5(path.read_bytes()).hexdigest()


def sync():
    """Копіює .env на E:\ якщо вміст змінився."""
    try:
        if not SOURCE.exists():
            return

        if not DESTINATION.parent.exists():
            # Диск E: не підключений
            return

        src_hash = file_hash(SOURCE)
        dst_hash = file_hash(DESTINATION)

        if src_hash != dst_hash:
            shutil.copy2(SOURCE, DESTINATION)
            log(f"✅ Синхронізовано .env → E:\\.env (hash: {src_hash[:8]}...)")
    except Exception as e:
        log(f"❌ Помилка синхронізації: {e}")


if __name__ == "__main__":
    log("🚀 ENV Watcher запущено. Слідкую за змінами...")

    last_hash = file_hash(SOURCE)

    while True:
        try:
            current_hash = file_hash(SOURCE)
            if current_hash != last_hash:
                sync()
                last_hash = current_hash
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            log("⏹️ ENV Watcher зупинено.")
            break
        except Exception as e:
            log(f"❌ Критична помилка: {e}")
            time.sleep(60)  # Чекаємо хвилину перед повтором
