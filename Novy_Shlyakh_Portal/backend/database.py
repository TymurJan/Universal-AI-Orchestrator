import sqlite3
import os
from datetime import datetime

# Шлях до бази даних всередині папки проєкту
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "novy_shlyakh.db")

def init_db():
    """Ініціалізація структури бази даних."""
    # Переконуємось, що папка data існує
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Спеціалісти (спільнота)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS specialists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            role TEXT,
            phone TEXT,          -- Публічний контакт спеціаліста (не шифрується)
            address TEXT,
            coordinates TEXT,    -- Зберігаємо як "lat, lng"
            bio TEXT,
            status TEXT DEFAULT 'pending', -- pending, verified, rejected
            rating REAL DEFAULT 5.0,
            tg_id TEXT,
            -- Конфіденційні регуляторні документи (зашифровані Fernet у crypto_utils.py)
            doc_diia_enc TEXT,       -- Виписка з ДІЯ (ідентифікація)
            doc_diploma_enc TEXT,    -- Диплом / сертифікат про освіту
            doc_license_enc TEXT,    -- Ліцензія на діяльність (медична/психологічна)
            doc_fop_enc TEXT,        -- Документи ФОП (якщо самозайнятий)
            photo_path TEXT,         -- Шлях до фото спеціаліста
            document_path TEXT,      -- Шлях до локального завантаженого PDF
            -- Audit Trail згоди (GDPR Art.7 / ЗУ «Про захист ПД»)
            consent_doc_path TEXT,   -- Шлях до consent_YYYY-MM-DD.md у папці спеціаліста
            consent_at TEXT,         -- Timestamp підпису (UTC) — незмінний після запису
            kep_signature_path TEXT, -- Шлях до .p7s (або .sig fallback) КЕП-підпису
            
            -- Нові тарифні та договірні поля
            court_cases INTEGER DEFAULT 0,
            team_work INTEGER DEFAULT 0,
            avg_service_price TEXT,
            tariff_stage TEXT DEFAULT 'stage_1',
            tariff_plan TEXT DEFAULT 'grant_standard',
            tariff_fixed_fee REAL DEFAULT 0.0,
            tariff_commission_pct REAL DEFAULT 0.0,
            contract_signed_date TEXT,
            contract_end_date TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Самооновлення схеми бази даних (Self-healing schema migration)
    try:
        cursor.execute("PRAGMA table_info(specialists)")
        columns = [row[1] for row in cursor.fetchall()]
        if "photo_path" not in columns:
            cursor.execute("ALTER TABLE specialists ADD COLUMN photo_path TEXT")
            print("🔧 Додано колонку photo_path в таблицю specialists")
        if "document_path" not in columns:
            cursor.execute("ALTER TABLE specialists ADD COLUMN document_path TEXT")
            print("🔧 Додано колонку document_path в таблицю specialists")
        if "consent_doc_path" not in columns:
            cursor.execute("ALTER TABLE specialists ADD COLUMN consent_doc_path TEXT")
            print("🔧 Додано колонку consent_doc_path в таблицю specialists")
        if "consent_at" not in columns:
            cursor.execute("ALTER TABLE specialists ADD COLUMN consent_at TEXT")
            print("🔧 Додано колонку consent_at в таблицю specialists")
        if "kep_signature_path" not in columns:
            cursor.execute("ALTER TABLE specialists ADD COLUMN kep_signature_path TEXT")
            print("🔧 Додано колонку kep_signature_path в таблицю specialists")
            
        # Міграція для нових тарифних колонок
        new_cols = {
            "court_cases": "INTEGER DEFAULT 0",
            "team_work": "INTEGER DEFAULT 0",
            "avg_service_price": "TEXT",
            "tariff_stage": "TEXT DEFAULT 'stage_1'",
            "tariff_plan": "TEXT DEFAULT 'grant_standard'",
            "tariff_fixed_fee": "REAL DEFAULT 0.0",
            "tariff_commission_pct": "REAL DEFAULT 0.0",
            "contract_signed_date": "TEXT",
            "contract_end_date": "TEXT"
        }
        for col_name, col_type in new_cols.items():
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE specialists ADD COLUMN {col_name} {col_type}")
                print(f"🔧 Додано тарифну колонку {col_name} в таблицю specialists")
    except Exception as e:
        print(f"Попередження міграції: {e}")

    # 2. Ветерани (користувачі)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS veterans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id TEXT UNIQUE,
            name TEXT,
            phone TEXT,
            verified_status INTEGER DEFAULT 0, -- 0-немає, 1-Дія
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Журнал координації (Логи диспетчерської)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intake_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veteran_id INTEGER,
            specialist_id INTEGER,
            status TEXT DEFAULT 'requested', -- requested, completed, cancelled
            feedback_score INTEGER,
            feedback_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(veteran_id) REFERENCES veterans(id),
            FOREIGN KEY(specialist_id) REFERENCES specialists(id)
        )
    ''')

    # 4. Освітній Хаб (Гранти та ваучери)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS education (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            institution TEXT,
            title TEXT,
            desc TEXT,
            price TEXT,
            link TEXT,
            deadline TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ База даних ініціалізована за шляхом: {DB_PATH}")

if __name__ == "__main__":
    init_db()
