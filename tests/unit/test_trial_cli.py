import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main


class TrialCliTest(unittest.TestCase):
    def test_trial_run_works_and_parser_rejects_permanent(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            args = ["trial", "run", "--root", str(base / "demo"), "--output", str(base / "trial")]
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(0, main(args))
            self.assertTrue((base / "trial/START_HERE.md").is_file())
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main([*args, "--permanent"])

    def test_trial_cli_confirm_uses_explicit_quarantine(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = main([
                    "trial", "run", "--root", str(base / "demo"),
                    "--output", str(base / "trial"), "--confirm",
                    "--quarantine-root", str(base / "quarantine"),
                ])
            self.assertEqual(0, code)
            self.assertTrue((base / "quarantine/manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
