import os
import sys
import zipfile
import pyminizip
import shutil
import logging
import time
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import base64
import requests

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
GDRIVE_CORE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "root")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_JSON", "service_account.json")
SERVICE_ACCOUNT_PATH = BASE_DIR / SERVICE_ACCOUNT_FILE
BACKUP_GATEWAY_URL = os.getenv("BACKUP_GATEWAY_URL")
BACKUP_PASSWORD = os.getenv("BACKUP_PASSWORD")
EXTERNAL_SYNC_PATH = Path("E:/BACKUP")
STATUS_FILE = BASE_DIR / "logs" / "status.json"

# --- Filtering Settings (what NOT to backup) ---
EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "logs", ".gemini", "gemini"}
EXCLUDE_FILES = {"bot.pid", ".python-version"}

def create_project_zip(output_path):
    """Creates an encrypted ZIP archive of the entire project."""
    log.info(f"📦 Starting encrypted archiving of the project into {output_path.name}...")
    
    file_list = []
    for root, dirs, files in os.walk(BASE_DIR):
        rel_path = Path(root).relative_to(BASE_DIR)
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        
        for file in files:
            if file in EXCLUDE_FILES:
                continue
            file_path = Path(root) / file
            if file_path == output_path:
                continue
            
            # Add to list for pyminizip (absolute path + relative in archive)
            file_list.append(str(file_path))

    # Create list of relative paths for pyminizip
    prefixed_file_list = []
    for f in file_list:
        rel = os.path.relpath(f, BASE_DIR)
        prefixed_file_list.append(rel)

    if not BACKUP_PASSWORD:
        log.warning("⚠️ BACKUP_PASSWORD not found! Archive will be created without a password.")
        # Fallback to standard zip if no password
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for f in file_list:
                zipf.write(f, os.path.relpath(f, BASE_DIR))
    else:
        try:
            # pyminizip.compress_multiple(src_files, prefix_paths, output, password, compress_level)
            pyminizip.compress_multiple(file_list, prefixed_file_list, str(output_path), BACKUP_PASSWORD, 5)
        except Exception as e:
            log.error(f"❌ pyminizip error: {e}. Attempting standard ZIP fallback...")
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for f in file_list:
                    zipf.write(f, os.path.relpath(f, BASE_DIR))
    
    log.info(f"✅ Archive created: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

def sync_env_to_external():
    """Syncs .env to external drive E:."""
    env_source = BASE_DIR / ".env"
    env_dest = EXTERNAL_SYNC_PATH / ".env"
    
    if not env_source.exists():
        log.error("❌ .env file not found for sync!")
        return
        
    try:
        if not EXTERNAL_SYNC_PATH.exists():
            EXTERNAL_SYNC_PATH.mkdir(parents=True, exist_ok=True)
            
        shutil.copy2(env_source, env_dest)
        log.info(f"🔄 .env successfully synced to {env_dest}")
        return True
    except Exception as e:
        log.error(f"❌ .env sync error: {e}")
        return False

def upload_via_gateway(file_path, gateway_url, max_retries=5):
    """Sends file via Google Apps Script Gateway with retry mechanism."""
    log.info(f"🚀 Sending archive via Apps Script Gateway...")
    
    retries = 0
    while retries < max_retries:
        try:
            with open(file_path, "rb") as f:
                encoded_content = base64.b64encode(f.read()).decode("utf-8")
            
            payload = {
                "fileName": file_path.name,
                "mimeType": "application/zip",
                "fileContent": encoded_content
            }
            
            # Apps Script can be slow with large files
            response = requests.post(gateway_url, json=payload, timeout=180)
            
            if response.status_code != 200:
                log.error(f"❌ HTTP Error: {response.status_code}")
                log.error(f"📝 Error text: {response.text[:500]}")
                retries += 1
                time.sleep(10 * retries)
                continue
                
            result = response.json()
            
            if result.get("status") == "success":
                log.info(f"✅ Backup successfully accepted by gateway! ID: {result.get('fileId')}")
                return result.get("fileId")
            else:
                log.error(f"❌ Gateway returned error: {result.get('message')}")
                retries += 1
                time.sleep(10 * retries)
                continue
                
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            log.error(f"⚠️ Network error (Attempt {retries+1}/{max_retries}): {e}")
            retries += 1
            # Exponential backoff
            time.sleep(2 ** retries * 5)
        except Exception as e:
            log.error(f"❌ Unexpected error during gateway upload: {e}")
            return None
            
    log.error(f"❌ Failed to upload after {max_retries} attempts.")
    return None

def find_file_id(service, name, folder_id):
    """Searches for a file by name in a specific folder and returns its ID."""
    try:
        query = f"name = '{name}' and '{folder_id}' in parents and trashed = false"
        response = service.files().list(q=query, spaces='drive', fields='files(id, name)', supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        files = response.get('files', [])
        if files:
            return files[0].get('id')
        return None
    except Exception as e:
        log.error(f"🔍 Error searching for file {name}: {e}")
        return None

def upload_to_drive_smart(file_path, folder_id):
    """Uploads or updates file on Google Drive (Smart Sync)."""
    if not SERVICE_ACCOUNT_PATH.exists():
        log.error(f"❌ Key file not found: {SERVICE_ACCOUNT_PATH}")
        return None

    log.info(f"☁️ Starting SMART Google Drive sync (Folder ID: {folder_id})...")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_PATH), 
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        service = build('drive', 'v3', credentials=creds)
        
        # Search for existing file
        existing_file_id = find_file_id(service, file_path.name, folder_id)
        
        media = MediaFileUpload(str(file_path), mimetype='application/zip', resumable=True, chunksize=5*1024*1024)
        
        if existing_file_id:
            log.info(f"🔄 Found existing file '{file_path.name}' (ID: {existing_file_id}). UPDATING content...")
            request = service.files().update(fileId=existing_file_id, media_body=media, supportsAllDrives=True)
        else:
            log.info(f"🆕 File '{file_path.name}' not found. CREATING new file...")
            file_metadata = {'name': file_path.name, 'parents': [folder_id]}
            request = service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True)
        
        log.info(f"📂 Syncing {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.2f} MB) in chunks...")
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                log.info(f"⬆️ Syncing... {int(status.progress() * 100)}%")
        
        file_id = response.get('id')
        log.info(f"🚀 SMART Sync completed! ID: {file_id}")
        return file_id
    except Exception as e:
        log.error(f"❌ Smart sync error: {e}")
        return None

