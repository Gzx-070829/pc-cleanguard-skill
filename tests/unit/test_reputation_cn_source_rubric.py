import unittest
from pathlib import Path

from pc_cleanguard.reputation import load_cn_source_rubric, validate_cn_source_rubric


ROOT = Path(__file__).resolve().parents[2]


class ReputationCnSourceRubricTest(unittest.TestCase):
    def test_checked_in_cn_rubric_is_valid_and_forbids_execution_uses(self):
        rubric = load_cn_source_rubric(ROOT / "data/reputation/cn_source_rubric.zh-CN.json")
        self.assertGreaterEqual(len(rubric), 4)
        forbidden = {"delete_authorization", "uninstall_authorization", "disable_authorization", "registry_edit_authorization"}
        for item in rubric:
            self.assertEqual(forbidden, set(item["forbidden_use"]))
            self.assertIn(item["allowed_use"], {"explanation_only", "review_hint", "publisher_level_warning", "name_collision_warning"})

    def test_rubric_rejects_missing_forbidden_boundary(self):
        item = {
            "source_reliability": "official", "entity_clarity": "mobile_only",
            "risk_category": "privacy_overreach", "allowed_use": "explanation_only",
            "forbidden_use": ["delete_authorization"],
        }
        with self.assertRaises(ValueError):
            validate_cn_source_rubric(item)


if __name__ == "__main__":
    unittest.main()
