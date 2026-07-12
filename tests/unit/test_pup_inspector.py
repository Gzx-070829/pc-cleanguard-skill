import unittest
from pathlib import Path

from pc_cleanguard.pup import inspect_pup_risk


class PupInspectorTest(unittest.TestCase):
    def test_inspector_combines_match_and_insight_without_authority(self) -> None:
        root = Path(__file__).resolve().parents[2]
        report = {"targets": [{"target_id": "x", "object_type": "SOFTWARE", "name": "Example Synthetic App 11"}]}
        result = inspect_pup_risk(report, root / "examples/reputation/seed_records.zh-CN.json")
        self.assertEqual(1, result["match_count"])
        self.assertFalse(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
