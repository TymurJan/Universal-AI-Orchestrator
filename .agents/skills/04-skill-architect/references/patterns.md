# Шаблони для Проектування (Skill Patterns)

Використовуйте ці шаблони як основу для структури нових навичок.

## 1. Simple/Hub (Простий Диспетчер)
Найкращий вибір для навичок, що охоплюють декілька пов'язаних, але окремих тем.
- **Trigger**: "How do I do X or Y?"
- **Structure**: `SKILL.md` (головний) + `topic-a.md`, `topic-b.md`.

## 2. Workflow (Робочий Процес)
Для послідовностей, де результат кроку А потрібен для кроку Б.
- **Trigger**: "Execute the process for X."
- **Structure**: `SKILL.md` (чекліст завдань) + `references/step-details.md`.

## 3. Rules-Based (Система Правил)
Для аудиту коду, тексту або дизайну на відповідність стандартам.
- **Trigger**: "Review this", "Check for errors", "Audit quality".
- **Structure**: 
  - `rules/_sections.md` (картування категорій)
  - `rules/_template.md` (Why it matters, Wrong vs Right)
  - `rules/prefix-slug.md` (індивідуальне правило)

## 4. Expert-System (Система Знань)
Для роботи з великими специфікаціями або науковими даними.
- **Trigger**: "Explain X in depth", "Analyze data based on Y".
- **Structure**: `SKILL.md` + `references/knowledge-base.md` + `references/definitions.md`.

---
*Примітка: При виборі патерна завжди пріоритезуйте той, який використовує менше токенів у головному файлі.*
