import sqlite3
import json
import os
from datetime import datetime

# Налаштування шляхів
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "novy_shlyakh.db")
JSON_BACKUP_PATH = os.path.join(BASE_DIR, "data", "specialists.json")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Дозволяє звертатися до колонок за іменами
    return conn

# --- РОБОТА ЗІ СПЕЦІАЛІСТАМИ ---

def get_specialists(status=None, category=None):
    """Отримує список спеціалістів з фільтрацією."""
    conn = get_db_connection()
    query = "SELECT * FROM specialists WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    
    query += " ORDER BY rating DESC"
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

try:
    import crypto_utils
except ImportError:
    import backend.crypto_utils as crypto_utils

def add_specialist(data):
    """Додає нового спеціаліста (або оновлює існуючого за tg_id)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Перевірка координат (якщо список - перетворюємо в рядок)
    coords = data.get('coordinates', "")
    if isinstance(coords, list):
        coords = f"{coords[0]}, {coords[1]}"
        
    try:
        # Автоматично шифруємо конфіденційні документи перед збереженням в БД
        doc_diia = crypto_utils.encrypt_doc(data.get('doc_diia_enc')) if data.get('doc_diia_enc') else None
        doc_diploma = crypto_utils.encrypt_doc(data.get('doc_diploma_enc')) if data.get('doc_diploma_enc') else None
        doc_license = crypto_utils.encrypt_doc(data.get('doc_license_enc')) if data.get('doc_license_enc') else None
        doc_fop = crypto_utils.encrypt_doc(data.get('doc_fop_enc')) if data.get('doc_fop_enc') else None

        cursor.execute('''
            INSERT INTO specialists (
                name, category, role, phone, address, coordinates, bio, status, tg_id,
                doc_diia_enc, doc_diploma_enc, doc_license_enc, doc_fop_enc,
                photo_path, document_path, consent_doc_path, consent_at,
                court_cases, team_work, avg_service_price,
                tariff_stage, tariff_plan, tariff_fixed_fee, tariff_commission_pct,
                contract_signed_date, contract_end_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name'),
            data.get('category'),
            data.get('role') or data.get('category'),
            data.get('phone'), # Публічний контакт (не шифрується)
            data.get('address'),
            coords,
            data.get('bio'),
            data.get('status', 'pending'),
            data.get('tg_id'),
            doc_diia,
            doc_diploma,
            doc_license,
            doc_fop,
            data.get('photo_path'),
            data.get('document_path'),
            data.get('consent_doc_path'),   # Шлях до consent_YYYY-MM-DD.md
            data.get('consent_at'),          # Timestamp UTC (GDPR Art.7)
            data.get('court_cases', 0),
            data.get('team_work', 0),
            data.get('avg_service_price'),
            data.get('tariff_stage', 'stage_1'),
            data.get('tariff_plan', 'grant_standard'),
            data.get('tariff_fixed_fee', 0.0),
            data.get('tariff_commission_pct', 0.0),
            data.get('contract_signed_date'),
            data.get('contract_end_date')
        ))
        conn.commit()
        last_id = cursor.lastrowid
        sync_to_json() # Автоматичний бекап в JSON
        return last_id
    except Exception as e:
        print(f"Error adding specialist: {e}")
        return None
    finally:
        conn.close()

def update_specialist_status(spec_id, status):
    """Змінює статус спеціаліста (verified/rejected/pending)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # spec_id може бути або внутрішнім ID, або рядком типу user_123_456
    if isinstance(spec_id, str) and "user_" in spec_id:
        cursor.execute("UPDATE specialists SET status = ? WHERE tg_id LIKE ?", (status, f"%{spec_id.split('_')[1]}%"))
    else:
        cursor.execute("UPDATE specialists SET status = ? WHERE id = ?", (status, spec_id))
    
    conn.commit()
    conn.close()
    sync_to_json()

