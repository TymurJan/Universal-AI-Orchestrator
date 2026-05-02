import argparse
import requests
import sys
import os

def send_telegram_message(token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"✅ Успішно опубліковано текст у Telegram (Chat: {chat_id})")
    else:
        print(f"❌ Помилка відправки Telegram: {response.text}")
        sys.exit(1)

def send_telegram_photo(token: str, chat_id: str, photo_path: str, caption: str):
    if not os.path.exists(photo_path):
        print(f"❌ Помилка: Файл фотографії не знайдено за шляхом {photo_path}")
        sys.exit(1)
        
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    data = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "HTML"
    }
    
    try:
        with open(photo_path, 'rb') as photo_file:
            files = {"photo": photo_file}
            response = requests.post(url, data=data, files=files)
            
        if response.status_code == 200:
            print(f"✅ Успішно опубліковано фото з текстом у Telegram (Chat: {chat_id})")
        else:
            print(f"❌ Помилка відправки фото: {response.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Помилка роботи з файлом {photo_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal AI Orchestrator: SMM Poster (Telegram)")
    parser.add_argument("--token", required=True, help="Telegram Bot Token")
    parser.add_argument("--chat", required=True, help="Telegram Chat ID (починається на -, якщо це канал)")
    parser.add_argument("--text", type=str, help="Текст або опис для публікації")
    parser.add_argument("--photo", type=str, help="Абсолютний шлях до зображення (опціонально)")
    
    args = parser.parse_args()
    
    if not args.text and not args.photo:
        print("❌ Помилка: Вкажіть текст (--text) або фото (--photo).")
        sys.exit(1)
        
    if args.photo:
        send_telegram_photo(args.token, args.chat, args.photo, args.text or "")
    else:
        send_telegram_message(args.token, args.chat, args.text)
