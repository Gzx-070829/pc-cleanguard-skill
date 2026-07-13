"""Offline intake and conversion for manually reviewed reputation evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NotRequired, TypedDict

from ..pipeline.input_loader import _validated_explicit_local_path
from .evidence_pack_loader import (
    ENTITY_SCOPES,
    MAPPING_TYPES,
    RELATION_CONFIDENCE,
    REVIEW_STATUS,
    validate_evidence_record,
)
from .pup_taxonomy import PUPBehaviorCategory


SOURCE_TYPES = {
    "public_regulatory_notice",
    "public_vendor_behavior_article",
    "public_news_or_public_report",
    "community_report",
    "synthetic_example",
}
EVIDENCE_SCOPES = {"explanation", "review", "sorting", "risk_hint"}
FALSE_POSITIVE_RISKS = {"low", "medium", "high"}


class EvidenceCandidate(TypedDict):
    candidate_id: str
    candidate_source_url: str
    candidate_source_title: str
    candidate_source_date: str
    candidate_source_name: str
    source_type: str
    claimed_software_name: str
    claimed_publisher: str
    claimed_aliases: list[str]
    raw_claim_summary: str
    proposed_behavior_categories: list[str]
    proposed_mapping_type: str
    proposed_entity_scope: str
    proposed_relation_confidence: str
    proposed_analogy_basis: str | None
    proposed_confidence: float
    proposed_false_positive_risk: str
    proposed_evidence_scope: str
    jurisdiction: str
    language: str
    license_note: str
    submitted_by: str
    review_notes: str
    recommended_human_checks: NotRequired[list[str]]
    created_at: str


CANDIDATE_OPTIONAL = {"recommended_human_checks"}
CANDIDATE_REQUIRED = set(EvidenceCandidate.__required_keys__) - CANDIDATE_OPTIONAL
CANDIDATE_ALLOWED = CANDIDATE_REQUIRED | CANDIDATE_OPTIONAL


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_evidence_candidate(candidate: dict) -> dict:
    """Validate one offline candidate without resolving or downloading its URL."""

    if (
        not isinstance(candidate, dict)
        or not CANDIDATE_REQUIRED.issubset(candidate)
        or set(candidate) - CANDIDATE_ALLOWED
    ):
        raise ValueError("evidence candidate fields do not match PR25 schema")
    required_strings = CANDIDATE_REQUIRED - {
        "claimed_aliases",
        "proposed_behavior_categories",
        "proposed_analogy_basis",
        "proposed_confidence",
    }
    if any(not _nonempty_string(candidate[field]) for field in required_strings):
        raise ValueError("evidence candidate requires non-empty reviewed metadata")
    if not candidate["candidate_source_url"].startswith(("https://", "http://")):
        raise ValueError("real evidence candidate requires an explicit public URL")
    if candidate["source_type"] not in SOURCE_TYPES or candidate["source_type"] == "synthetic_example":
        raise ValueError("real evidence candidate requires a public source type")
    if not isinstance(candidate["claimed_aliases"], list) or any(
        not isinstance(alias, str) for alias in candidate["claimed_aliases"]
    ):
        raise ValueError("claimed_aliases must be a string array")
    if "recommended_human_checks" in candidate and (
        not isinstance(candidate["recommended_human_checks"], list)
        or not candidate["recommended_human_checks"]
        or any(not _nonempty_string(check) for check in candidate["recommended_human_checks"])
    ):
        raise ValueError("recommended_human_checks must be a non-empty string array")
    taxonomy = {item.value for item in PUPBehaviorCategory}
    categories = candidate["proposed_behavior_categories"]
    if not isinstance(categories, list) or not categories or not set(categories).issubset(taxonomy):
        raise ValueError("invalid proposed behavior categories")
    if candidate["proposed_mapping_type"] not in MAPPING_TYPES:
        raise ValueError("invalid proposed mapping type")
    if candidate["proposed_entity_scope"] not in ENTITY_SCOPES:
        raise ValueError("invalid proposed entity scope")
    if candidate["proposed_relation_confidence"] not in RELATION_CONFIDENCE:
        raise ValueError("invalid proposed relation confidence")
    if candidate["proposed_false_positive_risk"] not in FALSE_POSITIVE_RISKS:
        raise ValueError("invalid proposed false-positive risk")
    if candidate["proposed_evidence_scope"] not in EVIDENCE_SCOPES:
        raise ValueError("invalid proposed evidence scope")
    confidence = candidate["proposed_confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValueError("proposed confidence must be between zero and one")
    if candidate["proposed_mapping_type"] == "analogical_behavior" and not _nonempty_string(
        candidate.get("proposed_analogy_basis")
    ):
        raise ValueError("analogical_behavior requires analogy_basis")
    if candidate["proposed_entity_scope"] in {"mobile_app", "mobile_sdk"} and candidate[
        "proposed_mapping_type"
    ] == "direct_entity":
        raise ValueError("mobile evidence cannot be a direct Windows entity")
    return candidate


def load_evidence_candidates(path: str | Path) -> list[dict]:
    candidate_path = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    data = json.loads(candidate_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("evidence candidates must be an array")
    candidates = [validate_evidence_candidate(item) for item in data]
    if len({item["candidate_id"] for item in candidates}) != len(candidates):
        raise ValueError("duplicate candidate_id")
    return candidates


def build_evidence_record_from_candidate(candidate: dict, review_item: dict) -> dict:
    """Build one guarded evidence record from an explicit accepted review."""

    from .evidence_review import validate_review_queue_item

    candidate = validate_evidence_candidate(candidate)
    review_item = validate_review_queue_item(review_item)
    if review_item["candidate_id"] != candidate["candidate_id"]:
        raise ValueError("candidate and review identifiers do not match")
    if review_item["reviewer_decision"] != "accept_as_evidence":
        raise ValueError("only accept_as_evidence can produce a real evidence record")
    if not _nonempty_string(review_item["accepted_record_id"]):
        raise ValueError("accepted review requires accepted_record_id")
    record = {
        "record_id": review_item["accepted_record_id"],
        "software_name": candidate["claimed_software_name"],
        "publisher": candidate["claimed_publisher"],
        "aliases": list(candidate["claimed_aliases"]),
        "source_type": candidate["source_type"],
        "source_name": candidate["candidate_source_name"],
        "source_url": candidate["candidate_source_url"],
        "source_title": candidate["candidate_source_title"],
        "source_date": candidate["candidate_source_date"],
        "evidence_summary": candidate["raw_claim_summary"],
        "behavior_categories": list(candidate["proposed_behavior_categories"]),
        "jurisdiction": candidate["jurisdiction"],
        "language": candidate["language"],
        "review_status": review_item["review_status"],
        "confidence": candidate["proposed_confidence"],
        "false_positive_risk": candidate["proposed_false_positive_risk"],
        "execution_authorized": False,
        "license_note": candidate["license_note"],
        "evidence_scope": candidate["proposed_evidence_scope"],
        "mapping_type": candidate["proposed_mapping_type"],
        "is_synthetic": False,
        "entity_scope": candidate["proposed_entity_scope"],
        "relation_confidence": candidate["proposed_relation_confidence"],
    }
    if "recommended_human_checks" in candidate:
        record["recommended_human_checks"] = list(candidate["recommended_human_checks"])
    analogy_basis = candidate.get("proposed_analogy_basis")
    if _nonempty_string(analogy_basis):
        record["analogy_basis"] = analogy_basis
    return validate_evidence_record(record)


def build_evidence_pack(candidates: list[dict], reviews: list[dict]) -> list[dict]:
    candidate_index = {
        item["candidate_id"]: validate_evidence_candidate(item) for item in candidates
    }
    if len(candidate_index) != len(candidates):
        raise ValueError("duplicate candidate_id")
    records = []
    seen_reviews: set[str] = set()
    for review in reviews:
        from .evidence_review import validate_review_queue_item

        review = validate_review_queue_item(review)
        candidate_id = review["candidate_id"]
        if candidate_id in seen_reviews:
            raise ValueError("duplicate review candidate_id")
        seen_reviews.add(candidate_id)
        if candidate_id not in candidate_index:
            raise ValueError("review references unknown candidate")
        if review["reviewer_decision"] == "accept_as_evidence":
            records.append(
                build_evidence_record_from_candidate(candidate_index[candidate_id], review)
            )
    if len({record["record_id"] for record in records}) != len(records):
        raise ValueError("duplicate accepted record_id")
    return records


def write_evidence_pack(path: str | Path, records: list[dict]) -> Path:
    destination = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    validated = [validate_evidence_record(record) for record in records]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(validated, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return destination
