import json
import unittest
from pathlib import Path

from pc_cleanguard.reputation import (
    build_indicators_from_evidence,
    load_evidence_pack,
    normalize_indicator_value,
    summarize_indicators,
    validate_indicator,
)

ROOT = Path(__file__).resolve().parents[2]


class ReputationIndicatorsTest(unittest.TestCase):
    def test_real_evidence_builds_guarded_indicators(self) -> None:
        records = load_evidence_pack(ROOT / "data/reputation/evidence_pack.real.zh-CN.json")
        indicators = [item for record in records for item in build_indicators_from_evidence(record)]
        self.assertTrue(indicators)
        self.assertTrue(all(validate_indicator(item) is item for item in indicators))
        detection = [item for item in indicators if item["indicator_type"] == "detection_family"]
        self.assertEqual(len(records), len(detection))
        self.assertTrue(all(item["match_scope"] == "report_level" for item in detection))
        self.assertTrue(all(item["match_strength"] == "informational" for item in detection))
        self.assertTrue(all(item["requires_human_review"] for item in indicators))

    def test_normalization_and_summary_are_deterministic(self) -> None:
        self.assertEqual("puawin32installcore", normalize_indicator_value("PUA:Win32/InstallCore"))
        record = load_evidence_pack(ROOT / "data/reputation/evidence_pack.real.zh-CN.json")[0]
        summary = summarize_indicators(build_indicators_from_evidence(record))
        self.assertGreaterEqual(summary["indicator_count"], 3)
        self.assertEqual(0, summary["execution_gating_eligible_count"])

    def test_indicator_schema_is_non_authorizing(self) -> None:
        schema = json.loads((ROOT / "schemas/reputation_evidence_indicator.schema.json").read_text(encoding="utf-8"))
        required = set(schema["required"])
        self.assertIn("requires_human_review", required)
        self.assertFalse(schema["properties"]["execution_gating_eligible"]["const"])


if __name__ == "__main__":
    unittest.main()
