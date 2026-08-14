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
from ..external_tools import ExternalToolCatalog, ToolRecommender, ToolTrustPolicy
from ..pipeline import run_readonly_scan_pipeline
from ..pipeline.input_loader import _validated_explicit_local_path
from ..persistence import (
    build_agent_governance_preview as build_agent_governance_preview_data,
    build_persistence_chain_graph as build_persistence_chain_graph_data,
    build_persistence_governance_plan as build_persistence_governance_plan_data,
    render_persistence_chain_markdown,
    validate_agent_execution_request as validate_agent_execution_request_data,
)
from ..quarantine import QuarantineManager
from ..pup import (
    build_pup_corroboration as build_pup_corroboration_data,
    build_behavior_indicators_from_report,
    build_pup_review_pack as build_pup_review_pack_offline,
    inspect_pup_risk as inspect_pup_risk_offline,
    summarize_behavior_indicators,
)
from ..reputation import (
    ReputationMatcher,
    build_pup_insight as build_pup_insight_data,
    evidence_pack_stats,
    load_evidence_pack,
    load_seed_records,
    load_cn_source_matrix,
    summarize_cn_source_matrix as summarize_cn_source_matrix_data,
    build_evidence_quality_summary as build_evidence_quality_summary_data,
    build_evidence_coverage_summary as build_evidence_coverage_summary_data,
    build_false_positive_feedback_template as build_false_positive_feedback_template_data,
)
from ..reporting import build_user_friendly_pup_report as build_user_friendly_pup_report_data
from ..validation import (
    build_no_match_report as build_no_match_report_data,
    build_real_report_trial as build_real_report_trial_data,
    validate_real_report_shape as validate_real_report_shape_data,
)
from .cleanup_plan import READ_ONLY_EXECUTION_LEVEL, build_cleanup_plan_from_report


