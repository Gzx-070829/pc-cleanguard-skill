import unittest
from pathlib import Path
from pc_cleanguard.pup import inspect_pup_risk

class PupEvidenceGuardTest(unittest.TestCase):
    def test_insight_exposes_guard_axes_and_uncertainty(self):
        root=Path(__file__).resolve().parents[2]
        report={"targets":[{"target_id":"x","object_type":"SOFTWARE","name":"Example Mobile Behavior Analogy"},{"target_id":"y","object_type":"SOFTWARE","name":"Example Common Name"}]}
        result=inspect_pup_risk(report,root/"data/reputation/evidence_pack.zh-CN.json",evidence_pack=True)
        matches=result["matches"]
        self.assertTrue(all(m["execution_authorized"] is False and m["guard_reason"] for m in matches))
        self.assertTrue(any(m["mapping_type"]=="analogical_behavior" for m in matches))
        self.assertTrue(result["insight"]["uncertainty_notes"])
