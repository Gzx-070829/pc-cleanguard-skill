import ast
import json
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from pc_cleanguard.audit import AuditEvent, JsonlAuditLogger
from pc_cleanguard.core.models import (
    ClassificationLabel,
    PermissionLevel,
    RiskLevel,
)


_REQUIRED_FIELDS = {
    "schema_version",
    "scan_id",
    "plan_id",
    "event_id",
    "timestamp",
    "actor",
    "mode",
    "action",
    "target_id",
    "target_name",
    "classification",
    "risk_level",
    "permission_level",
    "reason",
    "evidence_refs",
    "approved_by",
    "execution_method",
    "command_summary",
    "result",
    "rollback_available",
    "rollback_method",
    "dry_run",
    "policy_decision_id",
    "rulepack_version",
}


def make_event(**overrides) -> AuditEvent:
    values = {
        "action": "REPORT_ONLY",
        "target_id": "SOFTWARE:Runtime",
        "target_name": "Runtime",
        "classification": ClassificationLabel.KEEP,
        "risk_level": RiskLevel.LOW,
        "permission_level": PermissionLevel.LEVEL_0_READ_ONLY,
        "reason": "Synthetic protected runtime.",
        "evidence_refs": ("unit-test:evidence",),
    }
    values.update(overrides)
    return AuditEvent(**values)


class AuditEventTest(unittest.TestCase):
    def test_to_dict_contains_all_required_fields(self) -> None:
        data = make_event().to_dict()
        self.assertEqual(_REQUIRED_FIELDS, set(data))
        UUID(data["event_id"])
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        self.assertIsNotNone(timestamp.utcoffset())

    def test_default_dry_run_is_true(self) -> None:
        self.assertIs(True, make_event().dry_run)

    def test_default_actor_is_pc_cleanguard_skill(self) -> None:
        self.assertEqual("pc-cleanguard-skill", make_event().actor)

    def test_default_mode_is_safe(self) -> None:
        self.assertEqual("safe", make_event().mode)

    def test_result_success_is_rejected_by_logger(self) -> None:
        self._assert_tampered_event_rejected("result", "success")

    def test_dry_run_false_is_rejected_by_logger(self) -> None:
        self._assert_tampered_event_rejected("dry_run", False)

    def test_powershell_execution_method_is_rejected(self) -> None:
        self._assert_tampered_event_rejected("execution_method", "powershell")

    def test_winget_execution_method_is_rejected(self) -> None:
        self._assert_tampered_event_rejected("execution_method", "winget")

    def test_external_tool_execution_method_is_rejected(self) -> None:
        self._assert_tampered_event_rejected("execution_method", "external_tool")

    def _assert_tampered_event_rejected(self, field_name: str, value) -> None:
        event = make_event()
        object.__setattr__(event, field_name, value)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            logger = JsonlAuditLogger(path)
            with self.assertRaises(ValueError):
                logger.append_event(event)
            self.assertFalse(path.exists())


class JsonlAuditLoggerTest(unittest.TestCase):
    def test_append_event_appends_without_overwriting(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            logger = JsonlAuditLogger(path)
            logger.append_event(make_event(target_id="SOFTWARE:First"))
            first_content = path.read_text(encoding="utf-8")
            logger.append_event(make_event(target_id="SOFTWARE:Second"))
            final_content = path.read_text(encoding="utf-8")
            self.assertTrue(final_content.startswith(first_content))
            self.assertEqual(2, len(final_content.splitlines()))

    def test_append_event_separates_an_existing_unterminated_line(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            existing = json.dumps(make_event(target_id="SOFTWARE:Existing").to_dict())
            path.write_text(existing, encoding="utf-8")
            logger = JsonlAuditLogger(path)
            logger.append_event(make_event(target_id="SOFTWARE:Appended"))
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(2, len(lines))
            self.assertEqual("SOFTWARE:Existing", json.loads(lines[0])["target_id"])
            self.assertEqual("SOFTWARE:Appended", json.loads(lines[1])["target_id"])

    def test_read_events_returns_all_events(self) -> None:
        with TemporaryDirectory() as directory:
            logger = JsonlAuditLogger(Path(directory) / "audit.jsonl")
            logger.append_event(make_event(target_id="SOFTWARE:First"))
            logger.append_event(make_event(target_id="SOFTWARE:Second"))
            self.assertEqual(
                ["SOFTWARE:First", "SOFTWARE:Second"],
                [event["target_id"] for event in logger.read_events()],
            )

    def test_every_written_line_is_parseable_json(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            logger = JsonlAuditLogger(path)
            logger.append_event(make_event())
            for line in path.read_text(encoding="utf-8").splitlines():
                self.assertIsInstance(json.loads(line), dict)

    def test_example_audit_log_lines_are_parseable(self) -> None:
        events = self._example_events()
        self.assertEqual(5, len(events))
        self.assertTrue(all(set(event) == _REQUIRED_FIELDS for event in events))
        self.assertTrue(all(event["dry_run"] is True for event in events))
        self.assertTrue(
            all(
                event["result"]
                in {"planned", "simulated", "blocked", "refused", "skipped"}
                for event in events
            )
        )
        self.assertTrue(
            all(
                event["execution_method"]
                in {"none", "dry_run", "policy_engine", "report_builder"}
                for event in events
            )
        )

    def test_example_audit_log_contains_no_dangerous_commands(self) -> None:
        serialized = json.dumps(self._example_events()).casefold()
        forbidden = (
            "remove" + "-item",
            "winget " + "uninstall",
            "power" + "shell",
            "rm " + "-rf",
        )
        self.assertTrue(all(value not in serialized for value in forbidden))

    def test_logger_does_not_import_process_or_network_modules(self) -> None:
        logger_path = (
            Path(__file__).resolve().parents[2]
            / "pc_cleanguard"
            / "audit"
            / "jsonl_logger.py"
        )
        tree = ast.parse(logger_path.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        forbidden = {
            first + second
            for first, second in (
                ("sub", "process"),
                ("req", "uests"),
                ("url", "lib"),
                ("sock", "et"),
            )
        }
        self.assertTrue(forbidden.isdisjoint(imports))

    def test_logger_has_no_clear_or_delete_methods(self) -> None:
        method_names = {
            name
            for name, value in vars(JsonlAuditLogger).items()
            if callable(value)
        }
        self.assertNotIn("clear_log", method_names)
        self.assertNotIn("delete_log", method_names)

    def test_system_network_and_non_jsonl_paths_are_rejected(self) -> None:
        for path in (
            r"C:\Windows\audit.jsonl",
            r"\\server\share\audit.jsonl",
            "audit.log",
        ):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    JsonlAuditLogger(path)

    @staticmethod
    def _example_events() -> list[dict]:
        path = (
            Path(__file__).resolve().parents[2]
            / "examples"
            / "audit"
            / "sample_audit_log.jsonl"
        )
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


if __name__ == "__main__":
    unittest.main()
