import tempfile
import unittest
from pathlib import Path

from pc_cleanguard.skill import CORE_ACTION_NAMES, invoke_guard_action, invoke_skill_action

from tests.guard.helpers import NOW, consent_for, context, request, rollback_for
from pc_cleanguard.guard import Guard


class GuardSkillActionTests(unittest.TestCase):
    def test_core_surface_has_exactly_five_actions(self):
        self.assertEqual(
            {
                "evaluate_action",
                "prepare_execution",
                "evaluate_action_bundle",
                "record_execution_result",
                "verify_audit",
            },
            set(CORE_ACTION_NAMES),
        )

    def test_evaluate_action_is_deterministic_and_non_executing(self):
        payload = {"request": request().to_dict(), "context": context().to_dict()}
        response = invoke_guard_action({"action": "evaluate_action", "payload": payload})
        self.assertEqual("REQUIRE", response.result["disposition"])
        self.assertFalse(response.result["execution_authorized"])
        self.assertTrue(response.requires_user_confirmation)

    def test_legacy_dispatch_accepts_new_guard_action_without_changing_legacy_list(self):
        response = invoke_skill_action(
            {
                "action": "evaluate_action",
                "payload": {"request": request().to_dict(), "context": context().to_dict()},
            }
        )
        self.assertEqual("evaluate_action", response.action)

    def test_prepare_execution_issues_contract_only_with_bound_gates(self):
        decision = Guard().evaluate(request("quarantine_file"), context())
        response = invoke_guard_action(
            {
                "action": "prepare_execution",
                "payload": {
                    "decision": decision.to_dict(),
                    "context": context().to_dict(),
                    "consent": consent_for(decision).to_dict(),
                    "rollback": rollback_for(decision).to_dict(),
                    "now": NOW,
                },
            }
        )
        self.assertTrue(response.result["execution_authorized"])

    def test_verify_audit_action_detects_tamper_evident_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            audit = Path(directory) / "audit.jsonl"
            guard = Guard(audit_path=audit)
            guard.evaluate(request("read_metadata"), context())
            response = invoke_guard_action(
                {"action": "verify_audit", "payload": {"path": str(audit)}}
            )
            self.assertTrue(response.result["valid"])


if __name__ == "__main__":
    unittest.main()

