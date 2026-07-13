import unittest

from pc_cleanguard.persistence.agent_guard import validate_agent_execution_request


class AgentExecutionGuardTest(unittest.TestCase):
    def test_analysis_is_allowed_as_l0(self):
        result = validate_agent_execution_request({"action": "analyze_persistence", "reason": "explain chain"})
        self.assertTrue(result["allowed"])
        self.assertEqual("L0", result["maximum_allowed_level"])

    def test_read_only_analysis_may_name_sensitive_persistence_objects(self):
        for action in ("analyze service persistence", "review registry clues", "explain scheduled task graph"):
            with self.subTest(action=action):
                result = validate_agent_execution_request({"action": action})
                self.assertTrue(result["allowed"])
                self.assertEqual("allowed_l0", result["status"])

    def test_delete_uninstall_disable_registry_and_service_requests_fail_closed(self):
        for action in ("delete file", "uninstall app", "disable service", "edit registry", "delete scheduled task", "modify browser homepage"):
            with self.subTest(action=action):
                result = validate_agent_execution_request({"action": action})
                self.assertFalse(result["allowed"])
                self.assertEqual("blocked", result["status"])

    def test_unknown_request_fails_closed(self):
        self.assertFalse(validate_agent_execution_request({"action": "do something"})["allowed"])
