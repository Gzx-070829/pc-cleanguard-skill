import unittest
from pathlib import Path

from pc_cleanguard.skill import invoke_skill_action


class PupSkillActionsTest(unittest.TestCase):
    def test_three_readonly_pup_actions_run(self) -> None:
        root = Path(__file__).resolve().parents[2]
        seeds = str(root / "examples/reputation/seed_records.zh-CN.json")
        report = {"targets": [{"target_id": "x", "object_type": "SOFTWARE", "name": "Example Synthetic App 11"}]}
        matched = invoke_skill_action({"action": "match_reputation", "payload": {"report": report, "seed_path": seeds}})
        insight = invoke_skill_action({"action": "build_pup_insight", "payload": {"matches": matched.result["matches"]}})
        inspected = invoke_skill_action({"action": "inspect_pup_risk", "payload": {"report": report, "seed_path": seeds}})
        for response in (matched, insight, inspected):
            self.assertFalse(response.execution_authorized)
            self.assertEqual("LEVEL_0_READ_ONLY", response.execution_level)


if __name__ == "__main__":
    unittest.main()