def check_stability():
    """Checks bot stability before backup."""
    log.info("📝 Checking system stability...")
    bot_log = BASE_DIR / "logs" / "bot_log.txt"
    if not bot_log.exists():
        return True
        
    recent_errors = 0
    try:
        content = bot_log.read_text(encoding='utf-8')
        lines = content.splitlines()[-200:]
        for line in lines:
            if "[ERROR]" in line or "[CRITICAL]" in line:
                recent_errors += 1
        return recent_errors <= 5
    except Exception:
        return True

def split_file(file_path, chunk_size_mb=20):
    """Splits file into parts."""
    chunk_size = chunk_size_mb * 1024 * 1024
    parts = []
    
    file_size = file_path.stat().st_size
    if file_size <= chunk_size:
        return [file_path]
    
    log.info(f"✂️ Splitting large file ({file_size / 1024 / 1024:.2f} MB) into {chunk_size_mb} MB chunks...")
    
    with open(file_path, 'rb') as f:
        part_num = 1
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            part_path = file_path.with_suffix(f"{file_path.suffix}.{part_num:03d}")
            part_path.write_bytes(chunk)
            parts.append(part_path)
            part_num += 1
            
    log.info(f"✅ File split into {len(parts)} parts.")
    return parts

def update_status(process_name, status, details=None):
    """Updates status in central JSON file."""
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
        log.error(f"❌ Failed to update status.json: {e}")

def run_backup():
    log.info("=" * 60)
    log.info(f"🏁 SMART SYNC SESSION STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    is_stable = check_stability()
    sync_env_to_external()
    
    # Use static names for MIRROR strategy (no timestamps)
    prefix = "STABLE_" if is_stable else "UNSTABLE_"
    zip_name = f"{prefix}Talan_Mirror_DoNotDelete.zip"
    tmp_zip = BASE_DIR / zip_name
    
    try:
        create_project_zip(tmp_zip)
        file_size_mb = tmp_zip.stat().st_size / 1024 / 1024
        
        success = False
        
        # 1. Try SMART Sync (Service Account)
        if SERVICE_ACCOUNT_PATH.exists():
            log.info("💎 Attempting SMART DRIVE SYNC (Update Mode)...")
            file_id = upload_to_drive_smart(tmp_zip, GDRIVE_CORE_FOLDER_ID)
            if file_id:
                log.info("🌟 Smart sync completed successfully via Service Account.")
                update_status("backup", "success", f"In-place update ID: {file_id}")
                success = True
            else:
                log.warning("⚠️ Smart sync failed (likely quota issue). Trying Gateway fallback...")

        # 2. Fallback to Gateway (if Smart Sync failed or no Service Account)
        if not success and BACKUP_GATEWAY_URL:
            log.info("🚀 Using Gateway fallback upload...")
            if file_size_mb > 20:
                parts = split_file(tmp_zip, 20)
                success_count = 0
                for part in parts:
                    if upload_via_gateway(part, BACKUP_GATEWAY_URL):
                        success_count += 1
                    if part != tmp_zip: part.unlink()
                
                if success_count == len(parts):
                    log.info("✅ Gateway segmented upload successful.")
                    update_status("backup", "warning", "Sync via Gateway (may create copies)")
                    success = True
            else:
                if upload_via_gateway(tmp_zip, BACKUP_GATEWAY_URL):
                    log.info("✅ Gateway upload successful.")
                    update_status("backup", "warning", "Sync via Gateway (may create copies)")
                    success = True
        
        if not success:
            log.error("❌ All cloud upload methods failed!")
            update_status("backup", "error", "No valid upload method succeeded")
            
    except Exception as e:
        log.error(f"❌ Critical sync error: {e}")
        update_status("backup", "error", str(e))
            
    finally:
        if tmp_zip.exists():
            tmp_zip.unlink()
            log.info(f"🧹 Temporary zip {zip_name} cleaned up.")

if __name__ == "__main__":
    run_backup()
