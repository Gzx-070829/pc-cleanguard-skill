import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main


class CleanupCliPreviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.first = self.root / "first"
        self.second = self.root / "second"
        self.first.mkdir()
        self.second.mkdir()
        self.first_candidate = self.first / "one.tmp"
        self.second_candidate = self.second / "two.log"
        self.first_candidate.write_bytes(b"123")
        self.second_candidate.write_bytes(b"12345")
        self.output = self.root / "preview.json"

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _run(self, *extra: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        arguments = [
            "clean",
            "preview",
            "--path",
            str(self.first),
            "--path",
            str(self.second),
            "--output",
            str(self.output),
            *extra,
        ]
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_clean_preview_writes_json_for_multiple_explicit_paths(self) -> None:
        code, stdout, stderr = self._run()
        preview = json.loads(self.output.read_text(encoding="utf-8"))
        summary = json.loads(stdout)
        self.assertEqual(0, code)
        self.assertIn("Legacy compatibility interface", stderr)
        self.assertEqual(2, preview["total_candidates"])
        self.assertEqual(8, preview["total_reclaimable_bytes"])
        self.assertEqual(2, summary["total_candidates"])
        self.assertTrue(summary["dry_run_only"])
        self.assertTrue(self.first_candidate.exists())
        self.assertTrue(self.second_candidate.exists())

    def test_clean_preview_does_not_overwrite_by_default(self) -> None:
        self.output.write_text("preserve", encoding="utf-8")
        code, _, stderr = self._run()
        self.assertEqual(2, code)
        self.assertIn("exists", stderr.casefold())
        self.assertEqual("preserve", self.output.read_text(encoding="utf-8"))

    def test_clean_preview_can_explicitly_overwrite(self) -> None:
        self.output.write_text("old", encoding="utf-8")
        code, _, _ = self._run("--overwrite")
        self.assertEqual(0, code)
        self.assertIn(
            "total_candidates", json.loads(self.output.read_text(encoding="utf-8"))
        )

    def test_clean_preview_requires_explicit_paths(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as context:
            main(["clean", "preview", "--output", str(self.output)])
        self.assertEqual(2, context.exception.code)


if __name__ == "__main__":
    unittest.main()
