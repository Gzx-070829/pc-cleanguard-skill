import ast
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.pipeline import (
    run_readonly_scan_pipeline,
    write_pipeline_audit_jsonl,
    write_pipeline_report,
)


ROOT = Path(__file__).resolve().parents[2]


class ScanPipelineResultWriterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.result = run_readonly_scan_pipeline(
            {"startup_items": [{"name": "Example Toolbar Startup", "command": "metadata"}]},
            scan_id="scan-writer-test",
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_write_pipeline_report_writes_utf8_json(self) -> None:
        path = self.root / "report.json"
        write_pipeline_report(path, self.result)
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("scan-writer-test", data["scan_id"])

    def test_write_pipeline_audit_writes_jsonl(self) -> None:
        path = self.root / "audit.jsonl"
        write_pipeline_audit_jsonl(path, list(self.result.audit_events))
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertEqual("scan-writer-test", json.loads(lines[0])["scan_id"])

    def test_written_audit_events_are_dry_run(self) -> None:
        path = self.root / "audit.jsonl"
        write_pipeline_audit_jsonl(path, list(self.result.audit_events))
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(all(event["dry_run"] is True for event in events))
        self.assertTrue(all(event["command_summary"] is None for event in events))

    def test_report_writer_does_not_overwrite_by_default(self) -> None:
        path = self.root / "report.json"
        path.write_text("existing", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            write_pipeline_report(path, self.result)
        self.assertEqual("existing", path.read_text(encoding="utf-8"))

    def test_audit_writer_does_not_overwrite_by_default(self) -> None:
        path = self.root / "audit.jsonl"
        path.write_text("existing\n", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            write_pipeline_audit_jsonl(path, list(self.result.audit_events))
        self.assertEqual("existing\n", path.read_text(encoding="utf-8"))

    def test_report_writer_supports_explicit_overwrite(self) -> None:
        path = self.root / "report.json"
        path.write_text("existing", encoding="utf-8")
        write_pipeline_report(path, self.result, explicit_overwrite=True)
        self.assertEqual("scan-writer-test", json.loads(path.read_text(encoding="utf-8"))["scan_id"])

    def test_audit_writer_supports_explicit_overwrite(self) -> None:
        path = self.root / "audit.jsonl"
        path.write_text("existing\n", encoding="utf-8")
        write_pipeline_audit_jsonl(
            path, list(self.result.audit_events), explicit_overwrite=True
        )
        self.assertTrue(json.loads(path.read_text(encoding="utf-8"))["dry_run"])

    def test_writer_creates_only_explicit_parent(self) -> None:
        path = self.root / "explicit" / "report.json"
        write_pipeline_report(path, self.result)
        self.assertTrue(path.is_file())

    def test_writer_rejects_unc_paths(self) -> None:
        with self.assertRaises(ValueError):
            write_pipeline_report(r"\\server\share\report.json", self.result)

    def test_writer_rejects_device_paths(self) -> None:
        with self.assertRaises(ValueError):
            write_pipeline_report(r"\\?\C:\safe\report.json", self.result)

    def test_writer_rejects_windows_system_paths(self) -> None:
        for path in (r"C:\Windows\report.json", r"C:\Program Files\audit.jsonl"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                if path.endswith(".jsonl"):
                    write_pipeline_audit_jsonl(path, list(self.result.audit_events))
                else:
                    write_pipeline_report(path, self.result)

    def test_writers_reject_wrong_extensions(self) -> None:
        with self.assertRaises(ValueError):
            write_pipeline_report(self.root / "report.txt", self.result)
        with self.assertRaises(ValueError):
            write_pipeline_audit_jsonl(self.root / "audit.txt", list(self.result.audit_events))

    def test_audit_writer_rejects_non_event_values(self) -> None:
        with self.assertRaises(TypeError):
            write_pipeline_audit_jsonl(self.root / "audit.jsonl", [{}])

    def test_result_writer_has_no_process_or_network_imports(self) -> None:
        path = ROOT / "pc_cleanguard" / "pipeline" / "result_writer.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = set()
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
        forbidden = {a + b for a, b in (("sub", "process"), ("req", "uests"), ("url", "lib"), ("sock", "et"))}
        self.assertTrue(forbidden.isdisjoint(imports))
        self.assertTrue({"system", "popen", "run", "Popen"}.isdisjoint(calls))


if __name__ == "__main__":
    unittest.main()
