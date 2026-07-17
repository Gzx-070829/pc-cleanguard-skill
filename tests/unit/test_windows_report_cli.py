import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from pc_cleanguard.cli import main


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


class WindowsReportCliTests(unittest.TestCase):
    def _collector_dir(self, root: Path) -> Path:
        collector = root / "collectors"
        collector.mkdir()
        names = ("installed_apps", "startup_items", "services", "scheduled_tasks")
        records = {
            "installed_apps": [{"name": "Product", "install_location": r"C:\Users\cli-user\AppData\Local\Product"}],
            "startup_items": [{"name": "Product Start", "command": r"C:\Users\cli-user\AppData\Local\Product\app.exe"}],
            "services": [{"service_name": "ProductService"}],
            "scheduled_tasks": [{"task_name": "Product Task"}],
        }
        _json(collector / "collector_manifest.json", {
            "schema_version": "0.4.1", "source_kind": "windows_powershell_collector",
            "generated_at": "2026-07-17T00:00:00Z",
            "collectors": {name: {"status": "success", "file": f"{name}.json", "record_count": 1} for name in names},
        })
        _json(collector / "collector_errors.json", [])
        for name in names:
            _json(collector / f"{name}.json", records[name])
        return collector

    def _main(self, arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_build_defaults_to_redacted_and_supports_validate_and_stats(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            collector = self._collector_dir(root)
            report, validation, stats = root / "report.json", root / "validation.json", root / "stats.json"
            code, stdout, _ = self._main(["windows", "report", "build", "--collector-dir", str(collector), "--output", str(report), "--validation-output", str(validation)])
            self.assertEqual(0, code)
            self.assertNotIn("cli-user", stdout)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual("windows_collector_redacted", payload["source_kind"])
            self.assertNotIn("cli-user", report.read_text(encoding="utf-8"))
            self.assertEqual(0, self._main(["windows", "report", "validate", "--input", str(report), "--output", str(root / "validate-again.json")])[0])
            self.assertEqual(0, self._main(["windows", "report", "stats", "--input", str(report), "--output", str(stats)])[0])
            stat = json.loads(stats.read_text(encoding="utf-8"))
            self.assertEqual(1, stat["software_count"])
            self.assertTrue(stat["persistence_input_ready"])

    def test_raw_output_requires_explicit_sensitive_data_acknowledgement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            collector = self._collector_dir(root)
            raw = root / "raw.json"
            code, _, error = self._main(["windows", "report", "build", "--collector-dir", str(collector), "--output", str(root / "redacted.json"), "--raw-output", str(raw)])
            self.assertEqual(2, code)
            self.assertIn("sensitive", error.casefold())
            self.assertFalse(raw.exists())

    def test_default_does_not_overwrite_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            collector = self._collector_dir(root)
            output = root / "report.json"
            self.assertEqual(0, self._main(["windows", "report", "build", "--collector-dir", str(collector), "--output", str(output)])[0])
            self.assertEqual(2, self._main(["windows", "report", "build", "--collector-dir", str(collector), "--output", str(output)])[0])


if __name__ == "__main__":
    unittest.main()
