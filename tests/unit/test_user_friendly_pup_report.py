import json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main
from pc_cleanguard.reporting import build_user_friendly_pup_report, render_user_friendly_pup_report_markdown


class UserFriendlyPupReportTest(unittest.TestCase):
    def setUp(self):
        self.summary = {"strong_review_signal_count": 1, "moderate_review_signal_count": 0, "weak_name_only_signal_count": 0, "no_corroboration_count": 0, "cn_win_match_count": 1, "sources": ["公开安全文章"], "execution_gating_eligible_count": 0}

    def test_builds_plain_language_report(self):
        report = build_user_friendly_pup_report(self.summary)
        for key in ("headline", "signal_strength", "found_signals", "why_not_direct_action", "human_checks", "false_positive_feedback", "metadata_help", "safety_boundaries"):
            self.assertIn(key, report)

    def test_strong_signal_still_does_not_authorize(self):
        report = build_user_friendly_pup_report(self.summary)
        self.assertEqual("强复核", report["signal_strength"])
        self.assertFalse(report["execution_authorized"])

    def test_markdown_avoids_prohibited_claims(self):
        text = render_user_friendly_pup_report_markdown(build_user_friendly_pup_report(self.summary))
        for phrase in ("你必须删除", "建议立即卸载", "系统绝对安全", "一定是流氓", "自动处理", "已确认恶意"):
            self.assertNotIn(phrase, text)

    def test_cli_report_user_friendly_runs(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); pack = root / "pack"; pack.mkdir()
            (pack / "machine_summary.json").write_text(json.dumps(self.summary, ensure_ascii=False), encoding="utf-8")
            output = root / "summary.md"
            self.assertEqual(0, main(["report", "user-friendly", "--review-pack", str(pack), "--output", str(output)]))
            self.assertTrue(output.is_file())


if __name__ == "__main__": unittest.main()
