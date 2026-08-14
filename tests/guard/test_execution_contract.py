import unittest

from pc_cleanguard.guard import Guard

from tests.guard.helpers import NOW, consent_for, context, request, rollback_for


class ExecutionContractTests(unittest.TestCase):
    def test_contract_is_issued_only_after_all_l2_gates(self):
        guard = Guard()
        decision = guard.evaluate(request("quarantine_file"), context())
        contract = guard.prepare_execution(
            decision=decision,
            consent=consent_for(decision),
            rollback=rollback_for(decision),
            current_context=context(),
            now=NOW,
        )
        self.assertTrue(contract.execution_authorized)
        self.assertEqual(decision.action_fingerprint, contract.action_fingerprint)
        self.assertEqual(decision.target_fingerprints, contract.authorized_targets)
        self.assertIn("USER_CONFIRMATION", contract.requirements_satisfied)
        self.assertNotIn("command", contract.to_dict())

    def test_l4_contract_requires_high_risk_consent_and_backup(self):
        guard = Guard()
        decision = guard.evaluate(request("registry_mutation"), context())
        contract = guard.prepare_execution(
            decision=decision,
            consent=consent_for(decision, level="HIGH_RISK"),
            rollback=rollback_for(decision, backup_required=True),
            current_context=context(),
            now=NOW,
        )
        self.assertTrue(contract.execution_authorized)


if __name__ == "__main__":
    unittest.main()

