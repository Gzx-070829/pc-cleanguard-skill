import ast
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.skill import (
    ACTION_NAMES,
    SkillActionRequest,
    build_cleanup_plan,
    explain_report,
    invoke_skill_action,
    scan_from_json,
    write_audit,
    write_report,
)


ROOT = Path(__file__).resolve().parents[2]
SAMPLE_INPUT = ROOT / "examples" / "scan_samples" / "pr7_readonly_scan_input.json"
SAMPLE_REPORT = (
    ROOT / "examples" / "reports" / "pr7_readonly_scan_pipeline_report.json"
)


class SkillActionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.input_data = json.loads(SAMPLE_INPUT.read_text(encoding="utf-8"))
        self.report = json.loads(SAMPLE_REPORT.read_text(encoding="utf-8"))
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_action_names_include_pr13_recommender_scope(self) -> None:
        self.assertEqual(
            {
                "scan_from_json",
                "explain_report",
                "build_cleanup_plan",
                "write_report",
                "write_audit",
                "recommend_external_tools",
                "quarantine_file",
                "list_quarantine_items",
                "restore_quarantine_item",
                "match_reputation",
                "build_pup_insight",
                "inspect_pup_risk",
            },
            set(ACTION_NAMES),
        )

    def test_action_request_validates_and_round_trips(self) -> None:
        request = SkillActionRequest.from_dict(
            {
                "schema_version": "0.1",
                "request_id": "request:test",
                "action": "scan_from_json",
                "payload": {"input_data": {}},
            }
        )
        self.assertEqual("request:test", request.request_id)
        self.assertEqual("scan_from_json", request.to_dict()["action"])

    def test_action_request_rejects_unknown_action(self) -> None:
        with self.assertRaises(ValueError):
            SkillActionRequest.from_dict({"action": "execute", "payload": {}})

    def test_action_request_rejects_missing_payload(self) -> None:
        with self.assertRaises(ValueError):
            SkillActionRequest.from_dict({"action": "scan_from_json"})

    def test_action_request_rejects_unexpected_fields(self) -> None:
        with self.assertRaises(ValueError):
            SkillActionRequest.from_dict(
                {"action": "scan_from_json", "payload": {}, "auto_run": True}
            )

    def test_dispatch_rejects_unexpected_payload_fields(self) -> None:
        with self.assertRaises(ValueError):
            invoke_skill_action(
                {
                    "action": "scan_from_json",
                    "payload": {"input_data": {}, "extra": True},
                }
            )

    def test_scan_from_json_runs_pr7_pipeline(self) -> None:
        response = scan_from_json(self.input_data, scan_id="scan:pr10-test")
        result = response.result["scan_result"]
        self.assertEqual("scan:pr10-test", result["scan_id"])
        self.assertEqual(4, result["normalized_counts"]["total_targets"])
        self.assertEqual(4, len(result["decisions"]))
        self._assert_safe_response(response.to_dict())

    def test_explain_report_runs_pr9_mock(self) -> None:
        response = explain_report(self.report, provider="mock")
        self.assertEqual("mock", response.result["provider"])
        self.assertIn("safety_notice", response.result["markdown"])
        self._assert_safe_response(response.to_dict())

    def test_explain_report_supports_dry_run_prompt(self) -> None:
        response = explain_report(self.report, provider="dry-run-prompt")
        self.assertEqual("dry-run-prompt", response.result["provider"])
        self.assertIn("不要生成命令", response.result["markdown"])
        self._assert_safe_response(response.to_dict())

    def test_build_cleanup_plan_returns_plan_only_result(self) -> None:
        response = build_cleanup_plan(self.report, plan_id="plan:pr10-test")
        plan = response.result["cleanup_plan"]
        self.assertEqual("plan_only", plan["mode"])
        self.assertFalse(plan["execution_authorized"])
        self.assertEqual(4, len(plan["steps"]))
        self._assert_safe_response(response.to_dict())

    def test_write_report_writes_explicit_json(self) -> None:
        path = self.root / "report.json"
        response = write_report(path, self.report)
        self.assertEqual(self.report, json.loads(path.read_text(encoding="utf-8")))
        self.assertTrue(response.result["artifact_written"])
        self.assertFalse(response.result["system_change_performed"])
        self._assert_safe_response(response.to_dict())

    def test_write_report_does_not_overwrite_by_default(self) -> None:
        path = self.root / "report.json"
        path.write_text("preserve", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            write_report(path, self.report)
        self.assertEqual("preserve", path.read_text(encoding="utf-8"))

    def test_write_report_validates_serialization_before_creating_file(self) -> None:
        path = self.root / "invalid-report.json"
        with self.assertRaises(TypeError):
            write_report(path, {"invalid": {object()}})
        self.assertFalse(path.exists())

    def test_write_audit_writes_dry_run_jsonl(self) -> None:
        scan_response = scan_from_json(self.input_data, scan_id="scan:audit-source")
        events = scan_response.result["scan_result"]["audit_events"]
        path = self.root / "audit.jsonl"
        response = write_audit(path, events)
        written = [
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(4, len(written))
        self.assertTrue(all(event["dry_run"] is True for event in written))
        self.assertEqual(4, response.result["events_written"])
        self._assert_safe_response(response.to_dict())

    def test_write_audit_rejects_non_dry_run_event(self) -> None:
        event = {
            "dry_run": False,
            "command_summary": None,
            "result": "planned",
            "execution_method": "none",
        }
        with self.assertRaises(ValueError):
            write_audit(self.root / "audit.jsonl", [event])

    def test_write_audit_rejects_execution_claim(self) -> None:
        event = {
            "dry_run": True,
            "command_summary": "system change",
            "result": "planned",
            "execution_method": "none",
        }
        with self.assertRaises(ValueError):
            write_audit(self.root / "audit.jsonl", [event])

    def test_write_audit_rejects_unknown_fields(self) -> None:
        scan_response = scan_from_json(self.input_data)
        event = dict(scan_response.result["scan_result"]["audit_events"][0])
        event["unexpected"] = True
        with self.assertRaises(ValueError):
            write_audit(self.root / "audit.jsonl", [event])

    def test_write_audit_does_not_overwrite_by_default(self) -> None:
        scan_response = scan_from_json(self.input_data)
        events = scan_response.result["scan_result"]["audit_events"]
        path = self.root / "audit.jsonl"
        path.write_text("preserve\n", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            write_audit(path, events)
        self.assertEqual("preserve\n", path.read_text(encoding="utf-8"))

    def test_action_writers_reject_unc_paths(self) -> None:
        scan_response = scan_from_json(self.input_data)
        events = scan_response.result["scan_result"]["audit_events"]
        with self.assertRaises(ValueError):
            write_report(r"\\server\share\report.json", self.report)
        with self.assertRaises(ValueError):
            write_audit(r"\\server\share\audit.jsonl", events)

    def test_dispatch_preserves_request_id(self) -> None:
        response = invoke_skill_action(
            {
                "request_id": "request:external-ai",
                "action": "explain_report",
                "payload": {"report": self.report, "provider": "mock"},
            }
        )
        self.assertEqual("request:external-ai", response.request_id)

    def test_every_action_response_has_governance_fields(self) -> None:
        scan_response = scan_from_json(self.input_data)
        events = scan_response.result["scan_result"]["audit_events"]
        responses = (
            scan_response,
            explain_report(self.report),
            build_cleanup_plan(self.report),
            write_report(self.root / "governance-report.json", self.report),
            write_audit(self.root / "governance-audit.jsonl", events),
        )
        for response in responses:
            with self.subTest(action=response.action):
                data = response.to_dict()
                self.assertIn("requires_user_confirmation", data)
                self.assertIn("execution_level", data)
                self.assertIn("evidence", data)
                self._assert_safe_response(data)

    def test_action_modules_have_no_process_network_or_environment_access(self) -> None:
        paths = list((ROOT / "pc_cleanguard" / "skill").glob("*.py"))
        imports = set()
        calls = set()
        attributes = set()
        for path in paths:
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
                elif isinstance(node, ast.Attribute):
                    attributes.add(node.attr)
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
        self.assertTrue({"system", "popen", "Popen", "run"}.isdisjoint(calls))
        self.assertTrue({"getenv", "environ"}.isdisjoint(attributes | calls))

    def _assert_safe_response(self, response: dict) -> None:
        self.assertEqual("LEVEL_0_READ_ONLY", response["execution_level"])
        self.assertFalse(response["execution_authorized"])
        self.assertIsInstance(response["requires_user_confirmation"], bool)
        self.assertTrue(response["evidence"])


if __name__ == "__main__":
    unittest.main()
