import json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from pc_cleanguard.cli import main
from pc_cleanguard.validation import build_no_match_report, render_no_match_report_markdown

class NoMatchReportTest(unittest.TestCase):
    def setUp(self): self.report={"installed_apps":[{"display_name":"Example Unknown"}],"startup_items":[],"services":[],"scheduled_tasks":[]}
    def test_builds_value_summary(self):
        result=build_no_match_report(self.report,[[]],{"unsupported_fields":[],"matchability_score":55}); self.assertEqual(1,result["scanned_target_counts"]["installed_apps"]); self.assertTrue(result["missing_metadata"])
    def test_states_no_match_is_not_clean_verdict(self): self.assertIn("不等于系统干净",render_no_match_report_markdown(build_no_match_report(self.report,[[]],{})))
    def test_avoids_absolute_safe_phrases(self):
        text=render_no_match_report_markdown(build_no_match_report(self.report,[[]],{})); self.assertNotIn("绝对安全",text); self.assertNotIn("无需处理",text)
    def test_suggests_metadata(self):
        result=build_no_match_report(self.report,[[]],{}); self.assertIn("publisher", " ".join(result["how_to_improve_matchability"]))
    def test_never_authorizes_execution(self): self.assertFalse(build_no_match_report(self.report,[[]],{})["execution_authorized"])
    def test_cli_no_match_writes_markdown(self):
        with TemporaryDirectory() as d:
            root=Path(d); (root/"report.json").write_text(json.dumps(self.report),encoding="utf-8")
            self.assertEqual(0,main(["validation","no-match","--input",str(root/"report.json"),"--output",str(root/"no-match.md")]))
            self.assertTrue((root/"no-match.md").is_file())

if __name__ == "__main__": unittest.main()
