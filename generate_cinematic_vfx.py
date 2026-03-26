"""
Automation script to generate Cinematic VFX for the Universal AI Orchestrator.
This script uses the VFXConnector to prepare prompts and bridge with external APIs.
"""

from core.vfx_connector import VFXConnector
from rich.console import Console
from rich.panel import Panel

console = Console()

def run_cinematic_workflow():
    console.print(Panel("[bold cyan]🎬 AI Motion Director: Cinematic Orchestration[/bold cyan]", expand=False))
    
    # 1. Initialize Connectors for the best models
    luma = VFXConnector("luma")
    runway = VFXConnector("runway")
    
    console.print("\n[bold yellow]Step 1: Preparing High-Fidelity Prompts...[/bold yellow]")
    
    # Heart Prompt (Luma is best for biological loops)
    heart_prompt = luma.generate_video_prompt("heart", "beating")
    console.print(f"[bold red]❤️ Heart (Luma):[/bold red] {heart_prompt}")
    
    # Shield Prompt (Runway is best for energy motion)
    shield_prompt = runway.generate_video_prompt("shield", "protection")
    console.print(f"[bold blue]🛡️ Shield (Runway):[/bold blue] {shield_prompt}")
    
    console.print("\n[bold yellow]Step 2: Checking API Status...[/bold yellow]")
    
    # Check Luma status
    luma_status = luma.trigger_generation(heart_prompt)
    if luma_status["status"] == "AUTH_REQUIRED":
        console.print("[bold red]❌ AUTH REQUIRED:[/bold red] Please add [bold]LUMAAI_API_KEY[/bold] to your .env file.")
    else:
        console.print(f"[bold green]✅ Ready:[/bold green] {luma_status['message']}")
        
    console.print("\n[bold cyan]Step 3: Integration Guide[/bold cyan]")
    console.print("Once generated, place the .webm files in 'landing/' and update index.html to use <video>.")
    
    console.print("\n[bold green]Workflow Ready.[/bold green]")

if __name__ == "__main__":
    run_cinematic_workflow()
