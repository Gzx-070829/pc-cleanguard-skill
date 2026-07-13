import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


class V04RoadmapDocsTest(unittest.TestCase):
    def test_v04_docs_exist(self):
        self.assertTrue((ROOT/"docs/v0.4-roadmap.md").is_file()); self.assertTrue((ROOT/"docs/v0.4-execution-boundary.md").is_file())

    def test_roadmap_covers_product_priorities(self):
        text=(ROOT/"docs/v0.4-roadmap.md").read_text(encoding="utf-8")
        for term in ("中文 Windows evidence","浏览器主页","启动项","官方卸载器","L2","Registry backup","Agent","GUI","误报","不进入自动杀软"):
            self.assertIn(term,text)

    def test_boundary_keeps_evidence_non_authorizing(self):
        text=(ROOT/"docs/v0.4-execution-boundary.md").read_text(encoding="utf-8")
        self.assertIn("不能单独触发执行",text); self.assertIn("可逆",text); self.assertIn("用户确认",text)


if __name__ == "__main__": unittest.main()
