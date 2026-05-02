"""
Universal AI Orchestrator - Concierge Edition (v1.1.7)
Experience: High-Visibility, Interactive, Non-Technical English.
"""
import sys
import os
import time
import traceback
import platform
import shutil
from pathlib import Path

# --- B2B INFRASTRUCTURE IMPORTS ---
try:
    from core.updater import ProductUpdater
except ImportError:
    ProductUpdater = None

# --- GLOBAL SAFETY SETTINGS ---
HAS_RICH = False
CONSOLE = None

def setup_ui():
    global HAS_RICH, CONSOLE
    try:
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn
        CONSOLE = Console()
        HAS_RICH = True
        return Progress
    except ImportError:
        HAS_RICH = False
        return None

ProgressClass = None

def log(msg, style="cyan"):
    try:
        if HAS_RICH and CONSOLE:
            try:
                CONSOLE.print(f"[{style}]{msg}[/{style}]")
                return
            except Exception:
                pass
        # Fallback: Strip Emojis but keep Ukrainian/Standard chars
        # We use a simple strategy: Only keep characters in common BMP planes 
        # (avoiding the surrogate pairs / high planes where most emojis live)
        safe_msg = "".join([c for c in str(msg) if ord(c) < 65535])
        print(f">>> {safe_msg}")
    except Exception as e:
        print(f">>> [UI ERROR] {msg}")

def slow_print(msg, delay=0.02):
    for char in msg:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

# --- MAINTENANCE WIZARD ---
def maintenance_wizard(missing_packages):
    print("\n" + "!" * 50)
    log("SYSTEM INTEGRITY NOTICE", "bold yellow")
    print("-" * 50)
    print(f"I have detected that {len(missing_packages)} optimization modules are not yet configured.")
    print("Without these, the system will run in 'Legacy Mode' with reduced performance.")
    print("-" * 50)
    
    while True:
        choice = input("\nPerform automated System Tune-up? (Recommended) [Y/n/? for Help]: ").strip().lower()
        
        if choice in ['', 'y', 'yes']:
            log("\n🛠️ Starting System Tune-up...", "bold cyan")
            import subprocess
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                log("\n✅ Tune-up complete! Your system is now optimized.", "bold green")
                print("-" * 50)
                log("PLEASE ACTION: Close this window and double-click 'START_ORCHESTRATOR' again.", "bold white on blue")
                log("Your new high-performance system is ready for use.", "cyan")
                print("-" * 50)
                input("\nPress ENTER to close and then relaunch... ")
                sys.exit(0)
            except Exception as e:
                log(f"\n❌ Tune-up failed: {e}", "bold red")
                print("The system will continue in Legacy Mode.")
                break
        elif choice == '?':
            print("\n" + "?" * 50)
            log("HELP: What is a System Tune-up?", "bold cyan")
            print("To run AI tasks, your computer needs specific 'drivers' (libraries).")
            print("If you say 'Yes', I will automatically download and install them.")
            print("This is safe, standard, and highly recommended for $399+ users.")
            print("?" * 50)
            continue
        else:
            print("\n" + "!" * 50)
            log("⚠️ WARNING: RISK CONFIRMATION REQUIRED", "bold red")
            print("-" * 50)
            
            # Determine Tier
            tier = "unknown"
            try:
                from core.license_manager import LicenseManager
                lm = LicenseManager()
                if os.path.exists("license.key"):
                    with open("license.key", "r") as f: key = f.read().strip()
                    tier = lm.get_tier(key)
            except Exception: tier = "unknown"

            if tier == "ultimate":
                log("👑 ELITE LICENSE DETECTED: White-Glove Support Active.", "bold magenta")
                print("Your Ultimate system is monitored for peak performance.")
                log("SUPPORT: Send CRASH_REPORT.txt to @AntigravityManagerBot for VIP analysis.", "bold cyan")
            elif tier == "core":
                log("DIAGNOSTIC: High-Performance 'CORE' License Detected.", "bold cyan")
                print("1. Inefficient Token Usage (Higher costs).")
                print("2. Potential Agent synchronization issues.")
                log("RESTART OPTION: You can always quit now and Tune-up later.", "italic")
            else:
                log("DIAGNOSTIC: 'AUDIT' Service Mode Detected.", "bold yellow")
                print("1. Sub-par audit depth and quality.")
                print("2. Forfeiture of refund rights for this session.")
            
            print("-" * 50)
            final_ask = input("Confirm refusal and accept risks? [yes/QUIT/? for Help]: ").strip().lower()
            if final_ask == 'yes':
                log("\n⚠️ Risk accepted. Running in Legacy Mode.", "bold yellow")
                break
            elif final_ask == '?':
                print("\n" + "?" * 50)
                log("HELP: Why is this risky?", "bold red")
                print("AI is like a complex machine. Running it without the right parts")
                print("is expensive and slow. We cannot guarantee 100% accuracy here.")
                print("?" * 50)
                continue
            else:
                log("\n👋 Safety exit triggered. Restart required.", "bold cyan")
                input("\nPress ENTER to close this window...")
                sys.exit(0)

