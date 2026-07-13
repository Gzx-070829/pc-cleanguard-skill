import unittest

from pc_cleanguard.reputation.matcher import ReputationMatcher, normalize_reputation_name


class CnAliasNormalizationTest(unittest.TestCase):
    def test_full_width_ascii_normalizes(self):
        self.assertEqual(normalize_reputation_name("ＤＸ 强力修复"), normalize_reputation_name("DX强力修复"))

    def test_chinese_punctuation_normalizes(self):
        self.assertEqual(normalize_reputation_name("示例·搜索（助手）"), normalize_reputation_name("示例搜索助手"))

    def test_alias_does_not_expand_to_unrelated_substring(self):
        record = {"record_id": "r", "software_name": "示例搜索助手", "publisher": "示例厂商", "aliases": ["搜索助手"],
                  "behavior_categories": ["ad_popup"], "confidence": .8, "false_positive_risk": "high",
                  "review_status": "needs_human_review", "mapping_type": "direct_entity", "entity_scope": "windows_desktop_software",
                  "is_synthetic": True, "relation_confidence": "medium", "source_url": "synthetic://r", "source_title": "synthetic", "source_date": "2026-01-01"}
        report = {"installed_apps": [{"display_name": "搜索工具", "publisher": "其他厂商"}]}
        self.assertEqual([], ReputationMatcher([record]).match(report))

    def test_name_collision_is_downgraded(self):
        record = {"record_id": "r", "software_name": "通用助手", "publisher": "未知", "aliases": [],
                  "behavior_categories": ["ad_popup"], "confidence": .9, "false_positive_risk": "high",
                  "review_status": "needs_human_review", "mapping_type": "name_collision_candidate", "entity_scope": "unknown",
                  "is_synthetic": True, "relation_confidence": "low", "source_url": "synthetic://r", "source_title": "synthetic", "source_date": "2026-01-01"}
        match = ReputationMatcher([record]).match({"installed_apps": [{"display_name": "通用助手"}]})[0]
        self.assertLessEqual(match["confidence"], .3)
        self.assertTrue(match["uncertainty_notes"])

    def test_related_publisher_never_maps_to_concrete_software(self):
        record = {"record_id": "r", "software_name": "示例软件", "publisher": "示例发布者", "aliases": [],
                  "behavior_categories": ["malicious_bundling"], "confidence": .8, "false_positive_risk": "high",
                  "review_status": "needs_human_review", "mapping_type": "related_publisher", "entity_scope": "publisher_level",
                  "is_synthetic": True, "relation_confidence": "medium", "source_url": "synthetic://r", "source_title": "synthetic", "source_date": "2026-01-01"}
        report = {"installed_apps": [{"display_name": "示例软件", "publisher": "示例发布者"}]}
        self.assertEqual([], ReputationMatcher([record]).match(report))


if __name__ == "__main__":
    unittest.main()
