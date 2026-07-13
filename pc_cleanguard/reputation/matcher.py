"""Deterministic, evidence-only matching between local targets and reputation records."""

from __future__ import annotations

import re
from typing import Iterable

from .indicators import build_indicators_from_evidence


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
    def __init__(self, records: Iterable[dict], *, include_indicators: bool = False) -> None:
        if isinstance(records, (str, bytes, dict)):
            raise TypeError("records must be an iterable of record objects")
        self._records = tuple(records)
        if any(not isinstance(record, dict) for record in self._records):
            raise TypeError("records must contain dicts")
        if not isinstance(include_indicators, bool):
            raise TypeError("include_indicators must be bool")
        self._include_indicators = include_indicators
        self._indicators = {
            record.get("record_id"): build_indicators_from_evidence(record)
            for record in self._records
        } if include_indicators else {}

    @staticmethod
    def _scope_for_target(target_type: str) -> str:
        return {
            "SOFTWARE": "installed_app",
            "STARTUP_ITEM": "startup_item",
            "SERVICE": "service",
            "SCHEDULED_TASK": "scheduled_task",
        }.get(target_type, "report_level")

    def _indicator_match(self, record: dict, target: dict, target_name: str) -> dict | None:
        target_scope = self._scope_for_target(target["target_type"])
        for indicator in self._indicators.get(record.get("record_id"), ()):
            if indicator["indicator_type"] in {"publisher_hint", "behavior_hint", "detection_family"}:
                continue
            if indicator["match_scope"] not in {target_scope, "report_level"}:
                continue
            value = indicator["normalized_value"]
            if len(value) >= 4 and (value in target_name or target_name in value):
                return indicator
        return None

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
                software_name = normalize_reputation_name(record.get("software_name"))
                alias_names = [normalize_reputation_name(name) for name in record.get("aliases", ())]
                related = any(name in target_name or target_name in name for name in normalized_names)
                publisher = normalize_reputation_name(record.get("publisher"))
                publisher_match = bool(publisher and target_publisher and publisher == target_publisher)
                indicator = self._indicator_match(record, target, target_name) if self._include_indicators else None
                if not exact and not (related and publisher_match) and indicator is None:
                    continue
                if exact:
                    raw_name = target["name"].strip().casefold()
                    if raw_name == str(record.get("software_name", "")).strip().casefold():
                        match_basis, basis, match_strength = "direct_name", "exact evidence software_name", "exact"
                    elif target_name in alias_names:
                        match_basis, basis, match_strength = "alias", "exact normalized evidence alias", "strong"
                    else:
                        match_basis, basis, match_strength = "normalized_name", "normalized evidence name", "strong"
                    match_factor = 1.0
                elif related and publisher_match:
                    match_basis, basis, match_strength = "publisher_assisted", "related name plus matching publisher", "medium"
                    match_factor = 0.6
                else:
                    match_basis = "evidence_indicator"
                    match_strength = indicator["match_strength"]
                    basis = f"{indicator['indicator_type']} overlap requires human review"
                    match_factor = {"exact": 0.8, "strong": 0.65, "medium": 0.45, "weak": 0.25, "informational": 0.1}[match_strength]
                record_confidence = record.get("confidence", 0)
                confidence = record_confidence if isinstance(record_confidence, (int, float)) else 0
                if record.get("mapping_type") == "name_collision_candidate":
                    confidence = min(float(confidence), 0.3)
                from .evidence_policy import build_evidence_guard_reason, classify_evidence_use
                guard_reason = build_evidence_guard_reason(record)
                if indicator is not None:
                    guard_reason = [*guard_reason, indicator["notes"], "indicator matching cannot authorize execution"]
                checklist = [
                    "核对软件是否由用户主动安装以及安装来源。",
                    "核对本地发布者、版本、签名与来源页面描述是否属于同一实体。",
                    "检查是否存在捆绑、浏览器修改、异常启动项或安全工具独立提示。",
                ]
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
                    "mapping_type": record.get("mapping_type", "direct_entity"),
                    "entity_scope": record.get("entity_scope", "windows_desktop_software"),
                    "is_synthetic": record.get("is_synthetic", True),
                    "relation_confidence": record.get("relation_confidence", "unknown"),
                    "analogy_basis": record.get("analogy_basis"),
                    "source_url": record.get("source_url"),
                    "source_title": record.get("source_title", record.get("source_name")),
                    "source_date": record.get("source_date"),
                    "guard_reason": guard_reason,
                    "evidence_use": classify_evidence_use(record).value,
                    "match_basis": match_basis,
                    "matched_indicator_type": indicator["indicator_type"] if indicator else None,
                    "matched_indicator_value": indicator["indicator_value"] if indicator else None,
                    "target_observed_value": target["name"],
                    "match_scope": indicator["match_scope"] if indicator else self._scope_for_target(target["target_type"]),
                    "match_strength": match_strength,
                    "why_matched": basis,
                    "why_not_execution_authorization": "Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。",
                    "human_review_checklist": checklist,
                    "source_trace": {
                        "record_id": record.get("record_id"),
                        "source_title": record.get("source_title", record.get("source_name")),
                        "source_url": record.get("source_url"),
                        "source_date": record.get("source_date"),
                    },
                    "execution_gating_eligible": False,
                })
        return matches

