import sys
import os
import logging
import re
from datetime import datetime
from typing import Dict, Any

# Додаємо корінь проекту до шляху для імпорту інструментів
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tools.roi_optimizer import get_best_model
    from tools.integrity_check import IntegrityGuard
    from core.license_manager import LicenseManager
except ImportError:
    logging.error("Не вдалося імпортувати інструменти ROI, Integrity або LicenseManager.")

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class DynamicRouter:
    """
    Автоматичний Диспетчер (Роутер) моделей з функцією Чорної скриньки та прив'язкою до ліцензії.
    """
    
    def __init__(self, simulation_mode=True):
        self.simulation_mode = simulation_mode
        self.integrity_guard = IntegrityGuard()
        self.license_manager = LicenseManager()
        
        self.guard_short_markers = [
            "без змін", "unchanged", "решта", "аналогічно", 
            "пропущено", "skipped", "...", "placeholder"
        ]
        self.integrity_guard.short_markers = self.guard_short_markers
        
        # Налаштування логів форензики (Чорна скринька)
        self.forensics_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "forensics")
        os.makedirs(self.forensics_dir, exist_ok=True)

    def dispatch(self, prompt: str, quality: str = "standard", expected_output_words: int = 500) -> Dict[str, Any]:
        """
        Головний метод: оцінює, обирає модель та виконує запит.
        """
        input_words = len(prompt.split())
        recommendation = get_best_model(quality, input_words, expected_output_words)
        chosen_model = recommendation["model"]
        
        logging.info(f"🚀 Роутер обрав модель [{chosen_model}] для рівня якості [{quality}].")

        # Додаємо інструкцію про роздуми до промпту
        enhanced_prompt = prompt + "\n\nIMPORTANT: Wrap your internal reasoning in <thought> tags before providing the final answer."

        # 2. Виконання запиту
        if self.simulation_mode:
            raw_response = self._simulate_api_call(enhanced_prompt, chosen_model, quality)
        else:
            raw_response = self._real_api_call(enhanced_prompt, chosen_model)

        # 3. Екстракція роздумів (Black Box logic)
        thought_block = ""
        final_text = raw_response
        
        match = re.search(r'<thought>(.*?)</thought>', raw_response, re.DOTALL)
        if match:
            thought_block = match.group(1).strip()
            final_text = re.sub(r'<thought>.*?</thought>', '', raw_response, flags=re.DOTALL).strip()
            
            # ОТРИМАННЯ ДАНИХ ЛІЦЕНЗІЇ ДЛЯ ЛОГУ
            license_key = "UNKNOWN-LICENSE"
            if os.path.exists("license.key"):
                with open("license.key", "r") as f: license_key = f.read().strip()
            
            # Зберігаємо "докази" у Чорну скриньку з прив'язкою
            self._save_forensics(prompt, chosen_model, thought_block, license_key)
            self._rotate_logs() # Автоматична ротація (ліміт 100)

        success, violations = self.integrity_guard.check_content(final_text)
        status = "success" if success else "warning"
        
        return {
            "status": status,
            "model": chosen_model,
            "text": final_text,
            "thought_captured": bool(thought_block),
            "violations": violations if not success else [],
            "savings": recommendation["savings_pct"]
        }

    def _save_forensics(self, prompt: str, model: str, thought: str, license_key: str):
        """Зберігає роздуми ШІ в папку для аудиту з ідентифікацією заліза."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trace_{timestamp}.log"
        path = os.path.join(self.forensics_dir, filename)
        
        hwid = self.license_manager.hwid # Отримуємо унікальний ID заліза
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
            f.write(f"LICENSE_KEY: {license_key}\n")
            f.write(f"HARDWARE_ID (HWID): {hwid}\n")
            f.write(f"MODEL: {model}\n")
            f.write(f"PROMPT_PREVIEW: {prompt[:100]}...\n")
            f.write("-" * 50 + "\n")
            f.write(f"INTERNAL REASONING (BLACK BOX):\n{thought}\n")
            f.write("-" * 50 + "\n")
        
        logging.info(f"🛡️ Доказова база збережена (Прив'язано до HWID: {hwid[:10]}...)")

    def _rotate_logs(self, limit: int = 100):
        """Видаляє старі логи, якщо їх кількість перевищує ліміт."""
        try:
            logs = sorted(
                [os.path.join(self.forensics_dir, f) for f in os.listdir(self.forensics_dir) if f.endswith(".log")],
                key=os.path.getmtime
            )
            if len(logs) > limit:
                for i in range(len(logs) - limit):
                    os.remove(logs[i])
                    logging.info(f"🧹 Ротація: видалено застарілий лог [{os.path.basename(logs[i])}]")
        except Exception as e:
            logging.error(f"Помилка при ротації логів: {e}")

    def _simulate_api_call(self, prompt: str, model: str, quality: str) -> str:
        import time
        time.sleep(1)
        if quality == "high":
            return f"<thought>Запит високої складності. Використовую {model}. Перевіряю юридичні терміни.</thought>[FULL REPORT BY {model}]\nОсь детальний технічний аналіз вашого запиту."
        else:
            return f"<thought>Запит стандартний.</thought>[DRAFT BY {model}]\nОсь базова обробка."

    def _real_api_call(self, prompt: str, model: str) -> str:
        return "<thought>Реальний виклик.</thought>Відповідь від реального API."

if __name__ == "__main__":
    router = DynamicRouter(simulation_mode=True)
    res = router.dispatch("Створи юридичний звіт", quality="high")
    print(f"Captured: {res['thought_captured']}")
