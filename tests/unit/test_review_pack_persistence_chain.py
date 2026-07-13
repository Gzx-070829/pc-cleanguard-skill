import json, tempfile, unittest
from pathlib import Path

from pc_cleanguard.pup.review_pack import build_pup_review_pack


ROOT = Path(__file__).parents[2]


class ReviewPackPersistenceTest(unittest.TestCase):
    def test_review_pack_writes_persistence_assets(self):
        report = {"report_id": "r", "installed_apps": [{"target_id": "a", "display_name": "Example"}], "startup_items": [{"name": "Example Updater"}]}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pack"
            result = build_pup_review_pack(report, [], out, include_persistence_chain=True)
            for name in ("persistence_chain.md", "persistence_chain.json", "persistence_chain_mermaid.md", "persistence_governance_plan.md", "persistence_governance_plan.json", "agent_governance_preview.json"):
                self.assertTrue((out / name).is_file(), name)
            self.assertEqual("L0_REVIEW_ONLY", result["agent_boundary_status"])

    def test_strong_fixture_combines_evidence_and_persistence_review_signals(self):
        report = json.loads((ROOT / "tests/fixtures/reports/v040_persistence_strong_chain_report.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pack"
            result = build_pup_review_pack(report, [], out, cn_win_evidence_pack=ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json", include_behavior_indicators=True, include_corroboration=True, include_persistence_chain=True)
            graph = json.loads((out / "persistence_chain.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(result["cn_win_match_count"], 1)
            self.assertIn("evidence_match", {edge["edge_type"] for edge in graph["edges"]})
            self.assertIn(graph["risk_summary"]["review_signal"], {"strong_review_signal", "moderate_review_signal"})
            self.assertEqual(0, graph["execution_gating_eligible_count"])
