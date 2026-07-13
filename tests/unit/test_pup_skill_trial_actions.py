import unittest
from pathlib import Path
from pc_cleanguard.skill import invoke_skill_action, READ_ONLY_EXECUTION_LEVEL

ROOT=Path(__file__).resolve().parents[2]
class PupSkillTrialActionsTest(unittest.TestCase):
    def test_corroboration_action_is_level_zero(self):
        r=invoke_skill_action({"action":"build_pup_corroboration","payload":{"matches":[],"behavior_indicators":[]}}); self.assertEqual(READ_ONLY_EXECUTION_LEVEL,r.execution_level); self.assertEqual(0,r.result["execution_gating_eligible_count"])
    def test_no_match_action_is_level_zero(self):
        r=invoke_skill_action({"action":"build_no_match_report","payload":{"report":{},"evidence_packs":[],"matchability_summary":{}}}); self.assertEqual(READ_ONLY_EXECUTION_LEVEL,r.execution_level); self.assertFalse(r.execution_authorized)
    def test_real_trial_action_exists(self): self.assertIn("build_real_report_trial",__import__("pc_cleanguard.skill",fromlist=["ACTION_NAMES"]).ACTION_NAMES)

if __name__ == "__main__": unittest.main()
