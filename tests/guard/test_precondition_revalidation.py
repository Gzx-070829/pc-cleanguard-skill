import unittest
from dataclasses import replace

from pc_cleanguard.guard import (
    Guard,
    GuardContext,
    PreconditionValidationError,
    validate_preconditions,
)

from tests.guard.helpers import NOW, consent_for, context, request


class PreconditionRevalidationTests(unittest.TestCase):
    def test_changed_hash_is_a_toctou_failure(self):
        guard = Guard()
        decision = guard.evaluate(request(), context())
        changed = context(sha256="b" * 64)
        validation = validate_preconditions(decision, changed)
        self.assertFalse(validation.valid)
        self.assertIn("HASH_MATCH", validation.failed_checks)
        with self.assertRaises(PreconditionValidationError):
            guard.prepare_execution(
                decision=decision,
                consent=consent_for(decision),
                rollback=None,
                current_context=changed,
                now=NOW,
            )

    def test_target_substitution_is_rejected(self):
        decision = Guard().evaluate(request(), context())
        substituted = context(path=r"C:\Temp\different.tmp")
        self.assertFalse(validate_preconditions(decision, substituted).valid)

    def test_type_size_mtime_reparse_and_protection_changes_fail_closed(self):
        decision = Guard().evaluate(request(), context())
        identifier = "target-1"
        base = context().to_dict()
        mutations = {
            "target_type": "directory",
            "size_bytes": 99,
            "mtime_ns": 101,
            "is_reparse_point": True,
            "protected": True,
        }
        expected_checks = {
            "target_type": "TARGET_TYPE_MATCH",
            "size_bytes": "SIZE_MATCH",
            "mtime_ns": "MTIME_MATCH",
            "is_reparse_point": "NOT_REPARSE_POINT",
            "protected": "NOT_PROTECTED",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                current = GuardContext.from_dict(
                    {
                        **base,
                        "target_facts": {
                            identifier: {**base["target_facts"][identifier], field: value}
                        },
                    }
                )
                result = validate_preconditions(decision, current)
                self.assertFalse(result.valid)
                self.assertIn(expected_checks[field], result.failed_checks)

    def test_new_user_code_root_protection_is_rechecked_before_execution(self):
        decision = Guard().evaluate(request(), context())
        protected_now = replace(
            context(),
            user_policy={"user_code_roots": [r"C:\Temp"]},
        )
        result = validate_preconditions(decision, protected_now)
        self.assertFalse(result.valid)
        self.assertIn("NOT_PROTECTED", result.failed_checks)

    def test_nested_runtime_protection_status_is_fail_closed(self):
        decision = Guard().evaluate(request(), context())
        protected_now = replace(
            context(),
            protected_status={"target-1": {"protected": True}},
        )
        result = validate_preconditions(decision, protected_now)
        self.assertFalse(result.valid)
        self.assertIn("NOT_PROTECTED", result.failed_checks)


if __name__ == "__main__":
    unittest.main()
