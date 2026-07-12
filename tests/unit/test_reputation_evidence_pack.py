import json, unittest
from pathlib import Path
from pc_cleanguard.reputation import load_evidence_pack, validate_evidence_record

ROOT=Path(__file__).resolve().parents[2]
PACK=ROOT/"data/reputation/evidence_pack.zh-CN.json"

class EvidencePackTest(unittest.TestCase):
    def test_checked_in_pack_is_non_authorizing_and_axes_are_separate(self):
        records=load_evidence_pack(PACK)
        self.assertTrue(records)
        self.assertTrue(all(r["execution_authorized"] is False and type(r["is_synthetic"]) is bool for r in records))
        self.assertNotIn("synthetic_example", {r["mapping_type"] for r in records})
    def test_loader_rejects_execution_true_and_missing_analogy(self):
        record=load_evidence_pack(PACK)[1].copy(); record["execution_authorized"]=True
        with self.assertRaises(ValueError): validate_evidence_record(record)
        record=load_evidence_pack(PACK)[1].copy(); record.pop("analogy_basis")
        with self.assertRaises(ValueError): validate_evidence_record(record)
    def test_source_index_has_no_stable_batch_total(self):
        data=json.loads((ROOT/"data/reputation/source_index.zh-CN.json").read_text(encoding="utf-8"))
        self.assertNotIn("total_"+"batch_count", data)
        serialized=json.dumps(data,ensure_ascii=False)
        self.assertNotIn("56"+" 批", serialized); self.assertNotIn("57"+" 批", serialized)
