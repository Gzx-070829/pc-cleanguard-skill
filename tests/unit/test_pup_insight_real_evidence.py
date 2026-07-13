import unittest
from pathlib import Path

from pc_cleanguard.pup import inspect_pup_risk
from pc_cleanguard.reputation import build_pup_insight


ROOT = Path(__file__).resolve().parents[2]


class PupInsightRealEvidenceTest(unittest.TestCase):
    def test_insight_distinguishes_real_and_synthetic_matches(self) -> None:
        insight = build_pup_insight(
            [
                {
                    "target_id": "real",
                    "behavior_categories": ["malicious_bundling"],
                    "false_positive_risk": "medium",
                    "review_status": "approved_for_explanation",
                    "mapping_type": "direct_entity",
                    "is_synthetic": False,
                    "execution_authorized": False,
                },
                {
                    "target_id": "synthetic",
                    "behavior_categories": ["ad_popup"],
                    "false_positive_risk": "high",
                    "review_status": "needs_human_review",
                    "mapping_type": "analogical_behavior",
                    "is_synthetic": True,
                    "execution_authorized": False,
                },
            ]
        )
        summary = insight["summary"]
        self.assertEqual(1, summary["real_source_match_count"])
        self.assertEqual(1, summary["synthetic_match_count"])
        self.assertEqual(1, summary["direct_entity_count"])
        self.assertEqual(1, summary["analogical_behavior_count"])
        self.assertEqual(0, summary["execution_gating_eligible_count"])
        self.assertTrue(any("analogical_behavior" in note for note in insight["uncertainty_notes"]))

    def test_pup_inspect_loads_real_pack_and_renders_source_details(self) -> None:
        report = {
            "targets": [
                {
                    "target_id": "pua-installcore",
                    "object_type": "SOFTWARE",
                    "name": "PUA:Win32/InstallCore",
                    "publisher": "Microsoft Security Intelligence",
                }
            ]
        }
        result = inspect_pup_risk(
            report,
            ROOT / "data/reputation/evidence_pack.real.zh-CN.json",
            evidence_pack=True,
        )
        self.assertEqual(1, result["match_count"])
        self.assertEqual(1, result["insight"]["summary"]["real_source_match_count"])
        self.assertIn("source_url", result["markdown"])
        self.assertIn("真实来源 evidence 仅用于解释、排序和人工复核", result["markdown"])


if __name__ == "__main__":
    unittest.main()
