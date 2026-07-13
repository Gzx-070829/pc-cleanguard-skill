import json, unittest
from pathlib import Path

from pc_cleanguard.pup import build_pup_intelligence_report
from pc_cleanguard.reputation import load_evidence_pack
from pc_cleanguard.validation import build_no_match_report, validate_real_report_shape

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/reports"


class Pr31ReportFixturesTest(unittest.TestCase):
    def _load(self, name): return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def test_all_three_fixtures_are_redacted_synthetic_realistic(self):
        for name in ("pr31_no_match_report.json", "pr31_weak_match_report.json", "pr31_strong_review_signal_report.json"):
            report = self._load(name)
            self.assertTrue(report["fixture_metadata"]["synthetic_but_realistic"])
            self.assertNotIn("Alice", json.dumps(report))

    def test_no_match_fixture_produces_value_report(self):
        report = self._load("pr31_no_match_report.json")
        value = build_no_match_report(report, [[]], validate_real_report_shape(report))
        self.assertTrue(value["missing_metadata"])

    def test_weak_fixture_is_capped(self):
        report = self._load("pr31_weak_match_report.json")
        records = load_evidence_pack(ROOT / "data/reputation/evidence_pack.zh-CN.json")
        result = build_pup_intelligence_report(report, records, include_behavior_indicators=True)
        levels = {item["corroboration_level"] for item in result["corroboration"]["details"]}
        self.assertTrue(levels <= {"weak_name_only_signal", "publisher_only_signal", "no_corroboration"})

    def test_strong_fixture_is_review_only(self):
        report = self._load("pr31_strong_review_signal_report.json")
        records = load_evidence_pack(ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json")
        result = build_pup_intelligence_report(report, [], cn_win_evidence_pack=records, include_behavior_indicators=True)
        self.assertGreater(result["strong_review_signal_count"] + result["moderate_review_signal_count"], 0)
        self.assertFalse(result["execution_authorized"])


if __name__ == "__main__": unittest.main()
