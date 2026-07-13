import json, unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class V040EvidenceDensityTest(unittest.TestCase):
    def test_cn_windows_pack_is_dense_and_non_authorizing(self):
        records = json.loads((ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(records), 10)
        self.assertTrue(all(item["execution_authorized"] is False for item in records))
        for item in records:
            self.assertTrue(item.get("recommended_human_checks"))
            self.assertTrue(item.get("why_not_execution_authorization"))
            if item["mapping_type"] == "installer_artifact": self.assertTrue(item.get("affected_component"))
