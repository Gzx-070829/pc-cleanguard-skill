import unittest

from pc_cleanguard.reputation.pup_taxonomy import (
    PUPBehaviorCategory,
    pup_behavior_label_zh,
    pup_taxonomy_records,
)


class PupTaxonomyTest(unittest.TestCase):
    def test_enum_values_are_stable_and_complete(self) -> None:
        self.assertEqual(
            (
                "forced_installation",
                "difficult_uninstall",
                "browser_hijacking",
                "ad_popup",
                "malicious_collection",
                "malicious_uninstall",
                "malicious_bundling",
                "other_user_rights_violation",
            ),
            tuple(category.value for category in PUPBehaviorCategory),
        )

    def test_every_category_has_a_chinese_first_label(self) -> None:
        records = pup_taxonomy_records()

        self.assertEqual(8, len(records))
        self.assertEqual(
            "强制安装",
            pup_behavior_label_zh(PUPBehaviorCategory.FORCED_INSTALLATION),
        )
        self.assertTrue(
            all(record["label_zh"] and record["description_zh"] for record in records)
        )
        self.assertEqual(
            set(PUPBehaviorCategory),
            {record["category"] for record in records},
        )

    def test_taxonomy_is_classification_not_execution_authority(self) -> None:
        for record in pup_taxonomy_records():
            self.assertFalse(record["execution_authorized"])
            self.assertTrue(record["requires_human_review"])


if __name__ == "__main__":
    unittest.main()
