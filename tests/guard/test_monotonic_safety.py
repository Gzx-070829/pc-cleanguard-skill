import unittest

from pc_cleanguard.guard import Guard, Requirement, RiskSignal, merge_risk_signals

from tests.guard.helpers import context, request


class MonotonicSafetyTests(unittest.TestCase):
    def test_untrusted_signal_can_only_add_restrictions(self):
        baseline = Guard().evaluate(request(), context())
        strengthened = merge_risk_signals(
            baseline,
            (
                RiskSignal(
                    source="community-reputation",
                    signal_type="pup_claim",
                    severity="L4",
                    reason="untrusted synthetic claim",
                    requirements=(Requirement.ADMIN_ACKNOWLEDGEMENT,),
                ),
            ),
        )
        self.assertNotEqual("ALLOW", strengthened.disposition.value)
        self.assertGreaterEqual(strengthened.risk_level.rank, baseline.risk_level.rank)
        self.assertTrue(set(baseline.requirements).issubset(strengthened.requirements))
        for requirement in (
            Requirement.EXPLICIT_HIGH_RISK_CONFIRMATION,
            Requirement.ADMIN_ACKNOWLEDGEMENT,
            Requirement.BACKUP,
            Requirement.ROLLBACK_CONTRACT,
            Requirement.TARGET_REVALIDATION,
            Requirement.AUDIT,
            Requirement.POSTCONDITION_VERIFY,
        ):
            self.assertIn(requirement, strengthened.requirements)
        self.assertFalse(strengthened.execution_authorized)

    def test_high_reputation_confidence_does_not_authorize(self):
        decision = Guard().evaluate(
            request(parameters={"reputation_confidence": 1.0}), context()
        )
        self.assertFalse(decision.execution_authorized)
        self.assertNotEqual("ALLOW", decision.disposition.value)


if __name__ == "__main__":
    unittest.main()
