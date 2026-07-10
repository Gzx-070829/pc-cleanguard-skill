import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cleanup import (
    CleanupConfirmation,
    CleanupExecutor,
    JunkScanner,
    build_cleanup_preview,
    write_cleanup_execution_report,
)
from pc_cleanguard.cli import main


class CleanupCliReportingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / "example.tmp").write_bytes(b"1234")
        preview = build_cleanup_preview(JunkScanner().scan([self.root])).to_dict()
        self.preview = self.root / "preview.json"
        self.preview.write_text(json.dumps(preview), encoding="utf-8")
        execution = CleanupExecutor().execute(
            preview,
            CleanupConfirmation(False, (self.root,)),
            audit_path=self.root / "audit.jsonl",
        )
        self.result = self.root / "result.json"
        write_cleanup_execution_report(self.result, execution)
        self.output = self.root / "cleanup-report.md"

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _run(self, *extra: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        arguments = [
            "clean",
            "report",
            "--preview",
            str(self.preview),
            "--result",
            str(self.result),
            "--output",
            str(self.output),
            *extra,
        ]
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_clean_report_writes_markdown_from_explicit_inputs(self) -> None:
        code, stdout, stderr = self._run()

        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("Cleanup Report", self.output.read_text(encoding="utf-8"))
        summary = json.loads(stdout)
        self.assertEqual(1, summary["total_candidates"])
        self.assertEqual(1, summary["would_clean_count"])

    def test_clean_report_does_not_overwrite_by_default(self) -> None:
        self.output.write_text("preserve", encoding="utf-8")

        code, _, stderr = self._run()

        self.assertEqual(2, code)
        self.assertIn("exists", stderr.casefold())
        self.assertEqual("preserve", self.output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
