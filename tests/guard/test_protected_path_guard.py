import unittest
from dataclasses import replace

from pc_cleanguard.guard import Guard

from tests.guard.helpers import context, request


class ProtectedPathGuardTests(unittest.TestCase):
    def test_system32_is_always_level_five_blocked(self):
        path = r"C:\Windows\System32\kernel32.dll"
        decision = Guard().evaluate(
            request(path=path, reason="I am certain this is junk."),
            context(path=path),
        )
        self.assertEqual("L5", decision.risk_level.value)
        self.assertEqual("BLOCK", decision.disposition.value)
        self.assertTrue(decision.blocked_reasons)

    def test_developer_assets_are_blocked(self):
        path = r"C:\work\project\.git\objects\fixture.tmp"
        decision = Guard().evaluate(request(path=path), context(path=path))
        self.assertEqual("BLOCK", decision.disposition.value)

    def test_explicit_user_code_root_is_blocked_without_host_preclassification(self):
        path = r"C:\work\project\build\fixture.tmp"
        guarded_context = replace(
            context(path=path),
            user_policy={"user_code_roots": [r"C:\work\project"]},
        )
        decision = Guard().evaluate(request(path=path), guarded_context)
        self.assertEqual("BLOCK", decision.disposition.value)

    def test_all_execution_levels_have_deterministic_policy(self):
        cases = {
            "read_metadata": ("L0", "ALLOW"),
            "delete_temp_file": ("L1", "REQUIRE"),
            "quarantine_file": ("L2", "REQUIRE"),
            "official_uninstall": ("L3", "REQUIRE"),
            "service_mutation": ("L4", "REQUIRE"),
            "wildcard_delete": ("L5", "BLOCK"),
        }
        for action, expected in cases.items():
            with self.subTest(action=action):
                decision = Guard().evaluate(request(action), context())
                self.assertEqual(expected, (decision.risk_level.value, decision.disposition.value))


if __name__ == "__main__":
    unittest.main()
