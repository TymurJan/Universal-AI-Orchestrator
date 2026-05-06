import sys
import os
import re

def check_integrity(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: File {file_path} not found.")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    violations = []

    # 1. Спроба знайти трикрапки (поза межами блоків коду, якщо це можливо)
    # Але для спрощення шукаємо просто "..." як окремий елемент або в тексті
    if "..." in content:
        # Перевіряємо, чи це не частина синтаксису (хоча в нашому проекті краще уникати)
        # Якщо трикрапка стоїть окремою строкою або в оточенні тексту "(...)"
        if re.search(r'\(\.\.\.\)|\.{3,}', content):
            violations.append("Знайдено трикрапки (placeholder '...')")

    # 2. Пошук текстових маркерів скорочення
    short_markers = [
        "без змін", 
        "unchanged", 
        "решта пунктів", 
        "аналогічно", 
        "копіює попередній",
        "тільки заголовок"
    ]
    
    for marker in short_markers:
        if marker.lower() in content.lower():
            violations.append(f"Знайдено маркер скорочення: '{marker}'")

    # 3. Перевірка на критично малий обсяг для важливих файлів
    lines = content.splitlines()
    if file_path.endswith('.md') and len(lines) < 20 and "plan" in file_path.lower():
        violations.append(f"Занадто малий обсяг для плану ({len(lines)} рядків). Ймовірно, дані втрачені.")

    if violations:
        print(f"🛑 INTEGRITY VIOLATION in {file_path}:")
        for v in violations:
            print(f"   - {v}")
        return False
    
    print(f"✅ Integrity check passed for {file_path}.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python integrity_guard.py <file_path>")
        sys.exit(1)
    
    target = sys.argv[1]
    if check_integrity(target):
        sys.exit(0)
    else:
        sys.exit(1)
