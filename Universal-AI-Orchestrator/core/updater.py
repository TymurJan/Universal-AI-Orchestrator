import json
import os
import time
import sys
from pathlib import Path

# Спробуємо імпортувати rich для гарного UI
try:
    from rich.console import Console
    from rich.panel import Panel
    HAS_RICH = True
    CONSOLE = Console()
except ImportError:
    HAS_RICH = False

# Шляхи
BASE_DIR = Path(__file__).parent.parent
VERSION_FILE = BASE_DIR / "version.json"

# Конфігурація (в реальному продукті це URL вашого сервера)
REMOTE_REGISTRY_URL = "https://api.talan-ua.org/orchestrator/registry.json"

class ProductUpdater:
    def __init__(self, current_version="1.1.7"):
        self.current_version = current_version
        self._ensure_version_file()

    def _ensure_version_file(self):
        """Гарантує наявність локального файлу версії."""
        if not VERSION_FILE.exists():
            with open(VERSION_FILE, "w", encoding="utf-8") as f:
                json.dump({"version": self.current_version, "last_check": ""}, f)

    def get_local_version(self):
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("version", self.current_version)
        except Exception:
            return self.current_version

    def check_for_updates(self):
        """
        Перевіряє наявність оновлень. 
        У демо-режимі ми симулюємо знаходження нової версії.
        """
        local_v = self.get_local_version()
        
        # СИМУЛЯЦІЯ: На сервері вийшла версія 1.1.8
        remote_v = "1.1.8" 
        
        if remote_v > local_v:
            self.notify_user(remote_v)
            return True
        return False

    def notify_user(self, new_version):
        """Візуальне сповіщення користувача в стилі системного апдейта."""
        update_notes = [
            "• [БЕЗПЕКА] Впроваджено 'Чорну скриньку' для логування розсуду ШІ.",
            "• [ЛОГІКА] Оновлено промпти для NGO-грантів ( USAID v2.1 ).",
            "• [ROI] Додано підтримку нових моделей Claude 3.5 Haiku."
        ]
        
        if HAS_RICH:
            msg = f"\n[bold white]Доступне системне оновлення: v{new_version}[/bold white]\n"
            msg += "\n".join(update_notes)
            msg += "\n\n[italic cyan]Встановлення розпочнеться автоматично при наступному запиті...[/italic cyan]"
            
            CONSOLE.print(Panel(
                msg, 
                title="[bold red]🚀 ОНОВЛЕННЯ СИСТЕМИ[/bold red]", 
                border_style="bright_magenta",
                expand=False
            ))
        else:
            print(f"\n! --- ОНОВЛЕННЯ СИСТЕМИ: v{new_version} ---")
            for note in update_notes:
                print(note)
            print("! ------------------------------------------\n")

if __name__ == "__main__":
    # Тестовий запуск
    updater = ProductUpdater()
    updater.check_for_updates()
