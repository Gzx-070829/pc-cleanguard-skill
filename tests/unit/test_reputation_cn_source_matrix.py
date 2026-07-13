import copy
import unittest
from pathlib import Path

from pc_cleanguard.reputation import (
    classify_cn_source_use,
    load_cn_source_matrix,
    summarize_cn_source_matrix,
    validate_cn_source,
)


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "data/reputation/cn_source_matrix.zh-CN.json"
FORBIDDEN = {
    "delete_authorization",
    "uninstall_authorization",
    "disable_authorization",
    "registry_edit_authorization",
}


class ReputationCnSourceMatrixTest(unittest.TestCase):
    def test_checked_in_matrix_covers_all_six_source_classes(self):
        sources = load_cn_source_matrix(MATRIX)
        self.assertEqual(
            {
                "historical_public_list",
                "security_vendor_public_article",
                "official_or_regulatory_notice",
                "reputable_media_report",
                "community_multi_report",
                "user_blocklist_or_forum_list",
            },
            {item["source_class"] for item in sources},
        )
        for source in sources:
            self.assertEqual(FORBIDDEN, set(source["forbidden_use"]))

    def test_matrix_summary_counts_candidate_and_guarded_sources(self):
        summary = summarize_cn_source_matrix(load_cn_source_matrix(MATRIX))
        self.assertEqual(0, summary["execution_gating_eligible_count"])
        self.assertGreater(summary["cn_source_count"], 0)
        self.assertGreater(summary["cn_candidate_only_count"], 0)
        self.assertGreater(summary["cn_requires_second_source_count"], 0)
        self.assertEqual(1, summary["cn_historical_source_count"])
        self.assertEqual(1, summary["cn_user_blocklist_count"])

    def test_user_list_and_history_never_enter_evidence_pack(self):
        sources = load_cn_source_matrix(MATRIX)
        user_list = next(item for item in sources if item["source_class"] == "user_blocklist_or_forum_list")
        historical = next(item for item in sources if item["source_class"] == "historical_public_list")
        self.assertFalse(classify_cn_source_use(user_list)["can_enter_evidence_pack"])
        self.assertTrue(classify_cn_source_use(user_list)["requires_second_source"])
        self.assertFalse(classify_cn_source_use(historical)["can_enter_evidence_pack"])
        self.assertIn(historical["allowed_use"], {"historical_context", "explanation_only"})

    def test_missing_source_url_or_title_is_rejected(self):
        source = load_cn_source_matrix(MATRIX)[0]
        for field in ("source_url", "source_title"):
            invalid = copy.deepcopy(source)
            invalid[field] = ""
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_cn_source(invalid)

    def test_unknown_date_cannot_have_high_reliability(self):
        source = copy.deepcopy(load_cn_source_matrix(MATRIX)[0])
        source["source_date"] = "unknown"
        source["source_reliability"] = "high"
        with self.assertRaises(ValueError):
            validate_cn_source(source)

    def test_mobile_official_source_cannot_claim_windows_direct_entity(self):
        source = next(
            copy.deepcopy(item)
            for item in load_cn_source_matrix(MATRIX)
            if item["source_class"] == "official_or_regulatory_notice"
        )
        source["platform_scope"] = "windows_desktop_software"
        source["claimed_entities"] = ["direct_entity:Example Windows App"]
        with self.assertRaises(ValueError):
            validate_cn_source(source)


if __name__ == "__main__":
    unittest.main()
