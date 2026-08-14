import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pc_cleanguard.cli import _parser, main

from tests.guard.helpers import context, request


class GuardCliTests(unittest.TestCase):
    def _run(self, arguments, *, stdin_text=""):
        stdout = io.StringIO()
        stderr = io.StringIO()
        stdin = io.StringIO(stdin_text)
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), mock.patch.object(sys, "stdin", stdin):
            code = main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_help_positions_guard_before_legacy_commands(self):
        help_text = _parser().format_help()
        self.assertLess(help_text.index("guard"), help_text.index("windows"))
        self.assertIn("Legacy / Compatibility", help_text)
        for command in ("clean", "pup", "reputation", "persistence", "windows", "trial"):
            with self.subTest(command=command):
                self.assertRegex(
                    help_text,
                    rf"\n    {command}\s+Legacy / Compatibility:",
                )

    def test_evaluate_json_mode_has_machine_stdout_and_pending_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path = root / "request.json"
            context_path = root / "context.json"
            request_path.write_text(json.dumps(request().to_dict()), encoding="utf-8")
            context_path.write_text(json.dumps(context().to_dict()), encoding="utf-8")
            code, stdout, stderr = self._run(
                [
                    "guard", "evaluate", "--request", str(request_path),
                    "--context", str(context_path), "--json",
                ]
            )
            self.assertEqual(4, code)
            self.assertEqual("REQUIRE", json.loads(stdout)["disposition"])
            self.assertEqual("", stderr)

    def test_stdin_readonly_evaluation_returns_zero(self):
        envelope = {
            "request": request(
                "read_metadata", requested_effect="read TEMP usage metadata"
            ).to_dict(),
            "context": context().to_dict(),
        }
        code, stdout, _ = self._run(
            ["guard", "evaluate", "--stdin", "--json"],
            stdin_text=json.dumps(envelope),
        )
        self.assertEqual(0, code)
        self.assertEqual("ALLOW", json.loads(stdout)["disposition"])

    def test_blocked_evaluation_returns_three_with_decision_json(self):
        path = r"C:\Windows\System32\kernel32.dll"
        envelope = {
            "request": request(path=path).to_dict(),
            "context": context(path=path).to_dict(),
        }
        code, stdout, _ = self._run(
            ["guard", "evaluate", "--stdin", "--json"],
            stdin_text=json.dumps(envelope),
        )
        self.assertEqual(3, code)
        self.assertEqual("BLOCK", json.loads(stdout)["disposition"])

    def test_guard_doctor_is_offline_and_healthy(self):
        code, stdout, stderr = self._run(["guard", "doctor", "--json"])
        self.assertEqual(0, code)
        self.assertTrue(json.loads(stdout)["healthy"])
        self.assertEqual("", stderr)

    def test_legacy_command_warns_on_stderr_without_polluting_json_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "input.json"
            report_path = root / "report.json"
            audit_path = root / "audit.jsonl"
            input_path.write_text("{}", encoding="utf-8")
            code, stdout, stderr = self._run(
                [
                    "scan", "--input", str(input_path), "--report", str(report_path),
                    "--audit", str(audit_path),
                ]
            )
            self.assertEqual(0, code)
            json.loads(stdout)
            self.assertIn("Legacy compatibility interface", stderr)
            self.assertNotIn("Legacy", stdout)


if __name__ == "__main__":
    unittest.main()
