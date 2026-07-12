import unittest
from pathlib import Path
from pc_cleanguard.reputation import *

class EvidencePolicyTest(unittest.TestCase):
    def test_all_evidence_is_blocked_from_execution(self):
        records=load_evidence_pack(Path(__file__).resolve().parents[2]/"data/reputation/evidence_pack.zh-CN.json")
        self.assertTrue(all(not is_execution_gating_eligible(r) for r in records))
        uses={r["mapping_type"]:classify_evidence_use(r).value for r in records}
        self.assertEqual("publisher_level_warning",uses["related_publisher"])
        self.assertEqual("name_collision_warning",uses["name_collision_candidate"])
        self.assertEqual("review_hint",uses["direct_entity"])
