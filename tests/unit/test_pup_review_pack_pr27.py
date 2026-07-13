import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main
from pc_cleanguard.pup import build_pup_review_pack


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "tests/fixtures/reputation/pr26_realistic_windows_inventory.json"
REAL_PACK = ROOT / "data/reputation/evidence_pack.real.zh-CN.json"
CN_PACK = ROOT / "data/reputation/evidence_pack.cn.zh-CN.json"
ARTIFACTS = {
    "START_HERE.md", "user_summary.md", "machine_summary.json", "pup_insight.md",
    "reputation_matches.json", "evidence_indicators.json", "behavior_indicators.json",
    "behavior_indicators.md", "human_review_checklist.md", "source_trace.md",
    "false_positive_feedback.md", "safety_notice.md", "cn_evidence_summary.md",
    "adversarial_safety_summary.md",
}


class PupReviewPackPr27Test(unittest.TestCase):
    def test_review_pack_contains_cn_behavior_and_guard_artifacts(self):
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        with TemporaryDirectory() as directory:
            output = Path(directory) / "pack"
            summary = build_pup_review_pack(
                report, REAL_PACK, output, cn_evidence_pack=CN_PACK,
                include_behavior_indicators=True,
            )
            self.assertEqual(ARTIFACTS, {item.name for item in output.iterdir()})
            machine = json.loads((output / "machine_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(5, machine["cn_real_source_count"])
            self.assertGreater(machine["behavior_indicator_count"], 0)
            self.assertEqual("enforced", machine["adversarial_guard_status"])
            self.assertEqual(0, machine["execution_gating_eligible_count"])
            self.assertEqual(0, summary["execution_gating_eligible_count"])

    def test_pr27_review_pack_and_behavior_cli_run_offline(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            commands = [
                ["pup", "behavior", "--input", str(REPORT_PATH), "--output", str(root / "behavior.json")],
                ["pup", "review-pack", "--input", str(REPORT_PATH), "--evidence-pack", str(REAL_PACK), "--cn-evidence-pack", str(CN_PACK), "--output", str(root / "pack"), "--include-behavior-indicators"],
            ]
            for command in commands:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(0, main(command), command)
            self.assertTrue((root / "behavior.json").is_file())
            self.assertEqual(ARTIFACTS, {item.name for item in (root / "pack").iterdir()})


if __name__ == "__main__":
    unittest.main()
