import ast
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main


ROOT = Path(__file__).resolve().parents[2]


class MinimalReadOnlyCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.input_path = self.root / "input.json"
        self.report_path = self.root / "report.json"
        self.audit_path = self.root / "audit.jsonl"
        self.input_path.write_text(
            json.dumps(
                {
                    "privacy_mode": "offline",
                    "installed_apps": [
                        {"DisplayName": "Example Notes", "UninstallString": None}
                    ],
                    "startup_items": [
                        {"name": "Example Notes Startup", "command": "metadata"}
                    ],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _arguments(self, *extra: str) -> list[str]:
        return [
            "scan",
            "--input",
            str(self.input_path),
            "--report",
            str(self.report_path),
            "--audit",
            str(self.audit_path),
            *extra,
        ]

    def _run(self, *extra: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(self._arguments(*extra))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_scan_writes_report_and_audit(self) -> None:
        code, _, _ = self._run()
        self.assertEqual(0, code)
        self.assertTrue(self.report_path.is_file())
        self.assertTrue(self.audit_path.is_file())

    def test_report_contains_pipeline_results(self) -> None:
        self._run("--scan-id", "scan:cli-test")
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        self.assertEqual("scan:cli-test", report["scan_id"])
        self.assertEqual(2, report["normalized_counts"]["total_targets"])
        self.assertEqual(2, len(report["targets"]))
        self.assertEqual(2, len(report["decisions"]))

    def test_audit_is_jsonl_and_dry_run_only(self) -> None:
        self._run()
        events = [
            json.loads(line)
            for line in self.audit_path.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(2, len(events))
        self.assertTrue(all(event["dry_run"] is True for event in events))
        self.assertTrue(all(event["command_summary"] is None for event in events))

    def test_report_confirms_no_execution(self) -> None:
        self._run()
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        self.assertFalse(report["report"]["summary"]["destructive_actions_executed"])

    def test_stdout_is_machine_readable_summary(self) -> None:
        code, stdout, stderr = self._run("--scan-id", "scan:summary")
        summary = json.loads(stdout)
        self.assertEqual(0, code)
        self.assertIn("Legacy compatibility interface", stderr)
        self.assertEqual("scan:summary", summary["scan_id"])
        self.assertEqual(2, summary["decisions"])
        self.assertFalse(summary["execution_performed"])

    def test_missing_input_returns_error(self) -> None:
        missing_path = self.root / "missing.json"
        arguments = self._arguments()
        arguments[arguments.index(str(self.input_path))] = str(missing_path)
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            code = main(arguments)
        stdout = stdout_buffer.getvalue()
        stderr = stderr_buffer.getvalue()
        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("does not exist", stderr)
        self.assertFalse(self.report_path.exists())
        self.assertFalse(self.audit_path.exists())

    def test_invalid_json_returns_error(self) -> None:
        self.input_path.write_text("{invalid", encoding="utf-8")
        code, _, stderr = self._run()
        self.assertEqual(2, code)
        self.assertIn("invalid scan JSON", stderr)

    def test_existing_report_is_not_overwritten_by_default(self) -> None:
        self.report_path.write_text("preserve", encoding="utf-8")
        code, _, stderr = self._run()
        self.assertEqual(2, code)
        self.assertIn("exists", stderr.casefold())
        self.assertEqual("preserve", self.report_path.read_text(encoding="utf-8"))

    def test_existing_outputs_can_be_explicitly_overwritten(self) -> None:
        self.report_path.write_text("old report", encoding="utf-8")
        self.audit_path.write_text("old audit\n", encoding="utf-8")
        code, _, _ = self._run("--overwrite")
        self.assertEqual(0, code)
        self.assertIn("scan_id", json.loads(self.report_path.read_text(encoding="utf-8")))
        events = [
            json.loads(line)
            for line in self.audit_path.read_text(encoding="utf-8").splitlines()
        ]
        self.assertTrue(events)
        self.assertTrue(all(event["dry_run"] is True for event in events))

    def test_unc_input_is_rejected(self) -> None:
        arguments = self._arguments()
        arguments[arguments.index(str(self.input_path))] = r"\\server\share\input.json"
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = main(arguments)
        self.assertEqual(2, code)
        self.assertIn("UNC", stderr.getvalue())

    def test_system_report_path_is_rejected(self) -> None:
        arguments = self._arguments()
        arguments[arguments.index(str(self.report_path))] = r"C:\Windows\report.json"
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = main(arguments)
        self.assertEqual(2, code)
        self.assertIn("system directory", stderr.getvalue())

    def test_repository_sample_runs_end_to_end(self) -> None:
        sample = ROOT / "examples" / "scan_samples" / "windows_pr6_normalized_sample.json"
        arguments = self._arguments("--scan-id", "scan:sample")
        arguments[arguments.index(str(self.input_path))] = str(sample)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = main(arguments)
        self.assertEqual(0, code)
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        self.assertEqual(9, report["normalized_counts"]["total_targets"])

    def test_cli_requires_explicit_paths(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as context:
            main(["scan"])
        self.assertEqual(2, context.exception.code)

    def test_cli_has_no_process_network_or_collector_execution(self) -> None:
        path = ROOT / "pc_cleanguard" / "cli.py"
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
        self.assertTrue({"system", "popen", "Popen", "exec", "eval"}.isdisjoint(calls))
        self.assertNotIn(".ps1", source.casefold())


if __name__ == "__main__":
    unittest.main()
