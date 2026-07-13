"""Derive review-only behavior indicators from caller-supplied report metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from ..pipeline.input_loader import _validated_explicit_local_path


BEHAVIOR_TYPES = {
    "startup_persistence", "scheduled_task_persistence", "service_persistence",
    "browser_homepage_change", "browser_search_change", "browser_extension_presence",
    "bundled_installer_trace", "misleading_scan_claim", "difficult_uninstall_signal",
    "ad_popup_signal", "publisher_mismatch", "unsigned_or_unknown_publisher",
    "suspicious_install_location",
}
TARGET_TYPES = {
    "installed_app", "startup_item", "service", "scheduled_task",
    "browser_extension", "file_observation", "unknown",
}
FALSE_POSITIVE_RISKS = {"low", "medium", "high"}


class BehaviorIndicator(TypedDict):
    indicator_id: str
    target_id: str
    target_type: str
    behavior_type: str
    observed_value: str
    evidence_source: str
    confidence: float
    false_positive_risk: str
    requires_human_review: bool
    notes: str
    execution_gating_eligible: bool


REQUIRED = set(BehaviorIndicator.__required_keys__)


def validate_behavior_indicator(indicator: dict) -> dict:
    if not isinstance(indicator, dict) or set(indicator) != REQUIRED:
        raise ValueError("behavior indicator fields do not match PR27 schema")
    for field in ("indicator_id", "target_id", "observed_value", "evidence_source", "notes"):
        if not isinstance(indicator[field], str) or not indicator[field].strip():
            raise ValueError(f"behavior indicator {field} must be non-empty")
    if indicator["target_type"] not in TARGET_TYPES:
        raise ValueError("invalid behavior indicator target_type")
    if indicator["behavior_type"] not in BEHAVIOR_TYPES:
        raise ValueError("invalid behavior_type")
    confidence = indicator["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValueError("behavior indicator confidence must be between zero and one")
    if indicator["false_positive_risk"] not in FALSE_POSITIVE_RISKS:
        raise ValueError("invalid false_positive_risk")
    if indicator["requires_human_review"] is not True:
        raise ValueError("behavior indicators always require human review")
    if indicator["execution_gating_eligible"] is not False:
        raise ValueError("behavior indicators cannot enter execution gating")
    return indicator


def _first(item: dict, *fields: str) -> str:
    for field in fields:
        value = item.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _make(target_id: str, target_type: str, behavior_type: str, observed: str, source: str, confidence: float, note: str, index: int) -> dict:
    return validate_behavior_indicator({
        "indicator_id": f"behavior:{target_id}:{behavior_type}:{index}",
        "target_id": target_id,
        "target_type": target_type,
        "behavior_type": behavior_type,
        "observed_value": observed,
        "evidence_source": source,
        "confidence": confidence,
        "false_positive_risk": "high",
        "requires_human_review": True,
        "notes": note,
        "execution_gating_eligible": False,
    })


def build_behavior_indicators_from_report(report: dict) -> list[dict]:
    """Inspect report fields only; never read the registry, browser, filesystem, or network."""

    if not isinstance(report, dict):
        raise TypeError("report must be a dict")
    result: list[dict] = []

    def add_group(group: str, target_type: str, behavior_type: str, name_fields: tuple[str, ...], note: str) -> None:
        for index, item in enumerate(report.get(group, ())):
            if not isinstance(item, dict):
                continue
            target_id = _first(item, "target_id", "item_id", "service_id", "task_id") or f"{target_type}:{index}"
            observed = _first(item, *name_fields) or target_id
            result.append(_make(target_id, target_type, behavior_type, observed, f"report.{group}", 0.35, note, len(result)))

    add_group("startup_items", "startup_item", "startup_persistence", ("name", "display_name", "command"), "Startup metadata is a persistence review hint, not proof of unwanted behavior.")
    add_group("services", "service", "service_persistence", ("display_name", "service_name", "name", "path_name"), "Service presence requires identity and user-intent review.")
    add_group("scheduled_tasks", "scheduled_task", "scheduled_task_persistence", ("task_name", "name", "actions_summary"), "Scheduled-task metadata is review-only and does not justify disabling the task.")

    bundle_words = ("bundle", "bundler", "installer", "offer", "捆绑", "推广")
    suspicious_locations = ("\\appdata\\", "/appdata/", "\\temp\\", "/temp/", "\\tmp\\", "/tmp/")
    for index, item in enumerate(report.get("installed_apps", ())):
        if not isinstance(item, dict):
            continue
        target_id = _first(item, "target_id", "item_id") or f"installed_app:{index}"
        name = _first(item, "DisplayName", "display_name", "software_name", "name") or target_id
        normalized_name = name.casefold()
        if any(word in normalized_name for word in bundle_words):
            result.append(_make(target_id, "installed_app", "bundled_installer_trace", name, "report.installed_apps.display_name", 0.45, "Name text suggests an installer/bundle trace only; verify the actual package and source.", len(result)))
        publisher = _first(item, "Publisher", "publisher")
        if not publisher or publisher.casefold().startswith("unknown"):
            result.append(_make(target_id, "installed_app", "unsigned_or_unknown_publisher", publisher or "publisher metadata absent", "report.installed_apps.publisher", 0.25, "Missing publisher metadata is common and cannot establish a PUP verdict.", len(result)))
        location = _first(item, "InstallLocation", "install_location", "path")
        if location and any(part in location.casefold() for part in suspicious_locations):
            result.append(_make(target_id, "installed_app", "suspicious_install_location", location, "report.installed_apps.install_location", 0.3, "A user-writable location is only a context signal and requires identity review.", len(result)))
        explicit = item.get("behavior_metadata", ())
        if isinstance(explicit, list):
            for behavior in explicit:
                if behavior in BEHAVIOR_TYPES:
                    result.append(_make(
                        target_id, "installed_app", behavior, str(behavior),
                        "report.installed_apps.behavior_metadata", 0.4,
                        "Caller-supplied behavior metadata is review-only and must be independently verified.",
                        len(result),
                    ))
    return result


def summarize_behavior_indicators(indicators: list[dict]) -> dict:
    validated = [validate_behavior_indicator(item) for item in indicators]
    return {
        "behavior_indicator_count": len(validated),
        "by_behavior_type": {
            kind: sum(item["behavior_type"] == kind for item in validated)
            for kind in sorted(BEHAVIOR_TYPES)
        },
        "high_false_positive_risk_count": sum(item["false_positive_risk"] == "high" for item in validated),
        "human_review_required_count": len(validated),
        "execution_gating_eligible_count": 0,
    }


def render_behavior_indicator_section(indicators: list[dict]) -> str:
    validated = [validate_behavior_indicator(item) for item in indicators]
    lines = [
        "# Behavior Indicators / 行为线索", "",
        "这些线索仅来自输入 report 的元数据，只用于人工复核；不读取真实浏览器或注册表，不形成 PUP 定罪，也不授权系统操作。", "",
    ]
    for item in validated:
        lines.extend([
            f"## {item['target_id']}", "",
            f"- behavior_type: `{item['behavior_type']}`",
            f"- observed_value: {item['observed_value']}",
            f"- confidence: {item['confidence']}",
            f"- false_positive_risk: `{item['false_positive_risk']}`",
            f"- 人工复核说明: {item['notes']}", "",
        ])
    if not validated:
        lines.extend(["输入报告中没有可表达的行为线索；这不构成安全证明。", ""])
    return "\n".join(lines).rstrip() + "\n"


def write_behavior_indicators(path: str | Path, indicators: list[dict], *, overwrite: bool = False) -> Path:
    if not isinstance(overwrite, bool):
        raise TypeError("overwrite must be bool")
    destination = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    validated = [validate_behavior_indicator(item) for item in indicators]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
        json.dump(validated, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return destination
