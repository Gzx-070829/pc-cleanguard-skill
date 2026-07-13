import json, unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class V040ShowcaseTest(unittest.TestCase):
    def test_showcase_assets_exist_and_machine_summary_is_safe(self):
        base = ROOT / "examples/showcase/v0.4.0"
        names = ("README.md", "START_HERE.md", "user_friendly_summary.md", "machine_summary.json", "persistence_chain.md", "persistence_chain_mermaid.md", "persistence_governance_plan.md", "agent_governance_preview.json", "evidence_coverage.md", "evidence_quality.md", "corroboration_summary.md", "no_match_report.md", "false_positive_feedback_template.md", "safety_notice.md")
        for name in names: self.assertTrue((base / name).is_file(), name)
        summary = json.loads((base / "machine_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(0, summary["execution_gating_eligible_count"])
        self.assertFalse(summary["execution_authorized"])
