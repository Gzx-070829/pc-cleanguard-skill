import unittest
from pathlib import Path
from pc_cleanguard.reputation import load_evidence_pack

ROOT=Path(__file__).resolve().parents[2]; PACK=ROOT/"data/reputation/evidence_pack.cn_win.zh-CN.json"
class CnPupEvidenceExpansionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.records=load_evidence_pack(PACK)
    def test_has_five_to_eight_approved_real_records(self): self.assertGreaterEqual(len(self.records),5); self.assertLessEqual(len(self.records),8)
    def test_sources_and_summaries_are_complete(self):
        self.assertTrue(all(all(str(r[k]).strip() for k in ("source_url","source_title","source_date","evidence_summary","source_quote_summary")) for r in self.records))
    def test_records_are_non_authorizing_real_evidence(self): self.assertTrue(all(r["execution_authorized"] is False and r["is_synthetic"] is False for r in self.records))
    def test_no_user_blocklist_is_approved(self): self.assertFalse(any(r["source_type"]=="user_blocklist_or_forum_list" for r in self.records))
    def test_scoped_fields_are_complete(self): self.assertTrue(all(r["version_or_time_scope"] and r["affected_component"] and r["guard_reason"] for r in self.records))

if __name__ == "__main__": unittest.main()
