import json
import unittest
from pathlib import Path

from pc_cleanguard.reputation import (
    PUPBehaviorCategory,
    load_seed_records,
    load_source_manifest,
    validate_seed_record,
)


ROOT = Path(__file__).resolve().parents[2]
SEEDS = ROOT / "examples" / "reputation" / "seed_records.zh-CN.json"
SOURCES = ROOT / "examples" / "reputation" / "source_manifest.zh-CN.json"


class ReputationSeedPackTest(unittest.TestCase):
    def test_seed_pack_contains_at_least_twenty_non_authorizing_records(self) -> None:
        records = load_seed_records(SEEDS)
        self.assertGreaterEqual(len(records), 20)
        taxonomy = {category.value for category in PUPBehaviorCategory}
        for record in records:
            self.assertFalse(record["execution_authorized"])
            self.assertIn(
                record["review_status"],
                {"needs_human_review", "approved_for_explanation"},
            )
            self.assertTrue(set(record["behavior_categories"]).issubset(taxonomy))

    def test_source_manifest_accepts_only_documented_source_types(self) -> None:
        manifest = load_source_manifest(SOURCES)
        self.assertFalse(manifest["execution_authorized"])
        allowed = {
            "public_regulatory_notice",
            "public_vendor_behavior_article",
            "community_report",
            "synthetic_example",
        }
        self.assertTrue({source["source_type"] for source in manifest["sources"]}.issubset(allowed))

    def test_seed_record_cannot_authorize_execution(self) -> None:
        record = json.loads(SEEDS.read_text(encoding="utf-8"))[0]
        record["execution_authorized"] = True
        with self.assertRaises(ValueError):
            validate_seed_record(record)

    def test_seed_loader_does_not_mutate_execution_policy(self) -> None:
        records = load_seed_records(SEEDS)
        self.assertNotIn("action", records[0])
        self.assertNotIn("execution_level", records[0])

    def test_source_policy_document_exists(self) -> None:
        document = ROOT / "docs" / "reputation-source-policy.md"
        self.assertTrue(document.is_file())


if __name__ == "__main__":
    unittest.main()
