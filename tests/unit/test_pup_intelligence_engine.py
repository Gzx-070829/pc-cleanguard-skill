import json
import unittest
from pathlib import Path

from pc_cleanguard.pup import build_pup_intelligence_report

ROOT = Path(__file__).resolve().parents[2]


class PupIntelligenceEngineTest(unittest.TestCase):
    def test_engine_builds_non_authorizing_source_traceable_report(self) -> None:
        report = json.loads((ROOT / "tests/fixtures/reputation/pr26_realistic_windows_inventory.json").read_text(encoding="utf-8"))
        result = build_pup_intelligence_report(report, ROOT / "data/reputation/evidence_pack.real.zh-CN.json")
        self.assertGreaterEqual(result["indicator_match_count"], 1)
        self.assertGreaterEqual(result["real_source_match_count"], 1)
        self.assertEqual(0, result["execution_gating_eligible_count"])
        self.assertEqual(
            {"no_delete_authorization", "no_uninstall_authorization", "no_disable_authorization", "no_registry_edit_authorization"},
            set(result["blocked_actions"]),
        )
        match = result["matches"][0]
        self.assertTrue(match["source_url"] and match["source_title"] and match["source_date"])
        self.assertTrue(match["why_not_execution_authorization"])


if __name__ == "__main__":
    unittest.main()
