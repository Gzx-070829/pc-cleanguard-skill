import json
import unittest
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.pup import build_pup_review_pack
from pc_cleanguard.cli import main


ROOT = Path(__file__).resolve().parents[2]


class PupReviewPackCnWinTest(unittest.TestCase):
    def _build(self, output):
        report = json.loads((ROOT / "tests/fixtures/reputation/pr29_cn_win_pup_inventory.json").read_text(encoding="utf-8"))
        return build_pup_review_pack(report, [], output,
            cn_win_evidence_pack=ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json",
            include_behavior_indicators=True, include_evidence_quality=True,
            include_real_report_validation_summary=True)

    def test_pack_writes_cn_win_summary(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "pack"; self._build(output)
            self.assertTrue((output / "cn_win_evidence_summary.md").is_file())

    def test_pack_writes_quality_dashboard(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "pack"; self._build(output)
            self.assertTrue((output / "evidence_quality.md").is_file())

    def test_pack_writes_matchability_summary(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "pack"; self._build(output)
            self.assertTrue((output / "matchability_summary.md").is_file())

    def test_machine_summary_has_cn_win_metrics(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "pack"; summary = self._build(output)
            machine = json.loads((output / "machine_summary.json").read_text(encoding="utf-8"))
            fields = {"cn_win_real_source_count", "cn_win_direct_entity_count", "cn_win_installer_artifact_count", "cn_win_match_count", "evidence_quality_score", "matchability_score", "high_false_positive_risk_count", "execution_gating_eligible_count"}
            self.assertTrue(fields.issubset(machine)); self.assertEqual(0, summary["execution_gating_eligible_count"])

    def test_review_pack_cli_accepts_cn_win_pack(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "pack"
            command = ["pup", "review-pack", "--input", str(ROOT / "tests/fixtures/reputation/pr29_cn_win_pup_inventory.json"), "--evidence-pack", str(ROOT / "data/reputation/evidence_pack.real.zh-CN.json"), "--cn-win-evidence-pack", str(ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json"), "--output", str(output), "--include-behavior-indicators", "--include-evidence-quality", "--include-real-report-validation-summary"]
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(0, main(command))
            self.assertTrue((output / "cn_win_evidence_summary.md").is_file())


if __name__ == "__main__":
    unittest.main()
