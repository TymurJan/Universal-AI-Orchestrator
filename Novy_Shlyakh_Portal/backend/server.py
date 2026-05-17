import os
import json
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional
import shutil

# Імітація майбутнього сервера для AI-Чату
# Цей файл є заготовкою (boilerplate) для розгортання RAG-системи.
# Потребує: pip install fastapi uvicorn openai

app = FastAPI(title="Novy Shlyakh AI Backend", version="1.0.0")

class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"

class ChatResponse(BaseModel):
    reply: str
    sources: list = []

# Завантаження бази спеціалістів при старті
SPECIALISTS_DB = []
try:
    with open('data/specialists.json', 'r', encoding='utf-8') as f:
        SPECIALISTS_DB = json.load(f)
except FileNotFoundError:
    print("WARNING: Database not found. Fallback mode.")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Головний ендпоінт для спілкування з чатом на сайті.
    Коли з'явиться фінансування, тут буде додано логіку:
    1. Перетворення req.message на вектор.
    2. Пошук у Pinecone/Supabase.
    3. Звернення до OpenAI API.
    """
    
    # ІМІТАЦІЯ ВІДПОВІДІ (Stub)
    user_msg = req.message.lower()
    
    # Демонстрація реакції на ключові слова
    if "убд" in user_msg or "закон" in user_msg:
        reply = "Згідно з чинним законодавством України (Закон про статус ветеранів), ви маєте право на пільги. Детальну консультацію може надати наш юрист."
        sources = ["Закон України № 3551-XII"]
    elif "бізнес" in user_msg or "грант" in user_msg:
        reply = "Ви можете податися на державну програму «Власна справа». Вам може допомогти наша бізнес-ментор Ганна Грант."
        sources = ["Постанова КМУ № 738", "Ганна Грант (Ментор)"]
    else:
        reply = "Я AI-координатор центру «Новий Шлях». Я можу допомогти знайти потрібного спеціаліста або дати довідку по законодавству. Чим можу бути корисним?"
        sources = []

    return ChatResponse(reply=reply, sources=sources)

@app.post("/api/register-specialist")
async def register_specialist(
    name: str = Form(...),
    category: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    bio: str = Form(...),
    tg_id: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    document: UploadFile = File(...)
):
    """
    Ендпоінт для фінальної реєстрації спеціаліста (Крок 2).
    Зберігає дані та завантажені файли.
    """
    try:
        # Створюємо папки для завантажень, якщо їх немає
        os.makedirs("uploads/photos", exist_ok=True)
        os.makedirs("uploads/docs", exist_ok=True)
        
        photo_path = f"uploads/photos/{tg_id or 'anon'}_{photo.filename}"
        doc_path = f"uploads/docs/{tg_id or 'anon'}_{document.filename}"
        
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
            
        with open(doc_path, "wb") as buffer:
            shutil.copyfileobj(document.file, buffer)
            
        new_spec = {
            "id": tg_id or str(hash(phone)),
            "name": name,
            "category": category,
            "phone": phone,
            "address": address,
            "bio": bio,
            "photo_url": photo_path,
            "doc_url": doc_path,
            "status": "pending",
            "rating": "5.0",
            "reviews": []
        }
        
        # Завантажуємо поточну базу та додаємо нового
        db_path = "data/specialists.json"
        os.makedirs("data", exist_ok=True)
        
        current_db = []
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                current_db = json.load(f)
        
        current_db.append(new_spec)
        
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(current_db, f, ensure_ascii=False, indent=2)
            
        return {"status": "success", "message": "Заявка прийнята на модерацію"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "Novy Shlyakh AI Ready"}

if __name__ == "__main__":
    import uvicorn
    # Запуск: python server.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
