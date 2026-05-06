import re
from pathlib import Path
from datetime import datetime

class NotebookManager:
    """Керування базою знань ГО 'Талан ЮА' (NotebookLM Integration)"""
    def __init__(self, kb_path: Path, protocol_path: Path = None):
        self.kb_path = Path(kb_path)
        self.protocol_path = Path(protocol_path) if protocol_path else None

    def find_file(self, keyword: str) -> list[Path]:
        """Шукає файл у Knowledge_Base за ключовим словом у назві або імені папки."""
        keyword_lower = keyword.lower().strip()
        matches = []
        for path in self.kb_path.rglob("*.md"):
            if path.name == "README.md":
                continue
            if keyword_lower in path.stem.lower() or keyword_lower in str(path.parent.name).lower():
                matches.append(path)
        
        # Також шукаємо у Black_Swan_Protocol
        if self.protocol_path:
            for path in self.protocol_path.rglob("*.md"):
                if keyword_lower in path.stem.lower():
                    matches.append(path)
        return matches

    def minify_text_for_llm(self, text: str) -> str:
        """Стискає текст для зменшення споживання токенів (видаляє зайве форматування)."""
        if not text:
            return ""
        
        # Видаляємо надлишкові пусті рядки (більше 2 підряд)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Видаляємо HTML-коментарі <!-- --> якщо вони є
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        # Видаляємо серії пробілів/табів (але не ламаємо код або списки)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        
        return text.strip()

    def read_file(self, path: Path, max_chars: int = 6000) -> str:
        """Читає вміст файлу з обмеженням за символами та стискає його для економії токенів."""
        try:
            text = path.read_text(encoding="utf-8")
            
            # Мініфікуємо текст перед обрізкою
            minified_text = self.minify_text_for_llm(text)
            
            if len(minified_text) > max_chars:
                minified_text = minified_text[:max_chars] + "\n\n... (скорочено)"
            return minified_text
        except Exception as e:
            return f"Помилка читання: {e}"

    def get_kb_tree(self) -> str:
        """Повертає відформатовану текстову структуру бази знань."""
        if not self.kb_path.exists():
            return "❌ Папка Knowledge_Base не знайдена."
        
        lines = ["📚 **База Знань Антігравіті:**\n"]
        for category in sorted(self.kb_path.iterdir()):
            if category.is_dir():
                files = list(category.rglob("*.md"))
                icon = "📂"
                lines.append(f"{icon} **{category.name}** ({len(files)} файлів)")
                for f in files[:5]:  # Показуємо макс. 5 файлів
                    lines.append(f"   📄 `{f.name}`")
                if len(files) > 5:
                    lines.append(f"   ... та ще {len(files)-5}")
            elif category.suffix == ".md" and category.name != "README.md":
                lines.append(f"📄 `{category.name}`")
        
        lines.append(f"\n💡 Всього категорій: {sum(1 for d in self.kb_path.iterdir() if d.is_dir())}")
        lines.append("Команди: /аудіо, /квіз, /флешкартки, /записати, /блокнот")
        return "\n".join(lines)

    def create_notebook(self, topic: str, gpt_structure: str, project_path: Path) -> dict:
        """Створює новий блокнот з шаблонною або згенерованою структурою."""
        safe_name = re.sub(r'[^\w\s\-]', '', topic).strip().replace(' ', '_')
        
        structure = gpt_structure
        if not structure:
            structure = f"# {topic}\n\n## Мета\n\n## Контекст\n\n## Ключові факти\n\n## Контакти\n\n## Наступні кроки\n\n## Нотатки\n"
        
        # Визначаємо категорію (за замовчуванням — Service Activity)
        target_dir = self.kb_path / "02_Service_Activity_Partnerships"
        if not target_dir.exists():
            target_dir = self.kb_path
        
        file_path = target_dir / f"{safe_name}.md"
        file_path.write_text(structure, encoding="utf-8")
        
        try:
            rel_path = file_path.relative_to(project_path)
        except ValueError:
            rel_path = file_path.name
            
        return {
            "success": True,
            "path": file_path,
            "rel_path": rel_path,
            "message": f"✅ Блокнот створено!\n📂 Шлях: `{rel_path}`\n📝 Тепер ви можете додавати записи через `/записати {topic} | <текст>`"
        }

    def save_note(self, category: str, raw_text: str, formatted_text: str) -> dict:
        """Зберігає відформатований запис до нотаток відповідної категорії."""
        # Знаходимо або створюємо відповідну папку
        cat_dir = None
        for d in self.kb_path.iterdir():
            if d.is_dir() and category.lower() in d.name.lower():
                cat_dir = d
                break
        
        created_new = False
        if not cat_dir:
            # Створюємо нову категорію
            safe_name = re.sub(r'[^\w\s\-]', '', category).strip().replace(' ', '_')
            cat_dir = self.kb_path / f"99_{safe_name}"
            cat_dir.mkdir(parents=True, exist_ok=True)
            created_new = True
            
        # Зберігаємо у файл нотаток
        notes_file = cat_dir / "Notes.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n\n---\n### 📝 Запис від {timestamp}\n\n{formatted_text}\n"
        
        is_new_file = not notes_file.exists() or notes_file.stat().st_size == 0
        
        with open(notes_file, "a", encoding="utf-8") as f:
            if is_new_file:
                f.write(f"# Нотатки: {category}\n")
            f.write(entry)
            
        return {
            "success": True,
            "cat_dir_name": cat_dir.name,
            "file_name": notes_file.name,
            "created_new_category": created_new
        }
