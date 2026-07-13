import copy
import json
import unittest
from pathlib import Path

from pc_cleanguard.reputation import (
    load_cn_candidate_sources,
    validate_cn_candidate_source,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "data/reputation/cn_candidate_sources.zh-CN.json"


class ReputationCnCandidateSourcesTest(unittest.TestCase):
    def test_checked_in_candidates_are_review_only_and_traceable(self):
        candidates = load_cn_candidate_sources(CANDIDATES)
        self.assertGreaterEqual(len(candidates), 4)
        for candidate in candidates:
            self.assertIn(candidate["candidate_status"], {"candidate_only", "needs_human_review"})
            self.assertTrue(candidate["source_url"].startswith("https://"))
            self.assertTrue(candidate["source_title"].strip())
            self.assertTrue(candidate["evidence_summary"].strip())
            self.assertFalse(candidate["execution_authorized"])

    def test_candidate_cannot_claim_approved_or_execution_authorized(self):
        candidate = load_cn_candidate_sources(CANDIDATES)[0]
        invalid = copy.deepcopy(candidate)
        invalid["candidate_status"] = "approved_for_explanation"
        with self.assertRaises(ValueError):
            validate_cn_candidate_source(invalid)
        invalid = copy.deepcopy(candidate)
        invalid["execution_authorized"] = True
        with self.assertRaises(ValueError):
            validate_cn_candidate_source(invalid)

    def test_extra_candidate_and_review_backlog_are_not_approved(self):
        extra = json.loads((ROOT / "data/reputation/cn_evidence_candidates.extra.zh-CN.json").read_text(encoding="utf-8"))
        backlog = json.loads((ROOT / "data/reputation/cn_review_backlog.zh-CN.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(extra), 1)
        self.assertGreaterEqual(len(backlog), 1)
        self.assertTrue(all(item["review_status"] == "needs_human_review" for item in backlog))
        self.assertTrue(all(item["reviewer_decision"] == "needs_more_evidence" for item in backlog))


if __name__ == "__main__":
    unittest.main()
