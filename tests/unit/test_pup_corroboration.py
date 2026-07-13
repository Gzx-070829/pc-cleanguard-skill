import json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from pc_cleanguard.cli import main
from pc_cleanguard.pup import build_pup_corroboration, score_match_corroboration, render_corroboration_markdown

def match(mapping="direct_entity", target="app:1"):
    return {"target_id":target,"matched_record_id":"ev:1","mapping_type":mapping,"false_positive_risk":"high","execution_authorized":False}

def behavior(target="app:1", kind="ad_popup_signal"):
    return {"target_id":target,"behavior_type":kind,"execution_gating_eligible":False}

class PupCorroborationTest(unittest.TestCase):
    def test_direct_plus_behavior_is_strong_but_non_authorizing(self):
        result=score_match_corroboration(match(),[behavior()]); self.assertEqual("strong_review_signal",result["corroboration_level"]); self.assertFalse(result["execution_authorized"])
    def test_installer_plus_bundle_is_moderate(self):
        self.assertEqual("moderate_review_signal",score_match_corroboration(match("installer_artifact"),[behavior(kind="bundled_installer_trace")])["corroboration_level"])
    def test_related_publisher_is_capped(self):
        self.assertEqual("publisher_only_signal",score_match_corroboration(match("related_publisher"),[behavior()])["corroboration_level"])
    def test_name_collision_is_capped(self):
        self.assertEqual("weak_name_only_signal",score_match_corroboration(match("name_collision_candidate"),[behavior()])["corroboration_level"])
    def test_no_behavior_is_no_corroboration(self):
        result=score_match_corroboration(match(),[]); self.assertEqual("no_corroboration",result["corroboration_level"]); self.assertTrue(result["uncertainty_notes"])
    def test_behavior_only_is_not_verdict(self):
        result=build_pup_corroboration([],[behavior()]); self.assertEqual(1,result["behavior_only_signal_count"]); self.assertFalse(result["execution_authorized"])
    def test_summary_and_markdown_are_generated(self):
        result=build_pup_corroboration([match()],[behavior()]); self.assertEqual(0,result["execution_gating_eligible_count"]); self.assertIn("人工复核",render_corroboration_markdown(result))
    def test_cli_corroborate_writes_markdown(self):
        with TemporaryDirectory() as d:
            root=Path(d); (root/"matches.json").write_text(json.dumps([match()]),encoding="utf-8"); (root/"behavior.json").write_text(json.dumps([behavior()]),encoding="utf-8")
            self.assertEqual(0,main(["pup","corroborate","--matches",str(root/"matches.json"),"--behavior-indicators",str(root/"behavior.json"),"--output",str(root/"out.md")]))
            self.assertTrue((root/"out.md").is_file())

if __name__ == "__main__": unittest.main()
