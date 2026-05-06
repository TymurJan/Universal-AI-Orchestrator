import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from pathlib import Path
import subprocess

# --- Налаштування ---
app = Flask(__name__)
CORS(app)  # Дозволяємо запити з лендінгу

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "landing_api.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("LandingAPI")

# --- Конфігурація сповіщень (з .env) ---
from dotenv import load_dotenv
load_dotenv(dotenv_path=BASE_DIR / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ALLOWED_USER_IDS", "").split(",")[0]

def send_telegram_alert(message):
    import requests
    if not TELEGRAM_TOKEN or not ADMIN_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": ADMIN_ID, "text": f"🚀 НОВИЙ ЛІД (B2B):\n{message}"})
    except Exception as e:
        log.error(f"❌ Telegram Alert Error: {e}")

# --- API Endpoints ---

@app.route('/api/b2b/invoice', methods=['POST'])
def create_invoice():
    try:
        data = request.json
        email = data.get('email')
        edrpou = data.get('edrpou')
        position = data.get('position')
        tier = data.get('tier', 'basic')
        
        log.info(f"📩 Отримано запит: {edrpou} | {email} | {tier}")
        
        # 1. Логування ліда
        lead_entry = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "edrpou": edrpou,
            "position": position,
            "tier": tier
        }
        with open(LOGS_DIR / "leads.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(lead_entry, ensure_ascii=False) + "\n")
            
        # 2. Генерація договору (Підготовка MD)
        template_path = BASE_DIR / "talan" / "autobot" / "templates" / "contract_b2b.md"
        if not template_path.exists():
            return jsonify({"error": "Template not found"}), 500
            
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Заміна тегів
        content = content.replace("{{CONTRACT_NUMBER}}", datetime.now().strftime("%Y%m%d%H%M"))
        content = content.replace("{{TIER_NAME}}", tier.capitalize())
        content = content.replace("{{EDRPOU}}", edrpou)
        content = content.replace("{{POSITION}}", position)
        content = content.replace("{{PRICE_EUR}}", "600" if tier == "basic" else "1800" if tier == "corporate" else "6000")
        
        # Тимчасовий файл для генерації
        tmp_md = LOGS_DIR / f"contract_{edrpou}.md"
        with open(tmp_md, "w", encoding="utf-8") as f:
            f.write(content)
            
        # 3. Виклик docx_generator.py
        output_docx = LOGS_DIR / f"Contract_Universal_AI_{edrpou}.docx"
        gen_script = BASE_DIR / "talan" / "autobot" / "docx_generator.py"
        
        # Запускаємо через subprocess (чисто та безпечно)
        # Примітка: docx_generator.py має підтримувати запуск з аргументами
        subprocess.run([
            "python", str(gen_script), 
            "--input", str(tmp_md), 
            "--output", str(output_docx)
        ])
        
        # 4. Сповіщення Тимуру
        alert_msg = f"💳 Клієнт: {edrpou}\n📧 Email: {email}\n💼 Посада: {position}\n💎 Пакет: {tier}\n📄 Договір згенеровано: {output_docx.name}"
        # ТИМЧАСОВО ВИМКНЕНО: "не шли нічого бухгалтеру"
        log.info(f"TEST ALERT DEFERRED: {alert_msg}")
        # send_telegram_alert(alert_msg)
        
        return jsonify({"status": "success", "message": "Documents generated and team notified"}), 200
        
    except Exception as e:
        log.error(f"❌ API Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    log.info("🌐 Landing API Bridge заpuщено на порту 5000")
    app.run(port=5000, debug=False)
