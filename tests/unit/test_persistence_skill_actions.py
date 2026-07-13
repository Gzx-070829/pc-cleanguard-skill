import unittest

from pc_cleanguard.skill import READ_ONLY_EXECUTION_LEVEL, invoke_skill_action


class PersistenceSkillActionsTest(unittest.TestCase):
    def test_graph_and_plan_actions_are_level_zero(self):
        graph_response = invoke_skill_action({"action": "build_persistence_chain_graph", "payload": {"report": {"installed_apps": [{"display_name": "Example"}]}}})
        plan_response = invoke_skill_action({"action": "build_persistence_governance_plan", "payload": {"graph": graph_response.result}})
        self.assertEqual(READ_ONLY_EXECUTION_LEVEL, graph_response.execution_level)
        self.assertEqual(READ_ONLY_EXECUTION_LEVEL, plan_response.execution_level)
        self.assertEqual(0, plan_response.result["execution_gating_eligible_count"])

    def test_agent_preview_and_guard_are_non_executing(self):
        preview = invoke_skill_action({"action": "build_agent_governance_preview", "payload": {"report": {"services": [{"display_name": "Example"}]}}})
        blocked = invoke_skill_action({"action": "validate_agent_execution_request", "payload": {"request": {"action": "uninstall app"}}})
        self.assertFalse(preview.result["execution_authorized"])
        self.assertEqual("blocked", blocked.result["status"])
