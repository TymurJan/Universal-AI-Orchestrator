import sys
import os
import argparse
from pathlib import Path

try:
    import chromadb
except ImportError:
    print("Error: chromadb is not installed. Please run: pip install chromadb")
    sys.exit(1)

def get_db_path():
    # Робимо шлях локальним для програми Universal AI Orchestrator
    current_dir = Path(__file__).parent.parent
    return str(current_dir / ".orchestrator" / "chroma_db")

def init_client():
    db_path = get_db_path()
    os.makedirs(db_path, exist_ok=True)
    # Зберігання на диску (Persistent)
    return chromadb.PersistentClient(path=db_path)

def get_collection(client):
    try:
        # Для сумісності з різними версіями ChromaDB
        return client.get_or_create_collection(name="universal_knowledge_memory")
    except Exception as e:
        print(f"Error initializing collection: {e}")
        sys.exit(1)

def add_document(text: str, source: str = "manual"):
    client = init_client()
    collection = get_collection(client)
    
    import hashlib
    doc_id = hashlib.md5(text.encode('utf-8')).hexdigest()
    
    collection.add(
        documents=[text],
        metadatas=[{"source": source}],
        ids=[doc_id]
    )
    print(f"✅ Додано нотатку до пам'яті (Джерело: {source})")

def query_memory(query_text: str, n_results: int = 3):
    # Використовуємо кастомний логер або приховуємо warnings, оскільки ChromaDB любить сипати info-логами
    import logging
    logging.getLogger("chromadb").setLevel(logging.ERROR)
    
    client = init_client()
    collection = get_collection(client)
    
    count = collection.count()
    if count == 0:
        print("База порожня. Немає результатів.")
        return
        
    actual_results = min(n_results, count)
    results = collection.query(
        query_texts=[query_text],
        n_results=actual_results
    )
    
    print(f"\n🔍 РЕЗУЛЬТАТИ ПОШУКУ ПО ПАМ'ЯТІ:")
    print(f"Запит: '{query_text}'")
    print("=" * 60)
    
    if not results or not results['documents'] or not results['documents'][0]:
        print("Нічого релевантного не знайдено.")
        return
        
    for i, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][i] if results['metadatas'] else {}
        source = meta.get('source', 'unknown')
        print(f"🧠 Знахідка #{i+1} (Джерело: {os.path.basename(source)}):")
        print(doc)
        print("-" * 60)

def sync_feature(kb_path: str):
    p = Path(kb_path)
    if not p.exists() or not p.is_dir():
        print(f"Помилка: папка {kb_path} не існує.")
        sys.exit(1)
        
    client = init_client()
    collection = get_collection(client)
    
    docs = []
    ids = []
    metadatas = []
    
    import hashlib
    count = 0
    
    print(f"⌛ Сканування каталогу {kb_path}...")
    for root, _, files in os.walk(p):
        for file in files:
            if file.endswith(".md"):
                file_path = Path(root) / file
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                
                # Розбиваємо документ на логічні абзаци
                paragraphs = [par.strip() for par in content.split("\n\n") if len(par.strip()) > 40]
                
                for i, par in enumerate(paragraphs):
                    # Унікальний ID для кожного абзацу
                    doc_id = hashlib.md5((str(file_path) + str(i)).encode('utf-8')).hexdigest()
                    docs.append(par)
                    ids.append(doc_id)
                    metadatas.append({"source": str(file_path)})
                    count += 1
                    
                    # Пакетне додавання по 100 абзаців
                    if len(docs) >= 100: 
                        # Upsert оновлює існуючі або додає нові
                        collection.upsert(documents=docs, metadatas=metadatas, ids=ids)
                        docs, ids, metadatas = [], [], []

    if docs:
        collection.upsert(documents=docs, metadatas=metadatas, ids=ids)
        
    print(f"✅ Синхронізація завершена. У базу завантажено {count} інформаційних блоків.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal AI Orchestrator Semantic Memory Tool")
    subparsers = parser.add_subparsers(dest="command", help="Доступні команди")
    
    query_parser = subparsers.add_parser("query", help="Шукати в пам'яті")
    query_parser.add_argument("text", type=str, help="Запит")
    query_parser.add_argument("-n", "--results", type=int, default=3, help="Кількість результатів")
    
    add_parser = subparsers.add_parser("add", help="Зберегти до пам'яті")
    add_parser.add_argument("text", type=str, help="Текст для збереження")
    add_parser.add_argument("-s", "--source", type=str, default="Усна вказівка агента", help="Джерело")
    
    sync_parser = subparsers.add_parser("sync", help="Синхронізувати цілу папку з нотатками")
    sync_parser.add_argument("folder", type=str, help="Шлях до папки (наприклад, Knowledge_Base)")
    
    args = parser.parse_args()
    
    if args.command == "query":
        query_memory(args.text, args.results)
    elif args.command == "add":
        add_document(args.text, args.source)
    elif args.command == "sync":
        sync_feature(args.folder)
    else:
        parser.print_help()
