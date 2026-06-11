"""
Universal AI Orchestrator & Governance Guard
This script analyzes project structure, detects conflicts, and proposes optimizations.
"""

import os
import sys
import logging
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import json

# --- Config ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# --- Logging ---
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "orchestrator_log.txt", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("UniversalOrchestrator")

# --- Configuration ---
RECOMMENDATIONS_DIR = BASE_DIR / ".agents" / "recommendations"
RECOMMENDATIONS_DIR.mkdir(parents=True, exist_ok=True)

class MetaOptimizer:
    def __init__(self):
        pass

    def scan_project_structure(self):
        """Сканує структуру проєкту: скіли, промти, конфігурації."""
        log.info("🔍 Запускаю Deep Scan структури проєкту.")
        report = {
            "skills": self._scan_skills(),
            "prompts": self._scan_prompts(),
            "config": self._scan_configs()
        }
        return report

    def _scan_skills(self):
        skills_path = BASE_DIR / ".agents" / "skills"
        skills_info = []
        if skills_path.exists():
            for skill_dir in skills_path.iterdir():
                if skill_dir.is_dir():
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        skills_info.append({
                            "name": skill_dir.name,
                            "path": str(skill_md),
                            "size": skill_md.stat().st_size
                        })
        return skills_info

    def _scan_prompts(self):
        prompts = []
        # Пошук системних промтів у відомих місцях
        soul_profile = BASE_DIR / ".agents" / "skills" / "01-soul" / "SKILL.md"
        if soul_profile.exists():
            prompts.append({"name": "Soul Profile", "path": str(soul_profile)})
        return prompts

    def _scan_configs(self):
        configs = []
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            configs.append({"name": ".env", "path": str(env_file)})
        return configs

    def _read_log_tail(self, file_path, num_lines=500, max_bytes=102400):
        """Зчитує кінець лог-файлу для швидкого та економного аналізу."""
        if not file_path.exists():
            return ""
        try:
            file_size = file_path.stat().st_size
            if file_size == 0:
                return ""
            
            with open(file_path, 'rb') as f:
                if file_size > max_bytes:
                    f.seek(-max_bytes, os.SEEK_END)
                    chunk = f.read(max_bytes)
                else:
                    chunk = f.read()
                
                try:
                    text = chunk.decode('utf-8', errors='ignore')
                except Exception:
                    text = chunk.decode('cp1251', errors='ignore')
                
                lines = text.splitlines()
                return "\n".join(lines[-num_lines:])
        except Exception as e:
            log.error(f"❌ Помилка читання логу {file_path.name}: {e}")
            return ""

    def analyze_interactions(self):
        log.info("🔍 Аналіз локальних логів та структури.")
        
        # 1. Читаємо хвости логів
        logs_to_analyze = {
            "bot_log.txt": BASE_DIR / "logs" / "bot_log.txt",
            "backup_log.txt": BASE_DIR / "logs" / "backup_log.txt",
            "meta_optimizer_log.txt": BASE_DIR / "logs" / "meta_optimizer_log.txt"
        }
        
        log_contents_map = {}
        for name, log_file in logs_to_analyze.items():
            if log_file.exists():
                log_contents_map[name] = self._read_log_tail(log_file, num_lines=500)
            else:
                log_contents_map[name] = ""

        # 2. Скануємо структуру
        structure = self.scan_project_structure()
        
        # 3. Визначаємо потенціали
        return self._find_orchestration_opportunities(log_contents_map, structure)

    def _find_orchestration_opportunities(self, log_contents_map, structure):
        """Шукає можливості для оркестрації та виявляє конфлікти."""
        potentials = []
        
        # 1. Аналіз складності (Skill Overlap)
        skills = structure.get("skills", [])
        if len(skills) > 5:
            potentials.append({
                "topic": "architecture",
                "severity": "medium",
                "recommendation": f"Виявлено {len(skills)} скілів. Рекомендується об'єднати споріднені модулі для зменшення накладних витрат (Token Overhead).",
                "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

        # 2. Conflict Guard: Пошук суперечностей у промтах
        conflicts = self._detect_rule_conflicts(structure.get("prompts", []))
        if conflicts:
            potentials.extend(conflicts)

        # 3. Аналіз стабільності MCP та логів
        critical_issues = []
        transient_issues_count = 0
        
        # Ігноровані мережеві патерни (транзитні помилки Telegram API та запитів)
        ignore_keywords = [
            "api.telegram.org",
            "getupdates",
            "nameresolutionerror",
            "getaddrinfo failed",
            "connectionreseterror",
            "connection aborted",
            "forcibly closed",
            "remote host",
            "polling exception",
            "telebot",
            "max retries exceeded",
            "read timed out",
            "connectionerror",
            "reraise",
            "requests.exceptions",
            "exception_info",
            "polling_thread",
            "raise_exceptions",
            "another exception occurred",
            "handling of the above exception"
        ]
        
        for file_name, content in log_contents_map.items():
            for line in content.splitlines():
                line_lower = line.lower()
                if "[error]" in line_lower or "[critical]" in line_lower:
                    is_transient = any(kw in line_lower for kw in ignore_keywords)
                    if is_transient:
                        transient_issues_count += 1
                    else:
                        critical_issues.append((file_name, line.strip()))
                        
        if critical_issues:
            # Збираємо останні 3 унікальні помилки для деталізації
            unique_errors = list(dict.fromkeys([err[1] for err in critical_issues]))[-3:]
            details = "\n└ ".join(unique_errors)
            
            # Визначаємо, чи є помилки прав доступу або MCP
            has_permission_issue = any(any(pk in err.lower() for pk in ["permission", "access denied", "mcp", "rights"]) for err in unique_errors)
            
            recommendation = "Виявлено критичні системні помилки в логах:\n└ " + details
            if has_permission_issue:
                recommendation += "\n\nConflict Guard підозрює суперечність між MCP-інструментами та системними правами."
            
            potentials.append({
                "topic": "stability",
                "severity": "high",
                "recommendation": recommendation,
                "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        elif transient_issues_count > 20:
            potentials.append({
                "topic": "network_stability",
                "severity": "low",
                "recommendation": f"Виявлено {transient_issues_count} тимчасових мережевих помилок Telegram API. Перевірте стабільність інтернет-з'єднання хоста.",
                "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

        return potentials

    def _detect_rule_conflicts(self, prompts):
        """Conflict Guard: Логіка виявлення суперечливих інструкцій."""
        conflicts = []
        if len(prompts) > 1:
            conflicts.append({
                "topic": "prompt_conflict",
                "severity": "high",
                "recommendation": "Виявлено декілька активних системних профілів. Ризик 'розщеплення особистості' агента. Слід уніфікувати 'Soul Profile'.",
                "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        return conflicts

    def save_proposal(self, potentials):
        if not potentials:
            log.info("✅ Конфліктів та нових можливостей не виявлено.")
            return

        proposal_file = RECOMMENDATIONS_DIR / f"orchestrator_proposal_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        try:
            with open(proposal_file, "w", encoding="utf-8") as f:
                json.dump(potentials, f, ensure_ascii=False, indent=4)
            log.info(f"💡 Оркестратор знайшов {len(potentials)} тем для уваги! {proposal_file.name}")
        except Exception as e:
            log.error(f"❌ Помилка: {e}")

    def run(self):
        log.info("=" * 60)
        log.info(f"🧠 ЗАПУСК UNIVERSAL META-OPTIMIZER: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        potentials = self.analyze_interactions()
        self.save_proposal(potentials)
        
        log.info("🌟 Оркестрація завершена.")

if __name__ == "__main__":
    optimizer = MetaOptimizer()
    optimizer.run()
