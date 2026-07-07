"""Pure, offline orchestration for explicit scan JSON data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Tuple
from uuid import uuid4

from ..audit import AuditEvent
from ..core.models import (
    ClassificationLabel,
    GovernanceTarget,
    PolicyDecision,
)
from ..core.policy_engine import evaluate_target
from ..core.report_builder import build_report
from ..windows import (
    InstalledApp,
    ScheduledTask,
    StartupItem,
    WindowsService,
    installed_app_to_governance_target,
    installed_app_to_scan_target_record,
    normalize_registry_apps,
    normalize_scheduled_tasks,
    normalize_services,
    normalize_startup_items,
    scheduled_task_to_governance_target,
    scheduled_task_to_scan_target_record,
    service_to_governance_target,
    service_to_scan_target_record,
    startup_item_to_governance_target,
    startup_item_to_scan_target_record,
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class ScanPipelineInput:
    """Validated in-memory input for the four supported metadata families."""

    installed_apps: Tuple[dict, ...]
    startup_items: Tuple[dict, ...]
    services: Tuple[dict, ...]
    scheduled_tasks: Tuple[dict, ...]
    platform: str = "Windows"
    privacy_mode: str = "offline"


@dataclass(frozen=True, slots=True)
class ScanPipelineResult:
    """Structured recommendations and dry-run artifacts; never execution state."""

    scan_id: str
    created_at: str
    input_summary: dict
    normalized_counts: dict
    targets: Tuple[GovernanceTarget, ...]
    decisions: Tuple[PolicyDecision, ...]
    report: dict
    audit_events: Tuple[AuditEvent, ...]
    scan_target_records: Tuple[dict, ...]
    warnings: Tuple[str, ...]

    def to_dict(self) -> dict:
        """Return a JSON-safe representation without introducing commands."""

        return {
            "scan_id": self.scan_id,
            "created_at": self.created_at,
            "input_summary": dict(self.input_summary),
            "normalized_counts": dict(self.normalized_counts),
            "targets": [_target_to_dict(target) for target in self.targets],
            "decisions": [_decision_to_dict(decision) for decision in self.decisions],
            "report": self.report,
            "audit_events": [event.to_dict() for event in self.audit_events],
            "scan_target_records": [dict(record) for record in self.scan_target_records],
            "warnings": list(self.warnings),
        }


def _input_list(data: dict, key: str, *aliases: str) -> list[dict]:
    value: Any = None
    for candidate in (key, *aliases):
        if candidate in data:
            value = data[candidate]
            break
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{key} must contain JSON objects only")
    return value


def _pipeline_input(input_data: dict) -> ScanPipelineInput:
    if not isinstance(input_data, dict):
        raise TypeError("input_data must be a dict")
    platform = input_data.get("platform", "Windows")
    privacy_mode = input_data.get("privacy_mode", "offline")
    if not isinstance(platform, str) or not platform.strip():
        raise ValueError("platform must be a non-empty string")
    if privacy_mode != "offline":
        raise ValueError("PR7 scan pipeline supports offline privacy mode only")
    return ScanPipelineInput(
        installed_apps=tuple(_input_list(input_data, "installed_apps", "software_entries")),
        startup_items=tuple(_input_list(input_data, "startup_items")),
        services=tuple(_input_list(input_data, "services")),
        scheduled_tasks=tuple(_input_list(input_data, "scheduled_tasks")),
        platform=platform.strip(),
        privacy_mode=privacy_mode,
    )


def _target_to_dict(target: GovernanceTarget) -> dict:
    return {
        "target_id": target.target_id,
        "object_type": target.object_type.value,
        "name": target.name,
        "publisher": target.publisher,
        "version": target.version,
        "path": target.path,
        "uninstall_available": target.uninstall_available,
        "source": target.source,
        "evidence_chain": {
            "sources": list(target.evidence_chain.sources),
            "facts": list(target.evidence_chain.facts),
            "references": list(target.evidence_chain.references),
            "confidence": target.evidence_chain.confidence,
        },
    }


def _decision_to_dict(decision: PolicyDecision) -> dict:
    return {
        "target_id": decision.target_id,
        "classification": decision.classification.value,
        "risk_level": decision.risk_level.value,
        "permission_level": decision.permission_level.value,
        "allowed": decision.allowed,
        "reason": decision.reason,
        "required_confirmation": decision.required_confirmation,
        "rollback_required": decision.rollback_required,
        "audit_required": decision.audit_required,
        "blocked_by_hard_rule": decision.blocked_by_hard_rule,
        "evidence_chain": {
            "sources": list(decision.evidence_chain.sources),
            "facts": list(decision.evidence_chain.facts),
            "references": list(decision.evidence_chain.references),
            "confidence": decision.evidence_chain.confidence,
        },
    }


def _audit_event(
    target: GovernanceTarget,
    decision: PolicyDecision,
    *,
    scan_id: str,
    plan_id: str,
    timestamp: str,
    index: int,
) -> AuditEvent:
    result = "planned"
    if decision.classification is ClassificationLabel.KEEP:
        result = "skipped"
    elif decision.classification is ClassificationLabel.BLOCK:
        result = "blocked"
    return AuditEvent(
        action="POLICY_RECOMMENDATION",
        target_id=target.target_id,
        target_name=target.name,
        classification=decision.classification,
        risk_level=decision.risk_level,
        permission_level=decision.permission_level,
        reason=decision.reason,
        evidence_refs=decision.evidence_chain.references,
        result=result,
        timestamp=timestamp,
        execution_method="policy_engine",
        rollback_available=decision.rollback_required,
        scan_id=scan_id,
        plan_id=plan_id,
        dry_run=True,
        policy_decision_id=f"decision:{scan_id}:{index}",
    )


def run_readonly_scan_pipeline(
    input_data: dict,
    *,
    scan_id: Optional[str] = None,
) -> ScanPipelineResult:
    """Normalize explicit data and return recommendations without executing actions."""

    pipeline_input = _pipeline_input(input_data)
    if scan_id is None:
        scan_id = f"scan:{uuid4()}"
    if not isinstance(scan_id, str) or not scan_id.strip():
        raise ValueError("scan_id must be a non-empty string")
    scan_id = scan_id.strip()
    created_at = _utc_timestamp()

    installed_apps: list[InstalledApp] = normalize_registry_apps(
        list(pipeline_input.installed_apps)
    )
    startup_items: list[StartupItem] = normalize_startup_items(
        list(pipeline_input.startup_items)
    )
    services: list[WindowsService] = normalize_services(list(pipeline_input.services))
    scheduled_tasks: list[ScheduledTask] = normalize_scheduled_tasks(
        list(pipeline_input.scheduled_tasks)
    )

    targets = tuple(
        [installed_app_to_governance_target(app) for app in installed_apps]
        + [startup_item_to_governance_target(item) for item in startup_items]
        + [service_to_governance_target(service) for service in services]
        + [scheduled_task_to_governance_target(task) for task in scheduled_tasks]
    )
    decisions = tuple(evaluate_target(target) for target in targets)
    report = build_report(
        scan_id,
        pipeline_input.platform,
        pipeline_input.privacy_mode,
        list(decisions),
    )
    plan_id = report["execution_plan"]["plan_id"]
    audit_events = tuple(
        _audit_event(
            target,
            decision,
            scan_id=scan_id,
            plan_id=plan_id,
            timestamp=created_at,
            index=index,
        )
        for index, (target, decision) in enumerate(zip(targets, decisions), start=1)
    )
    scan_target_records = tuple(
        [installed_app_to_scan_target_record(app, scan_id) for app in installed_apps]
        + [startup_item_to_scan_target_record(item, scan_id) for item in startup_items]
        + [service_to_scan_target_record(service, scan_id) for service in services]
        + [
            scheduled_task_to_scan_target_record(task, scan_id)
            for task in scheduled_tasks
        ]
    )

    input_summary = {
        "installed_apps_count": len(pipeline_input.installed_apps),
        "startup_items_count": len(pipeline_input.startup_items),
        "services_count": len(pipeline_input.services),
        "scheduled_tasks_count": len(pipeline_input.scheduled_tasks),
    }
    normalized_counts = {
        "installed_apps": len(installed_apps),
        "startup_items": len(startup_items),
        "services": len(services),
        "scheduled_tasks": len(scheduled_tasks),
        "total_targets": len(targets),
    }
    warnings = tuple(
        f"{key} omitted {input_summary[key + '_count'] - normalized_counts[key]} nameless record(s)"
        for key in ("installed_apps", "startup_items", "services", "scheduled_tasks")
        if input_summary[key + "_count"] > normalized_counts[key]
    )
    return ScanPipelineResult(
        scan_id=scan_id,
        created_at=created_at,
        input_summary=input_summary,
        normalized_counts=normalized_counts,
        targets=targets,
        decisions=decisions,
        report=report,
        audit_events=audit_events,
        scan_target_records=scan_target_records,
        warnings=warnings,
    )