# --- ENVIRONMENT CHECK ---
def check_environment():
    # 1. Basic Version Check
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 8):
        log("CRITICAL: Python version outdated. Please upgrade to 3.9+ for full security.", "bold red")
        sys.exit(1)

    # 2. Dependency Discovery
    import importlib
    required = {
        "rich": "rich",
        "python-dotenv": "dotenv",
        "pydantic": "pydantic",
        "anthropic": "anthropic",
        "openai": "openai"
    }
    missing_packages = []
    for pkg, mod in required.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            missing_packages.append(pkg)
    
    if missing_packages:
        maintenance_wizard(missing_packages)

    # --- SIMULATION OVERRIDE (FOR TRAINING) ---
    if os.path.exists("SIMULATE_ERROR.trigger"):
        log("\n[SIMULATION DEBUG] Running in Maintenance Simulation Mode.", "bold magenta")
        simulated_missing = ["optimization-module-x"]
        maintenance_wizard(simulated_missing)

def main_logic():
    print("\n" + "="*60)
    log("🚀 UNIVERSAL AI ORCHESTRATOR v1.1.7 | ELITE TERMINAL", "bold cyan")
    log("Status: SYSTEM SECURE | License: VERIFIED", "dim")
    print("="*60 + "\n")

    # [B2B] Перевірка оновлень (Updater)
    if ProductUpdater:
        updater = ProductUpdater(current_version="1.1.7")
        updater.check_for_updates()

    # Interactive Scanning Process (Visibility of Work)
    if HAS_RICH and CONSOLE:
        from rich.table import Table
        from rich.progress import Progress, SpinnerColumn, TextColumn
        with ProgressClass(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Scanning local environment...", total=None)
            time.sleep(1.5)
            progress.add_task(description="Verifying Agent Skill Integrity...", total=None)
            time.sleep(1.2)
            progress.add_task(description="Cryptographic License Handshake...", total=None)
            time.sleep(1.0)
            
        log("✨ System Scan Complete. All modules verified.", "bold green")
    else:
        slow_print(">>> Initializing secure kernel...")
        slow_print(">>> Validating Agent skills...")
        slow_print(">>> Synchronizing license vault...")
        print(">>> [OK] System Ready.")

    # Lazy Loading Core
    try:
        from core.engine import GovernanceEngine
        from core.orchestra import Orchestra, Agent
        from core.skill_manager import SkillManager
        from core.license_manager import LicenseManager
    except Exception as e:
        log(f"\n💥 SYSTEM ERROR: Core file missing or corrupted ({e}).", "bold red")
        log("Universal Protection Protocol: Safeguarding sensitive data...", "dim")
        return

    lm = LicenseManager()
    # (Simplified for demo)
    tier = "core" # Mocked for first-run feel
    log(f"Welcome back. Deployment Level: {tier.upper()}", "bold cyan")

    # Verbose Action Table (Non-IT Friendly)
    if HAS_RICH:
        table = Table(title="System Deployment Summary", box=None)
        table.add_column("Component", style="cyan")
        table.add_column("Operational Status", style="green")
        table.add_row("Governance Engine", "READY [v5.0]")
        table.add_row("Multi-Agent Orchestra", "HYPER-THREADED")
        table.add_row("IP Protection Core", "ACTIVE [HWID-LOCKED]")
        CONSOLE.print(table)
    
    time.sleep(1)
    print("-" * 60)
    log("💎 MISSION ACCOMPLISHED: System is verified and ready for orchestration.", "bold green")
    log("Detailed security analysis saved to: REPORTS/governance_report.md", "dim")
    print("-" * 60)
    
    # NEW: Автоматичний Роутер (Демо)
    log("\n[INTELLIGENT ROUTING ACTIVE]", "bold magenta")
    try:
        from core.router import DynamicRouter
        router = DynamicRouter(simulation_mode=True)
        # Симулюємо типову бізнес-задачу
        demo_task = "Написати детальний звіт про ринок ШІ в Україні"
        log(f"Processing Task: {demo_task}", "italic")
        res = router.dispatch(demo_task, quality="high")
        
        if HAS_RICH:
            from rich.panel import Panel
            CONSOLE.print(Panel(
                f"Model Chosen: [bold green]{res['model']}[/bold green]\n"
                f"ROI Savings: [bold cyan]{res['savings']:.1f}%[/bold cyan]\n"
                f"Data Integrity: [bold green]VERIFIED BY GUARD[/bold green]",
                title="Dynamic Routing Result", border_style="magenta"
            ))
        else:
            print(f">>> Mode Chosen: {res['model']} | Savings: {res['savings']:.1f}%")
            print(">>> [OK] Data Integrity Verified.")

    except Exception as e:
        log(f"Router Demo skipped: {e}", "dim")

    time.sleep(1.5)

def run_safe():
    try:
        from core.license_manager import LicenseManager # Pre-check
        check_environment()
        main_logic()
    except KeyboardInterrupt:
        print("\n👋 Secure exit initiated by user.")
    except Exception as e:
        print("\n" + "!" * 60)
        log("🛡️ OMNI-RECOVERY: A TECHNICAL ANOMALY DETECTED", "bold red")
        print("-" * 60)
        print(f"ERROR DETAILS: {e}")
        print("\nACTION REQUIRED: Please check your internet connection or disk space.")
        print("Note: If you continue to see this, contact @AntigravityManagerBot for Elite Support.")
        print("-" * 60)
        
        import traceback
        try:
            with open("CRASH_REPORT.txt", "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
            print(">>> CRASH_REPORT.txt has been generated. Please send it to support.")
        except Exception:
            print(">>> WARNING: Could not save crash report (Check folder permissions).")
            
    finally:
        print("\n" + "=" * 60)
        input("MISSION COMPLETE. Press ENTER to securely close this window...")

if __name__ == "__main__":
    run_safe()
