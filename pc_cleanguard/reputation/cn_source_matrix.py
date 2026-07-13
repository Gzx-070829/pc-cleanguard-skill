"""Offline loaders and validators for the Chinese public-source matrix."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..pipeline.input_loader import _validated_explicit_local_path


SOURCE_CLASSES = {
    "historical_public_list",
    "security_vendor_public_article",
    "official_or_regulatory_notice",
    "reputable_media_report",
    "community_multi_report",
    "user_blocklist_or_forum_list",
}
ALLOWED_USES = {
    "candidate_only",
    "explanation_only",
    "review_hint",
    "historical_context",
    "publisher_level_warning",
}
FORBIDDEN_USES = {
    "delete_authorization",
    "uninstall_authorization",
    "disable_authorization",
    "registry_edit_authorization",
}
PLATFORM_SCOPES = {
    "windows_desktop_software",
    "windows_installer_or_bundle",
    "mobile_app",
    "mobile_sdk",
    "cross_platform_behavior",
    "online_domain_blocklist",
    "publisher_level",
    "unknown",
}
SOURCE_FIELDS = {
    "source_id",
    "source_class",
    "source_name",
    "source_url",
    "source_title",
    "source_date",
    "source_access_status",
    "claimed_entities",
    "claimed_behaviors",
    "platform_scope",
    "source_reliability",
    "machine_readable",
    "license_note",
    "review_notes",
    "allowed_use",
    "forbidden_use",
    "version_or_time_scope",
    "evidence_freshness",
    "cross_source_count",
    "requires_second_source",
}
CANDIDATE_FIELDS = SOURCE_FIELDS | {
    "candidate_id",
    "candidate_entity",
    "candidate_status",
    "mapping_type",
    "evidence_summary",
    "execution_authorized",
}

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MOBILE_TITLE = re.compile(r"\b(?:app|sdk)\b", re.IGNORECASE)
_PROPRIETARY_TERMS = ("proprietary_rule", "signature", "detection_logic", "sample_library")


def _non_empty_string(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def validate_cn_source(source: dict) -> dict:
    """Validate one source record without fetching or trusting its URL."""

    if not isinstance(source, dict) or set(source) != SOURCE_FIELDS:
        unexpected = set(source) - SOURCE_FIELDS if isinstance(source, dict) else set()
        if unexpected & set(_PROPRIETARY_TERMS):
            raise ValueError("security-vendor source cannot carry proprietary detection fields")
        raise ValueError("CN source fields do not match the v0.3.1 contract")
    for field in (
        "source_id", "source_name", "source_url", "source_title",
        "source_access_status", "license_note", "review_notes",
        "version_or_time_scope", "evidence_freshness",
    ):
        _non_empty_string(source[field], field)
    if not source["source_url"].startswith(("https://", "http://")):
        raise ValueError("source_url must be an explicit public HTTP(S) URL")
    if source["source_class"] not in SOURCE_CLASSES:
        raise ValueError("invalid source_class")
    if source["allowed_use"] not in ALLOWED_USES:
        raise ValueError("invalid allowed_use")
    if not isinstance(source["forbidden_use"], list) or set(source["forbidden_use"]) != FORBIDDEN_USES:
        raise ValueError("forbidden_use must contain every execution boundary")
    if source["platform_scope"] not in PLATFORM_SCOPES:
        raise ValueError("invalid platform_scope")
    if source["source_reliability"] not in {"high", "medium", "low", "unknown"}:
        raise ValueError("invalid source_reliability")
    if source["source_access_status"] not in {"accessible", "archived", "access_limited", "unknown"}:
        raise ValueError("invalid source_access_status")
    if source["evidence_freshness"] not in {"current", "time_scoped", "historical", "unknown"}:
        raise ValueError("invalid evidence_freshness")
    if not isinstance(source["machine_readable"], bool):
        raise TypeError("machine_readable must be bool")
    if not isinstance(source["requires_second_source"], bool):
        raise TypeError("requires_second_source must be bool")
    if not isinstance(source["cross_source_count"], int) or isinstance(source["cross_source_count"], bool) or source["cross_source_count"] < 0:
        raise ValueError("cross_source_count must be a non-negative integer")
    for field in ("claimed_entities", "claimed_behaviors"):
        if not isinstance(source[field], list) or any(not isinstance(item, str) or not item.strip() for item in source[field]):
            raise ValueError(f"{field} must be a list of non-empty strings")
    if source["source_date"] != "unknown" and not _DATE.fullmatch(str(source["source_date"])):
        raise ValueError("source_date must be YYYY-MM-DD or unknown")
    if source["source_date"] == "unknown" and source["source_reliability"] == "high":
        raise ValueError("unknown source_date cannot have high reliability")
    if source["source_class"] in {"user_blocklist_or_forum_list", "community_multi_report"} and not source["requires_second_source"]:
        raise ValueError("community and user lists require a second source")
    if source["source_class"] == "historical_public_list":
        if source["evidence_freshness"] != "historical":
            raise ValueError("historical_public_list must remain historical")
        if source["allowed_use"] not in {"historical_context", "explanation_only"}:
            raise ValueError("historical_public_list cannot be used beyond context/explanation")
    if source["source_class"] == "user_blocklist_or_forum_list" and source["allowed_use"] != "candidate_only":
        raise ValueError("user blocklists are candidate-only")
    if source["source_class"] == "community_multi_report" and source["allowed_use"] != "candidate_only":
        raise ValueError("community reports are candidate-only")
    if (
        source["source_class"] == "official_or_regulatory_notice"
        and _MOBILE_TITLE.search(source["source_title"])
        and source["platform_scope"] not in {"mobile_app", "mobile_sdk"}
    ):
        raise ValueError("APP/SDK regulatory notices must keep mobile platform scope")
    if source["platform_scope"] in {"mobile_app", "mobile_sdk"} and any(
        item.lower().startswith("direct_entity:") for item in source["claimed_entities"]
    ):
        raise ValueError("mobile sources cannot create a Windows direct_entity mapping")
    return source


def load_cn_source_matrix(path: str | Path) -> list[dict]:
    source = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("CN source matrix must be an array")
    records = [validate_cn_source(item) for item in data]
    ids = [item["source_id"] for item in records]
    if len(ids) != len(set(ids)):
        raise ValueError("CN source_id values must be unique")
    return records


def validate_cn_candidate_source(candidate: dict) -> dict:
    if not isinstance(candidate, dict) or set(candidate) != CANDIDATE_FIELDS:
        raise ValueError("CN candidate-source fields do not match the v0.3.1 contract")
    validate_cn_source({field: candidate[field] for field in SOURCE_FIELDS})
    for field in ("candidate_id", "candidate_entity", "evidence_summary"):
        _non_empty_string(candidate[field], field)
    if candidate["candidate_status"] not in {"candidate_only", "needs_human_review"}:
        raise ValueError("candidate sources cannot be approved directly")
    if candidate["mapping_type"] not in {
        "source_level_only", "analogical_behavior", "related_publisher",
        "name_collision_candidate", "direct_entity_candidate",
    }:
        raise ValueError("invalid candidate mapping_type")
    if candidate["execution_authorized"] is not False:
        raise ValueError("candidate source can never authorize execution")
    if candidate["platform_scope"] in {"mobile_app", "mobile_sdk"} and candidate["mapping_type"] != "analogical_behavior":
        raise ValueError("mobile candidates must remain analogical_behavior")
    return candidate


def load_cn_candidate_sources(path: str | Path) -> list[dict]:
    source = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("CN candidate sources must be an array")
    records = [validate_cn_candidate_source(item) for item in data]
    ids = [item["candidate_id"] for item in records]
    if len(ids) != len(set(ids)):
        raise ValueError("CN candidate_id values must be unique")
    return records
