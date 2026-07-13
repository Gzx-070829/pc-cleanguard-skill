import tempfile, unittest
from pathlib import Path

from pc_cleanguard.validation.trial_flow import build_real_report_trial


class TrialPersistenceTest(unittest.TestCase):
    def test_trial_report_can_include_persistence_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_real_report_trial({"report_id": "r", "installed_apps": [{"display_name": "Example"}]}, Path(tmp) / "trial", [], include_persistence_chain=True)
            self.assertEqual(0, result["execution_gating_eligible_count"])
            self.assertTrue((Path(result["output_dir"]) / "pup_review_pack" / "persistence_chain.json").is_file())
