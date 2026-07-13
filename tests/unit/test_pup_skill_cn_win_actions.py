import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.skill import READ_ONLY_EXECUTION_LEVEL, invoke_skill_action


ROOT = Path(__file__).resolve().parents[2]


class PupSkillCnWinActionsTest(unittest.TestCase):
    def test_build_evidence_quality_summary_is_level_zero(self):
        response = invoke_skill_action({"action": "build_evidence_quality_summary", "payload": {"inputs": [str(ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json")]}})
        self.assertEqual(READ_ONLY_EXECUTION_LEVEL, response.execution_level)
        self.assertEqual(0, response.result["execution_gating_eligible_count"])

    def test_validate_real_report_shape_is_level_zero(self):
        report = json.loads((ROOT / "tests/fixtures/reputation/pr29_cn_win_pup_inventory.json").read_text(encoding="utf-8"))
        response = invoke_skill_action({"action": "validate_real_report_shape", "payload": {"report": report}})
        self.assertEqual(READ_ONLY_EXECUTION_LEVEL, response.execution_level)
        self.assertFalse(response.execution_authorized)

    def test_build_cn_win_review_pack_is_level_zero(self):
        report = json.loads((ROOT / "tests/fixtures/reputation/pr29_cn_win_pup_inventory.json").read_text(encoding="utf-8"))
        with TemporaryDirectory() as directory:
            response = invoke_skill_action({"action": "build_cn_win_pup_review_pack", "payload": {"report": report, "evidence_pack_path": [], "cn_win_evidence_pack_path": str(ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json"), "output_dir": str(Path(directory) / "pack")}})
            self.assertEqual(READ_ONLY_EXECUTION_LEVEL, response.execution_level)
            self.assertEqual(0, response.result["execution_gating_eligible_count"])

    def test_actions_never_authorize_execution(self):
        report = json.loads((ROOT / "tests/fixtures/reputation/pr29_cn_win_pup_inventory.json").read_text(encoding="utf-8"))
        response = invoke_skill_action({"action": "validate_real_report_shape", "payload": {"report": report}})
        self.assertFalse(response.to_dict()["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
