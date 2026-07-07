import ast
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from pc_cleanguard.core.models import (
    ClassificationLabel,
    EvidenceChain,
    GovernanceTarget,
    PermissionLevel,
    PolicyDecision,
    RiskLevel,
)
from pc_cleanguard.pipeline import ScanPipelineResult, run_readonly_scan_pipeline


ROOT = Path(__file__).resolve().parents[2]


class ScanPipelineTest(unittest.TestCase):
    def test_pipeline_processes_installed_apps(self) -> None:
        result = self._run(installed_apps=self._sample("windows_installed_apps_registry_sample.json"))
        self.assertEqual(6, result.normalized_counts["installed_apps"])

    def test_pipeline_processes_startup_items(self) -> None:
        result = self._run(startup_items=self._sample("windows_startup_items_sample.json"))
        self.assertEqual(3, result.normalized_counts["startup_items"])

    def test_pipeline_processes_services(self) -> None:
        result = self._run(services=self._sample("windows_services_sample.json"))
        self.assertEqual(3, result.normalized_counts["services"])

    def test_pipeline_processes_scheduled_tasks(self) -> None:
        result = self._run(scheduled_tasks=self._sample("windows_scheduled_tasks_sample.json"))
        self.assertEqual(3, result.normalized_counts["scheduled_tasks"])

    def test_pipeline_processes_all_four_input_families(self) -> None:
        result = self._run_all()
        self.assertEqual(
            {
                "installed_apps": 6,
                "startup_items": 3,
                "services": 3,
                "scheduled_tasks": 3,
                "total_targets": 15,
            },
            result.normalized_counts,
        )

    def test_pipeline_outputs_input_summary(self) -> None:
        result = self._run_all()
        self.assertEqual(6, result.input_summary["installed_apps_count"])
        self.assertEqual(3, result.input_summary["scheduled_tasks_count"])

    def test_pipeline_outputs_governance_targets(self) -> None:
        result = self._run_all()
        self.assertEqual(15, len(result.targets))
        self.assertTrue(all(isinstance(target, GovernanceTarget) for target in result.targets))

    def test_pipeline_outputs_policy_decisions(self) -> None:
        result = self._run_all()
        self.assertEqual(15, len(result.decisions))
        self.assertTrue(all(isinstance(decision, PolicyDecision) for decision in result.decisions))

    def test_pipeline_outputs_report(self) -> None:
        result = self._run_all()
        self.assertEqual("scan-pr7-test", result.report["summary"]["scan_id"])
        self.assertFalse(result.report["summary"]["destructive_actions_executed"])
        self.assertFalse(result.report["managed_mode_compatibility"]["automatic_execution_allowed"])

    def test_pipeline_outputs_one_dry_run_event_per_target(self) -> None:
        result = self._run_all()
        self.assertEqual(len(result.targets), len(result.audit_events))
        self.assertTrue(all(event.dry_run is True for event in result.audit_events))
        self.assertTrue(all(event.execution_method == "policy_engine" for event in result.audit_events))

    def test_pipeline_outputs_scan_target_records(self) -> None:
        result = self._run_all()
        self.assertEqual(15, len(result.scan_target_records))
        self.assertTrue(all(record["scan_id"] == "scan-pr7-test" for record in result.scan_target_records))

    def test_startup_off_remains_dry_run_recommendation(self) -> None:
        result = self._run(
            startup_items=[{"name": "Example Toolbar Startup", "command": "example"}]
        )
        self.assertEqual(ClassificationLabel.STARTUP_OFF, result.decisions[0].classification)
        self.assertTrue(result.audit_events[0].dry_run)
        self.assertIsNone(result.audit_events[0].command_summary)
        self.assertFalse(result.report["summary"]["destructive_actions_executed"])

    def test_safe_remove_decision_does_not_execute(self) -> None:
        decision = PolicyDecision(
            target_id="WINDOWS_APP:synthetic",
            classification=ClassificationLabel.SAFE_REMOVE,
            risk_level=RiskLevel.MEDIUM,
            permission_level=PermissionLevel.LEVEL_3_STANDARD_UNINSTALL,
            allowed=True,
            reason="Synthetic candidate only.",
            evidence_chain=EvidenceChain(sources=("test",), facts=("candidate",), confidence=0.5),
            required_confirmation=True,
            rollback_required=False,
            audit_required=True,
            blocked_by_hard_rule=False,
        )
        with patch("pc_cleanguard.pipeline.scan_pipeline.evaluate_target", return_value=decision):
            result = self._run(installed_apps=[{"name": "Example App", "uninstall_string": "metadata"}])
        self.assertEqual(ClassificationLabel.SAFE_REMOVE, result.decisions[0].classification)
        self.assertTrue(result.audit_events[0].dry_run)
        self.assertIsNone(result.audit_events[0].command_summary)
        self.assertFalse(result.report["summary"]["destructive_actions_executed"])

    def test_pipeline_accepts_software_entries_alias(self) -> None:
        sample = self._sample("windows_installed_apps_normalized_sample.json")
        result = run_readonly_scan_pipeline(sample, scan_id="scan-alias")
        self.assertEqual(6, result.normalized_counts["installed_apps"])

    def test_pipeline_rejects_non_offline_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "offline"):
            run_readonly_scan_pipeline({"privacy_mode": "cloud_deep"})

    def test_pipeline_rejects_non_list_input_family(self) -> None:
        with self.assertRaisesRegex(ValueError, "services must be a list"):
            run_readonly_scan_pipeline({"services": {}})

    def test_pipeline_warns_when_nameless_records_are_omitted(self) -> None:
        result = self._run(services=[{"State": "Stopped"}])
        self.assertEqual(0, result.normalized_counts["services"])
        self.assertIn("services omitted 1 nameless record(s)", result.warnings)

    def test_pipeline_generates_scan_id_when_omitted(self) -> None:
        result = run_readonly_scan_pipeline({})
        self.assertTrue(result.scan_id.startswith("scan:"))

    def test_result_serializes_to_json(self) -> None:
        result = self._run_all()
        serialized = json.dumps(result.to_dict(), ensure_ascii=False)
        self.assertIn('"dry_run": true', serialized)
        self.assertNotIn('"command_summary": "', serialized)

    def test_pr7_example_input_runs_end_to_end(self) -> None:
        path = ROOT / "examples" / "scan_samples" / "pr7_readonly_scan_input.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        result = run_readonly_scan_pipeline(data, scan_id="scan:pr7-example")
        self.assertEqual(4, result.normalized_counts["total_targets"])
        self.assertEqual(4, len(result.decisions))
        self.assertEqual(4, len(result.audit_events))
        self.assertFalse(result.report["summary"]["destructive_actions_executed"])

    def test_pr7_report_example_matches_example_pipeline_identity(self) -> None:
        path = ROOT / "examples" / "reports" / "pr7_readonly_scan_pipeline_report.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("scan:pr7-example", report["scan_id"])
        self.assertEqual(4, report["normalized_counts"]["total_targets"])
        self.assertTrue(all(event["dry_run"] for event in report["audit_events"]))
        self.assertFalse(report["report"]["summary"]["destructive_actions_executed"])

    def test_pr7_audit_example_is_dry_run_jsonl(self) -> None:
        path = ROOT / "examples" / "audit" / "pr7_readonly_scan_pipeline_audit.jsonl"
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(4, len(events))
        self.assertTrue(all(event["dry_run"] is True for event in events))
        self.assertTrue(all(event["command_summary"] is None for event in events))

    def test_pipeline_module_has_no_process_network_or_collector_execution(self) -> None:
        path = ROOT / "pc_cleanguard" / "pipeline" / "scan_pipeline.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        calls = set()
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
        forbidden = {a + b for a, b in (("sub", "process"), ("req", "uests"), ("url", "lib"), ("sock", "et"))}
        self.assertTrue(forbidden.isdisjoint(imports))
        self.assertTrue({"system", "popen", "run", "Popen", "exec", "eval"}.isdisjoint(calls))
        self.assertNotIn(".ps1", source.casefold())

    def _run(self, **families) -> ScanPipelineResult:
        return run_readonly_scan_pipeline(
            {"platform": "Windows", "privacy_mode": "offline", **families},
            scan_id="scan-pr7-test",
        )

    def _run_all(self) -> ScanPipelineResult:
        return self._run(
            installed_apps=self._sample("windows_installed_apps_registry_sample.json"),
            startup_items=self._sample("windows_startup_items_sample.json"),
            services=self._sample("windows_services_sample.json"),
            scheduled_tasks=self._sample("windows_scheduled_tasks_sample.json"),
        )

    @staticmethod
    def _sample(name: str):
        return json.loads((ROOT / "examples" / "scan_samples" / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
