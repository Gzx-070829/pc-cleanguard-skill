import ast
import json
import unittest
from pathlib import Path

from pc_cleanguard.core.execution_plan_builder import build_execution_plan
from pc_cleanguard.core.models import (
    ClassificationLabel,
    EvidenceChain,
    PermissionLevel,
    PolicyDecision,
    RiskLevel,
)
from pc_cleanguard.core.report_builder import build_report


_RISK_BY_LABEL = {
    ClassificationLabel.KEEP: RiskLevel.LOW,
    ClassificationLabel.ASK_USER: RiskLevel.MEDIUM,
    ClassificationLabel.SAFE_REMOVE: RiskLevel.MEDIUM,
    ClassificationLabel.STARTUP_OFF: RiskLevel.MEDIUM,
    ClassificationLabel.QUARANTINE: RiskLevel.HIGH,
    ClassificationLabel.BLOCK: RiskLevel.CRITICAL,
}

_PERMISSION_BY_LABEL = {
    ClassificationLabel.KEEP: PermissionLevel.LEVEL_0_READ_ONLY,
    ClassificationLabel.ASK_USER: PermissionLevel.LEVEL_0_READ_ONLY,
    ClassificationLabel.SAFE_REMOVE: PermissionLevel.LEVEL_3_STANDARD_UNINSTALL,
    ClassificationLabel.STARTUP_OFF: PermissionLevel.LEVEL_2_REVERSIBLE,
    ClassificationLabel.QUARANTINE: PermissionLevel.LEVEL_2_REVERSIBLE,
    ClassificationLabel.BLOCK: PermissionLevel.LEVEL_5_FORBIDDEN,
}


def make_decision(
    classification: ClassificationLabel,
    target_id: str,
    *,
    permission_level: PermissionLevel | None = None,
    required_confirmation: bool | None = None,
) -> PolicyDecision:
    confirmation_labels = {
        ClassificationLabel.ASK_USER,
        ClassificationLabel.SAFE_REMOVE,
        ClassificationLabel.STARTUP_OFF,
        ClassificationLabel.QUARANTINE,
    }
    return PolicyDecision(
        target_id=target_id,
        classification=classification,
        risk_level=_RISK_BY_LABEL[classification],
        permission_level=permission_level or _PERMISSION_BY_LABEL[classification],
        allowed=classification
        in {
            ClassificationLabel.SAFE_REMOVE,
            ClassificationLabel.STARTUP_OFF,
            ClassificationLabel.QUARANTINE,
        },
        reason=f"Synthetic {classification.value} policy decision.",
        evidence_chain=EvidenceChain(
            sources=("unit_test",),
            facts=(f"Evidence for {target_id}.",),
            confidence=0.8,
        ),
        required_confirmation=(
            classification in confirmation_labels
            if required_confirmation is None
            else required_confirmation
        ),
        rollback_required=classification
        in {ClassificationLabel.STARTUP_OFF, ClassificationLabel.QUARANTINE},
        audit_required=classification is not ClassificationLabel.KEEP,
        blocked_by_hard_rule=classification is ClassificationLabel.BLOCK,
    )


class ReportBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.decisions = [
            make_decision(
                ClassificationLabel.KEEP,
                "SOFTWARE:Microsoft Visual C++ Redistributable",
            ),
            make_decision(
                ClassificationLabel.ASK_USER,
                "STARTUP_ITEM:Unknown Toolbar Startup",
            ),
            make_decision(
                ClassificationLabel.SAFE_REMOVE,
                "SOFTWARE:Known Bloatware With Uninstaller",
            ),
            make_decision(
                ClassificationLabel.STARTUP_OFF,
                "STARTUP_ITEM:Optional Startup Helper",
            ),
            make_decision(
                ClassificationLabel.QUARANTINE,
                "FILE:Suspicious Temp File",
            ),
            make_decision(
                ClassificationLabel.BLOCK,
                r"DIRECTORY:C:\Windows\System32",
            ),
        ]
        self.report = build_report(
            "scan-unit-001",
            "Windows",
            "offline",
            self.decisions,
        )

    def test_report_contains_seven_required_sections(self) -> None:
        self.assertEqual(
            {
                "summary",
                "findings",
                "recommendations",
                "execution_plan",
                "managed_mode_compatibility",
                "risk_notes",
                "audit_notes",
            },
            set(self.report),
        )

    def test_summary_classification_counts_are_correct(self) -> None:
        summary = self.report["summary"]
        self.assertEqual(6, summary["total_findings"])
        self.assertEqual(1, summary["keep_count"])
        self.assertEqual(1, summary["ask_user_count"])
        self.assertEqual(1, summary["safe_remove_count"])
        self.assertEqual(1, summary["startup_off_count"])
        self.assertEqual(1, summary["quarantine_count"])
        self.assertEqual(1, summary["block_count"])
        self.assertEqual(2, summary["high_risk_findings"])
        self.assertEqual(1, summary["ambiguous_items"])

    def test_destructive_actions_executed_is_always_false(self) -> None:
        self.assertIs(False, self.report["summary"]["destructive_actions_executed"])
        empty = build_report("empty", "Windows", "offline", [])
        self.assertIs(False, empty["summary"]["destructive_actions_executed"])

    def test_every_recommendation_has_evidence_chain(self) -> None:
        for recommendation in self.report["recommendations"]:
            with self.subTest(target=recommendation["target_id"]):
                self.assertTrue(recommendation["evidence_chain"])
                self.assertIn("source", recommendation["evidence_chain"][0])
                self.assertIn("fact", recommendation["evidence_chain"][0])

    def test_safe_remove_recommendation_requires_confirmation(self) -> None:
        decision = make_decision(
            ClassificationLabel.SAFE_REMOVE,
            "SOFTWARE:Candidate",
            required_confirmation=False,
        )
        report = build_report("safe", "Windows", "offline", [decision])
        recommendation = report["recommendations"][0]
        self.assertTrue(recommendation["required_confirmation"])

    def test_block_decision_enters_blocked_steps(self) -> None:
        blocked = self.report["execution_plan"]["blocked_steps"]
        self.assertEqual(1, len(blocked))
        self.assertEqual("BLOCK", blocked[0]["classification"])
        self.assertTrue(blocked[0]["blocked"])

    def test_level_five_decision_is_blocked_regardless_of_label(self) -> None:
        malformed = make_decision(
            ClassificationLabel.ASK_USER,
            "SOFTWARE:Level Five Review",
            permission_level=PermissionLevel.LEVEL_5_FORBIDDEN,
        )
        plan = build_execution_plan([malformed])
        self.assertFalse(plan["steps"])
        self.assertTrue(plan["blocked_steps"][0]["blocked"])

    def test_execution_plan_contains_no_real_command_fields_or_values(self) -> None:
        plan = self.report["execution_plan"]
        serialized = json.dumps(plan).casefold()
        for forbidden in (
            "remove" + "-item",
            "rm " + "-rf",
            "winget " + "uninstall",
            "power" + "shell",
            "start" + "-process",
        ):
            self.assertNotIn(forbidden, serialized)
        for step in plan["steps"] + plan["blocked_steps"]:
            self.assertNotIn("command", step)
            self.assertNotIn("executable", step)

    def test_managed_mode_never_allows_block_or_automatic_execution(self) -> None:
        compatibility = self.report["managed_mode_compatibility"]
        self.assertIs(False, compatibility["automatic_execution_allowed"])
        self.assertIs(False, compatibility["block_execution_allowed"])
        self.assertIs(False, compatibility["level_5_execution_allowed"])

    def test_example_reports_are_valid_json(self) -> None:
        root = Path(__file__).resolve().parents[2]
        parsed = {}
        for relative_path in (
            "examples/reports/sample_safe_report.json",
            "examples/reports/sample_blocked_report.json",
            "examples/scan_samples/sample_policy_targets.json",
        ):
            with self.subTest(path=relative_path):
                content = json.loads((root / relative_path).read_text(encoding="utf-8"))
                self.assertIsInstance(content, (dict, list))
                parsed[relative_path] = content

        safe = parsed["examples/reports/sample_safe_report.json"]
        self.assertIs(False, safe["summary"]["destructive_actions_executed"])
        safe_labels = {
            finding["classification"] for finding in safe["findings"]
        }
        self.assertEqual(
            {"KEEP", "SAFE_REMOVE", "STARTUP_OFF", "QUARANTINE"},
            safe_labels,
        )
        self.assertTrue(
            all(
                recommendation["required_confirmation"]
                for recommendation in safe["recommendations"]
                if recommendation["classification"] != "KEEP"
            )
        )

        blocked = parsed["examples/reports/sample_blocked_report.json"]
        self.assertTrue(
            all(
                finding["classification"] == "BLOCK"
                for finding in blocked["findings"]
            )
        )
        self.assertEqual(2, len(blocked["execution_plan"]["blocked_steps"]))

    def test_builders_do_not_call_system_command_apis(self) -> None:
        for tree in self._builder_trees():
            called_attributes = {
                node.func.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            }
            self.assertTrue(
                {"run", "Popen", "system", "spawn"}.isdisjoint(called_attributes)
            )

    def test_builders_do_not_import_network_or_process_modules(self) -> None:
        forbidden_roots = {
            first + second
            for first, second in (
                ("sub", "process"),
                ("req", "uests"),
                ("url", "lib"),
                ("sock", "et"),
            )
        }
        for tree in self._builder_trees():
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertTrue(forbidden_roots.isdisjoint(imports))

    def test_classifications_map_to_declarative_actions(self) -> None:
        expected = {
            ClassificationLabel.KEEP: "REPORT_ONLY",
            ClassificationLabel.ASK_USER: "ASK_USER_CONFIRMATION",
            ClassificationLabel.SAFE_REMOVE: "PLAN_STANDARD_UNINSTALL",
            ClassificationLabel.STARTUP_OFF: "PLAN_DISABLE_STARTUP",
            ClassificationLabel.QUARANTINE: "PLAN_QUARANTINE",
            ClassificationLabel.BLOCK: "BLOCKED_BY_POLICY",
        }
        decisions = [
            make_decision(label, f"SOFTWARE:{label.value}") for label in expected
        ]
        plan = build_execution_plan(decisions)
        all_steps = plan["steps"] + plan["blocked_steps"]
        actions = {
            ClassificationLabel(step["classification"]): step["action"]
            for step in all_steps
        }
        self.assertEqual(expected, actions)

    def test_normalized_target_id_provides_display_metadata(self) -> None:
        finding = self.report["findings"][0]
        self.assertEqual("SOFTWARE", finding["object_type"])
        self.assertEqual("Microsoft Visual C++ Redistributable", finding["name"])
        self.assertIsNone(finding["publisher"])

    def test_report_builder_validates_required_inputs(self) -> None:
        with self.assertRaises(ValueError):
            build_report("", "Windows", "offline", [])
        with self.assertRaises(TypeError):
            build_report("scan", "Windows", "offline", [object()])
        with self.assertRaises(TypeError):
            build_execution_plan(tuple())

    @staticmethod
    def _builder_trees() -> list[ast.AST]:
        core = Path(__file__).resolve().parents[2] / "pc_cleanguard" / "core"
        return [
            ast.parse((core / filename).read_text(encoding="utf-8"))
            for filename in ("report_builder.py", "execution_plan_builder.py")
        ]


if __name__ == "__main__":
    unittest.main()
