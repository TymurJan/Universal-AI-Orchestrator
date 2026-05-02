"""
Governance and Audit Engine for Universal AI Orchestrator
This module contains real audit logic for security, ROI, and logic collision.
"""

import os
import re
import logging
from typing import List, Dict, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()
log = logging.getLogger("GovernanceEngine")

class GovernanceEngine:
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.findings = []

    def scan_for_secrets(self) -> List[Dict[str, Any]]:
        """Real scan for potential API keys or secrets in the codebase."""
        secret_patterns = {
            "OpenAI API Key": r"sk-[a-zA-Z0-9]{32,}",
            "Anthropic API Key": r"sk-ant-[a-zA-Z0-9]{32,}",
            "Generic Secret": r"(?i)(password|secret|key|token)\s*[:=]\s*['\"][^'\"]+['\"]"
        }
        
        findings = []
        for root, _, files in os.walk(self.project_path):
            if ".git" in root or ".orchestrator" in root:
                continue
            for file in files:
                if file.endswith((".py", ".env", ".html", ".js", ".md")):
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text(errors="ignore")
                        for name, pattern in secret_patterns.items():
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                findings.append({
                                    "type": "Security",
                                    "severity": "CRITICAL",
                                    "item": name,
                                    "file": str(file_path),
                                    "line": content.count("\n", 0, match.start()) + 1,
                                    "desc": f"Potential {name} exposed in plain text."
                                })
                    except Exception as e:
                        log.error(f"Could not read {file_path}: {e}")
        return findings

    def audit_logic_collisions(self) -> List[Dict[str, Any]]:
        """Scan for TODOs, FIXMEs, and potential logical conflicts in comments."""
        findings = []
        logic_patterns = {
            "TODO/FIXME": r"(?i)#\s*(TODO|FIXME|BUG)",
            "Logic Collision": r"(?i)conflict|contradict|collision"
        }
        
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    content = file_path.read_text(errors="ignore")
                    for name, pattern in logic_patterns.items():
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            findings.append({
                                "type": "Logic",
                                "severity": "MEDIUM" if "TODO" in name else "HIGH",
                                "item": name,
                                "file": str(file_path),
                                "line": content.count("\n", 0, match.start()) + 1,
                                "desc": f"Detected {name} marker requiring attention."
                            })
        return findings

    def audit_ui_accessibility(self) -> List[Dict[str, Any]]:
        """Scan for basic UI/UX formatting and WCAG compliance issues."""
        findings = []
        ui_patterns = {
            "Missing ALT tag": r"(?i)<img(?![^>]*\balt=)[^>]*>",
            "Missing HTML Lang": r"(?i)<html(?![^>]*\blang=)[^>]*>",
            "Hardcoded Contrast Risk": r"(?i)color:\s*(#F00|#FF0000|red|blue|#00F|#0000FF)"
        }
        
        for root, _, files in os.walk(self.project_path):
            if ".git" in root or ".orchestrator" in root:
                continue
            for file in files:
                if file.endswith((".html", ".css", ".jsx", ".tsx", ".js")):
                    file_path = Path(root) / file
                    content = file_path.read_text(errors="ignore")
                    for name, pattern in ui_patterns.items():
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            findings.append({
                                "type": "UI/UX",
                                "severity": "MEDIUM",
                                "item": name,
                                "file": str(file_path),
                                "line": content.count("\n", 0, match.start()) + 1,
                                "desc": f"UI Accessibility Issue: {name} detected."
                            })
        return findings

    def audit_skill_conflicts(self) -> List[Dict[str, Any]]:
        """Scan installed agent skills for domain overlaps and recommend resolution."""
        findings = []
        skills_path = self.project_path / ".agents" / "skills"
        if not skills_path.exists():
            return []

        domain_groups: Dict[str, List[str]] = {
            "design": ["ui", "ux", "design", "frontend", "css", "tailwind", "figma", "wcag", "interface", "visual"],
            "security": ["security", "auth", "vault", "pentest", "access", "credential", "vulnerability"],
            "management": ["manager", "orchestrat", "govern", "coordinator", "planner", "scheduler"],
            "legal": ["legal", "contract", "law", "regulation", "compliance", "gdpr", "privacy"],
            "grant": ["grant", "donor", "fund", "ngo", "proposal", "application"],
            "ai-model": ["gpt", "claude", "llm", "model", "inference", "openai", "anthropic"],
        }

        # Parse each skill: content, size, domain keyword density
        skill_data: Dict[str, Dict] = {}
        for skill_dir in skills_path.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            content = skill_md.read_text(errors="ignore")
            lower = content.lower()
            matched = [domain for domain, kws in domain_groups.items() if any(kw in lower for kw in kws)]
            if matched:
                skill_data[skill_dir.name] = {
                    "domains": matched,
                    "lines": len(content.splitlines()),
                    "density": {d: sum(1 for kw in kws if kw in lower) for d, kws in domain_groups.items() if d in matched}
                }

        # Find overlaps and compare skills in same domain
        domain_to_skills: Dict[str, List[str]] = {}
        for skill_name, data in skill_data.items():
            for domain in data["domains"]:
                domain_to_skills.setdefault(domain, []).append(skill_name)

        for domain, skills in domain_to_skills.items():
            if len(skills) < 2:
                continue

            # Compare by line count (richness) + keyword density in this domain
            scored = sorted(
                skills,
                key=lambda s: skill_data[s]["lines"] + skill_data[s]["density"].get(domain, 0) * 10,
                reverse=True
            )
            winner = scored[0]
            losers = scored[1:]

            # Determine if they are very close (merge candidate) or clearly different
            winner_score = skill_data[winner]["lines"] + skill_data[winner]["density"].get(domain, 0) * 10
            loser_score = skill_data[losers[0]]["lines"] + skill_data[losers[0]]["density"].get(domain, 0) * 10 if losers else 0
            ratio = loser_score / winner_score if winner_score > 0 else 0

            if ratio > 0.75:
                resolution = f"MERGE recommended: '{winner}' and '{losers[0]}' are similar in depth. Consider combining them into one comprehensive skill."
            else:
                resolution = f"KEEP '{winner}' (richer), REMOVE '{', '.join(losers)}': significantly less coverage."

            findings.append({
                "type": "Skill Conflict",
                "severity": "HIGH",
                "item": f"Domain overlap: '{domain}'",
                "file": ".agents/skills/",
                "line": 0,
                "desc": f"Conflict in '{domain}' domain between {skills}. RESOLUTION: {resolution}"
            })
        return findings

    def check_mirror_law_compliance(self) -> List[Dict[str, Any]]:
        """Check if all capabilities in capabilities.json are marked as synced (Mirror Law Guard)."""
        import json
        findings = []
        manifest_path = self.project_path / ".orchestrator" / "capabilities.json"
        if not manifest_path.exists():
            findings.append({
                "type": "Mirror Law",
                "severity": "CRITICAL",
                "item": "capabilities.json missing",
                "file": str(manifest_path),
                "line": 0,
                "desc": "Mirror Law manifest not found. Cannot verify Agent ↔ Product sync. Create .orchestrator/capabilities.json"
            })
            return findings

        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            findings.append({"type": "Mirror Law", "severity": "CRITICAL", "item": "Parse error", "file": str(manifest_path), "line": 0, "desc": str(e)})
            return findings

        for cap in data.get("capabilities", []):
            if cap.get("status") != "synced":
                findings.append({
                    "type": "Mirror Law Violation",
                    "severity": "CRITICAL",
                    "item": cap.get("name", "Unknown"),
                    "file": str(manifest_path),
                    "line": 0,
                    "desc": f"Capability '{cap['id']}' is NOT synced between Agent ('{cap['agent_section']}') and Product ('{cap['product_function']}')."
                })
        return findings

    def perform_complete_audit(self):
        """Runs all real audit modules and returns a consolidated report."""
        console.print("[bold cyan]🛡️ Universal AI Orchestrator: Starting Deep Scan...[/bold cyan]")
        
        all_findings = []
        all_findings.extend(self.check_mirror_law_compliance())
        all_findings.extend(self.scan_for_secrets())
        all_findings.extend(self.audit_logic_collisions())
        all_findings.extend(self.audit_ui_accessibility())
        all_findings.extend(self.audit_skill_conflicts())
        
        self.findings = all_findings
        
        if not all_findings:
            console.print("[bold green]✅ No high-severity issues found. Project is secure.[/bold green]")
        else:
            table = Table(title="Governance Audit Results")
            table.add_column("Severity", justify="center", style="bold red")
            table.add_column("Type", style="cyan")
            table.add_column("Item", style="white")
            table.add_column("Location", style="dim")
            
            for f in all_findings:
                style = "red" if f["severity"] == "CRITICAL" else "yellow"
                table.add_row(f["severity"], f["type"], f["item"], f"{f['file']}:{f['line']}", style=style)
            
            console.print(table)
            
        return all_findings

    def generate_markdown_report(self, output_path: str = "REPORTS/governance_report.md"):
        """Generates a professional Markdown report based on real findings in Ukrainian."""
        report = "# Universal AI Orchestrator: Звіт з управління (Governance Report)\n\n"
        report += "Згенеровано модулем Commercial Core v1.0.0\n\n"
        
        if not self.findings:
            report += "## ✅ Статус: БЕЗПЕЧНО\nКритичних проблем не виявлено.\n"
        else:
            report += "## 🚨 Виявлені зауваження\n\n"
            for f in self.findings:
                # Severity translation
                sev = "КРИТИЧНО" if f["severity"] == "CRITICAL" else "ВИСОКА" if f["severity"] == "HIGH" else "СЕРЕДНЯ"
                report += f"### [{sev}] {f['item']}\n"
                report += f"- **Тип:** {f['type']}\n"
                report += f"- **Файл:** `{f['file']}:{f['line']}`\n"
                report += f"- **Опис:** {f['desc']}\n\n"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        Path(output_path).write_text(report, encoding="utf-8")
        console.print(f"[bold green]📄 Звіт збережено у {output_path}[/bold green]")
        return output_path

if __name__ == "__main__":
    engine = GovernanceEngine(".")
    engine.perform_complete_audit()
    engine.generate_markdown_report()
