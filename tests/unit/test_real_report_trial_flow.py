import json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from pc_cleanguard.validation import build_real_report_trial
from pc_cleanguard.cli import main

ROOT=Path(__file__).resolve().parents[2]; REPORT=ROOT/"tests/fixtures/reputation/pr29_cn_win_pup_inventory.json"
class RealReportTrialFlowTest(unittest.TestCase):
    def test_trial_writes_complete_directory(self):
        with TemporaryDirectory() as d:
            out=Path(d)/"trial"; result=build_real_report_trial(json.loads(REPORT.read_text(encoding="utf-8")),out,ROOT/"data/reputation/evidence_pack.real.zh-CN.json",cn_win_evidence_pack=ROOT/"data/reputation/evidence_pack.cn_win.zh-CN.json",include_behavior_indicators=True,include_evidence_quality=True)
            for name in ("START_HERE.md","report_shape_summary.json","pii_redaction_checklist.md","matchability_summary.md","pup_review_pack","evidence_quality.md","next_steps.md","safety_notice.md"): self.assertTrue((out/name).exists(),name)
            self.assertEqual(0,result["execution_gating_eligible_count"])
    def test_trial_default_does_not_overwrite(self):
        with TemporaryDirectory() as d:
            out=Path(d)/"trial"; report=json.loads(REPORT.read_text(encoding="utf-8")); build_real_report_trial(report,out,[])
            with self.assertRaises(FileExistsError): build_real_report_trial(report,out,[])
    def test_trial_is_offline(self):
        with TemporaryDirectory() as d: self.assertFalse(build_real_report_trial({},Path(d)/"trial",[])["runtime_network_access"])
    def test_cli_trial_report_runs(self):
        with TemporaryDirectory() as d:
            out=Path(d)/"trial"
            self.assertEqual(0,main(["trial","report","--input",str(REPORT),"--output",str(out),"--evidence-pack",str(ROOT/"data/reputation/evidence_pack.real.zh-CN.json"),"--cn-win-evidence-pack",str(ROOT/"data/reputation/evidence_pack.cn_win.zh-CN.json"),"--include-behavior-indicators","--include-evidence-quality"]))
            self.assertTrue((out/"START_HERE.md").is_file())

if __name__ == "__main__": unittest.main()
