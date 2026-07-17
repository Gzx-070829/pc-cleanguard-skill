import json, unittest
from pathlib import Path
import pc_cleanguard

ROOT=Path(__file__).resolve().parents[2]
class V032ReleaseReadinessTest(unittest.TestCase):
    def test_current_version_is_041_while_v032_assets_remain(self): self.assertEqual("0.4.1",pc_cleanguard.__version__)
    def test_release_docs_exist(self):
        for name in ("docs/release-v0.3.2-checklist.md","docs/v0.3.2-public-preview.md","docs/v0.3.2-release-notes.md"): self.assertTrue((ROOT/name).is_file(),name)
    def test_showcase_exists(self):
        base=ROOT/"examples/showcase/v0.3.2"
        for name in ("README.md","START_HERE.md","user_summary.md","machine_summary.json","pup_insight.md","corroboration_summary.md","evidence_quality.md","no_match_report.md","matchability_summary.md","safety_notice.md"): self.assertTrue((base/name).is_file(),name)
        json.loads((base/"machine_summary.json").read_text(encoding="utf-8"))

if __name__ == "__main__": unittest.main()
