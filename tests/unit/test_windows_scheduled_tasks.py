import ast
import json
import unittest
from pathlib import Path

from pc_cleanguard.core.models import ClassificationLabel, GovernanceTarget, ObjectType
from pc_cleanguard.core.policy_engine import evaluate_target
from pc_cleanguard.windows import (
    ScheduledTask,
    normalize_scheduled_task,
    normalize_scheduled_tasks,
    scheduled_task_to_governance_target,
    scheduled_task_to_scan_target_record,
)


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-07-06T00:00:00Z"


class WindowsScheduledTasksTest(unittest.TestCase):
    def test_normalize_task_record(self) -> None:
        task = normalize_scheduled_task(
            {"TaskName": "Example Task", "TaskPath": "\\Example\\", "State": "Ready"}
        )
        self.assertEqual("Example Task", task.task_name)
        self.assertEqual("\\Example\\", task.task_path)

    def test_task_fields_are_preserved(self) -> None:
        task = self._task()
        self.assertEqual("Ready", task.state)
        self.assertEqual("Example Vendor", task.author)
        self.assertEqual("Limited", task.run_level)
        self.assertIn("StartBoundary", task.triggers_summary)

    def test_nameless_task_is_skipped(self) -> None:
        self.assertIsNone(normalize_scheduled_task({"State": "Ready"}))
        self.assertEqual([], normalize_scheduled_tasks([{"State": "Ready"}]))

    def test_actions_summary_is_metadata_only(self) -> None:
        actions = '[{"Execute":"example-task.exe"}]'
        task = self._task(actions_summary=actions)
        self.assertEqual(actions, task.actions_summary)
        self.assertNotIn(actions, repr(task))

    def test_task_id_is_stable_and_excludes_actions(self) -> None:
        first = self._task(actions_summary="first-action")
        second = self._task(actions_summary="second-action")
        self.assertEqual(first.task_id, second.task_id)
        self.assertNotIn("first-action", first.task_id)

    def test_governance_target_has_task_type_without_classification(self) -> None:
        target = scheduled_task_to_governance_target(self._task())
        self.assertIsInstance(target, GovernanceTarget)
        self.assertEqual(ObjectType.SCHEDULED_TASK, target.object_type)
        self.assertIsNone(target.requested_classification)

    def test_unknown_task_remains_ask_user(self) -> None:
        task = self._task(task_name="Unknown Scheduled Task", task_path="\\Unknown\\")
        decision = evaluate_target(scheduled_task_to_governance_target(task))
        self.assertEqual(ClassificationLabel.ASK_USER, decision.classification)
        self.assertNotEqual(ClassificationLabel.SAFE_REMOVE, decision.classification)

    def test_scan_target_record_matches_sqlite_fields(self) -> None:
        record = scheduled_task_to_scan_target_record(self._task(), "scan-1")
        self.assertEqual("SCHEDULED_TASK", record["object_type"])
        self.assertNotIn("actions_summary", record)
        self.assertEqual("\\Example\\", record["path"])

    def test_scheduled_task_sample_is_safe_and_parseable(self) -> None:
        data = json.loads(
            (ROOT / "examples" / "scan_samples" / "windows_scheduled_tasks_sample.json").read_text(encoding="utf-8")
        )
        self.assertEqual(3, len(normalize_scheduled_tasks(data)))
        serialized = json.dumps(data)
        self.assertNotIn("C:\\Users\\", serialized)
        self.assertIn("%USERPROFILE%", serialized)

    def test_module_imports_no_process_or_network_packages(self) -> None:
        path = ROOT / "pc_cleanguard" / "windows" / "scheduled_tasks.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        forbidden = {a + b for a, b in (("sub", "process"), ("req", "uests"), ("url", "lib"), ("sock", "et"))}
        self.assertTrue(forbidden.isdisjoint(imports))

    def test_pr6_normalized_sample_is_complete_and_deidentified(self) -> None:
        data = json.loads(
            (
                ROOT
                / "examples"
                / "scan_samples"
                / "windows_pr6_normalized_sample.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(3, len(data["startup_items"]))
        self.assertEqual(3, len(data["services"]))
        self.assertEqual(3, len(data["scheduled_tasks"]))
        serialized = json.dumps(data)
        self.assertNotIn("C:\\Users\\", serialized)
        self.assertNotIn("token", serialized.casefold())

    def test_scan_schema_has_observation_fields_without_execution_fields(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "scan_result.schema.json").read_text(encoding="utf-8")
        )
        self.assertIn("scheduled_tasks", schema["properties"])
        fields = set(schema["$defs"]["discovered_object"]["properties"])
        self.assertTrue(
            {
                "command",
                "path_name",
                "actions_summary",
                "triggers_summary",
                "service_id",
                "task_id",
                "item_id",
            }.issubset(fields)
        )
        self.assertTrue(
            {
                "disable_command",
                "stop_command",
                "delete_command",
                "uninstall_command",
            }.isdisjoint(fields)
        )

    @staticmethod
    def _task(**overrides) -> ScheduledTask:
        raw = {
            "task_name": "Example Scheduled Task",
            "task_path": "\\Example\\",
            "state": "Ready",
            "author": "Example Vendor",
            "description": "Synthetic task.",
            "uri": r"\Example\Example Scheduled Task",
            "actions_summary": '[{"Execute":"example-task.exe"}]',
            "triggers_summary": '[{"StartBoundary":null,"Enabled":true}]',
            "principal_user_id": "SYSTEM",
            "run_level": "Limited",
            "source": "windows_scheduled_task",
            "collected_at": NOW,
        }
        raw.update(overrides)
        return normalize_scheduled_task(raw)


if __name__ == "__main__":
    unittest.main()
