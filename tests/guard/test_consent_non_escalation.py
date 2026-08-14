import unittest

from pc_cleanguard.guard import (
    ConsentGrant,
    Guard,
    PolicyBlockedError,
    RequirementPendingError,
    validate_consent,
)

from tests.guard.helpers import NOW, consent_for, context, request


class ConsentBoundaryTests(unittest.TestCase):
    def test_missing_real_grant_cannot_be_replaced_by_self_assertion(self):
        guard = Guard()
        decision = guard.evaluate(
            request(parameters={"user_confirmed": True}), context()
        )
        with self.assertRaises(RequirementPendingError):
            guard.prepare_execution(
                decision=decision,
                consent=None,
                rollback=None,
                current_context=context(),
                now=NOW,
            )

    def test_expired_consent_is_rejected(self):
        decision = Guard().evaluate(request(), context())
        validation = validate_consent(
            decision,
            consent_for(decision, expires_at="2025-12-31T23:59:59Z"),
            NOW,
        )
        self.assertFalse(validation.valid)
        self.assertIn("expired", " ".join(validation.errors).lower())

    def test_scope_expansion_is_rejected(self):
        decision = Guard().evaluate(request(), context())
        valid = consent_for(decision)
        expanded = ConsentGrant(
            **{
                **valid.to_dict(),
                "allowed_scope": {"allowed_paths": ["C:\\"]},
            }
        )
        self.assertFalse(validate_consent(decision, expanded, NOW).valid)

    def test_every_binding_dimension_and_confirmation_strength_is_checked(self):
        decision = Guard().evaluate(request("registry_mutation"), context())
        base = consent_for(decision, level="HIGH_RISK")
        mutations = {
            "decision_id": "decision:other",
            "action_fingerprint": "b" * 64,
            "allowed_targets": ("c" * 64,),
            "allowed_effect": "different effect",
            "confirmation_level": "STANDARD",
            "confirmation_source": "agent",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                changed = ConsentGrant.from_dict({**base.to_dict(), field: value})
                self.assertFalse(validate_consent(decision, changed, NOW).valid)

    def test_consent_cannot_override_level_five_block(self):
        guard = Guard()
        decision = guard.evaluate(
            request(path=r"C:\Windows\System32\kernel32.dll"),
            context(path=r"C:\Windows\System32\kernel32.dll"),
        )
        self.assertEqual("BLOCK", decision.disposition.value)
        with self.assertRaises(PolicyBlockedError):
            guard.prepare_execution(
                decision=decision,
                consent=consent_for(decision, level="HIGH_RISK"),
                rollback=None,
                current_context=context(path=r"C:\Windows\System32\kernel32.dll"),
                now=NOW,
            )


if __name__ == "__main__":
    unittest.main()
