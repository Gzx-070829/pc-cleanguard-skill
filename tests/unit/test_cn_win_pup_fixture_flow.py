import json
import unittest
from pathlib import Path

from pc_cleanguard.pup import build_pup_intelligence_report
from pc_cleanguard.reputation import load_evidence_pack


ROOT = Path(__file__).resolve().parents[2]


class CnWinPupFixtureFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / "tests/fixtures/reputation/pr29_cn_win_pup_inventory.json").read_text(encoding="utf-8"))
        cls.records = load_evidence_pack(ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json")
        cls.result = build_pup_intelligence_report(cls.report, [], cn_evidence_pack=cls.records, include_behavior_indicators=True)

    def test_fixture_is_declared_synthetic(self):
        self.assertTrue(self.report["fixture_metadata"]["synthetic_but_realistic"])

    def test_fixture_produces_review_hint(self):
        self.assertGreaterEqual(len(self.result["matches"]), 1)

    def test_matches_include_public_source_trace(self):
        match = self.result["matches"][0]
        self.assertTrue(match["source_url"] and match["source_title"] and match["source_date"])

    def test_matches_remain_non_authorizing(self):
        self.assertTrue(all(item["why_not_execution_authorization"] for item in self.result["matches"]))
        self.assertEqual(0, self.result["execution_gating_eligible_count"])

    def test_explicit_behavior_metadata_enters_checklist(self):
        kinds = {item["behavior_type"] for item in self.result["behavior_indicators"]}
        self.assertIn("browser_search_change", kinds)
        self.assertIn("ad_popup_signal", kinds)


if __name__ == "__main__":
    unittest.main()
