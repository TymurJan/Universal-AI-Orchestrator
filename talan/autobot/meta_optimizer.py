"""
Universal AI Orchestrator & Governance Guard
This script analyzes project structure, detects conflicts, and proposes optimizations.
"""

import os
import sys
import logging
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
        log.info("🔍 Запускаю Deep Scan структури проєкту...")
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

    def analyze_interactions(self):
        log.info("🔍 Аналіз локальних логів та структури...")
        
        # 1. Читаємо логи
        logs_to_analyze = [
            BASE_DIR / "logs" / "bot_log.txt",
            BASE_DIR / "logs" / "backup_log.txt",
            BASE_DIR / "logs" / "meta_optimizer_log.txt"
        ]
        
        log_content = ""
        for log_file in logs_to_analyze:
            if log_file.exists():
                try:
                    log_content += log_file.read_text(encoding="utf-8") + "\n"
                except: pass

        # 2. Скануємо структуру
        structure = self.scan_project_structure()
        
        # 3. Визначаємо потенціали
        return self._find_orchestration_opportunities(log_content, structure)

    def _find_orchestration_opportunities(self, log_content, structure):
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
        if "error" in log_content.lower():
            potentials.append({
                "topic": "stability",
                "severity": "high",
                "recommendation": "Виявлено критичні помилки. Conflict Guard підозрює суперечність між MCP-інструментами та системними правами.",
                "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

        return potentials

    def _detect_rule_conflicts(self, prompts):
        """Conflict Guard: Логіка виявлення суперечливих інструкцій."""
        # У майбутньому тут працюватиме LLM для аналізу змісту.
        # Зараз: пошук 'Hard Conflicts' (наприклад, декілька профілів душі)
        conflicts = []
        if len(prompts) > 1:
            # Якщо знайдено більше одного системного профілю
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
