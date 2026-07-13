import unittest
from pathlib import Path

from pc_cleanguard.reputation import load_evidence_pack


ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json"


class CnWinPupEvidencePackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_evidence_pack(PACK)

    def test_pack_contains_small_real_reviewed_set(self):
        self.assertGreaterEqual(len(self.records), 2)
        self.assertTrue(all(item["is_synthetic"] is False for item in self.records))

    def test_pack_never_authorizes_execution(self):
        self.assertTrue(all(item["execution_authorized"] is False for item in self.records))

    def test_public_source_trace_is_complete(self):
        for item in self.records:
            for field in ("source_url", "source_title", "source_date", "evidence_summary"):
                self.assertTrue(str(item[field]).strip(), (item["record_id"], field))

    def test_cn_windows_precision_fields_are_present(self):
        fields = {"version_or_time_scope", "affected_component", "distribution_channel",
                  "observed_behaviors", "source_quote_summary", "reviewer_notes", "guard_reason"}
        self.assertTrue(all(fields.issubset(item) for item in self.records))


if __name__ == "__main__":
    unittest.main()
