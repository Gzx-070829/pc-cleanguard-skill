import copy
import unittest
from pathlib import Path

from pc_cleanguard.reputation import (
    build_cn_source_guard_reason,
    classify_cn_source_use,
    load_cn_source_matrix,
    validate_cn_source,
)


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "data/reputation/cn_source_matrix.zh-CN.json"


class ReputationCnSourcePolicyTest(unittest.TestCase):
    def test_community_requires_second_source_and_stays_out_of_pack(self):
        source = next(
            item for item in load_cn_source_matrix(MATRIX)
            if item["source_class"] == "community_multi_report"
        )
        decision = classify_cn_source_use(source)
        self.assertTrue(decision["requires_second_source"])
        self.assertFalse(decision["can_enter_evidence_pack"])
        self.assertTrue(decision["can_enter_review_queue"])
        self.assertTrue(decision["can_enter_candidate_only"])

    def test_security_vendor_article_rejects_proprietary_detection_fields(self):
        source = next(
            copy.deepcopy(item)
            for item in load_cn_source_matrix(MATRIX)
            if item["source_class"] == "security_vendor_public_article"
        )
        for field in ("proprietary_rule", "signature", "detection_logic", "sample_library"):
            invalid = copy.deepcopy(source)
            invalid[field] = "must-not-be-copied"
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_cn_source(invalid)

    def test_guard_reason_explains_non_authorizing_boundaries(self):
        source = next(
            item for item in load_cn_source_matrix(MATRIX)
            if item["source_class"] == "user_blocklist_or_forum_list"
        )
        reasons = build_cn_source_guard_reason(source)
        self.assertTrue(any("candidate" in reason for reason in reasons))
        self.assertTrue(any("执行授权" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
