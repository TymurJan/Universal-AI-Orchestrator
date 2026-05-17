import json
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "novy_shlyakh.db")
SPEC_JSON = os.path.join(os.path.dirname(__file__), "data", "specialists.json")
EDU_JSON = os.path.join(os.path.dirname(__file__), "data", "education.json")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Міграція спеціалістів
    if os.path.exists(SPEC_JSON):
        with open(SPEC_JSON, 'r', encoding='utf-8') as f:
            specialists = json.load(f)
            for s in specialists:
                # Обробка координат (JSON list -> SQL string)
                coords = ""
                if "coordinates" in s and isinstance(s["coordinates"], list):
                    coords = f"{s['coordinates'][0]}, {s['coordinates'][1]}"
                
                cursor.execute('''
                    INSERT INTO specialists (name, category, role, phone, address, coordinates, bio, status, tg_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    s.get("name"),
                    s.get("category"),
                    s.get("role") or s.get("category"),
                    s.get("phone"),
                    s.get("address"),
                    coords,
                    s.get("bio"),
                    s.get("status", "verified"),
                    s.get("id")
                ))
        print(f"✅ Перенесено {len(specialists)} спеціалістів.")

    # 2. Міграція освітніх програм
    if os.path.exists(EDU_JSON):
        with open(EDU_JSON, 'r', encoding='utf-8') as f:
            education = json.load(f)
            for e in education:
                cursor.execute('''
                    INSERT INTO education (category, institution, title, desc, price, link, deadline)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    e.get("category"),
                    e.get("institution"),
                    e.get("title"),
                    e.get("desc"),
                    e.get("price"),
                    e.get("link"),
                    e.get("deadline")
                ))
        print(f"✅ Перенесено {len(education)} освітніх програм.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
