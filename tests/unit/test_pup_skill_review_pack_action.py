import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.skill import READ_ONLY_EXECUTION_LEVEL, invoke_skill_action

ROOT = Path(__file__).resolve().parents[2]


class PupSkillReviewPackActionTest(unittest.TestCase):
    def test_build_review_pack_action_is_level_zero(self) -> None:
        report = json.loads((ROOT / "tests/fixtures/reputation/pr26_realistic_windows_inventory.json").read_text(encoding="utf-8"))
        with TemporaryDirectory() as directory:
            response = invoke_skill_action({
                "action": "build_pup_review_pack",
                "payload": {
                    "report": report,
                    "evidence_pack_path": str(ROOT / "data/reputation/evidence_pack.real.zh-CN.json"),
                    "output_dir": str(Path(directory) / "pack"),
                },
            })
            data = response.to_dict()
            self.assertEqual(READ_ONLY_EXECUTION_LEVEL, data["execution_level"])
            self.assertFalse(data["execution_authorized"])
            self.assertEqual(0, data["result"]["execution_gating_eligible_count"])

    def test_inspect_action_supports_real_evidence_indicators(self) -> None:
        report = json.loads((ROOT / "tests/fixtures/reputation/pr26_realistic_windows_inventory.json").read_text(encoding="utf-8"))
        response = invoke_skill_action({
            "action": "inspect_pup_risk",
            "payload": {
                "report": report,
                "seed_path": str(ROOT / "data/reputation/evidence_pack.real.zh-CN.json"),
                "evidence_pack": True,
                "include_indicators": True,
            },
        }).to_dict()
        self.assertGreaterEqual(response["result"]["match_count"], 1)
        self.assertEqual(0, response["result"]["insight"]["summary"]["execution_gating_eligible_count"])


if __name__ == "__main__":
    unittest.main()
