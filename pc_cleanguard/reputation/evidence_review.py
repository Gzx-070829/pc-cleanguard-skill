"""Offline validation for human evidence-review decisions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from ..pipeline.input_loader import _validated_explicit_local_path
from .evidence_pack_loader import REVIEW_STATUS


REVIEWER_DECISIONS = {
    "accept_as_evidence",
    "reject",
    "needs_more_evidence",
    "downgrade_to_synthetic",
    "split_record",
    "merge_duplicate",
}
MISCLASSIFICATION_RISKS = {"low", "medium", "high"}


class ReviewQueueItem(TypedDict):
    candidate_id: str
    review_status: str
    reviewer_decision: str
    reviewer_notes: str
    accepted_record_id: str | None
    rejection_reason: str | None
    requires_more_evidence: bool
    risk_of_misclassification: str


REVIEW_REQUIRED = set(ReviewQueueItem.__required_keys__)


def validate_review_queue_item(item: dict) -> dict:
    if (
        not isinstance(item, dict)
        or not REVIEW_REQUIRED.issubset(item)
        or set(item) - REVIEW_REQUIRED
    ):
        raise ValueError("review queue fields do not match PR25 schema")
    if not isinstance(item["candidate_id"], str) or not item["candidate_id"].strip():
        raise ValueError("review requires candidate_id")
    if item["review_status"] not in REVIEW_STATUS:
        raise ValueError("invalid evidence review status")
    if item["reviewer_decision"] not in REVIEWER_DECISIONS:
        raise ValueError("invalid reviewer decision")
    if not isinstance(item["reviewer_notes"], str) or not item["reviewer_notes"].strip():
        raise ValueError("reviewer_notes must explain the decision")
    if item["accepted_record_id"] is not None and not isinstance(item["accepted_record_id"], str):
        raise ValueError("accepted_record_id must be a string or null")
    if item["rejection_reason"] is not None and not isinstance(item["rejection_reason"], str):
        raise ValueError("rejection_reason must be a string or null")
    if type(item["requires_more_evidence"]) is not bool:
        raise ValueError("requires_more_evidence must be bool")
    if item["risk_of_misclassification"] not in MISCLASSIFICATION_RISKS:
        raise ValueError("invalid risk_of_misclassification")
    if item["reviewer_decision"] == "accept_as_evidence" and (
        not isinstance(item["accepted_record_id"], str)
        or not item["accepted_record_id"].strip()
    ):
        raise ValueError("accepted evidence requires accepted_record_id")
    return item


def load_evidence_review_queue(path: str | Path) -> list[dict]:
    review_path = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    data = json.loads(review_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("evidence review queue must be an array")
    reviews = [validate_review_queue_item(item) for item in data]
    if len({item["candidate_id"] for item in reviews}) != len(reviews):
        raise ValueError("duplicate review candidate_id")
    return reviews
