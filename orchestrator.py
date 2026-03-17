"""
Universal AI Orchestrator & Governance Guard
Version: 1.0.0
Author: TymurJan (https://github.com/TymurJan)

This script provides deep structure scanning, conflict detection, 
and resource optimization for autonomous AI agents.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import json

from core.engine import GovernanceEngine, generate_governance_report

# --- Logging Configuration ---
log = logging.getLogger("UniversalOrchestrator")
log.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

class AIOrchestrator:
    def __init__(self, project_root=None):
        self.base_dir = Path(project_root) if project_root else Path(__file__).resolve().parent
        self.rec_dir = self.base_dir / ".orchestrator" / "recommendations"
        self.rec_dir.mkdir(parents=True, exist_ok=True)
        self.engine = GovernanceEngine(self.base_dir)

    def scan_structure(self):
        log.info("🔍 Initiating Deep Scan...")
        report = {
            "modules": self._get_modules(),
            "configs": self._get_configs()
        }
        return report

    def _get_modules(self):
        modules = []
        for path in self.base_dir.rglob("*.py"):
            if "__" not in path.name and "dist" not in str(path):
                modules.append({"name": path.name, "size": path.stat().st_size})
        return modules

    def _get_configs(self):
        configs = []
        for ext in ["*.env", "config.json", "*.yaml"]:
            for path in self.base_dir.glob(ext):
                configs.append({"name": path.name, "path": str(path)})
        return configs

    def run(self, logs_path=None):
        log.info("=" * 60)
        log.info(f"🧠 STARTING UNIVERSAL AI ORCHESTRATOR: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        log.info("Commercial Core Active | License: Proprietary")
        
        structure = self.scan_structure()
        roi_results = self.engine.analyze_roi(logs_path)
        security_results = self.engine.security_audit()
        conflicts = self.engine.detect_logic_collisions(self.base_dir)
        ui_ux_results = self.engine.ui_ux_audit()
        
        # Simulate social impact for a standard audit (e.g. $500 value)
        impact_results = self.engine.calculate_social_impact(500.0)
        
        full_results = {
            "timestamp": datetime.now().isoformat(),
            "roi": roi_results,
            "security": security_results,
            "conflicts": conflicts,
            "ui_ux": ui_ux_results,
            "impact": impact_results
        }
        
        report_name = f"governance_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        output_file = self.rec_dir / report_name
        generate_governance_report(full_results, output_file)
        
        log.info(f"✅ Governance Audit complete. Report saved: {output_file.name}")
        return full_results

if __name__ == "__main__":
    orchestrator = AIOrchestrator()
    orchestrator.run()
