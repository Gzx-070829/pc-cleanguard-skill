import json
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.pup import build_pup_review_pack
from pc_cleanguard.cli import main

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = {
    "START_HERE.md", "user_summary.md", "machine_summary.json", "pup_insight.md",
    "reputation_matches.json", "evidence_indicators.json", "human_review_checklist.md",
    "source_trace.md", "false_positive_feedback.md", "safety_notice.md",
    "behavior_indicators.json", "behavior_indicators.md", "cn_evidence_summary.md",
    "adversarial_safety_summary.md",
}


class PupReviewPackTest(unittest.TestCase):
    def test_review_pack_writes_complete_local_folder_and_controls_overwrite(self) -> None:
        report = json.loads((ROOT / "tests/fixtures/reputation/pr26_realistic_windows_inventory.json").read_text(encoding="utf-8"))
        evidence = ROOT / "data/reputation/evidence_pack.real.zh-CN.json"
        with TemporaryDirectory() as directory:
            output = Path(directory) / "review"
            summary = build_pup_review_pack(report, evidence, output)
            self.assertEqual(ARTIFACTS, {path.name for path in output.iterdir()})
            self.assertEqual(0, summary["execution_gating_eligible_count"])
            machine = json.loads((output / "machine_summary.json").read_text(encoding="utf-8"))
            for field in ("real_source_match_count", "indicator_match_count", "execution_gating_eligible_count"):
                self.assertIn(field, machine)
            with self.assertRaises(FileExistsError):
                build_pup_review_pack(report, evidence, output)
            build_pup_review_pack(report, evidence, output, overwrite=True)
            self.assertIn("不是删除", (output / "START_HERE.md").read_text(encoding="utf-8"))

    def test_review_pack_cli_writes_complete_folder(self) -> None:
        source = ROOT / "tests/fixtures/reputation/pr26_realistic_windows_inventory.json"
        evidence = ROOT / "data/reputation/evidence_pack.real.zh-CN.json"
        with TemporaryDirectory() as directory:
            output = Path(directory) / "cli-review"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = main(["pup", "review-pack", "--input", str(source), "--evidence-pack", str(evidence), "--output", str(output)])
            self.assertEqual(0, code)
            self.assertEqual(ARTIFACTS, {path.name for path in output.iterdir()})


if __name__ == "__main__":
    unittest.main()
