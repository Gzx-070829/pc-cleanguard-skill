import unittest
from pathlib import Path
from pc_cleanguard.reputation import build_evidence_quality_summary, load_evidence_pack

ROOT=Path(__file__).resolve().parents[2]
class EvidenceQualityGateTest(unittest.TestCase):
    def setUp(self): self.records=load_evidence_pack(ROOT/"data/reputation/evidence_pack.cn_win.zh-CN.json")
    def test_checked_in_pack_passes_quality_gate(self): self.assertTrue(build_evidence_quality_summary([self.records])["quality_gate_passed"])
    def test_execution_true_fails_gate(self):
        records=[dict(self.records[0],execution_authorized=True)]; self.assertFalse(build_evidence_quality_summary([records])["quality_gate_passed"])
    def test_positive_gating_fails_gate(self):
        records=[dict(self.records[0],execution_gating_eligible=True)]; self.assertFalse(build_evidence_quality_summary([records])["quality_gate_passed"])
    def test_missing_source_fails_gate(self): self.assertFalse(build_evidence_quality_summary([[dict(self.records[0],source_url="")]])["quality_gate_passed"])
    def test_new_cn_metrics_exist(self):
        result=build_evidence_quality_summary([self.records],cn_candidates=[{}]*3,review_backlog=[{}]*2); self.assertEqual(3,result["cn_win_candidate_count"]); self.assertEqual(2,result["cn_win_review_backlog_count"])

if __name__ == "__main__": unittest.main()
