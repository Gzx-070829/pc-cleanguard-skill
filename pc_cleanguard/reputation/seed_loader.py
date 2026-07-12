"""Load curated local Reputation Seed Packs without network or execution access."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from .pup_taxonomy import PUPBehaviorCategory
from .source_pack import ALLOWED_SEED_REVIEW_STATUSES, ALLOWED_SEED_SOURCE_TYPES
from .source_validation import _valid_public_url, validate_source_manifest


_RECORD_FIELDS = {
    "record_id", "software_name", "publisher", "aliases", "behavior_categories",
    "source_type", "source_name", "source_url", "source_date", "evidence_summary",
    "confidence", "jurisdiction", "language", "false_positive_risk", "review_status",
    "license_note", "created_at", "updated_at", "execution_authorized",
}


def validate_seed_record(record: dict) -> dict:
    if not isinstance(record, dict) or set(record) != _RECORD_FIELDS:
        raise ValueError("seed record fields do not match reputation_record schema")
    if record["execution_authorized"] is not False:
        raise ValueError("reputation evidence cannot authorize execution")
    if record["review_status"] not in ALLOWED_SEED_REVIEW_STATUSES:
        raise ValueError("seed review_status is not explanation-safe")
    if record["source_type"] not in ALLOWED_SEED_SOURCE_TYPES:
        raise ValueError("unsupported seed source type")
    taxonomy = {category.value for category in PUPBehaviorCategory}
    categories = record["behavior_categories"]
    if not isinstance(categories, list) or not categories or not set(categories).issubset(taxonomy):
        raise ValueError("seed behavior_categories must use the PR18 taxonomy")
    if len(categories) != len(set(categories)):
        raise ValueError("seed behavior_categories must be unique")
    if not _valid_public_url(record["source_url"]):
        raise ValueError("seed source_url must be an explicit HTTP(S) URL")
    for field in (
        "record_id", "software_name", "publisher", "source_name", "source_date",
        "evidence_summary", "jurisdiction", "language", "license_note", "created_at", "updated_at",
    ):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"{field} must be non-empty")
    if record["false_positive_risk"] not in {"low", "medium", "high"}:
        raise ValueError("invalid false_positive_risk")
    confidence = record["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValueError("confidence must be between zero and one")
    if not isinstance(record["aliases"], list) or any(not isinstance(alias, str) for alias in record["aliases"]):
        raise ValueError("aliases must be strings")
    try:
        date.fromisoformat(record["source_date"])
        datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("seed dates must use ISO date/date-time formats") from error
    return record


def _load_json(path: str | Path):
    candidate = Path(path)
    if candidate.suffix.casefold() != ".json" or not candidate.is_file():
        raise ValueError("an explicit existing .json path is required")
    return json.loads(candidate.read_text(encoding="utf-8"))


def load_seed_records(path: str | Path) -> list[dict]:
    records = _load_json(path)
    if not isinstance(records, list) or not records:
        raise ValueError("seed pack must be a non-empty array")
    validated = [validate_seed_record(record) for record in records]
    ids = [record["record_id"] for record in validated]
    if len(ids) != len(set(ids)):
        raise ValueError("seed record IDs must be unique")
    return validated


def load_source_manifest(path: str | Path) -> dict:
    return validate_source_manifest(_load_json(path))
