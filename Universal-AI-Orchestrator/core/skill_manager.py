"""
Skill Manager for Universal AI Orchestrator
Detects installed AI Agent Skills, reads their metadata,
resolves inheritance (extends), and auto-syncs capabilities.json.
"""

import os
import re
import logging
import urllib.request
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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
        self.capabilities_path = self.project_path / ".orchestrator" / "capabilities.json"

    # --------------------------------------------------
    # CORE: Skill Detection
    # --------------------------------------------------

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

    # --------------------------------------------------
    # NEW: YAML Metadata Reader
    # --------------------------------------------------

    def read_skill_metadata(self, skill_dir: Path) -> dict:
        """
        Parse YAML frontmatter from SKILL.md.
        Returns dict with: name, capability_id, domain, version,
                           synced_function, extends, description.
        Returns empty dict if SKILL.md not found or has no frontmatter.
        """
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            return {}

        content = skill_md.read_text(encoding="utf-8", errors="ignore")

        # Extract YAML block between --- markers
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return {}

        yaml_block = match.group(1)
        meta = {"_folder": skill_dir.name}

        # Parse each key: value line (simple, no PyYAML dependency)
        for line in yaml_block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ": " in line:
                key, _, value = line.partition(": ")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Skip multi-line description markers
                if value == ">":
                    continue
                meta[key] = value

        return meta

    def scan_all_skills(self) -> list:
        """
        Scan all installed skills and return list of metadata dicts.
        Resolves 'extends' inheritance automatically.
        """
        if not self.skills_path.exists():
            return []

        all_meta = {}
        for skill_dir in self.skills_path.iterdir():
            if skill_dir.is_dir():
                meta = self.read_skill_metadata(skill_dir)
                if meta:
                    all_meta[meta.get("name", skill_dir.name)] = meta

        # Resolve extends: inherit capability_id and domain from parent if missing
        for name, meta in all_meta.items():
            parent_name = meta.get("extends")
            if parent_name and parent_name in all_meta:
                parent = all_meta[parent_name]
                # Child inherits domain if not specified
                if "domain" not in meta and "domain" in parent:
                    meta["domain"] = parent["domain"]
                meta["_extends_resolved"] = True

        return list(all_meta.values())

    # --------------------------------------------------
    # NEW: Auto-Sync capabilities.json
    # --------------------------------------------------

    def sync_capabilities(self) -> dict:
        """
        Compare installed skills with capabilities.json.
        Adds new skills as 'pending', marks removed skills as 'orphaned'.
        Returns sync report.
        """
        skills = self.scan_all_skills()
        report = {"synced": [], "pending": [], "orphaned": [], "skipped": []}

        # Load existing capabilities.json
        if self.capabilities_path.exists():
            with open(self.capabilities_path, "r", encoding="utf-8") as f:
                caps_data = json.load(f)
        else:
            caps_data = {"_comment": "Auto-generated by SkillManager", "version": "1.0.0", "capabilities": []}

        existing_caps = {c["id"]: c for c in caps_data.get("capabilities", [])}

        # Check each installed skill
        for meta in skills:
            cap_id = meta.get("capability_id")
            if not cap_id:
                report["skipped"].append(meta.get("name", meta.get("_folder", "unknown")))
                continue

            if cap_id in existing_caps:
                report["synced"].append(cap_id)
            else:
                # New skill discovered — add as pending
                product_fn = meta.get("synced_function")
                is_synced = product_fn and str(product_fn).lower() != "null"
                new_entry = {
                    "id": cap_id,
                    "name": f"{meta.get('domain', 'general').title()}: {meta.get('name', cap_id)}",
                    "agent_section": "auto-discovered",
                    "product_function": product_fn if product_fn else "null",
                    "status": "synced" if is_synced else "pending"
                }
                caps_data["capabilities"].append(new_entry)
                existing_caps[cap_id] = new_entry
                report["pending"].append(cap_id)

        # Mark missing skills as orphaned
        installed_ids = {m.get("capability_id") for m in skills if m.get("capability_id")}
        for cap_id, cap in existing_caps.items():
            if cap_id not in installed_ids and cap.get("status") != "orphaned":
                cap["status"] = "orphaned"
                report["orphaned"].append(cap_id)

        # Save updated capabilities.json
        self.capabilities_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.capabilities_path, "w", encoding="utf-8") as f:
            json.dump(caps_data, f, ensure_ascii=False, indent=2)

        return report

    def print_sync_report(self, report: dict):
        """Display sync results in a styled table."""
        table = Table(title="🔄 Skill Sync Report", border_style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Skills")

        table.add_row("[green]✅ Synced[/green]", ", ".join(report["synced"]) or "—")
        table.add_row("[yellow]⏳ Pending[/yellow]", ", ".join(report["pending"]) or "—")
        table.add_row("[red]👻 Orphaned[/red]", ", ".join(report["orphaned"]) or "—")
        table.add_row("[dim]⏭ Skipped[/dim]", ", ".join(report["skipped"]) or "—")

        console.print(table)

        if report["pending"]:
            console.print(
                "[yellow]⚠️  Нові скіли знайдено. Перевір capabilities.json та додай synced_function якщо є.[/yellow]"
            )
        if report["orphaned"]:
            console.print(
                "[red]❗ Деякі скіли видалено. Позначено як 'orphaned' у capabilities.json.[/red]"
            )

    # --------------------------------------------------
    # EXISTING: Bonus Skill Downloader
    # --------------------------------------------------

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
    console.print("[bold cyan]🔄 Синхронізація скілів...[/bold cyan]")
    report = sm.sync_capabilities()
    sm.print_sync_report(report)
    sm.offer_bonus_skills()
