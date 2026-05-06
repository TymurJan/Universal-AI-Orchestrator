import requests
import json
import os

# КОНФІГУРАЦІЯ
SHEET_ID = "1o8vCAj5O7T3vP209KZmCDGzi5SDbX1F0GFfaIUI7nAA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
CRM_FILE = r"d:\ГО Талан UA\Talan UA Antigravity manager\Black_Swan_Protocol\02_Project_Ashram\Contacts\Mailing_List.md"
LAST_COUNT_FILE = r"d:\ГО Талан UA\Talan UA Antigravity manager\talan\autobot\last_response_count.json"

def get_response_count():
    try:
        response = requests.get(CSV_URL)
        if response.status_code == 200:
            lines = response.text.strip().split("\n")
            return len(lines) - 1 # Виключаємо хедер
    except Exception as e:
        print(f"Помилка моніторингу: {e}")
    return 0

def silent_check():
    current_count = get_response_count()
    
    # Завантажуємо попередню кількість
    last_count = 0
    if os.path.exists(LAST_COUNT_FILE):
        with open(LAST_COUNT_FILE, "r") as f:
            data = json.load(f)
            last_count = data.get("count", 0)
    
    if current_count > last_count:
        print(f"ЗНАЙДЕНО НОВІ ВІДПОВІДІ: {current_count - last_count} нових записів.")
        # Оновлюємо лічильник
        with open(LAST_COUNT_FILE, "w") as f:
            json.dump({"count": current_count}, f)
        return True
    
    print("Змін не виявлено.")
    return False

if __name__ == "__main__":
    silent_check()
