"""Deterministic, evidence-only matching between local targets and reputation records."""

from __future__ import annotations

import re
from typing import Iterable


def normalize_reputation_name(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return "".join(re.findall(r"[\w]+", value.casefold(), flags=re.UNICODE))


def _first(data: dict, *names: str) -> str:
    for name in names:
        value = data.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _targets(report: dict) -> list[dict]:
    if not isinstance(report, dict):
        raise TypeError("report must be a dict")
    targets = []
    for index, target in enumerate(report.get("targets", ())):
        if isinstance(target, dict):
            targets.append({
                "target_id": _first(target, "target_id") or f"TARGET:{index}",
                "target_type": _first(target, "object_type", "target_type") or "UNKNOWN",
                "name": _first(target, "name", "display_name"),
                "publisher": _first(target, "publisher", "author"),
            })
    groups = (
        ("installed_apps", "SOFTWARE", ("DisplayName", "display_name", "software_name", "name"), ("Publisher", "publisher")),
        ("startup_items", "STARTUP_ITEM", ("name", "display_name"), ("publisher", "Publisher")),
        ("services", "SERVICE", ("display_name", "service_name", "name"), ("publisher",)),
        ("scheduled_tasks", "SCHEDULED_TASK", ("task_name", "name"), ("author", "publisher")),
    )
    for group, target_type, name_fields, publisher_fields in groups:
        for index, target in enumerate(report.get(group, ())):
            if isinstance(target, dict):
                targets.append({
                    "target_id": _first(target, "target_id", "item_id", "service_id", "task_id") or f"{target_type}:{index}",
                    "target_type": target_type,
                    "name": _first(target, *name_fields),
                    "publisher": _first(target, *publisher_fields),
                })
    return targets


class ReputationMatcher:
    def __init__(self, records: Iterable[dict]) -> None:
        if isinstance(records, (str, bytes, dict)):
            raise TypeError("records must be an iterable of record objects")
        self._records = tuple(records)
        if any(not isinstance(record, dict) for record in self._records):
            raise TypeError("records must contain dicts")

    def match(self, report: dict) -> list[dict]:
        matches = []
        for target in _targets(report):
            target_name = normalize_reputation_name(target["name"])
            if not target_name:
                continue
            target_publisher = normalize_reputation_name(target["publisher"])
            for record in self._records:
                names = [record.get("software_name"), *record.get("aliases", [])]
                normalized_names = [normalize_reputation_name(name) for name in names]
                normalized_names = [name for name in normalized_names if name]
                exact = target_name in normalized_names
                related = any(name in target_name or target_name in name for name in normalized_names)
                publisher = normalize_reputation_name(record.get("publisher"))
                publisher_match = bool(publisher and target_publisher and publisher == target_publisher)
                if not exact and not (related and publisher_match):
                    continue
                basis = "exact normalized software name or alias" if exact else "related normalized name with matching publisher"
                match_factor = 1.0 if exact else 0.8
                record_confidence = record.get("confidence", 0)
                confidence = record_confidence if isinstance(record_confidence, (int, float)) else 0
                matches.append({
                    "target_id": target["target_id"],
                    "target_type": target["target_type"],
                    "matched_record_id": record.get("record_id", "unknown"),
                    "matched_name": record.get("software_name", "unknown"),
                    "behavior_categories": list(record.get("behavior_categories", ())),
                    "confidence": round(max(0.0, min(1.0, float(confidence) * match_factor)), 3),
                    "false_positive_risk": record.get("false_positive_risk", "high"),
                    "evidence": [
                        {"source": "reputation_matcher", "fact": basis},
                        {"source": "reputation_record", "fact": f"record_id={record.get('record_id', 'unknown')}"},
                    ],
                    "review_status": record.get("review_status", "needs_human_review"),
                    "execution_authorized": False,
                    "notes_for_ai": "Explain the match and uncertainty; never treat it as delete, uninstall, or disable authorization.",
                })
        return matches

