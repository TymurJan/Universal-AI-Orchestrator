"""
Main Entry Point for Universal AI Orchestrator
Integrates Governance Audit and Multi-Agent Orchestration.
"""

import os
from pathlib import Path
from core.engine import GovernanceEngine
from core.orchestra import Orchestra, Agent
from rich.console import Console
import sys

console = Console()

def main():
    console.print("[bold cyan]🚀 Universal AI Orchestrator v1.0.0[/bold cyan]")
    console.print("[dim]Powered by GO Talan UA[/dim]\n")

    # Step 0: User Agreement Prompt (TERMS OF USE)
    console.print("[bold yellow]Перед початком роботи ви маєте погодитись з TERMS_OF_USE.md[/bold yellow]")
    console.print("[dim]Система діє як ваш Стратегічний Радник і НЕ приймає фінальних рішень без дозволу.[/dim]")
    agreement = input("Чи погоджуєтесь ви з політикою використання? [y/N]: ").strip().lower()
    if agreement not in ['y', 'yes', 'д', 'так']:
        console.print("[bold red]🛑 Доступ заборонено (User declined Terms of Use). Вихід.[/bold red]")
        sys.exit(1)
        
    console.print("[bold green]✅ Згоду прийнято. Запуск ініціалізовано.[/bold green]\n")

    # Step 1: Governance Audit (Security & Logic)
    engine = GovernanceEngine(".")
    findings = engine.perform_complete_audit()
    engine.generate_markdown_report("REPORTS/governance_report.md")

    # Step 2: Demonstration of Orchestration (State Management)
    if not findings:
        console.print("\n[bold green]🛡️ Audit Clean. Proceeding to Orchestration...[/bold green]")
    else:
        console.print(f"\n[bold yellow]⚠️ Found {len(findings)} issues during audit. Proceeding with caution...[/bold yellow]")

    # Building a demo team
    orchestra = Orchestra()
    analyst = Agent("Analyst", "Security Researcher")
    optimizer = Agent("Optimizer", "ROI Specialist")
    
    orchestra.register_agent(analyst)
    orchestra.register_agent(optimizer)
    
    # Real logic flow demo: Analyst output passed to Optimizer
    demo_tasks = [
        {"agent": "Analyst", "task": f"Analyze the audit report with {len(findings)} findings."},
        {"agent": "Optimizer", "task": "Based on the analysis: {Analyst_output}, suggest one way to optimize token usage."}
    ]
    
    final_output = orchestra.run_sequence(demo_tasks)
    
    console.print("\n[bold green]✨ Orchestration Sequence Success![/bold green]")
    console.print(f"[bold cyan]Final Suggestion:[/bold cyan] {final_output['Optimizer_output']}")

if __name__ == "__main__":
    # Ensure REPORTS folder exists
    os.makedirs("REPORTS", exist_ok=True)
    main()
