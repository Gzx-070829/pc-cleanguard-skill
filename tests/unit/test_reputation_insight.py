import unittest
import json
from pathlib import Path

from pc_cleanguard.reputation import build_pup_insight, render_pup_insight_markdown


class ReputationInsightTest(unittest.TestCase):
    def test_pr21_schemas_fix_execution_authorized_false(self) -> None:
        root = Path(__file__).resolve().parents[2] / "schemas"
        match_schema = json.loads((root / "reputation_match.schema.json").read_text(encoding="utf-8"))
        insight_schema = json.loads((root / "pup_insight.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(match_schema["properties"]["execution_authorized"]["const"])
        self.assertFalse(insight_schema["properties"]["execution_authorized"]["const"])

    def test_insight_is_explanation_only(self) -> None:
        insight = build_pup_insight([{
            "target_id": "app:1", "target_type": "SOFTWARE", "matched_record_id": "r1",
            "matched_name": "Example", "behavior_categories": ["ad_popup"],
            "confidence": 0.5, "false_positive_risk": "high", "evidence": [{"source": "name", "fact": "exact"}],
            "review_status": "needs_human_review", "execution_authorized": False,
            "notes_for_ai": "Explain only.",
        }])
        self.assertFalse(insight["execution_authorized"])
        self.assertIn("不是删除授权", insight["safety_notice"])
        self.assertTrue(insight["recommended_review"])
        markdown = render_pup_insight_markdown(insight)
        self.assertIn("不是卸载授权", markdown)
        self.assertIn("ad_popup", markdown)


if __name__ == "__main__":
    unittest.main()
