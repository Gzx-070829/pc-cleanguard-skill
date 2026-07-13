import json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.pup import build_pup_review_pack

ROOT = Path(__file__).resolve().parents[2]


class ReviewPackProductizationTest(unittest.TestCase):
    def test_review_pack_outputs_product_assets(self):
        report = json.loads((ROOT / "tests/fixtures/reports/pr31_strong_review_signal_report.json").read_text(encoding="utf-8"))
        with TemporaryDirectory() as directory:
            out = Path(directory) / "pack"
            result = build_pup_review_pack(report, [], out, cn_win_evidence_pack=ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json", cn_candidate_sources=ROOT / "data/reputation/cn_win_pup_evidence_candidates.zh-CN.json", review_backlog=ROOT / "data/reputation/cn_win_pup_review_backlog.zh-CN.json", include_behavior_indicators=True, include_corroboration=True, include_coverage=True, include_user_friendly_report=True, include_false_positive_template=True)
            for name in ("user_friendly_summary.md", "evidence_coverage.md", "false_positive_feedback_template.json", "false_positive_feedback_template.md", "data_gap_summary.md"):
                self.assertTrue((out / name).is_file(), name)
            machine = json.loads((out / "machine_summary.json").read_text(encoding="utf-8"))
            for key in ("approved_cn_win_total", "candidate_cn_win_total", "backlog_cn_win_total", "coverage_score", "data_gap_count", "top_missing_targets", "user_friendly_report_available", "false_positive_feedback_available"):
                self.assertIn(key, machine)
            self.assertEqual(0, result["execution_gating_eligible_count"])


if __name__ == "__main__": unittest.main()
