import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cleanup import JunkScanner, build_cleanup_preview
from pc_cleanguard.cli import main


class CleanupCliExecuteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.candidate = self.root / "cli-test.tmp"
        self.candidate.write_bytes(b"1234")
        preview = build_cleanup_preview(JunkScanner().scan([self.root])).to_dict()
        self.preview = self.root / "preview.json"
        self.preview.write_text(json.dumps(preview), encoding="utf-8")
        self.result = self.root / "result.json"
        self.audit = self.root / "audit.jsonl"

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _arguments(self, *extra: str) -> list[str]:
        return [
            "clean",
            "execute",
            "--preview",
            str(self.preview),
            "--allow-root",
            str(self.root),
            "--result",
            str(self.result),
            "--audit",
            str(self.audit),
            *extra,
        ]

    def _run(self, *extra: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(self._arguments(*extra))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_execute_defaults_to_dry_run(self) -> None:
        code, stdout, stderr = self._run()
        report = json.loads(self.result.read_text(encoding="utf-8"))
        self.assertEqual(0, code)
        self.assertIn("Legacy compatibility interface", stderr)
        self.assertEqual("would_clean", report["results"][0]["status"])
        self.assertTrue(self.candidate.exists())
        self.assertTrue(self.audit.is_file())
        self.assertFalse(json.loads(stdout)["confirmed"])

    def test_execute_confirm_deletes_l1_file_in_temporary_allow_root(self) -> None:
        code, stdout, stderr = self._run(
            "--confirm", "--permanent", "--i-understand-permanent-delete"
        )
        report = json.loads(self.result.read_text(encoding="utf-8"))
        audit = [
            json.loads(line) for line in self.audit.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(0, code)
        self.assertIn("Legacy compatibility interface", stderr)
        self.assertFalse(self.candidate.exists())
        self.assertEqual("cleaned", report["results"][0]["status"])
        self.assertEqual(4, report["results"][0]["bytes_reclaimed"])
        self.assertFalse(audit[0]["dry_run"])
        self.assertTrue(json.loads(stdout)["confirmed"])

    def test_existing_result_blocks_before_confirmed_deletion(self) -> None:
        self.result.write_text("preserve", encoding="utf-8")
        code, _, stderr = self._run(
            "--confirm", "--permanent", "--i-understand-permanent-delete"
        )
        self.assertEqual(2, code)
        self.assertIn("exists", stderr.casefold())
        self.assertEqual("preserve", self.result.read_text(encoding="utf-8"))
        self.assertTrue(self.candidate.exists())
        self.assertFalse(self.audit.exists())

    def test_execute_requires_explicit_allow_root(self) -> None:
        arguments = self._arguments()
        index = arguments.index("--allow-root")
        del arguments[index : index + 2]
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as context:
            main(arguments)
        self.assertEqual(2, context.exception.code)


if __name__ == "__main__":
    unittest.main()
