"""JSON-friendly, offline action interface for external AI callers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Tuple
from uuid import uuid4

from ..ai import (
    DryRunPromptProvider,
    MockAIProvider,
    explain_report as explain_report_offline,
)
from ..pipeline import run_readonly_scan_pipeline
from ..pipeline.input_loader import _validated_explicit_local_path
from .cleanup_plan import READ_ONLY_EXECUTION_LEVEL, build_cleanup_plan_from_report


ACTION_NAMES = (
    "scan_from_json",
    "explain_report",
    "build_cleanup_plan",
    "write_report",
    "write_audit",
)

_AUDIT_RESULTS = {"planned", "simulated", "blocked", "refused", "skipped"}
_AUDIT_METHODS = {"none", "dry_run", "policy_engine", "report_builder"}
_AUDIT_FIELDS = {
    "schema_version",
    "scan_id",
    "plan_id",
    "event_id",
    "timestamp",
    "actor",
    "mode",
    "action",
    "target_id",
    "target_name",
    "classification",
    "risk_level",
    "permission_level",
    "reason",
    "evidence_refs",
    "approved_by",
    "execution_method",
    "command_summary",
    "result",
    "rollback_available",
    "rollback_method",
    "dry_run",
    "policy_decision_id",
    "rulepack_version",
}


@dataclass(frozen=True, slots=True)
class SkillActionRequest:
    """Validated request envelope accepted from an external AI caller."""

    action: str
    payload: dict
    request_id: str
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise ValueError("request_id must be a non-empty string")
        if self.schema_version != "0.1":
            raise ValueError("unsupported skill action schema version")
        if self.action not in ACTION_NAMES:
            raise ValueError("unsupported skill action")
        if not isinstance(self.payload, dict):
            raise TypeError("payload must be a dict")
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise ValueError("request_id must be a non-empty string")
        if self.schema_version != "0.1":
            raise ValueError("unsupported skill action schema version")

    @classmethod
    def from_dict(cls, data: dict) -> "SkillActionRequest":
        if not isinstance(data, dict):
            raise TypeError("action request must be a dict")
        allowed = {"schema_version", "request_id", "action", "payload"}
        unexpected = set(data) - allowed
        if unexpected:
            raise ValueError(f"unexpected action request fields: {sorted(unexpected)}")
        if "action" not in data or "payload" not in data:
            raise ValueError("action request requires action and payload")
        request_id = data.get("request_id")
        if request_id is None:
            request_id = f"request:{uuid4()}"
        return cls(
            action=data["action"],
            payload=data["payload"],
            request_id=request_id,
            schema_version=data.get("schema_version", "0.1"),
        )

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "action": self.action,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True, slots=True)
class SkillActionResponse:
    """A Level 0 result envelope that never grants execution authority."""

    request_id: str
    action: str
    status: str
    requires_user_confirmation: bool
    execution_level: str
    evidence: Tuple[dict, ...]
    result: dict
    schema_version: str = "0.1"
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if self.action not in ACTION_NAMES:
            raise ValueError("unsupported skill action")
        if self.status not in {"completed", "planned"}:
            raise ValueError("unsupported action response status")
        if not isinstance(self.requires_user_confirmation, bool):
            raise TypeError("requires_user_confirmation must be a bool")
        if self.execution_level != READ_ONLY_EXECUTION_LEVEL:
            raise ValueError("skill actions are restricted to Level 0")
        if self.execution_authorized is not False:
            raise ValueError("PR10 skill actions cannot authorize execution")
        if not isinstance(self.result, dict):
            raise TypeError("result must be a dict")
        if not self.evidence or any(
            not isinstance(item, dict)
            or not isinstance(item.get("source"), str)
            or not item["source"].strip()
            or not isinstance(item.get("fact"), str)
            or not item["fact"].strip()
            for item in self.evidence
        ):
            raise ValueError("evidence must contain source/fact objects")

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "action": self.action,
            "status": self.status,
            "requires_user_confirmation": self.requires_user_confirmation,
            "execution_level": self.execution_level,
            "evidence": [dict(item) for item in self.evidence],
            "execution_authorized": False,
            "result": dict(self.result),
        }


def _request_id(value: str | None) -> str:
    if value is None:
        return f"request:{uuid4()}"
    if not isinstance(value, str) or not value.strip():
        raise ValueError("request_id must be a non-empty string")
    return value.strip()


def _response(
    *,
    action: str,
    result: dict,
    evidence: Tuple[dict, ...],
    requires_user_confirmation: bool,
    status: str = "completed",
    request_id: str | None = None,
) -> SkillActionResponse:
    return SkillActionResponse(
        request_id=_request_id(request_id),
        action=action,
        status=status,
        requires_user_confirmation=requires_user_confirmation,
        execution_level=READ_ONLY_EXECUTION_LEVEL,
        evidence=evidence,
        result=result,
        schema_version="0.1",
        execution_authorized=False,
    )


def scan_from_json(
    input_data: dict,
    *,
    scan_id: str | None = None,
    request_id: str | None = None,
) -> SkillActionResponse:
    """Run the PR7 in-memory pipeline without invoking a collector."""

    pipeline_result = run_readonly_scan_pipeline(input_data, scan_id=scan_id)
    serialized = pipeline_result.to_dict()
    confirmation_labels = {"ASK_USER", "SAFE_REMOVE", "STARTUP_OFF", "QUARANTINE"}
    requires_confirmation = any(
        decision["required_confirmation"] is True
        or decision["classification"] in confirmation_labels
        for decision in serialized["decisions"]
    )
    total = serialized["normalized_counts"]["total_targets"]
    return _response(
        action="scan_from_json",
        request_id=request_id,
        requires_user_confirmation=requires_confirmation,
        evidence=(
            {
                "source": "readonly_scan_pipeline",
                "fact": f"normalized {total} target(s) through Policy Engine",
            },
        ),
        result={"scan_result": serialized},
    )


def explain_report(
    report: dict,
    *,
    provider: str = "mock",
    request_id: str | None = None,
) -> SkillActionResponse:
    """Run the PR9 offline explainer through an approved local provider."""

    if provider == "mock":
        selected_provider = MockAIProvider()
    elif provider == "dry-run-prompt":
        selected_provider = DryRunPromptProvider()
    else:
        raise ValueError("provider must be mock or dry-run-prompt")
    explanation = explain_report_offline(report, selected_provider)
    return _response(
        action="explain_report",
        request_id=request_id,
        requires_user_confirmation=True,
        evidence=(
            {
                "source": "offline_report_explainer",
                "fact": f"generated explanation with {explanation.provider}",
            },
        ),
        result={
            "provider": explanation.provider,
            "safety_notice": explanation.safety_notice,
            "markdown": explanation.markdown,
            "execution_authorized": False,
        },
    )


def build_cleanup_plan(
    report: dict,
    *,
    plan_id: str | None = None,
    request_id: str | None = None,
) -> SkillActionResponse:
    """Build a symbolic review plan without commands or execution."""

    plan = build_cleanup_plan_from_report(report, plan_id=plan_id)
    serialized = plan.to_dict()
    return _response(
        action="build_cleanup_plan",
        request_id=request_id,
        status="planned",
        requires_user_confirmation=plan.requires_user_confirmation,
        evidence=(
            {
                "source": "policy_decisions",
                "fact": f"built {len(plan.steps)} non-executable review step(s)",
            },
        ),
        result={"cleanup_plan": serialized},
    )


def write_report(
    path: str | Path,
    report: dict,
    *,
    explicit_overwrite: bool = False,
    request_id: str | None = None,
) -> SkillActionResponse:
    """Write one JSON report artifact to an explicit safe local path."""

    if not isinstance(report, dict):
        raise TypeError("report must be a dict")
    if not isinstance(explicit_overwrite, bool):
        raise TypeError("explicit_overwrite must be a bool")
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    destination = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if explicit_overwrite else "x"
    with destination.open(mode, encoding="utf-8", newline="\n") as stream:
        stream.write(serialized)
    return _response(
        action="write_report",
        request_id=request_id,
        requires_user_confirmation=False,
        evidence=(
            {
                "source": "explicit_local_path",
                "fact": "wrote the caller-supplied report artifact",
            },
        ),
        result={
            "artifact_type": "report_json",
            "path": str(destination),
            "artifact_written": True,
            "system_change_performed": False,
        },
    )


def _validated_audit_events(events: list[dict]) -> list[dict]:
    if not isinstance(events, list) or not all(
        isinstance(item, dict) for item in events
    ):
        raise TypeError("events must be a list of dicts")
    validated = []
    for event in events:
        missing = _AUDIT_FIELDS - set(event)
        if missing:
            raise ValueError(f"missing audit fields: {sorted(missing)}")
        unexpected = set(event) - _AUDIT_FIELDS
        if unexpected:
            raise ValueError(f"unexpected audit fields: {sorted(unexpected)}")
        if event.get("dry_run") is not True:
            raise ValueError("audit events must remain dry-run")
        if event.get("command_summary") is not None:
            raise ValueError("audit command_summary must remain null")
        if event.get("result") not in _AUDIT_RESULTS:
            raise ValueError("audit result is not allowed")
        if event.get("execution_method") not in _AUDIT_METHODS:
            raise ValueError("audit execution method is not allowed")
        validated.append(dict(event))
    return validated


def write_audit(
    path: str | Path,
    events: list[dict],
    *,
    explicit_overwrite: bool = False,
    request_id: str | None = None,
) -> SkillActionResponse:
    """Write validated dry-run JSONL to an explicit safe local path."""

    if not isinstance(explicit_overwrite, bool):
        raise TypeError("explicit_overwrite must be a bool")
    validated = _validated_audit_events(events)
    serialized = [
        json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        for event in validated
    ]
    destination = _validated_explicit_local_path(path, allowed_suffixes={".jsonl"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if explicit_overwrite else "x"
    with destination.open(mode, encoding="utf-8", newline="\n") as stream:
        for line in serialized:
            stream.write(line + "\n")
    return _response(
        action="write_audit",
        request_id=request_id,
        requires_user_confirmation=False,
        evidence=(
            {
                "source": "dry_run_audit_events",
                "fact": f"wrote {len(validated)} validated audit event(s)",
            },
        ),
        result={
            "artifact_type": "audit_jsonl",
            "path": str(destination),
            "events_written": len(validated),
            "artifact_written": True,
            "system_change_performed": False,
        },
    )


def _validated_payload(payload: dict, required: set[str], optional: set[str]) -> dict:
    missing = required - set(payload)
    if missing:
        raise ValueError(f"missing action payload fields: {sorted(missing)}")
    unexpected = set(payload) - required - optional
    if unexpected:
        raise ValueError(f"unexpected action payload fields: {sorted(unexpected)}")
    return payload


def invoke_skill_action(request: SkillActionRequest | dict) -> SkillActionResponse:
    """Validate and dispatch one external AI action request."""

    if isinstance(request, dict):
        request = SkillActionRequest.from_dict(request)
    if not isinstance(request, SkillActionRequest):
        raise TypeError("request must be a SkillActionRequest or dict")
    payload = request.payload

    if request.action == "scan_from_json":
        _validated_payload(payload, {"input_data"}, {"scan_id"})
        return scan_from_json(
            payload["input_data"],
            scan_id=payload.get("scan_id"),
            request_id=request.request_id,
        )
    if request.action == "explain_report":
        _validated_payload(payload, {"report"}, {"provider"})
        return explain_report(
            payload["report"],
            provider=payload.get("provider", "mock"),
            request_id=request.request_id,
        )
    if request.action == "build_cleanup_plan":
        _validated_payload(payload, {"report"}, {"plan_id"})
        return build_cleanup_plan(
            payload["report"],
            plan_id=payload.get("plan_id"),
            request_id=request.request_id,
        )
    if request.action == "write_report":
        _validated_payload(
            payload,
            {"path", "report"},
            {"explicit_overwrite"},
        )
        return write_report(
            payload["path"],
            payload["report"],
            explicit_overwrite=payload.get("explicit_overwrite", False),
            request_id=request.request_id,
        )
    if request.action == "write_audit":
        _validated_payload(
            payload,
            {"path", "events"},
            {"explicit_overwrite"},
        )
        return write_audit(
            payload["path"],
            payload["events"],
            explicit_overwrite=payload.get("explicit_overwrite", False),
            request_id=request.request_id,
        )
    raise ValueError("unsupported skill action")
