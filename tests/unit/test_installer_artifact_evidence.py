import unittest
from pathlib import Path

from pc_cleanguard.reputation import load_evidence_pack, validate_evidence_record


ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json"


class InstallerArtifactEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.record = next(item for item in load_evidence_pack(PACK) if item["mapping_type"] == "installer_artifact")

    def test_artifact_requires_named_artifact(self):
        invalid = dict(self.record, installer_or_bundle_artifact="")
        with self.assertRaises(ValueError):
            validate_evidence_record(invalid)

    def test_artifact_requires_time_scope(self):
        invalid = dict(self.record, version_or_time_scope="")
        with self.assertRaises(ValueError):
            validate_evidence_record(invalid)

    def test_artifact_requires_affected_component(self):
        invalid = dict(self.record, affected_component="")
        with self.assertRaises(ValueError):
            validate_evidence_record(invalid)

    def test_artifact_guard_rejects_whole_product_conviction(self):
        invalid = dict(self.record, evidence_summary="该软件本体永久属于流氓软件，必须处理")
        with self.assertRaises(ValueError):
            validate_evidence_record(invalid)


if __name__ == "__main__":
    unittest.main()
