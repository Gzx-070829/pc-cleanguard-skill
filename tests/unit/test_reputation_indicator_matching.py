import unittest
from pathlib import Path

from pc_cleanguard.reputation import ReputationMatcher, build_pup_insight, load_evidence_pack

ROOT = Path(__file__).resolve().parents[2]


class ReputationIndicatorMatchingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.records = load_evidence_pack(ROOT / "data/reputation/evidence_pack.real.zh-CN.json")

    def test_installer_family_indicator_matches_conservatively(self) -> None:
        report = {"installed_apps": [{"display_name": "Example InstallCore Bundle Helper", "publisher": "Example Fixture Publisher"}]}
        matches = ReputationMatcher(self.records, include_indicators=True).match(report)
        self.assertEqual(1, len(matches))
        match = matches[0]
        self.assertEqual("evidence_indicator", match["match_basis"])
        self.assertEqual("installer_family", match["matched_indicator_type"])
        self.assertFalse(match["execution_authorized"])
        self.assertFalse(match["execution_gating_eligible"])
        self.assertIn("不能", match["why_not_execution_authorization"])

    def test_publisher_hint_cannot_match_by_itself(self) -> None:
        report = {"installed_apps": [{"display_name": "Unrelated Example App", "publisher": "Piriform"}]}
        self.assertEqual([], ReputationMatcher(self.records, include_indicators=True).match(report))

    def test_informational_and_behavior_context_enter_uncertainty(self) -> None:
        insight = build_pup_insight([{
            "target_id": "fixture", "behavior_categories": ["ad_popup"],
            "false_positive_risk": "high", "review_status": "needs_human_review",
            "mapping_type": "direct_entity", "match_basis": "behavior_context",
            "match_strength": "informational", "is_synthetic": False,
            "execution_authorized": False, "execution_gating_eligible": False,
        }])
        self.assertTrue(any("informational" in note or "behavior_context" in note for note in insight["uncertainty_notes"]))


if __name__ == "__main__":
    unittest.main()
