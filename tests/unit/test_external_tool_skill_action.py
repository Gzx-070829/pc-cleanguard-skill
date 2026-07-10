import unittest

from pc_cleanguard.external_tools import ExternalToolType
from pc_cleanguard.skill import ACTION_NAMES, invoke_skill_action

from .test_external_tool_catalog import make_record
from .test_external_tool_recommender import cleanup_plan


class ExternalToolSkillActionTest(unittest.TestCase):
    def _payload(self) -> dict:
        record = make_record(
            ExternalToolType.OFFICIAL_UNINSTALLER,
            tool_id="example-official-tool",
        )
        return {
            "cleanup_plan": cleanup_plan(),
            "catalog": {"records": [record.to_dict()]},
            "allowlisted_tool_ids": [record.tool_id],
            "governance_decisions": [],
            "evidence": [
                {"source": "caller", "fact": "synthetic PR13 action request"}
            ],
            "installed_apps": [],
        }

    def test_action_name_is_available(self) -> None:
        self.assertIn("recommend_external_tools", ACTION_NAMES)

    def test_recommend_external_tools_action_runs(self) -> None:
        response = invoke_skill_action(
            {
                "schema_version": "0.1",
                "request_id": "request:pr13-test",
                "action": "recommend_external_tools",
                "payload": self._payload(),
            }
        ).to_dict()
        self.assertEqual("recommend_external_tools", response["action"])
        self.assertEqual("planned", response["status"])
        self.assertEqual("LEVEL_0_READ_ONLY", response["execution_level"])
        self.assertFalse(response["execution_authorized"])
        self.assertTrue(response["requires_user_confirmation"])
        self.assertEqual(1, len(response["result"]["recommendations"]))

    def test_action_recommendations_are_always_safe_plans(self) -> None:
        response = invoke_skill_action(
            {"action": "recommend_external_tools", "payload": self._payload()}
        )
        for recommendation in response.result["recommendations"]:
            self.assertTrue(recommendation["plan_only"])
            self.assertTrue(recommendation["requires_user_confirmation"])
            self.assertFalse(recommendation["execution_authorized"])
            self.assertNotIn("command", recommendation)

    def test_action_accepts_report_summary_instead_of_cleanup_plan(self) -> None:
        payload = self._payload()
        payload.pop("cleanup_plan")
        payload["report_summary"] = {
            "scan_id": "scan:pr13-report",
            "decisions": [
                {
                    "target_id": "SOFTWARE:example-notes",
                    "classification": "SAFE_REMOVE",
                    "permission_level": "LEVEL_3_STANDARD_UNINSTALL",
                    "required_confirmation": True,
                    "blocked_by_hard_rule": False,
                }
            ],
        }
        response = invoke_skill_action(
            {"action": "recommend_external_tools", "payload": payload}
        )
        self.assertEqual(1, len(response.result["recommendations"]))

    def test_action_requires_exactly_one_plan_source(self) -> None:
        payload = self._payload()
        payload["report_summary"] = {}
        with self.assertRaises(ValueError):
            invoke_skill_action(
                {"action": "recommend_external_tools", "payload": payload}
            )


if __name__ == "__main__":
    unittest.main()
