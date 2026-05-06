"""
Knowledge Base Auto-Sync з Google Drive
ГО "ТАЛАН ЮА" / Antigravity Manager

Скрипт завантажує файли з вказаної папки Google Drive у локальну Knowledge_Base.
Запускається через Планувальник завдань Windows або вручну.

Потребує:
1. Google Service Account (JSON key file)
2. Доступ до папки Drive для сервісного акаунту
3. Змінні у .env: GDRIVE_FOLDER_ID, SERVICE_ACCOUNT_JSON
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import json

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# --- Логування ---
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "kb_sync_log.txt", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("KB_Sync")

# --- Конфігурація ---
KB_PATH = BASE_DIR / "Knowledge_Base"
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_JSON", "service_account.json")
SERVICE_ACCOUNT_PATH = BASE_DIR / SERVICE_ACCOUNT_FILE
STATUS_FILE = LOG_DIR / "status.json"

def check_prerequisites():
    """Перевіряє наявність всіх необхідних компонентів."""
    issues = []
    
    if not GDRIVE_FOLDER_ID:
        issues.append("❌ GDRIVE_FOLDER_ID не задано у .env")
    
    if not SERVICE_ACCOUNT_PATH.exists():
        issues.append(f"❌ Файл сервісного акаунту не знайдено: {SERVICE_ACCOUNT_PATH}")
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        issues.append("❌ Не встановлено google-api-python-client. Виконайте: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    
    return issues

def sync_drive_to_kb():
    """Синхронізує файли з Google Drive у Knowledge_Base."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    creds = service_account.Credentials.from_service_account_file(
        str(SERVICE_ACCOUNT_PATH), scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)
    
    log.info(f"📂 Синхронізація з Google Drive (folder: {GDRIVE_FOLDER_ID})...")
    
    # Отримуємо список файлів
    results = service.files().list(
        q=f"'{GDRIVE_FOLDER_ID}' in parents and trashed = false",
        pageSize=100,
        fields="files(id, name, mimeType, modifiedTime)"
    ).execute()
    
    files = results.get('files', [])
    log.info(f"Знайдено файлів у Drive: {len(files)}")
    
    synced = 0
    skipped = 0
    
    # Маппінг MIME-типів для Google Docs
    EXPORT_MAP = {
        'application/vnd.google-apps.document': ('text/markdown', '.md'),
        'application/vnd.google-apps.spreadsheet': ('text/csv', '.csv'),
    }
    
    SYNC_DIR = KB_PATH / "99_Drive_Sync"
    SYNC_DIR.mkdir(parents=True, exist_ok=True)
    
    for f in files:
        name = f['name']
        mime = f['mimeType']
        file_id = f['id']
        
        if mime in EXPORT_MAP:
            # Google Docs — експортуємо
            export_mime, ext = EXPORT_MAP[mime]
            target_path = SYNC_DIR / f"{Path(name).stem}{ext}"
            
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
        elif mime.startswith('application/vnd.google-apps.'):
            # Інші Google форми (Forms, Slides) — пропускаємо
            log.info(f"⏭️ Пропущено (Google App): {name}")
            skipped += 1
            continue
        else:
            # Звичайні файли — завантажуємо
            target_path = SYNC_DIR / name
            request = service.files().get_media(fileId=file_id)
        
        # Перевіряємо чи файл оновився
        if target_path.exists():
            drive_modified = datetime.fromisoformat(f['modifiedTime'].replace('Z', '+00:00'))
            local_modified = datetime.fromtimestamp(target_path.stat().st_mtime).astimezone()
            if drive_modified <= local_modified:
                skipped += 1
                continue
        
        # Завантажуємо
        try:
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            target_path.write_bytes(fh.getvalue())
            synced += 1
            log.info(f"✅ Синхронізовано: {name} -> {target_path.name}")
        except Exception as e:
            log.error(f"❌ Помилка завантаження {name}: {e}")
    
    log.info(f"📊 Синхронізація завершена: {synced} оновлено, {skipped} пропущено")
    return synced, skipped

def update_status(process_name, status, details=None):
    """Оновлює статус у центральному JSON файлі."""
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

def main():
    log.info("=" * 50)
    log.info(f"🔄 KB Sync запущено: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    issues = check_prerequisites()
    if issues:
        log.warning("⚠️ Не всі вимоги виконані:")
        for issue in issues:
            log.warning(f"  {issue}")
        log.info("💡 Інструкція:")
        log.info("  1. Створіть Service Account: https://console.cloud.google.com")
        log.info("  2. Завантажте JSON ключ у папку проєкту як service_account.json")
        log.info("  3. Поділіться папкою Drive із сервісним акаунтом")
        log.info("  4. Додайте GDRIVE_FOLDER_ID=<id> у .env")
        return
    
    try:
        synced, skipped = sync_drive_to_kb()
        log.info(f"✅ Результат: {synced} синхронізовано, {skipped} пропущено")
        update_status("kb_sync", "success", f"{synced} updated, {skipped} skipped")
    except Exception as e:
        log.error(f"❌ Критична помилка синхронізації: {e}")
        update_status("kb_sync", "error", str(e))

if __name__ == "__main__":
    main()
