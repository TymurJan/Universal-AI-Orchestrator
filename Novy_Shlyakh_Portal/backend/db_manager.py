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

def add_specialist(data):
    """Додає нового спеціаліста (або оновлює існуючого за tg_id)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Перевірка координат (якщо список - перетворюємо в рядок)
    coords = data.get('coordinates', "")
    if isinstance(coords, list):
        coords = f"{coords[0]}, {coords[1]}"
        
    try:
        cursor.execute('''
            INSERT INTO specialists (name, category, role, phone, address, coordinates, bio, status, tg_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name'),
            data.get('category'),
            data.get('role') or data.get('category'),
            data.get('phone'),
            data.get('address'),
            coords,
            data.get('bio'),
            data.get('status', 'pending'),
            data.get('tg_id')
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
    # Форматуємо для сумісності зі старим JS
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
            "rating": s['rating']
        })
        
    with open(JSON_BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(formatted_specs, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON Backup updated: {len(formatted_specs)} specialists.")

if __name__ == "__main__":
    # Тестова синхронізація при запуску файлу
    sync_to_json()
