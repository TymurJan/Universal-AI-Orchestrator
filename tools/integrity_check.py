import os
import re
import json
import logging
import sys

# Налаштування логування: виводимо все у stderr для чистоти
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class IntegrityGuard:
    def __init__(self):
        self.truth_vault_path = r"d:/ГО Талан UA/Talan UA Antigravity manager/.agents/internal_forensics/truth_vault.json"

    def load_truth(self):
        with open(self.truth_vault_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def check_content(self, content):
        violations = []
        truth = self.load_truth()

        # БЕЗУМОВНА ПЕРЕВІРКА (Жодних 'if header in content')
        print("\n--- [IRON GUARD STRICT AUDIT START] ---")
        
        # 1. Перевірка Фіч (мінімум 2 згадки кожна)
        for feature in truth["features"]:
            count = content.lower().count(feature.lower())
            if count < 2:
                violations.append(f"ВТРАЧЕНО ФІЧУ: [{feature}] (Знайдено лише {count} разів, а має бути 2)")
            else:
                print(f"  [OK] Feature: {feature} ({count} times)")

        # 2. Перевірка СЕО (має бути хоча б 1 згадка)
        for kw in truth["seo_core"]:
            if kw.lower() not in content.lower():
                violations.append(f"ВТРАЧЕНО СЕО: [{kw}]")
            else:
                pass # Не забиваємо лог успішними СЕО, їх багато

        print("--- [AUDIT END] ---\n")

        if violations:
            for v in violations:
                logging.error(f"  [CRITICAL ERROR] {v}")
            return False
        
        return True

    def check_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if not self.check_content(content):
                logging.error(f"🛑 ПРОВАЛ ЦІЛІСНОСТІ: {os.path.basename(file_path)}")
                return False
            logging.info(f"✅ Iron Guard: {os.path.basename(file_path)} — ПОВНА ЦІЛІСНІСТЬ.")
            return True
        except Exception as e:
            logging.error(f"Помилка аудиту: {e}")
            return False

if __name__ == "__main__":
    guard = IntegrityGuard()
    target = sys.argv[1] if len(sys.argv) > 1 else "docs/landing_plan.md"
    if guard.check_file(target):
        sys.exit(0)
    else:
        sys.exit(1)