ACTION_NAMES = (
    "scan_from_json",
    "explain_report",
    "build_cleanup_plan",
    "write_report",
    "write_audit",
    "recommend_external_tools",
    "quarantine_file",
    "list_quarantine_items",
    "restore_quarantine_item",
    "match_reputation",
    "build_pup_insight",
    "inspect_pup_risk",
    "build_pup_review_pack",
    "build_behavior_indicators",
    "validate_cn_evidence_pack",
    "validate_cn_source_matrix",
    "summarize_cn_source_matrix",
    "build_evidence_quality_summary",
    "validate_real_report_shape",
    "build_cn_win_pup_review_pack",
    "build_pup_corroboration",
    "build_real_report_trial",
    "build_no_match_report",
    "build_evidence_coverage_summary",
    "build_user_friendly_pup_report",
    "build_false_positive_feedback_template",
    "build_persistence_chain_graph",
    "build_persistence_governance_plan",
    "explain_persistence_chain",
    "build_agent_governance_preview",
    "validate_agent_execution_request",
)
REVERSIBLE_EXECUTION_LEVEL = "LEVEL_2_REVERSIBLE"

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
        if self.execution_level not in {READ_ONLY_EXECUTION_LEVEL, REVERSIBLE_EXECUTION_LEVEL}:
            raise ValueError("unsupported skill action execution level")
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
    execution_level: str = READ_ONLY_EXECUTION_LEVEL,
) -> SkillActionResponse:
    return SkillActionResponse(
        request_id=_request_id(request_id),
        action=action,
        status=status,
        requires_user_confirmation=requires_user_confirmation,
        execution_level=execution_level,
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


def recommend_external_tools(
    *,
    catalog: dict,
    allowlisted_tool_ids: list[str] | tuple[str, ...],
    cleanup_plan: dict | None = None,
    report_summary: dict | None = None,
    governance_decisions: list[dict] | tuple[dict, ...] = (),
    evidence: list[dict] | tuple[dict, ...] = (),
    installed_apps: list[dict] | tuple[dict, ...] = (),
    request_id: str | None = None,
) -> SkillActionResponse:
    """Recommend cataloged tool review paths without commands or execution."""

    if (cleanup_plan is None) == (report_summary is None):
        raise ValueError("provide exactly one of cleanup_plan or report_summary")
    if not isinstance(catalog, dict):
        raise TypeError("catalog must be a dict")
    if not isinstance(allowlisted_tool_ids, (list, tuple)) or any(
        not isinstance(tool_id, str) or not tool_id.strip()
        for tool_id in allowlisted_tool_ids
    ):
        raise TypeError("allowlisted_tool_ids must contain strings")
    if report_summary is not None:
        if not isinstance(report_summary, dict):
            raise TypeError("report_summary must be a dict")
        cleanup_plan = build_cleanup_plan_from_report(report_summary).to_dict()
    if not isinstance(cleanup_plan, dict):
        raise TypeError("cleanup_plan must be a dict")

    parsed_catalog = ExternalToolCatalog.from_dict(catalog)
    policy = ToolTrustPolicy(tuple(allowlisted_tool_ids))
    recommendations = ToolRecommender(parsed_catalog, policy).recommend(
        cleanup_plan,
        governance_decisions=governance_decisions,
        evidence=evidence,
        installed_apps=installed_apps,
    )
    serialized = [item.to_dict() for item in recommendations]
    trusted_count = sum(item["trusted"] is True for item in serialized)
    blocked_count = sum(item["blocked"] is True for item in serialized)
    return _response(
        action="recommend_external_tools",
        request_id=request_id,
        status="planned",
        requires_user_confirmation=True,
        evidence=(
            {
                "source": "external_tool_recommender",
                "fact": (
                    f"produced {len(serialized)} Level 0 recommendation(s); "
                    f"{blocked_count} blocked by trust policy"
                ),
            },
        ),
        result={
            "mode": "plan_only",
            "recommendations": serialized,
            "recommendation_count": len(serialized),
            "trusted_count": trusted_count,
            "blocked_count": blocked_count,
            "execution_authorized": False,
        },
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


def quarantine_file_action(
    root,
    path,
    reason: str,
    *,
    evidence=(),
    confirmed: bool,
    request_id: str | None = None,
) -> SkillActionResponse:
    if confirmed is not True:
        raise ValueError("quarantine_file requires explicit confirmed=true")
    evidence_items = tuple(evidence) or (
        {"source": "skill_action", "fact": "explicit confirmed quarantine request"},
    )
    item = QuarantineManager.create_quarantine(root).quarantine_file(
        path, reason=reason, evidence=evidence_items
    )
    return _response(
        action="quarantine_file",
        request_id=request_id,
        requires_user_confirmation=True,
        execution_level=REVERSIBLE_EXECUTION_LEVEL,
        evidence=(
            {"source": "quarantine_manifest", "fact": f"item_id={item.item_id}"},
        ),
        result={**item.to_dict(), "status": "quarantined", "system_change_performed": True},
    )


def list_quarantine_items_action(root, *, request_id: str | None = None) -> SkillActionResponse:
    manager = QuarantineManager(root)
    items = [item.to_dict() for item in manager.list_items()]
    return _response(
        action="list_quarantine_items",
        request_id=request_id,
        requires_user_confirmation=False,
        evidence=({"source": "quarantine_manifest", "fact": f"listed {len(items)} item(s)"},),
        result={"root": str(manager.root), "items": items, "system_change_performed": False},
    )


def restore_quarantine_item_action(
    root,
    item_id: str,
    *,
    confirmed: bool,
    request_id: str | None = None,
) -> SkillActionResponse:
    if confirmed is not True:
        raise ValueError("restore_quarantine_item requires explicit confirmed=true")
    item = QuarantineManager(root).restore_item(item_id)
    return _response(
        action="restore_quarantine_item",
        request_id=request_id,
        requires_user_confirmation=True,
        execution_level=REVERSIBLE_EXECUTION_LEVEL,
        evidence=({"source": "quarantine_manifest", "fact": f"restored item_id={item.item_id}"},),
        result={**item.to_dict(), "system_change_performed": True},
    )


def match_reputation(report: dict, seed_path, *, request_id: str | None = None) -> SkillActionResponse:
    matches = ReputationMatcher(load_seed_records(seed_path)).match(report)
    return _response(
        action="match_reputation",
        request_id=request_id,
        requires_user_confirmation=True,
        evidence=({"source": "reputation_matcher", "fact": f"matched {len(matches)} target(s) using local seed evidence"},),
        result={"matches": matches, "match_count": len(matches), "execution_authorized": False},
    )


def build_pup_insight(matches: list[dict], *, request_id: str | None = None) -> SkillActionResponse:
    insight = build_pup_insight_data(matches)
    return _response(
        action="build_pup_insight",
        request_id=request_id,
        requires_user_confirmation=True,
        evidence=({"source": "pup_insight_builder", "fact": f"explained {len(matches)} non-authorizing match(es)"},),
        result={"pup_insight": insight, "execution_authorized": False},
    )


def inspect_pup_risk(
    report: dict,
    seed_path,
    *,
    evidence_pack: bool = False,
    include_indicators: bool = False,
    request_id: str | None = None,
) -> SkillActionResponse:
    result = inspect_pup_risk_offline(
        report, seed_path, evidence_pack=evidence_pack, include_indicators=include_indicators
    )
    return _response(
        action="inspect_pup_risk",
        request_id=request_id,
        requires_user_confirmation=True,
        evidence=({"source": "pup_inspector", "fact": f"built insight for {result['match_count']} local seed match(es)"},),
        result=result,
    )


def build_pup_review_pack(
    report: dict,
    evidence_pack_path,
    output_dir,
    *,
    cn_evidence_pack_path=None,
    cn_source_matrix_path=None,
    cn_candidate_sources_path=None,
    include_behavior_indicators: bool = False,
    overwrite: bool = False,
    request_id: str | None = None,
) -> SkillActionResponse:
    result = build_pup_review_pack_offline(
        report,
        evidence_pack_path,
        output_dir,
        cn_evidence_pack=cn_evidence_pack_path,
        cn_source_matrix=cn_source_matrix_path,
        cn_candidate_sources=cn_candidate_sources_path,
        include_behavior_indicators=include_behavior_indicators,
        overwrite=overwrite,
    )
    return _response(
        action="build_pup_review_pack",
        request_id=request_id,
        requires_user_confirmation=True,
        evidence=({
            "source": "pup_review_pack",
            "fact": f"wrote {result['artifact_count']} local explanation/review artifact(s)",
        },),
        result=result,
    )


def build_behavior_indicators(report: dict, *, request_id: str | None = None) -> SkillActionResponse:
    indicators = build_behavior_indicators_from_report(report)
    summary = summarize_behavior_indicators(indicators)
    return _response(
        action="build_behavior_indicators",
        request_id=request_id,
        requires_user_confirmation=True,
        evidence=({"source": "report_metadata", "fact": f"derived {len(indicators)} review-only behavior indicator(s)"},),
        result={**summary, "indicators": indicators, "execution_authorized": False},
    )


def validate_cn_evidence_pack(path, *, request_id: str | None = None) -> SkillActionResponse:
    records = load_evidence_pack(path)
    if any(item["language"] != "zh-CN" for item in records):
        raise ValueError("CN evidence pack requires language=zh-CN")
    stats = evidence_pack_stats(records)
    return _response(
        action="validate_cn_evidence_pack",
        request_id=request_id,
        requires_user_confirmation=False,
        evidence=({"source": "explicit_local_cn_evidence_pack", "fact": f"validated {len(records)} guarded record(s)"},),
        result={
            "valid": True,
            "cn_real_source_count": sum(item["is_synthetic"] is False for item in records),
            **stats,
            "runtime_network_access": False,
            "execution_authorized": False,
        },
    )


def validate_cn_source_matrix(path, *, request_id: str | None = None) -> SkillActionResponse:
    sources = load_cn_source_matrix(path)
    summary = summarize_cn_source_matrix_data(sources)
    return _response(
        action="validate_cn_source_matrix",
        request_id=request_id,
        requires_user_confirmation=False,
        evidence=({
            "source": "explicit_local_cn_source_matrix",
            "fact": f"validated {len(sources)} guarded public-source record(s)",
        },),
        result={"valid": True, **summary},
    )


def summarize_cn_source_matrix(path, *, request_id: str | None = None) -> SkillActionResponse:
    sources = load_cn_source_matrix(path)
    summary = summarize_cn_source_matrix_data(sources)
    return _response(
        action="summarize_cn_source_matrix",
        request_id=request_id,
        requires_user_confirmation=False,
        evidence=({
            "source": "explicit_local_cn_source_matrix",
            "fact": f"summarized {len(sources)} non-authorizing public source(s)",
        },),
        result=summary,
    )


def build_evidence_quality_summary(inputs, *, request_id: str | None = None) -> SkillActionResponse:
    if not isinstance(inputs, list) or not inputs:
        raise ValueError("inputs must be a non-empty list")
    records = [load_evidence_pack(path) for path in inputs]
    summary = build_evidence_quality_summary_data(records)
    return _response(
        action="build_evidence_quality_summary", request_id=request_id,
        requires_user_confirmation=False,
        evidence=({"source": "explicit_local_evidence_packs", "fact": f"scored {summary['total_records']} record(s) offline"},),
        result={**summary, "runtime_network_access": False, "execution_authorized": False},
    )


def validate_real_report_shape(report: dict, *, request_id: str | None = None) -> SkillActionResponse:
    summary = validate_real_report_shape_data(report)
    return _response(
        action="validate_real_report_shape", request_id=request_id,
        requires_user_confirmation=False,
        evidence=({"source": "caller_supplied_report", "fact": "validated report shape without reading other files"},),
        result=summary,
    )


def build_cn_win_pup_review_pack(
    report: dict, evidence_pack_path, cn_win_evidence_pack_path, output_dir, *,
    overwrite: bool = False, request_id: str | None = None,
) -> SkillActionResponse:
    result = build_pup_review_pack_offline(
        report, evidence_pack_path, output_dir,
        cn_win_evidence_pack=cn_win_evidence_pack_path,
        include_behavior_indicators=True,
        include_evidence_quality=True,
        include_corroboration=True,
        include_coverage=True,
        include_user_friendly_report=True,
        include_false_positive_template=True,
        include_real_report_validation_summary=True,
        overwrite=overwrite,
    )
    return _response(
        action="build_cn_win_pup_review_pack", request_id=request_id,
        requires_user_confirmation=True,
        evidence=({"source": "explicit_local_cn_win_evidence", "fact": f"wrote {result['artifact_count']} offline review artifact(s)"},),
        result=result,
    )


def build_pup_corroboration(matches, behavior_indicators, *, request_id=None):
    result = build_pup_corroboration_data(matches, behavior_indicators)
    return _response(
        action="build_pup_corroboration", request_id=request_id,
        requires_user_confirmation=False,
        evidence=({"source": "caller_supplied_review_metadata", "fact": "correlated evidence and behavior indicators offline"},),
        result=result,
    )


def build_no_match_report(report, evidence_packs, matchability_summary, *, request_id=None):
    result = build_no_match_report_data(report, evidence_packs, matchability_summary)
    return _response(
        action="build_no_match_report", request_id=request_id,
        requires_user_confirmation=False,
        evidence=({"source": "caller_supplied_report", "fact": "explained no-match coverage and metadata gaps offline"},),
        result=result,
    )


def build_real_report_trial(report, output_dir, evidence_pack, *, request_id=None, **options):
    result = build_real_report_trial_data(report, output_dir, evidence_pack, **options)
    return _response(
        action="build_real_report_trial", request_id=request_id,
        requires_user_confirmation=False,
        evidence=({"source": "explicit_local_report_and_evidence", "fact": "wrote a Level 0 offline report trial"},),
        result=result,
    )


def build_evidence_coverage_summary(evidence_packs, candidates, backlog, *, request_id=None):
    result = build_evidence_coverage_summary_data(evidence_packs, candidates, backlog)
    return _response(action="build_evidence_coverage_summary", request_id=request_id, requires_user_confirmation=False,
        evidence=({"source":"caller_supplied_evidence_metadata","fact":"summarized offline evidence coverage and data gaps"},), result=result)


def build_user_friendly_pup_report(review_pack_summary, *, request_id=None):
    result = build_user_friendly_pup_report_data(review_pack_summary)
    return _response(action="build_user_friendly_pup_report", request_id=request_id, requires_user_confirmation=False,
        evidence=({"source":"caller_supplied_review_summary","fact":"rendered a non-authorizing plain-language summary"},), result=result)


def build_false_positive_feedback_template(match, report_metadata, *, request_id=None):
    result = build_false_positive_feedback_template_data(match, report_metadata)
    return _response(action="build_false_positive_feedback_template", request_id=request_id, requires_user_confirmation=False,
        evidence=({"source":"caller_supplied_redacted_metadata","fact":"built a local review-queue feedback template"},), result=result)


def build_persistence_chain_graph(report, evidence_matches=None, behavior_indicators=None, *, request_id=None):
    result = build_persistence_chain_graph_data(report, evidence_matches, behavior_indicators)
    return _response(action="build_persistence_chain_graph", request_id=request_id, requires_user_confirmation=False,
        evidence=({"source":"caller_supplied_report","fact":"built an offline L0 persistence graph without reading the system"},), result=result)


def build_persistence_governance_plan(graph, *, request_id=None):
    result = build_persistence_governance_plan_data(graph)
    return _response(action="build_persistence_governance_plan", request_id=request_id, requires_user_confirmation=False,
        evidence=({"source":"caller_supplied_graph","fact":"built an L0 proposal-only governance view"},), result=result)


def explain_persistence_chain(graph, *, request_id=None):
    result = {"markdown": render_persistence_chain_markdown(graph), "risk_summary": graph.get("risk_summary", {}), "execution_gating_eligible_count": 0, "execution_authorized": False}
    return _response(action="explain_persistence_chain", request_id=request_id, requires_user_confirmation=False,
        evidence=({"source":"caller_supplied_graph","fact":"rendered a non-authorizing explanation"},), result=result)


def build_agent_governance_preview(report, evidence_matches=None, behavior_indicators=None, *, request_id=None):
    result = build_agent_governance_preview_data(report, evidence_matches, behavior_indicators)
    return _response(action="build_agent_governance_preview", request_id=request_id, requires_user_confirmation=False,
        evidence=({"source":"caller_supplied_report","fact":"built an L0 Agent governance preview"},), result=result)


def validate_agent_execution_request(request, *, request_id=None):
    result = validate_agent_execution_request_data(request)
    return _response(action="validate_agent_execution_request", request_id=request_id, requires_user_confirmation=False,
        evidence=({"source":"caller_supplied_agent_request","fact":"applied a fail-closed mutation guard"},), result=result)


def invoke_skill_action(request: SkillActionRequest | dict) -> SkillActionResponse:
    """Dispatch a primary Guard action or a legacy compatibility action."""

    if isinstance(request, dict) and request.get("action") in {
        "evaluate_action",
        "prepare_execution",
        "evaluate_action_bundle",
        "record_execution_result",
        "verify_audit",
    }:
        from .guard_actions import invoke_guard_action

        return invoke_guard_action(request)

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
    if request.action == "recommend_external_tools":
        _validated_payload(
            payload,
            {"catalog", "allowlisted_tool_ids"},
            {
                "cleanup_plan",
                "report_summary",
                "governance_decisions",
                "evidence",
                "installed_apps",
            },
        )
        return recommend_external_tools(
            cleanup_plan=payload.get("cleanup_plan"),
            report_summary=payload.get("report_summary"),
            catalog=payload["catalog"],
            allowlisted_tool_ids=payload["allowlisted_tool_ids"],
            governance_decisions=payload.get("governance_decisions", ()),
            evidence=payload.get("evidence", ()),
            installed_apps=payload.get("installed_apps", ()),
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
    if request.action == "quarantine_file":
        _validated_payload(payload, {"root", "path", "reason", "confirmed"}, {"evidence"})
        return quarantine_file_action(
            payload["root"], payload["path"], payload["reason"],
            evidence=payload.get("evidence", ()), confirmed=payload["confirmed"],
            request_id=request.request_id,
        )
    if request.action == "list_quarantine_items":
        _validated_payload(payload, {"root"}, set())
        return list_quarantine_items_action(payload["root"], request_id=request.request_id)
    if request.action == "restore_quarantine_item":
        _validated_payload(payload, {"root", "item_id", "confirmed"}, set())
        return restore_quarantine_item_action(
            payload["root"], payload["item_id"], confirmed=payload["confirmed"],
            request_id=request.request_id,
        )
    if request.action == "match_reputation":
        _validated_payload(payload, {"report", "seed_path"}, set())
        return match_reputation(payload["report"], payload["seed_path"], request_id=request.request_id)
    if request.action == "build_pup_insight":
        _validated_payload(payload, {"matches"}, set())
        return build_pup_insight(payload["matches"], request_id=request.request_id)
    if request.action == "inspect_pup_risk":
        _validated_payload(payload, {"report", "seed_path"}, {"evidence_pack", "include_indicators"})
        return inspect_pup_risk(
            payload["report"], payload["seed_path"],
            evidence_pack=payload.get("evidence_pack", False),
            include_indicators=payload.get("include_indicators", False),
            request_id=request.request_id,
        )
    if request.action == "build_pup_review_pack":
        _validated_payload(
            payload,
            {"report", "evidence_pack_path", "output_dir"},
            {
                "cn_evidence_pack_path", "cn_source_matrix_path",
                "cn_candidate_sources_path", "include_behavior_indicators", "overwrite",
            },
        )
        return build_pup_review_pack(
            payload["report"], payload["evidence_pack_path"], payload["output_dir"],
            cn_evidence_pack_path=payload.get("cn_evidence_pack_path"),
            cn_source_matrix_path=payload.get("cn_source_matrix_path"),
            cn_candidate_sources_path=payload.get("cn_candidate_sources_path"),
            include_behavior_indicators=payload.get("include_behavior_indicators", False),
            overwrite=payload.get("overwrite", False), request_id=request.request_id,
        )
    if request.action == "build_behavior_indicators":
        _validated_payload(payload, {"report"}, set())
        return build_behavior_indicators(payload["report"], request_id=request.request_id)
    if request.action == "validate_cn_evidence_pack":
        _validated_payload(payload, {"path"}, set())
        return validate_cn_evidence_pack(payload["path"], request_id=request.request_id)
    if request.action == "validate_cn_source_matrix":
        _validated_payload(payload, {"path"}, set())
        return validate_cn_source_matrix(payload["path"], request_id=request.request_id)
    if request.action == "summarize_cn_source_matrix":
        _validated_payload(payload, {"path"}, set())
        return summarize_cn_source_matrix(payload["path"], request_id=request.request_id)
    if request.action == "build_evidence_quality_summary":
        _validated_payload(payload, {"inputs"}, set())
        return build_evidence_quality_summary(payload["inputs"], request_id=request.request_id)
    if request.action == "validate_real_report_shape":
        _validated_payload(payload, {"report"}, set())
        return validate_real_report_shape(payload["report"], request_id=request.request_id)
    if request.action == "build_cn_win_pup_review_pack":
        _validated_payload(
            payload, {"report", "evidence_pack_path", "cn_win_evidence_pack_path", "output_dir"}, {"overwrite"}
        )
        return build_cn_win_pup_review_pack(
            payload["report"], payload["evidence_pack_path"], payload["cn_win_evidence_pack_path"], payload["output_dir"],
            overwrite=payload.get("overwrite", False), request_id=request.request_id,
        )
    if request.action == "build_pup_corroboration":
        _validated_payload(payload, {"matches", "behavior_indicators"}, set())
        return build_pup_corroboration(
            payload["matches"], payload["behavior_indicators"], request_id=request.request_id
        )
    if request.action == "build_no_match_report":
        _validated_payload(payload, {"report", "evidence_packs", "matchability_summary"}, set())
        return build_no_match_report(
            payload["report"], payload["evidence_packs"], payload["matchability_summary"],
            request_id=request.request_id,
        )
    if request.action == "build_real_report_trial":
        _validated_payload(
            payload, {"report", "output_dir", "evidence_pack"},
            {"cn_win_evidence_pack", "cn_source_matrix", "include_behavior_indicators", "include_evidence_quality", "include_coverage", "include_user_friendly_report", "include_persistence_chain", "overwrite"},
        )
        return build_real_report_trial(
            payload["report"], payload["output_dir"], payload["evidence_pack"],
            cn_win_evidence_pack=payload.get("cn_win_evidence_pack"),
            cn_source_matrix=payload.get("cn_source_matrix"),
            include_behavior_indicators=payload.get("include_behavior_indicators", False),
            include_evidence_quality=payload.get("include_evidence_quality", False),
            include_coverage=payload.get("include_coverage", False),
            include_user_friendly_report=payload.get("include_user_friendly_report", False),
            include_persistence_chain=payload.get("include_persistence_chain", False),
            overwrite=payload.get("overwrite", False), request_id=request.request_id,
        )
    if request.action == "build_evidence_coverage_summary":
        _validated_payload(payload, {"evidence_packs", "candidates", "backlog"}, set())
        return build_evidence_coverage_summary(payload["evidence_packs"], payload["candidates"], payload["backlog"], request_id=request.request_id)
    if request.action == "build_user_friendly_pup_report":
        _validated_payload(payload, {"review_pack_summary"}, set())
        return build_user_friendly_pup_report(payload["review_pack_summary"], request_id=request.request_id)
    if request.action == "build_false_positive_feedback_template":
        _validated_payload(payload, {"match", "report_metadata"}, set())
        return build_false_positive_feedback_template(payload["match"], payload["report_metadata"], request_id=request.request_id)
    if request.action == "build_persistence_chain_graph":
        _validated_payload(payload, {"report"}, {"evidence_matches", "behavior_indicators"})
        return build_persistence_chain_graph(payload["report"], payload.get("evidence_matches"), payload.get("behavior_indicators"), request_id=request.request_id)
    if request.action == "build_persistence_governance_plan":
        _validated_payload(payload, {"graph"}, set())
        return build_persistence_governance_plan(payload["graph"], request_id=request.request_id)
    if request.action == "explain_persistence_chain":
        _validated_payload(payload, {"graph"}, set())
        return explain_persistence_chain(payload["graph"], request_id=request.request_id)
    if request.action == "build_agent_governance_preview":
        _validated_payload(payload, {"report"}, {"evidence_matches", "behavior_indicators"})
        return build_agent_governance_preview(payload["report"], payload.get("evidence_matches"), payload.get("behavior_indicators"), request_id=request.request_id)
    if request.action == "validate_agent_execution_request":
        _validated_payload(payload, {"request"}, set())
        return validate_agent_execution_request(payload["request"], request_id=request.request_id)
    raise ValueError("unsupported skill action")
