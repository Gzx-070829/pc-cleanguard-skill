import json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main
from pc_cleanguard.reputation import build_evidence_coverage_summary, render_evidence_coverage_markdown

ROOT = Path(__file__).resolve().parents[2]


class EvidenceCoverageDashboardTest(unittest.TestCase):
    def setUp(self):
        self.records = json.loads((ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json").read_text(encoding="utf-8"))
        self.candidates = json.loads((ROOT / "data/reputation/cn_win_pup_evidence_candidates.zh-CN.json").read_text(encoding="utf-8"))
        self.backlog = json.loads((ROOT / "data/reputation/cn_win_pup_review_backlog.zh-CN.json").read_text(encoding="utf-8"))

    def test_summary_reports_approved_candidates_and_backlog(self):
        result = build_evidence_coverage_summary([self.records], self.candidates, self.backlog)
        self.assertEqual(len(self.records), result["approved_cn_win_total"])
        self.assertEqual(len(self.candidates), result["candidate_total"])
        self.assertEqual(len(self.backlog), result["backlog_total"])

    def test_summary_has_required_missing_targets(self):
        missing = " ".join(build_evidence_coverage_summary([self.records], self.candidates, self.backlog)["top_missing_targets"])
        for name in ("万能五笔", "搜狗输入法", "2345", "驱动工具", "浏览器主页"):
            self.assertIn(name, missing)

    def test_summary_never_authorizes_execution(self):
        result = build_evidence_coverage_summary([self.records], [], [])
        self.assertEqual(0, result["execution_gating_eligible_count"])
        self.assertFalse(result["execution_authorized"])

    def test_markdown_explains_coverage_is_not_blacklist(self):
        text = render_evidence_coverage_markdown(build_evidence_coverage_summary([self.records], [], []))
        self.assertIn("不是黑名单", text)

    def test_cli_evidence_coverage_writes_markdown(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "coverage.md"
            code = main(["reputation", "evidence", "coverage", "--inputs", str(ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json"), "--candidates", str(ROOT / "data/reputation/cn_win_pup_evidence_candidates.zh-CN.json"), "--backlog", str(ROOT / "data/reputation/cn_win_pup_review_backlog.zh-CN.json"), "--output", str(output)])
            self.assertEqual(0, code)
            self.assertTrue(output.is_file())


if __name__ == "__main__": unittest.main()
