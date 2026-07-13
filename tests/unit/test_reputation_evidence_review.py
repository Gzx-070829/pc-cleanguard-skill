import copy
import json
import unittest
from pathlib import Path

from pc_cleanguard.reputation import (
    build_evidence_record_from_candidate,
    load_evidence_candidates,
    load_evidence_review_queue,
    validate_review_queue_item,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "data/reputation/evidence_candidates.zh-CN.json"
REVIEWS = ROOT / "data/reputation/evidence_review_queue.zh-CN.json"


class ReputationEvidenceReviewTest(unittest.TestCase):
    def test_checked_in_review_queue_loads_and_schema_lists_decisions(self) -> None:
        reviews = load_evidence_review_queue(REVIEWS)
        self.assertGreaterEqual(len(reviews), 5)
        schema = json.loads(
            (ROOT / "schemas/reputation_evidence_review_queue.schema.json").read_text(
                encoding="utf-8"
            )
        )
        decisions = schema["items"]["properties"]["reviewer_decision"]["enum"]
        self.assertEqual(
            {
                "accept_as_evidence",
                "reject",
                "needs_more_evidence",
                "downgrade_to_synthetic",
                "split_record",
                "merge_duplicate",
            },
            set(decisions),
        )

    def test_accept_builds_non_authorizing_pr24_record(self) -> None:
        candidate = load_evidence_candidates(CANDIDATES)[0]
        review = load_evidence_review_queue(REVIEWS)[0]
        record = build_evidence_record_from_candidate(candidate, review)
        self.assertFalse(record["execution_authorized"])
        self.assertFalse(record["is_synthetic"])
        self.assertEqual(review["accepted_record_id"], record["record_id"])

    def test_invalid_review_status_is_rejected(self) -> None:
        review = copy.deepcopy(load_evidence_review_queue(REVIEWS)[0])
        review["review_status"] = "approved_for_removal"
        with self.assertRaises(ValueError):
            validate_review_queue_item(review)


if __name__ == "__main__":
    unittest.main()
