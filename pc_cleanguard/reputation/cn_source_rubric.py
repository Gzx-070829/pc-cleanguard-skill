"""Offline validation for conservative Chinese PUP source-review rubrics."""

from __future__ import annotations

import json
from pathlib import Path

from ..pipeline.input_loader import _validated_explicit_local_path


SOURCE_RELIABILITY = {
    "official", "vendor_public_article", "reputable_media",
    "security_vendor_public_article", "community_multi_report", "weak_source",
}
ENTITY_CLARITY = {
    "exact_windows_desktop_entity", "installer_or_bundle_artifact",
    "publisher_level_only", "name_collision_possible", "mobile_only", "unclear",
}
RISK_CATEGORIES = {
    "forced_install", "difficult_uninstall", "browser_hijack", "adware_popup",
    "bundled_install", "misleading_scan_or_repair", "privacy_overreach",
    "startup_persistence", "scheduled_task_persistence", "unknown",
}
ALLOWED_USES = {
    "explanation_only", "review_hint", "publisher_level_warning",
    "name_collision_warning",
}
FORBIDDEN_USES = {
    "delete_authorization", "uninstall_authorization",
    "disable_authorization", "registry_edit_authorization",
}
RUBRIC_FIELDS = {
    "source_reliability", "entity_clarity", "risk_category",
    "allowed_use", "forbidden_use",
}


def validate_cn_source_rubric(item: dict) -> dict:
    if not isinstance(item, dict) or set(item) != RUBRIC_FIELDS:
        raise ValueError("CN source rubric fields do not match PR27 contract")
    if item["source_reliability"] not in SOURCE_RELIABILITY:
        raise ValueError("invalid source_reliability")
    if item["entity_clarity"] not in ENTITY_CLARITY:
        raise ValueError("invalid entity_clarity")
    if item["risk_category"] not in RISK_CATEGORIES:
        raise ValueError("invalid risk_category")
    if item["allowed_use"] not in ALLOWED_USES:
        raise ValueError("invalid allowed_use")
    if not isinstance(item["forbidden_use"], list) or set(item["forbidden_use"]) != FORBIDDEN_USES:
        raise ValueError("forbidden_use must contain every execution boundary")
    return item


def load_cn_source_rubric(path: str | Path) -> list[dict]:
    source = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("CN source rubric must be an array")
    return [validate_cn_source_rubric(item) for item in data]
