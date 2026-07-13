import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pc_cleanguard
from pc_cleanguard.cli import main
from pc_cleanguard.experience import run_release_smoke_check


ROOT = Path(__file__).resolve().parents[2]


class ReleaseSmokeTest(unittest.TestCase):
    def test_version_is_v032(self) -> None:
        self.assertEqual("0.3.3", pc_cleanguard.__version__)

    def test_cli_version(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as context:
            main(["--version"])
        self.assertEqual(0, context.exception.code)
        self.assertEqual("PC CleanGuard Skill 0.3.3", output.getvalue().strip())

    def test_release_smoke_assets_and_commands(self) -> None:
        result = run_release_smoke_check()
        self.assertTrue(result["passed"])
        self.assertTrue(all(result["checks"].values()))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("trial run --root .pcg-demo --output .pcg-trial", readme)
        self.assertIn("quarantine restore --root .pcg-quarantine", readme)

    def test_issue_templates_cover_trial_and_pup_feedback(self) -> None:
        templates = ROOT / ".github" / "ISSUE_TEMPLATE"
        for name in (
            "bug_report.yml", "cleanup_false_positive.yml", "software_rule_feedback.yml",
            "trial_experience_feedback.yml", "pup_reputation_feedback.yml",
        ):
            self.assertTrue((templates / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
