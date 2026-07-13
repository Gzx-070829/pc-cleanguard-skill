import json, unittest
from pathlib import Path

from pc_cleanguard.skill import ACTION_NAMES, READ_ONLY_EXECUTION_LEVEL, invoke_skill_action

ROOT = Path(__file__).resolve().parents[2]


class AgentActionExamplesTest(unittest.TestCase):
    def test_pr31_agent_json_examples_parse(self):
        for path in (ROOT / "examples/agent").glob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(list((ROOT / "examples/agent").glob("*.json"))), 8)

    def test_new_level_zero_actions_are_public(self):
        for name in ("build_evidence_coverage_summary", "build_user_friendly_pup_report", "build_false_positive_feedback_template"):
            self.assertIn(name, ACTION_NAMES)

    def test_coverage_action_runs_level_zero(self):
        response = invoke_skill_action({"action":"build_evidence_coverage_summary","payload":{"evidence_packs":[],"candidates":[],"backlog":[]}})
        self.assertEqual(READ_ONLY_EXECUTION_LEVEL, response.execution_level); self.assertFalse(response.execution_authorized)

    def test_user_report_action_runs_level_zero(self):
        response = invoke_skill_action({"action":"build_user_friendly_pup_report","payload":{"review_pack_summary":{}}})
        self.assertEqual(READ_ONLY_EXECUTION_LEVEL, response.execution_level); self.assertEqual(0, response.result["execution_gating_eligible_count"])

    def test_feedback_action_runs_level_zero(self):
        response = invoke_skill_action({"action":"build_false_positive_feedback_template","payload":{"match":{},"report_metadata":{}}})
        self.assertEqual(READ_ONLY_EXECUTION_LEVEL, response.execution_level); self.assertFalse(response.execution_authorized)


if __name__ == "__main__": unittest.main()
