"""Create symbolic external-tool review plans without commands or execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from uuid import uuid4

from ..core.models import RiskLevel
from .catalog import ExternalToolCatalog, ExternalToolRecord, ExternalToolType
from .trust_policy import ToolTrustDecision, ToolTrustPolicy


READ_ONLY_EXECUTION_LEVEL = "LEVEL_0_READ_ONLY"


@dataclass(frozen=True, slots=True)
class ExternalToolInvocationPlan:
    """A plan-only artifact, never an instruction to invoke an external tool."""

    plan_id: str
    tool_id: str
    tool_name: str
    tool_type: ExternalToolType
    requested_action: str
    risk_level: RiskLevel
    evidence: Tuple[dict, ...]
    reason: str
    required_user_confirmation: bool
    execution_level: str
    blocked_if_untrusted: bool
    blocked: bool
    trusted: bool
    mode: str = "plan_only"
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        for field_name, value in (
            ("plan_id", self.plan_id),
            ("tool_id", self.tool_id),
            ("tool_name", self.tool_name),
            ("requested_action", self.requested_action),
            ("reason", self.reason),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not isinstance(self.tool_type, ExternalToolType):
            raise TypeError("tool_type must be an ExternalToolType")
        if not isinstance(self.risk_level, RiskLevel):
            raise TypeError("risk_level must be a RiskLevel")
        if self.execution_level != READ_ONLY_EXECUTION_LEVEL:
            raise ValueError("external-tool plans are restricted to Level 0")
        if self.mode != "plan_only" or self.execution_authorized is not False:
            raise ValueError("external-tool plans cannot authorize execution")
        if self.blocked_if_untrusted is not True:
            raise ValueError("plans must be blocked if trust is absent")
        if self.blocked != (not self.trusted):
            raise ValueError("blocked state must match trust decision")
        if self.required_user_confirmation is not True:
            raise ValueError("external-tool plans always require user confirmation")
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
            "plan_id": self.plan_id,
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "tool_type": self.tool_type.value,
            "requested_action": self.requested_action,
            "risk_level": self.risk_level.value,
            "evidence": [dict(item) for item in self.evidence],
            "reason": self.reason,
            "required_user_confirmation": True,
            "execution_level": READ_ONLY_EXECUTION_LEVEL,
            "blocked_if_untrusted": True,
            "blocked": self.blocked,
            "trusted": self.trusted,
            "mode": "plan_only",
            "execution_authorized": False,
        }


def _caller_evidence(evidence: Tuple[dict, ...] | list[dict]) -> Tuple[dict, ...]:
    evidence = tuple(evidence)
    if any(
        not isinstance(item, dict)
        or not isinstance(item.get("source"), str)
        or not item["source"].strip()
        or not isinstance(item.get("fact"), str)
        or not item["fact"].strip()
        for item in evidence
    ):
        raise ValueError("evidence must contain source/fact objects")
    return tuple({"source": item["source"], "fact": item["fact"]} for item in evidence)


def _catalog_evidence(record: ExternalToolRecord) -> dict:
    return {
        "source": "external_tool_catalog",
        "fact": f"catalog record type is {record.tool_type.value}",
    }


def build_external_tool_invocation_plan(
    catalog: ExternalToolCatalog,
    trust_policy: ToolTrustPolicy,
    *,
    tool_id: str,
    requested_action: str,
    reason: str,
    evidence: Tuple[dict, ...] | list[dict] = (),
    plan_id: str | None = None,
) -> ExternalToolInvocationPlan:
    """Build a confirmation-only review plan for an explicitly cataloged tool."""

    if not isinstance(catalog, ExternalToolCatalog):
        raise TypeError("catalog must be an ExternalToolCatalog")
    if not isinstance(trust_policy, ToolTrustPolicy):
        raise TypeError("trust_policy must be a ToolTrustPolicy")
    if not isinstance(requested_action, str) or not requested_action.strip():
        raise ValueError("requested_action must be a non-empty string")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("reason must be a non-empty string")
    record = catalog.require(tool_id)
    if requested_action not in record.supported_actions:
        raise ValueError("requested_action is not supported by the cataloged tool")
    if plan_id is None:
        plan_id = f"external-tool-plan:{uuid4()}"
    if not isinstance(plan_id, str) or not plan_id.strip():
        raise ValueError("plan_id must be a non-empty string")

    decision: ToolTrustDecision = trust_policy.evaluate(record)
    combined_evidence = (
        _catalog_evidence(record),
        *decision.evidence,
        *_caller_evidence(evidence),
    )
    return ExternalToolInvocationPlan(
        plan_id=plan_id.strip(),
        tool_id=record.tool_id,
        tool_name=record.name,
        tool_type=record.tool_type,
        requested_action=requested_action,
        risk_level=record.risk_level,
        evidence=combined_evidence,
        reason=reason.strip(),
        required_user_confirmation=True,
        execution_level=READ_ONLY_EXECUTION_LEVEL,
        blocked_if_untrusted=True,
        blocked=not decision.trusted,
        trusted=decision.trusted,
        mode="plan_only",
        execution_authorized=False,
    )
