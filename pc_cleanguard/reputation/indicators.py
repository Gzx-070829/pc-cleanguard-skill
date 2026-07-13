"""Offline, non-authorizing indicators derived from reviewed evidence."""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import TypedDict

from ..pipeline.input_loader import _validated_explicit_local_path


INDICATOR_TYPES = {
    "detection_family", "installer_family", "bundle_name", "display_name_hint",
    "publisher_hint", "file_name_hint", "startup_name_hint", "service_name_hint",
    "scheduled_task_hint", "browser_extension_hint", "behavior_hint",
}
MATCH_SCOPES = {
    "installed_app", "startup_item", "service", "scheduled_task",
    "browser_extension", "file_observation", "publisher_level", "report_level",
}
MATCH_STRENGTHS = {"exact", "strong", "medium", "weak", "informational"}
FALSE_POSITIVE_RISKS = {"low", "medium", "high"}


class EvidenceIndicator(TypedDict):
    indicator_id: str
    record_id: str
    indicator_type: str
    indicator_value: str
    normalized_value: str
    source_field: str
    match_scope: str
    match_strength: str
    false_positive_risk: str
    requires_human_review: bool
    notes: str
    execution_gating_eligible: bool


REQUIRED = set(EvidenceIndicator.__required_keys__)


def normalize_indicator_value(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return "".join(re.findall(r"[\w]+", value.casefold(), flags=re.UNICODE))


def validate_indicator(indicator: dict) -> dict:
    if not isinstance(indicator, dict) or set(indicator) != REQUIRED:
        raise ValueError("indicator fields do not match PR26 schema")
    for field in ("indicator_id", "record_id", "indicator_value", "normalized_value", "source_field", "notes"):
        if not isinstance(indicator[field], str) or not indicator[field].strip():
            raise ValueError(f"indicator {field} must be non-empty")
    if indicator["indicator_type"] not in INDICATOR_TYPES:
        raise ValueError("invalid indicator_type")
    if indicator["match_scope"] not in MATCH_SCOPES:
        raise ValueError("invalid match_scope")
    if indicator["match_strength"] not in MATCH_STRENGTHS:
        raise ValueError("invalid match_strength")
    if indicator["false_positive_risk"] not in FALSE_POSITIVE_RISKS:
        raise ValueError("invalid false_positive_risk")
    if indicator["requires_human_review"] is not True:
        raise ValueError("all indicators require human review")
    if indicator["execution_gating_eligible"] is not False:
        raise ValueError("indicators cannot enter execution gating")
    return indicator


def _indicator(record: dict, kind: str, value: str, field: str, scope: str, strength: str, note: str, index: int) -> dict:
    normalized = normalize_indicator_value(value)
    if not normalized:
        raise ValueError("indicator value must normalize to non-empty text")
    return validate_indicator({
        "indicator_id": f"{record.get('record_id', 'unknown')}:{kind}:{index}",
        "record_id": str(record.get("record_id", "unknown")),
        "indicator_type": kind,
        "indicator_value": value,
        "normalized_value": normalized,
        "source_field": field,
        "match_scope": scope,
        "match_strength": strength,
        "false_positive_risk": record.get("false_positive_risk", "high"),
        "requires_human_review": True,
        "notes": note,
        "execution_gating_eligible": False,
    })


def build_indicators_from_evidence(record: dict) -> list[dict]:
    if not isinstance(record, dict) or not str(record.get("record_id", "")).strip():
        raise ValueError("evidence record requires record_id")
    name = str(record.get("software_name", "")).strip()
    if not name:
        raise ValueError("evidence record requires software_name")
    result = [
        _indicator(
            record, "detection_family", name, "software_name", "report_level",
            "informational",
            "Detection-family text is source context; it is not an installed-app identity verdict.", 0,
        )
    ]
    family = name.rsplit("/", 1)[-1].strip() if "/" in name else ""
    if family and normalize_indicator_value(family) != normalize_indicator_value(name):
        result.append(
            _indicator(
                record, "installer_family", family, "software_name", "installed_app",
                "medium",
                "Family-name overlap is a high-false-positive review hint and requires local identity checks.", 1,
            )
        )
    for alias_index, alias in enumerate(record.get("aliases", ()), start=2):
        if isinstance(alias, str) and alias.strip():
            result.append(
                _indicator(
                    record, "display_name_hint", alias.strip(), "aliases", "installed_app",
                    "weak", "Alias overlap cannot establish entity identity.", alias_index,
                )
            )
    publisher = str(record.get("publisher", "")).strip()
    if publisher and not publisher.casefold().startswith("unknown"):
        result.append(
            _indicator(
                record, "publisher_hint", publisher, "publisher", "publisher_level",
                "weak", "Publisher evidence is auxiliary and cannot form a match by itself.", len(result),
            )
        )
    for category in record.get("behavior_categories", ()):
        if isinstance(category, str) and category.strip():
            result.append(
                _indicator(
                    record, "behavior_hint", category, "behavior_categories", "report_level",
                    "informational", "Behavior context is explanation-only and never identifies software.", len(result),
                )
            )
    return result


def summarize_indicators(indicators: list[dict]) -> dict:
    validated = [validate_indicator(item) for item in indicators]
    return {
        "indicator_count": len(validated),
        "by_type": {kind: sum(item["indicator_type"] == kind for item in validated) for kind in sorted(INDICATOR_TYPES)},
        "by_strength": {strength: sum(item["match_strength"] == strength for item in validated) for strength in sorted(MATCH_STRENGTHS)},
        "human_review_required_count": sum(item["requires_human_review"] is True for item in validated),
        "execution_gating_eligible_count": 0,
    }


def write_indicators(path: str | Path, indicators: list[dict], *, overwrite: bool = False) -> Path:
    if not isinstance(overwrite, bool):
        raise TypeError("overwrite must be bool")
    destination = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    validated = [validate_indicator(item) for item in indicators]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
        json.dump(validated, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return destination
