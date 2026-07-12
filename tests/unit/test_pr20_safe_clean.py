import io
import os
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cleanup import JunkScanner, build_cleanup_preview
from pc_cleanguard.cli import main


class Pr20SafeCleanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.candidate = self.root / "safe.tmp"
        self.candidate.write_bytes(b"safe")
        preview = build_cleanup_preview(JunkScanner().scan([self.root])).to_dict()
        self.preview = self.root / "preview.json"
        self.preview.write_text(json.dumps(preview), encoding="utf-8")

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _execute(self, *extra: str) -> tuple[int, str]:
        stderr = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            code = main([
                "clean", "execute", "--preview", str(self.preview),
                "--allow-root", str(self.root), "--result", str(self.root / "result.json"),
                "--audit", str(self.root / "audit.jsonl"), *extra,
            ])
        return code, stderr.getvalue()

    def test_confirm_without_quarantine_uses_default_quarantine(self) -> None:
        previous = Path.cwd()
        os.chdir(self.root)
        try:
            code, error = self._execute("--confirm")
        finally:
            os.chdir(previous)
        self.assertEqual(0, code, error)
        self.assertFalse(self.candidate.exists())
        report = json.loads((self.root / "result.json").read_text(encoding="utf-8"))
        self.assertTrue(report["summary"]["default_quarantine_root"])
        self.assertIn("使用默认隔离目录：.pcg-quarantine", (self.root / "audit.jsonl").read_text(encoding="utf-8"))

    def test_permanent_requires_second_confirmation(self) -> None:
        code, error = self._execute("--confirm", "--permanent")
        self.assertEqual(2, code)
        self.assertIn("i-understand-permanent-delete", error)
        self.assertTrue(self.candidate.exists())

    def test_permanent_with_both_confirmations_deletes_l1_only(self) -> None:
        code, error = self._execute(
            "--confirm", "--permanent", "--i-understand-permanent-delete"
        )
        self.assertEqual(0, code, error)
        self.assertFalse(self.candidate.exists())

    def test_clean_safe_defaults_to_complete_dry_run_artifacts(self) -> None:
        output = self.root / "safe-output"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = main(["clean", "safe", "--path", str(self.root), "--output", str(output)])
        self.assertEqual(0, code)
        self.assertTrue(self.candidate.exists())
        self.assertEqual(
            {"preview.json", "result.json", "audit.jsonl", "cleanup_report.md", "summary.json"},
            {path.name for path in output.iterdir()},
        )
        result = json.loads((output / "result.json").read_text(encoding="utf-8"))
        self.assertEqual("dry_run", result["mode"])

    def test_clean_safe_confirm_uses_quarantine(self) -> None:
        output = self.root / "confirmed-output"
        quarantine = self.root / "quarantine"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = main([
                "clean", "safe", "--path", str(self.root), "--output", str(output),
                "--confirm", "--quarantine-root", str(quarantine),
            ])
        self.assertEqual(0, code)
        self.assertFalse(self.candidate.exists())
        result = json.loads((output / "result.json").read_text(encoding="utf-8"))
        self.assertEqual("confirmed_l1_quarantine", result["mode"])
        self.assertEqual(1, result["summary"]["quarantined"])

    def test_clean_safe_confirm_without_root_uses_default(self) -> None:
        output = self.root / "default-output"
        previous = Path.cwd(); os.chdir(self.root)
        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = main(["clean", "safe", "--path", str(self.root), "--output", str(output), "--confirm"])
        finally:
            os.chdir(previous)
        self.assertEqual(0, code)
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        self.assertTrue(summary["default_quarantine_root"])

    def test_clean_safe_parser_has_no_permanent_option(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main([
                "clean", "safe", "--path", str(self.root),
                "--output", str(self.root / "out"), "--permanent",
            ])


if __name__ == "__main__":
    unittest.main()
