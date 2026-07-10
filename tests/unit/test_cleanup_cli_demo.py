import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main


class CleanupCliDemoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.base = Path(self.directory.name)
        self.root = self.base / ".pcg-demo"
        self.output = self.base / ".pcg-demo-output"

    def tearDown(self) -> None:
        self.directory.cleanup()

    @staticmethod
    def _run(arguments: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_demo_init_and_run_produce_tryable_dry_run(self) -> None:
        init_code, _, init_stderr = self._run(
            ["demo", "init-cleanup", "--root", str(self.root)]
        )
        run_code, stdout, run_stderr = self._run(
            [
                "demo",
                "run-cleanup",
                "--root",
                str(self.root),
                "--output",
                str(self.output),
            ]
        )

        self.assertEqual(0, init_code)
        self.assertEqual("", init_stderr)
        self.assertEqual(0, run_code)
        self.assertEqual("", run_stderr)
        self.assertFalse(json.loads(stdout)["confirmed"])
        self.assertTrue((self.output / "cleanup_report.md").is_file())
        self.assertTrue((self.root / "temp" / "example.tmp").exists())

    def test_demo_init_requires_force_to_refresh(self) -> None:
        arguments = ["demo", "init-cleanup", "--root", str(self.root)]
        self.assertEqual(0, self._run(arguments)[0])

        second_code, _, second_stderr = self._run(arguments)
        force_code, _, force_stderr = self._run([*arguments, "--force"])

        self.assertEqual(2, second_code)
        self.assertIn("exists", second_stderr.casefold())
        self.assertEqual(0, force_code)
        self.assertEqual("", force_stderr)

    def test_demo_run_confirm_remains_bounded_to_demo_l1(self) -> None:
        self.assertEqual(
            0,
            self._run(["demo", "init-cleanup", "--root", str(self.root)])[0],
        )

        code, stdout, stderr = self._run(
            [
                "demo",
                "run-cleanup",
                "--root",
                str(self.root),
                "--output",
                str(self.output),
                "--confirm",
            ]
        )

        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertTrue(json.loads(stdout)["confirmed"])
        self.assertFalse((self.root / "temp" / "example.tmp").exists())
        self.assertTrue((self.root / "dumps" / "example.dmp").exists())
        self.assertTrue((self.root / "installers" / "example.old").exists())

    def test_demo_quickstart_initializes_and_runs_dry_run_only(self) -> None:
        code, stdout, stderr = self._run(
            [
                "demo",
                "quickstart",
                "--root",
                str(self.root),
                "--output",
                str(self.output),
            ]
        )

        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        summary = json.loads(stdout)
        self.assertTrue(summary["quickstart"])
        self.assertFalse(summary["confirmed"])
        self.assertFalse(summary["execution_performed"])
        self.assertTrue((self.output / "preview.json").is_file())
        self.assertTrue((self.output / "cleanup_report.md").is_file())
        self.assertTrue((self.root / "temp" / "example.tmp").is_file())

    def test_demo_quickstart_has_no_confirm_option(self) -> None:
        arguments = [
            "demo",
            "quickstart",
            "--root",
            str(self.root),
            "--output",
            str(self.output),
            "--confirm",
        ]

        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as context:
            main(arguments)

        self.assertEqual(2, context.exception.code)
        self.assertFalse(self.root.exists())


if __name__ == "__main__":
    unittest.main()
