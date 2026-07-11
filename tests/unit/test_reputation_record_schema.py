import json
import unittest
from pathlib import Path

from pc_cleanguard.reputation import PUPBehaviorCategory


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples"


class ReputationRecordSchemaTest(unittest.TestCase):
    def _json(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_reputation_record_schema_has_required_contract(self) -> None:
        schema = self._json(SCHEMAS / "reputation_record.schema.json")
        expected = {
            "record_id",
            "software_name",
            "publisher",
            "aliases",
            "behavior_categories",
            "source_type",
            "source_name",
            "source_url",
            "source_date",
            "evidence_summary",
            "confidence",
            "jurisdiction",
            "language",
            "false_positive_risk",
            "review_status",
            "license_note",
            "created_at",
            "updated_at",
            "execution_authorized",
        }
        self.assertEqual(expected, set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["properties"]["execution_authorized"]["const"])

    def test_schema_uses_stable_taxonomy_and_review_status(self) -> None:
        schema = self._json(SCHEMAS / "reputation_record.schema.json")
        self.assertEqual(
            {category.value for category in PUPBehaviorCategory},
            set(schema["properties"]["behavior_categories"]["items"]["enum"]),
        )
        self.assertEqual(
            {
                "draft",
                "needs_human_review",
                "approved_for_explanation",
                "deprecated",
                "rejected",
            },
            set(schema["properties"]["review_status"]["enum"]),
        )

    def test_reputation_examples_are_synthetic_non_authorizing_records(self) -> None:
        schema = self._json(SCHEMAS / "reputation_record.schema.json")
        records = self._json(
            EXAMPLES / "reputation" / "pr18_reputation_records.json"
        )
        required = set(schema["required"])
        for record in records:
            with self.subTest(record_id=record["record_id"]):
                self.assertEqual(required, set(record))
                self.assertIn("synthetic", record["software_name"].casefold())
                self.assertIn("example.invalid", record["source_url"])
                self.assertFalse(record["execution_authorized"])
                self.assertTrue(record["behavior_categories"])

    def test_developer_guard_schema_and_examples_match_runtime_contract(self) -> None:
        schema = self._json(SCHEMAS / "developer_guard_decision.schema.json")
        decisions = self._json(
            EXAMPLES / "protection" / "pr18_developer_guard_examples.json"
        )
        required = set(schema["required"])
        self.assertFalse(schema["properties"]["execution_authorized"]["const"])
        for decision in decisions:
            with self.subTest(path=decision["path"]):
                self.assertEqual(required, set(decision))
                self.assertFalse(decision["execution_authorized"])
                self.assertTrue(decision["evidence"])


if __name__ == "__main__":
    unittest.main()
