import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.reputation import (
    build_evidence_record_from_candidate,
    load_evidence_candidates,
    load_evidence_review_queue,
    validate_evidence_candidate,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "data/reputation/evidence_candidates.zh-CN.json"
REVIEWS = ROOT / "data/reputation/evidence_review_queue.zh-CN.json"


class ReputationEvidenceIntakeTest(unittest.TestCase):
    def test_checked_in_candidates_load_and_have_schema_contract(self) -> None:
        records = load_evidence_candidates(CANDIDATES)
        self.assertGreaterEqual(len(records), 5)
        schema = json.loads(
            (ROOT / "schemas/reputation_evidence_candidate.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("array", schema["type"])
        self.assertIn("candidate_source_url", schema["items"]["required"])

    def test_candidate_rejects_analogical_behavior_without_basis(self) -> None:
        candidate = copy.deepcopy(load_evidence_candidates(CANDIDATES)[0])
        candidate["proposed_mapping_type"] = "analogical_behavior"
        candidate["proposed_analogy_basis"] = ""
        with self.assertRaises(ValueError):
            validate_evidence_candidate(candidate)

    def test_build_requires_source_url_and_source_title(self) -> None:
        candidate = copy.deepcopy(load_evidence_candidates(CANDIDATES)[0])
        review = load_evidence_review_queue(REVIEWS)[0]
        for field in ("candidate_source_url", "candidate_source_title"):
            broken = copy.deepcopy(candidate)
            broken[field] = ""
            with self.assertRaises(ValueError):
                build_evidence_record_from_candidate(broken, review)

    def test_only_accept_decision_can_build_record(self) -> None:
        candidate = load_evidence_candidates(CANDIDATES)[0]
        review = copy.deepcopy(load_evidence_review_queue(REVIEWS)[0])
        review["reviewer_decision"] = "needs_more_evidence"
        review["requires_more_evidence"] = True
        with self.assertRaises(ValueError):
            build_evidence_record_from_candidate(candidate, review)

    def test_mobile_scope_cannot_be_direct_entity(self) -> None:
        candidate = copy.deepcopy(load_evidence_candidates(CANDIDATES)[0])
        candidate["proposed_entity_scope"] = "mobile_app"
        candidate["proposed_mapping_type"] = "direct_entity"
        with self.assertRaises(ValueError):
            validate_evidence_candidate(candidate)


if __name__ == "__main__":
    unittest.main()