def update_specialist_documents(spec_id, doc_data):
    """
    Оновлює зашифровані документи та інші поля спеціаліста.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fields = []
    params = []
    
    # Визначаємо, які поля оновлювати і шифруємо їх за потреби
    doc_cols = ["doc_diia_enc", "doc_diploma_enc", "doc_license_enc", "doc_fop_enc"]
    other_cols = [
        "photo_path", "document_path", "status", "consent_doc_path", "consent_at", "kep_signature_path",
        "court_cases", "team_work", "avg_service_price",
        "tariff_stage", "tariff_plan", "tariff_fixed_fee", "tariff_commission_pct",
        "contract_signed_date", "contract_end_date"
    ]
    
    for col in doc_cols:
        if col in doc_data:
            fields.append(f"{col} = ?")
            val = doc_data[col]
            if val and not val.startswith("gAAAAAB"):
                val = crypto_utils.encrypt_doc(val)
            params.append(val)
            
    for col in other_cols:
        if col in doc_data:
            fields.append(f"{col} = ?")
            params.append(doc_data[col])
            
    if not fields:
        conn.close()
        return False
        
    # Визначаємо тип ідентифікатора
    if isinstance(spec_id, str) and "user_" in spec_id:
        tg_id = spec_id.replace("user_", "").split("_")[0]
        params.append(tg_id)
        query = f"UPDATE specialists SET {', '.join(fields)} WHERE tg_id = ?"
    elif isinstance(spec_id, str) and spec_id.isdigit():
        params.append(int(spec_id))
        query = f"UPDATE specialists SET {', '.join(fields)} WHERE id = ?"
    elif isinstance(spec_id, int):
        params.append(spec_id)
        query = f"UPDATE specialists SET {', '.join(fields)} WHERE id = ?"
    else:
        params.append(str(spec_id))
        query = f"UPDATE specialists SET {', '.join(fields)} WHERE tg_id = ?"
        
    try:
        cursor.execute(query, params)
        conn.commit()
        sync_to_json()
        return True
    except Exception as e:
        print(f"Error updating specialist documents: {e}")
        return False
    finally:
        conn.close()

# --- РОБОТА З ВЕТЕРАНАМИ ТА ЛОГАМИ ---

def add_veteran(tg_id, name=None, phone=None):
    """Реєструє ветерана або оновлює дані."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO veterans (tg_id, name, phone)
        VALUES (?, ?, ?)
        ON CONFLICT(tg_id) DO UPDATE SET
            name = COALESCE(excluded.name, veterans.name),
            phone = COALESCE(excluded.phone, veterans.phone)
    ''', (tg_id, name, phone))
    conn.commit()
    conn.close()

def log_intake(tg_id, spec_id, status='requested'):
    """Записує факт звернення ветерана до спеціаліста."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Знаходимо внутрішній ID ветерана за tg_id
    cursor.execute("SELECT id FROM veterans WHERE tg_id = ?", (str(tg_id),))
    vet = cursor.fetchone()
    if not vet:
        add_veteran(str(tg_id))
        cursor.execute("SELECT id FROM veterans WHERE tg_id = ?", (str(tg_id),))
        vet = cursor.fetchone()
    
    cursor.execute('''
        INSERT INTO intake_logs (veteran_id, specialist_id, status)
        VALUES (?, ?, ?)
    ''', (vet['id'], spec_id, status))
    
    conn.commit()
    conn.close()

# --- СИНХРОНІЗАЦІЯ (БЕЗПЕКА) ---

def sync_to_json():
    """Експортує верифікованих спеціалістів у JSON для фронтенду та бекапу."""
    specs = get_specialists(status='verified')
    formatted_specs = []
    for s in specs:
        coords = [49.4444, 32.0597] # Default
        if s['coordinates'] and ',' in s['coordinates']:
            try:
                coords = [float(x.strip()) for x in s['coordinates'].split(',')]
            except: pass
            
        formatted_specs.append({
            "id": s['tg_id'] or f"spec_{s['id']}",
            "name": s['name'],
            "role": s['role'],
            "category": s['category'],
            "address": s['address'],
            "phone": s['phone'],
            "bio": s['bio'],
            "status": s['status'],
            "coordinates": coords,
            "rating": s['rating'],
            "doc_diia_enc": s.get('doc_diia_enc'),
            "doc_diploma_enc": s.get('doc_diploma_enc'),
            "doc_license_enc": s.get('doc_license_enc'),
            "doc_fop_enc": s.get('doc_fop_enc'),
            "photo_path": s.get('photo_path'),
            "document_path": s.get('document_path'),
            
            # Тарифні та анкетні поля для синхронізації
            "court_cases": s.get('court_cases'),
            "team_work": s.get('team_work'),
            "avg_service_price": s.get('avg_service_price'),
            "tariff_stage": s.get('tariff_stage'),
            "tariff_plan": s.get('tariff_plan'),
            "tariff_fixed_fee": s.get('tariff_fixed_fee'),
            "tariff_commission_pct": s.get('tariff_commission_pct'),
            "contract_signed_date": s.get('contract_signed_date'),
            "contract_end_date": s.get('contract_end_date')
        })
        
    with open(JSON_BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(formatted_specs, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON Backup updated: {len(formatted_specs)} specialists.")

if __name__ == "__main__":
    # Тестова синхронізація при запуску файлу
    sync_to_json()
