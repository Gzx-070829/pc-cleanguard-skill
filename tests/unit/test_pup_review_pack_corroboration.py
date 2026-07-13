import json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from pc_cleanguard.pup import build_pup_review_pack

ROOT=Path(__file__).resolve().parents[2]
class PupReviewPackCorroborationTest(unittest.TestCase):
    def test_outputs_corroboration_and_match_summary(self):
        report=json.loads((ROOT/"tests/fixtures/reputation/pr29_cn_win_pup_inventory.json").read_text(encoding="utf-8"))
        with TemporaryDirectory() as d:
            out=Path(d)/"pack"; result=build_pup_review_pack(report,[],out,cn_win_evidence_pack=ROOT/"data/reputation/evidence_pack.cn_win.zh-CN.json",include_behavior_indicators=True,include_evidence_quality=True,include_corroboration=True)
            for name in ("corroboration_summary.md","corroboration_details.json","cn_win_evidence_quality.md","match_or_no_match_summary.md"): self.assertTrue((out/name).is_file(),name)
            machine=json.loads((out/"machine_summary.json").read_text(encoding="utf-8")); self.assertIn("corroborated_match_count",machine); self.assertTrue(machine["quality_gate_passed"])

if __name__ == "__main__": unittest.main()
