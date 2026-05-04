import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "Novy Shlyakh AI Ready"}

if __name__ == "__main__":
    import uvicorn
    # Запуск: python server.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
