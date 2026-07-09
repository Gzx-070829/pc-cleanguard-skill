import ast
import json
import unittest
from pathlib import Path

from pc_cleanguard.skill.cleanup_plan import build_cleanup_plan_from_report


ROOT = Path(__file__).resolve().parents[2]


class CleanupPlanTest(unittest.TestCase):
    def _report(self, decisions: list[dict]) -> dict:
        return {
            "scan_id": "scan:cleanup-plan-test",
            "decisions": decisions,
        }

    def _decision(
        self,
        classification: str,
        permission_level: str,
        *,
        required_confirmation: bool = False,
        blocked_by_hard_rule: bool = False,
    ) -> dict:
        return {
            "target_id": f"SOFTWARE:{classification}",
            "classification": classification,
            "permission_level": permission_level,
            "required_confirmation": required_confirmation,
            "blocked_by_hard_rule": blocked_by_hard_rule,
            "evidence_chain": {"sources": ["unit_test"]},
        }

    def test_plan_is_level_zero_and_non_executable(self) -> None:
        plan = build_cleanup_plan_from_report(self._report([])).to_dict()
        self.assertEqual("plan_only", plan["mode"])
        self.assertEqual("LEVEL_0_READ_ONLY", plan["execution_level"])
        self.assertFalse(plan["execution_authorized"])

    def test_safe_remove_is_candidate_not_authorization(self) -> None:
        plan = build_cleanup_plan_from_report(
            self._report(
                [
                    self._decision(
                        "SAFE_REMOVE",
                        "LEVEL_3_STANDARD_UNINSTALL",
                    )
                ]
            )
        ).to_dict()
        step = plan["steps"][0]
        self.assertEqual("REVIEW_REMOVAL_CANDIDATE", step["review_action"])
        self.assertTrue(step["requires_user_confirmation"])
        self.assertFalse(step["execution_authorized"])

    def test_startup_off_is_candidate_not_authorization(self) -> None:
        plan = build_cleanup_plan_from_report(
            self._report(
                [
                    self._decision(
                        "STARTUP_OFF",
                        "LEVEL_2_REVERSIBLE",
                    )
                ]
            )
        ).to_dict()
        step = plan["steps"][0]
        self.assertEqual("REVIEW_STARTUP_CANDIDATE", step["review_action"])
        self.assertTrue(step["requires_user_confirmation"])
        self.assertFalse(step["execution_authorized"])

    def test_block_is_never_reviewed_as_executable(self) -> None:
        plan = build_cleanup_plan_from_report(
            self._report(
                [
                    self._decision(
                        "BLOCK",
                        "LEVEL_5_FORBIDDEN",
                        blocked_by_hard_rule=True,
                    )
                ]
            )
        ).to_dict()
        step = plan["steps"][0]
        self.assertEqual("BLOCKED_BY_POLICY", step["review_action"])
        self.assertTrue(step["blocked"])
        self.assertFalse(step["execution_authorized"])

    def test_level_five_is_blocked_for_any_classification(self) -> None:
        plan = build_cleanup_plan_from_report(
            self._report(
                [
                    self._decision(
                        "ASK_USER",
                        "LEVEL_5_FORBIDDEN",
                    )
                ]
            )
        ).to_dict()
        self.assertTrue(plan["steps"][0]["blocked"])
        self.assertEqual("BLOCKED_BY_POLICY", plan["steps"][0]["review_action"])

    def test_keep_requires_no_confirmation(self) -> None:
        plan = build_cleanup_plan_from_report(
            self._report([self._decision("KEEP", "LEVEL_0_READ_ONLY")])
        ).to_dict()
        self.assertFalse(plan["steps"][0]["requires_user_confirmation"])

    def test_unknown_classification_requires_user_review(self) -> None:
        plan = build_cleanup_plan_from_report(
            self._report([self._decision("INVALID", "LEVEL_0_READ_ONLY")])
        ).to_dict()
        step = plan["steps"][0]
        self.assertEqual("UNKNOWN", step["classification"])
        self.assertEqual("REQUEST_USER_REVIEW", step["review_action"])
        self.assertTrue(step["requires_user_confirmation"])

    def test_every_step_contains_evidence(self) -> None:
        plan = build_cleanup_plan_from_report(
            self._report([self._decision("ASK_USER", "LEVEL_0_READ_ONLY")])
        ).to_dict()
        self.assertEqual("unit_test", plan["steps"][0]["evidence"][0]["source"])

    def test_bare_report_preserves_finding_permission_levels(self) -> None:
        report = json.loads(
            (
                ROOT / "examples" / "reports" / "sample_safe_report.json"
            ).read_text(encoding="utf-8")
        )
        plan = build_cleanup_plan_from_report(report).to_dict()
        levels = {
            step["classification"]: step["proposed_execution_level"]
            for step in plan["steps"]
        }
        self.assertEqual("LEVEL_3_STANDARD_UNINSTALL", levels["SAFE_REMOVE"])
        self.assertEqual("LEVEL_2_REVERSIBLE", levels["STARTUP_OFF"])

    def test_cleanup_plan_contains_no_real_command_fields_or_templates(self) -> None:
        decisions = [
            self._decision("KEEP", "LEVEL_0_READ_ONLY"),
            self._decision("ASK_USER", "LEVEL_0_READ_ONLY"),
            self._decision("SAFE_REMOVE", "LEVEL_3_STANDARD_UNINSTALL"),
            self._decision("STARTUP_OFF", "LEVEL_2_REVERSIBLE"),
            self._decision("QUARANTINE", "LEVEL_2_REVERSIBLE"),
            self._decision("BLOCK", "LEVEL_5_FORBIDDEN"),
        ]
        plan = build_cleanup_plan_from_report(self._report(decisions)).to_dict()
        serialized = json.dumps(plan).casefold()
        forbidden_templates = (
            "remove" + "-item",
            "winget" + " uninstall",
            "stop" + "-service",
            "disable" + "-scheduledtask",
            "start" + "-process",
        )
        for template in forbidden_templates:
            with self.subTest(template=template):
                self.assertNotIn(template, serialized)
        for step in plan["steps"]:
            self.assertFalse(any("command" in key.casefold() for key in step))

    def test_builder_does_not_import_or_call_execution_modules(self) -> None:
        path = ROOT / "pc_cleanguard" / "skill" / "cleanup_plan.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue({"run", "Popen", "system", "spawn"}.isdisjoint(calls))


if __name__ == "__main__":
    unittest.main()
