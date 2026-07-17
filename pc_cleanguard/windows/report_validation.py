"""Validate and summarize the canonical Windows report contract."""

from __future__ import annotations

from .collector_manifest import COLLECTOR_NAMES, COLLECTOR_STATUSES


_REQUIRED = (
    "schema_version", "scan_id", "timestamp", "platform", "privacy_mode",
    "collector_status", "installed_apps", "startup_items", "services",
    "scheduled_tasks", "collection_errors", "unsupported_collectors",
    "redaction_summary", "source_kind",
)


def validate_windows_canonical_report(report: dict) -> list[str]:
    if not isinstance(report, dict):
        return ["report must be a JSON object"]
    errors = [f"missing required field: {field}" for field in _REQUIRED if field not in report]
    if report.get("schema_version") != "0.4.1":
        errors.append("schema_version must be 0.4.1")
    if report.get("platform") != "Windows":
        errors.append("platform must be Windows")
    if report.get("privacy_mode") != "offline":
        errors.append("privacy_mode must be offline")
    if report.get("source_kind") not in {"windows_collector_raw", "windows_collector_redacted"}:
        errors.append("source_kind is invalid")
    for name in COLLECTOR_NAMES:
        values = report.get(name)
        if not isinstance(values, list):
            errors.append(f"{name} must be an array")
        elif any(not isinstance(item, dict) or not str(item.get("target_id", "")).strip() for item in values):
            errors.append(f"{name} entries require target_id")
    statuses = report.get("collector_status")
    if not isinstance(statuses, dict):
        errors.append("collector_status must be an object")
    else:
        for name in COLLECTOR_NAMES:
            item = statuses.get(name)
            if not isinstance(item, dict) or item.get("status") not in COLLECTOR_STATUSES:
                errors.append(f"collector_status.{name} is invalid")
    if report.get("execution_authorized") is not False:
        errors.append("execution_authorized must be false")
    if report.get("runtime_network_access") is not False:
        errors.append("runtime_network_access must be false")
    return errors


def windows_report_stats(report: dict) -> dict:
    errors = validate_windows_canonical_report(report)
    statuses = report.get("collector_status", {}) if isinstance(report, dict) else {}
    groups = [report.get(name, ()) for name in COLLECTOR_NAMES] if isinstance(report, dict) else []
    entries = [item for group in groups for item in group if isinstance(item, dict)]
    metadata_fields = {"name", "display_name", "publisher", "path", "install_location", "path_name", "command", "task_name"}
    behavior_fields = {"actions_summary", "triggers_summary", "behavior_metadata"}
    group_score = sum(bool(group) for group in groups) / len(COLLECTOR_NAMES) if groups else 0
    metadata_score = min(1.0, sum(any(item.get(field) not in (None, "", []) for field in metadata_fields) for item in entries) / max(1, len(entries)))
    behavior_score = min(1.0, sum(any(item.get(field) not in (None, "", []) for field in behavior_fields) for item in entries) / max(1, len(entries)))
    matchability_score = round(100 * (0.5 * group_score + 0.35 * metadata_score + 0.15 * behavior_score), 1)
    return {
        "software_count": len(report.get("installed_apps", ())) if isinstance(report, dict) else 0,
        "startup_count": len(report.get("startup_items", ())) if isinstance(report, dict) else 0,
        "service_count": len(report.get("services", ())) if isinstance(report, dict) else 0,
        "scheduled_task_count": len(report.get("scheduled_tasks", ())) if isinstance(report, dict) else 0,
        "collector_success_count": sum(item.get("status") == "success" for item in statuses.values() if isinstance(item, dict)),
        "collector_failure_count": sum(item.get("status") in {"failed", "unsupported"} for item in statuses.values() if isinstance(item, dict)),
        "unsupported_field_count": len(report.get("unsupported_fields", ())) if isinstance(report, dict) else 0,
        "redacted_value_count": report.get("redaction_summary", {}).get("redacted_value_count", 0) if isinstance(report, dict) else 0,
        "matchability_score": matchability_score,
        "persistence_input_ready": not errors and all(isinstance(report.get(name), list) for name in COLLECTOR_NAMES),
        "canonical": not errors,
        "validation_errors": errors,
        "execution_gating_eligible_count": 0,
        "execution_authorized": False,
        "runtime_network_access": False,
    }
