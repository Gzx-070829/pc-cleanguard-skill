import json
import unittest
from pathlib import Path

from pc_cleanguard.skill import READ_ONLY_EXECUTION_LEVEL, invoke_skill_action


ROOT = Path(__file__).resolve().parents[2]


class PupSkillBehaviorActionsTest(unittest.TestCase):
    def test_build_behavior_indicators_is_level_zero(self):
        report = json.loads((ROOT / "tests/fixtures/reputation/pr26_realistic_windows_inventory.json").read_text(encoding="utf-8"))
        response = invoke_skill_action({"action": "build_behavior_indicators", "payload": {"report": report}}).to_dict()
        self.assertEqual(READ_ONLY_EXECUTION_LEVEL, response["execution_level"])
        self.assertFalse(response["execution_authorized"])
        self.assertGreater(response["result"]["behavior_indicator_count"], 0)
        self.assertEqual(0, response["result"]["execution_gating_eligible_count"])

    def test_validate_cn_evidence_pack_is_level_zero(self):
        response = invoke_skill_action({
            "action": "validate_cn_evidence_pack",
            "payload": {"path": str(ROOT / "data/reputation/evidence_pack.cn.zh-CN.json")},
        }).to_dict()
        self.assertEqual(READ_ONLY_EXECUTION_LEVEL, response["execution_level"])
        self.assertFalse(response["execution_authorized"])
        self.assertEqual(5, response["result"]["cn_real_source_count"])
        self.assertEqual(0, response["result"]["execution_gating_eligible_count"])


if __name__ == "__main__":
    unittest.main()
