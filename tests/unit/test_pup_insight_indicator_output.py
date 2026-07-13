import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main
from pc_cleanguard.pup import inspect_pup_risk

ROOT = Path(__file__).resolve().parents[2]


class PupInsightIndicatorOutputTest(unittest.TestCase):
    def test_inspect_with_indicators_exposes_required_counts(self) -> None:
        report = json.loads((ROOT / "tests/fixtures/reputation/pr26_realistic_windows_inventory.json").read_text(encoding="utf-8"))
        result = inspect_pup_risk(report, ROOT / "data/reputation/evidence_pack.real.zh-CN.json", evidence_pack=True, include_indicators=True)
        summary = result["insight"]["summary"]
        for field in ("indicator_match_count", "high_uncertainty_match_count", "detection_family_match_count", "publisher_hint_match_count", "human_review_required_count"):
            self.assertIn(field, summary)

    def test_cli_inspect_can_write_human_review_checklist(self) -> None:
        source = ROOT / "tests/fixtures/reputation/pr26_realistic_windows_inventory.json"
        evidence = ROOT / "data/reputation/evidence_pack.real.zh-CN.json"
        with TemporaryDirectory() as directory:
            insight = Path(directory) / "insight.md"
            checklist = Path(directory) / "checklist.md"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = main(["pup", "inspect", "--input", str(source), "--evidence-pack", str(evidence), "--output", str(insight), "--include-indicators", "--human-review-checklist", str(checklist)])
            self.assertEqual(0, code)
            self.assertTrue(insight.is_file() and checklist.is_file())


if __name__ == "__main__":
    unittest.main()
