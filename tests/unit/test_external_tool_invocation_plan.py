import ast
import json
import unittest
from pathlib import Path

from pc_cleanguard.external_tools.catalog import ExternalToolCatalog
from pc_cleanguard.external_tools.invocation_plan import (
    build_external_tool_invocation_plan,
)
from pc_cleanguard.external_tools.trust_policy import ToolTrustPolicy

from .test_external_tool_catalog import make_record


ROOT = Path(__file__).resolve().parents[2]


class ExternalToolInvocationPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.record = make_record()
        self.catalog = ExternalToolCatalog((self.record,))
        self.evidence = (
            {"source": "policy_decision", "fact": "candidate requires review"},
        )

    def _plan(self, policy: ToolTrustPolicy):
        return build_external_tool_invocation_plan(
            self.catalog,
            policy,
            tool_id=self.record.tool_id,
            requested_action="standard_uninstall",
            reason="Synthetic plan for a reviewed software candidate.",
            evidence=self.evidence,
            plan_id="external-plan:test",
        )

    def test_allowlisted_tool_creates_level_zero_nonexecuting_plan(self) -> None:
        plan = self._plan(ToolTrustPolicy((self.record.tool_id,))).to_dict()
        self.assertTrue(plan["trusted"])
        self.assertFalse(plan["blocked"])
        self.assertTrue(plan["required_user_confirmation"])
        self.assertEqual("LEVEL_0_READ_ONLY", plan["execution_level"])
        self.assertFalse(plan["execution_authorized"])
        self.assertEqual("plan_only", plan["mode"])
        self.assertTrue(plan["evidence"])
        self.assertIn("reason", plan)

    def test_untrusted_cataloged_tool_creates_blocked_plan(self) -> None:
        plan = self._plan(ToolTrustPolicy()).to_dict()
        self.assertFalse(plan["trusted"])
        self.assertTrue(plan["blocked"])
        self.assertTrue(plan["blocked_if_untrusted"])
        self.assertFalse(plan["execution_authorized"])

    def test_unknown_tool_cannot_enter_plan(self) -> None:
        with self.assertRaises(ValueError):
            build_external_tool_invocation_plan(
                self.catalog,
                ToolTrustPolicy(),
                tool_id="unknown-tool",
                requested_action="standard_uninstall",
                reason="Unknown tool must not be planned.",
            )

    def test_unsupported_action_cannot_enter_plan(self) -> None:
        with self.assertRaises(ValueError):
            build_external_tool_invocation_plan(
                self.catalog,
                ToolTrustPolicy((self.record.tool_id,)),
                tool_id=self.record.tool_id,
                requested_action="unsupported_action",
                reason="Unsupported action must not be planned.",
            )

    def test_plan_contains_no_command_or_execution_templates(self) -> None:
        plan = self._plan(ToolTrustPolicy((self.record.tool_id,))).to_dict()
        serialized = json.dumps(plan).casefold()
        forbidden_templates = (
            "remove" + "-item",
            "winget" + " uninstall",
            "start" + "-process",
            "stop" + "-service",
            "disable" + "-scheduledtask",
        )
        for template in forbidden_templates:
            with self.subTest(template=template):
                self.assertNotIn(template, serialized)
        self.assertFalse(any("command" in key.casefold() for key in plan))

    def test_plan_requires_evidence_items_with_source_and_fact(self) -> None:
        with self.assertRaises(ValueError):
            build_external_tool_invocation_plan(
                self.catalog,
                ToolTrustPolicy((self.record.tool_id,)),
                tool_id=self.record.tool_id,
                requested_action="standard_uninstall",
                reason="Evidence is mandatory.",
                evidence=({"source": "only-source"},),
            )

    def test_external_tool_modules_have_no_process_network_or_execution_calls(self) -> None:
        imports = set()
        calls = set()
        for path in (ROOT / "pc_cleanguard" / "external_tools").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        calls.add(node.func.attr)
        forbidden_imports = {
            first + second
            for first, second in (
                ("sub", "process"),
                ("req", "uests"),
                ("url", "lib"),
                ("sock", "et"),
            )
        }
        self.assertTrue(forbidden_imports.isdisjoint(imports))
        self.assertTrue({"run", "Popen", "system", "popen", "spawn"}.isdisjoint(calls))


if __name__ == "__main__":
    unittest.main()
