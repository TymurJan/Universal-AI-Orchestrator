"""
Skill Manager for Universal AI Orchestrator
Detects installed AI Agent Skills and offers free bonus skills from the official repository.
"""

import os
import logging
import urllib.request
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()
log = logging.getLogger("SkillManager")

# =====================================================
# 🎁 Official Bonus Skill Registry (Free for all users)
# Source: https://github.com/TymurJan/
# =====================================================
BONUS_SKILLS_REGISTRY = [
    {
        "id": "the-ultimate-ui",
        "name": "The Ultimate UI (Expert UI/UX Architect)",
        "description": "Expert UI/UX Architect & Lead Design Engineer. Creates professional interfaces with design principles, WCAG system approach.",
        "source_url": "https://raw.githubusercontent.com/TymurJan/Universal-AI-Orchestrator/main/skills/the-ultimate-ui/SKILL.md",
        "install_path": ".agents/skills/The Ultimate UI/SKILL.md",
        "tags": ["ui", "ux", "design", "wcag", "frontend"]
    }
]


class SkillManager:
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.skills_path = self.project_path / ".agents" / "skills"

    def detect_installed_skills(self) -> list:
        """Scan for installed agent skills in the current project space."""
        if not self.skills_path.exists():
            return []
        return [d.name for d in self.skills_path.iterdir() if d.is_dir()]

    def check_ui_skill_present(self) -> bool:
        """Check if a UI/UX design skill is installed."""
        installed = [s.lower() for s in self.detect_installed_skills()]
        ui_keywords = ["ui", "design", "ux", "frontend", "ultimate"]
        return any(kw in s for s in installed for kw in ui_keywords)

    def offer_bonus_skills(self) -> bool:
        """
        Check for missing expert skills and propose free bonus download.
        Returns True if any skill was installed, False otherwise.
        """
        installed_any = False

        if not self.check_ui_skill_present():
            console.print(Panel(
                "[bold yellow]🎁 FREE BONUS SKILL DETECTED[/bold yellow]\n\n"
                "[white]The Ultimate UI (Expert UI/UX Architect)[/white] is not installed in this space.\n\n"
                "[dim]This free skill provides:\n"
                "• Expert UI/UX audit based on WCAG 2.1 standards\n"
                "• Design system review (typography, colors, accessibility)\n"
                "• Professional frontend code review\n\n"
                "Source: github.com/TymurJan/[/dim]",
                title="🛡️ Universal AI Orchestrator — Bonus Skill Available",
                border_style="yellow"
            ))

            answer = input("Завантажити безкоштовний UI/UX скіл? [y/N]: ").strip().lower()
            if answer in ['y', 'yes', 'д', 'так']:
                installed_any = self._install_skill(BONUS_SKILLS_REGISTRY[0])

        return installed_any

    def _install_skill(self, skill: dict) -> bool:
        """Download and install a skill from the official registry."""
        target_path = self.project_path / skill["install_path"]
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            console.print(f"[dim]⬇️  Завантаження {skill['name']}...[/dim]")
            urllib.request.urlretrieve(skill["source_url"], str(target_path))
            console.print(f"[bold green]✅ Скіл встановлено: {target_path}[/bold green]")
            return True
        except Exception as e:
            log.error(f"Не вдалося завантажити скіл: {e}")
            console.print(f"[bold red]❌ Помилка завантаження. Спробуйте вручну: {skill['source_url']}[/bold red]")
            return False


if __name__ == "__main__":
    sm = SkillManager(".")
    sm.offer_bonus_skills()
