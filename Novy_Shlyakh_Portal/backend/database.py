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
            phone TEXT,
            address TEXT,
            coordinates TEXT, -- Зберігаємо як "lat, lng"
            bio TEXT,
            status TEXT DEFAULT 'pending', -- pending, verified, rejected
            rating REAL DEFAULT 5.0,
            tg_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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
