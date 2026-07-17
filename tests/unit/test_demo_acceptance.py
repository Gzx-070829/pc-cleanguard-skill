import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from pc_cleanguard.cli import main
from pc_cleanguard.demo import init_cleanup_demo, run_demo_acceptance


class DemoAcceptanceTests(unittest.TestCase):
    def test_desktop_protection_remains_enabled(self):
        with tempfile.TemporaryDirectory() as directory:
            protected = Path(directory) / "Desktop" / "ordinary-demo"
            with self.assertRaisesRegex(ValueError, "demo acceptance"):
                init_cleanup_demo(protected)

    def test_acceptance_quarantines_restores_and_matches_sha256(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "acceptance"
            result = run_demo_acceptance(output, confirm_synthetic=True)
            self.assertTrue(result["quarantine_succeeded"])
            self.assertTrue(result["restore_succeeded"])
            self.assertTrue(result["restored_sha256_matches"])
            self.assertFalse(result["permanent_delete_performed"])
            self.assertTrue((output / "acceptance_result.json").is_file())
            self.assertTrue((output / "audit.jsonl").is_file())
            audit = [json.loads(line) for line in (output / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertTrue(audit)
            self.assertTrue(all(event["execution_method"] in {"pathlib_replace", "none"} for event in audit))

    def test_cli_requires_explicit_synthetic_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "acceptance"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(["demo", "acceptance", "--output", str(output)])
            self.assertEqual(2, code)
            self.assertFalse(output.exists())

    def test_cli_acceptance_generates_report_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "acceptance"
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(["demo", "acceptance", "--output", str(output), "--confirm-synthetic"])
            self.assertEqual(0, code)
            for name in ("START_HERE.md", "preview.json", "execution_result.json", "audit.jsonl", "acceptance_result.json"):
                self.assertTrue((output / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
