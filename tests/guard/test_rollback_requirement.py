import unittest
from dataclasses import replace

from pc_cleanguard.guard import Guard, RequirementPendingError, validate_rollback

from tests.guard.helpers import NOW, consent_for, context, request, rollback_for


class RollbackRequirementTests(unittest.TestCase):
    def test_l2_l3_l4_require_a_rollback_contract(self):
        for action_type in ("quarantine_file", "official_uninstall", "registry_mutation"):
            with self.subTest(action_type=action_type):
                guard = Guard()
                decision = guard.evaluate(request(action_type), context())
                self.assertIn(decision.risk_level.value, {"L2", "L3", "L4"})
                self.assertFalse(validate_rollback(decision, None, NOW).valid)
                level = "HIGH_RISK" if decision.risk_level.value == "L4" else "STANDARD"
                with self.assertRaises(RequirementPendingError):
                    guard.prepare_execution(
                        decision=decision,
                        consent=consent_for(decision, level=level),
                        rollback=None,
                        current_context=context(),
                        now=NOW,
                    )

    def test_bound_rollback_contract_is_valid_for_l2(self):
        decision = Guard().evaluate(request("quarantine_file"), context())
        self.assertTrue(validate_rollback(decision, rollback_for(decision), NOW).valid)

    def test_rollback_binding_and_expiry_cannot_be_bypassed(self):
        decision = Guard().evaluate(request("quarantine_file"), context())
        valid = rollback_for(decision)
        invalid_contracts = (
            replace(valid, decision_id="decision:other"),
            replace(valid, action_fingerprint="b" * 64),
            replace(valid, expires_at=NOW),
            replace(valid, reversible=False),
        )
        for contract in invalid_contracts:
            with self.subTest(contract=contract):
                self.assertFalse(validate_rollback(decision, contract, NOW).valid)

    def test_l4_requires_a_referenced_backup(self):
        decision = Guard().evaluate(request("registry_mutation"), context())
        without_backup = rollback_for(decision)
        with_backup = rollback_for(decision, backup_required=True)

        self.assertFalse(validate_rollback(decision, without_backup, NOW).valid)
        self.assertTrue(validate_rollback(decision, with_backup, NOW).valid)


if __name__ == "__main__":
    unittest.main()
