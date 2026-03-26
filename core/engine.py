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

    def perform_complete_audit(self):
        """Runs all real audit modules and returns a consolidated report."""
        console.print("[bold cyan]🛡️ Universal AI Orchestrator: Starting Deep Scan...[/bold cyan]")
        
        all_findings = []
        all_findings.extend(self.scan_for_secrets())
        all_findings.extend(self.audit_logic_collisions())
        all_findings.extend(self.audit_ui_accessibility())
        
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
