import ast
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import pc_cleanguard
from pc_cleanguard.guard import (
    ActionRequest,
    ConsentGrant,
    Guard,
    GuardContext,
    GuardDecision,
    GuardInputError,
    ExecutionContract,
    RollbackContract,
    load_policy_pack,
)

from tests.guard.helpers import consent_for, context, request, rollback_for


ROOT = Path(__file__).resolve().parents[2]


class ContractStrictnessAndDependencyTests(unittest.TestCase):
    def test_root_public_api_exposes_thin_guard_contract(self):
        self.assertIs(Guard, pc_cleanguard.Guard)
        self.assertIs(ActionRequest, pc_cleanguard.ActionRequest)
        self.assertIs(GuardContext, pc_cleanguard.GuardContext)
        for operation in (
            "evaluate", "prepare_execution", "record_execution_result", "verify_audit"
        ):
            self.assertTrue(callable(getattr(Guard, operation)))

    def test_guard_core_has_at_most_twelve_modules_and_no_forbidden_imports(self):
        paths = sorted((ROOT / "pc_cleanguard/guard").glob("*.py"))
        self.assertGreaterEqual(len(paths), 10)
        self.assertLessEqual(len(paths), 12)
        forbidden_roots = {
            "subprocess", "requests", "httpx", "socket", "urllib", "openai",
            "anthropic", "pup", "reputation", "persistence", "cleanup", "windows",
        }
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertFalse(imports.intersection(forbidden_roots), path.name)

    def test_boundary_contracts_reject_unknown_fields(self):
        decision = Guard().evaluate(request(), context())
        cases = (
            (ActionRequest.from_dict, {**request().to_dict(), "force_allow": True}),
            (GuardContext.from_dict, {**context().to_dict(), "agent_authorized": True}),
            (ConsentGrant.from_dict, {**consent_for(decision).to_dict(), "user_confirmed": True}),
            (RollbackContract.from_dict, {**rollback_for(decision).to_dict(), "command": "restore"}),
        )
        for loader, data in cases:
            with self.subTest(loader=loader.__qualname__), self.assertRaises(GuardInputError):
                loader(data)

    def test_browser_profile_unc_and_user_policy_targets_are_blocked(self):
        browser_path = r"C:\Users\Example\AppData\Local\Google\Chrome\User Data\Default\Login Data"
        browser = Guard().evaluate(request(path=browser_path), context(path=browser_path))
        self.assertEqual("BLOCK", browser.disposition.value)

        unc_path = r"\\server\share\fixture.tmp"
        unc = Guard().evaluate(request(path=unc_path), context(path=unc_path))
        self.assertEqual("BLOCK", unc.disposition.value)

        req = request()
        protected_context = replace(
            context(), user_policy={"protected_targets": [req.targets[0].identifier]}
        )
        protected = Guard().evaluate(req, protected_context)
        self.assertEqual("BLOCK", protected.disposition.value)

    def test_decision_and_execution_contract_detect_field_tampering(self):
        decision = Guard().evaluate(request("quarantine_file"), context())
        tampered_decision = decision.to_dict()
        tampered_decision["requirements"] = [
            item for item in tampered_decision["requirements"]
            if item != "ROLLBACK_CONTRACT"
        ]
        with self.assertRaises(GuardInputError):
            GuardDecision.from_dict(tampered_decision)

        contract = Guard().prepare_execution(
            decision=decision,
            consent=consent_for(decision),
            rollback=rollback_for(decision),
            current_context=context(),
            now="2026-01-01T00:00:00Z",
        )
        tampered_contract = {**contract.to_dict(), "authorized_effect": "broader effect"}
        with self.assertRaises(GuardInputError):
            ExecutionContract.from_dict(tampered_contract)

    def test_unc_policy_is_rejected_before_any_file_read(self):
        with mock.patch.object(
            Path,
            "read_text",
            side_effect=AssertionError("UNC policy must not be read"),
        ) as read_text:
            with self.assertRaises(GuardInputError):
                load_policy_pack(r"\\server\share\policy.json")
        read_text.assert_not_called()


if __name__ == "__main__":
    unittest.main()
