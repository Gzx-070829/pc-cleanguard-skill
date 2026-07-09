"""Build non-executable cleanup review plans from policy report data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple
from uuid import uuid4


READ_ONLY_EXECUTION_LEVEL = "LEVEL_0_READ_ONLY"

_CLASSIFICATIONS = {
    "KEEP",
    "ASK_USER",
    "SAFE_REMOVE",
    "STARTUP_OFF",
    "QUARANTINE",
    "BLOCK",
}
_PERMISSION_LEVELS = {
    "LEVEL_0_READ_ONLY",
    "LEVEL_1_LOW_RISK_CLEANUP",
    "LEVEL_2_REVERSIBLE",
    "LEVEL_3_STANDARD_UNINSTALL",
    "LEVEL_4_HIGH_RISK_SYSTEM_MODIFICATION",
    "LEVEL_5_FORBIDDEN",
}
_REVIEW_ACTIONS = {
    "KEEP": "PRESERVE",
    "ASK_USER": "REQUEST_USER_REVIEW",
    "SAFE_REMOVE": "REVIEW_REMOVAL_CANDIDATE",
    "STARTUP_OFF": "REVIEW_STARTUP_CANDIDATE",
    "QUARANTINE": "REVIEW_ISOLATION_CANDIDATE",
    "BLOCK": "BLOCKED_BY_POLICY",
    "UNKNOWN": "REQUEST_USER_REVIEW",
}


@dataclass(frozen=True, slots=True)
class CleanupPlanStep:
    """A symbolic review step that can never authorize execution."""

    step_id: str
    target_id: str
    classification: str
    review_action: str
    proposed_execution_level: str
    requires_user_confirmation: bool
    blocked: bool
    evidence: Tuple[dict, ...]
    execution_authorized: bool = False

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "target_id": self.target_id,
            "classification": self.classification,
            "review_action": self.review_action,
            "proposed_execution_level": self.proposed_execution_level,
            "requires_user_confirmation": self.requires_user_confirmation,
            "blocked": self.blocked,
            "evidence": [dict(item) for item in self.evidence],
            "execution_authorized": False,
        }


@dataclass(frozen=True, slots=True)
class CleanupPlan:
    """A Level 0 policy artifact with no commands or execution mechanism."""

    plan_id: str
    source_scan_id: str | None
    steps: Tuple[CleanupPlanStep, ...]
    requires_user_confirmation: bool
    execution_level: str = READ_ONLY_EXECUTION_LEVEL
    mode: str = "plan_only"
    execution_authorized: bool = False

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "source_scan_id": self.source_scan_id,
            "mode": self.mode,
            "execution_level": self.execution_level,
            "requires_user_confirmation": self.requires_user_confirmation,
            "execution_authorized": False,
            "steps": [step.to_dict() for step in self.steps],
        }


def _report_layer(report: dict) -> dict:
    nested = report.get("report")
    return nested if isinstance(nested, dict) else report


def _decision_rows(report: dict) -> list[dict]:
    decisions = report.get("decisions")
    if isinstance(decisions, list):
        return [item for item in decisions if isinstance(item, dict)]
    layer = _report_layer(report)
    findings = layer.get("findings")
    if isinstance(findings, list):
        rows = [dict(item) for item in findings if isinstance(item, dict)]
        recommendations = layer.get("recommendations")
        if isinstance(recommendations, list):
            by_target = {
                item.get("target_id"): item
                for item in recommendations
                if isinstance(item, dict) and isinstance(item.get("target_id"), str)
            }
            for row in rows:
                recommendation = by_target.get(row.get("target_id"))
                if recommendation:
                    row["required_confirmation"] = recommendation.get(
                        "required_confirmation"
                    )
                    row["evidence_chain"] = recommendation.get("evidence_chain")
        return rows
    recommendations = layer.get("recommendations")
    if isinstance(recommendations, list):
        return [item for item in recommendations if isinstance(item, dict)]
    return []


def _source_scan_id(report: dict) -> str | None:
    scan_id = report.get("scan_id")
    if isinstance(scan_id, str) and scan_id.strip():
        return scan_id.strip()
    summary = _report_layer(report).get("summary", {})
    if isinstance(summary, dict):
        scan_id = summary.get("scan_id")
        if isinstance(scan_id, str) and scan_id.strip():
            return scan_id.strip()
    return None


def _safe_target_id(value: Any, index: int) -> str:
    if not isinstance(value, str) or not value.strip():
        return f"UNSPECIFIED:{index}"
    return " ".join(value.split())[:256]


def _classification(value: Any) -> str:
    return value if isinstance(value, str) and value in _CLASSIFICATIONS else "UNKNOWN"


def _permission(value: Any) -> str:
    if isinstance(value, str) and value in _PERMISSION_LEVELS:
        return value
    return READ_ONLY_EXECUTION_LEVEL


def _evidence(decision: dict, classification: str) -> Tuple[dict, ...]:
    sources: list[str] = []
    chain = decision.get("evidence_chain")
    if isinstance(chain, dict) and isinstance(chain.get("sources"), list):
        sources = [
            source.strip()
            for source in chain["sources"]
            if isinstance(source, str) and source.strip()
        ]
    elif isinstance(chain, list):
        sources = [
            item["source"].strip()
            for item in chain
            if isinstance(item, dict)
            and isinstance(item.get("source"), str)
            and item["source"].strip()
        ]
    if not sources:
        sources = ["policy_decision"]
    return tuple(
        {
            "source": source[:128],
            "fact": f"policy classification is {classification}",
        }
        for source in sources[:8]
    )


def build_cleanup_plan_from_report(
    report: dict,
    *,
    plan_id: str | None = None,
) -> CleanupPlan:
    """Convert report decisions into symbolic review steps only."""

    if not isinstance(report, dict):
        raise TypeError("report must be a dict")
    if plan_id is None:
        plan_id = f"cleanup-plan:{uuid4()}"
    if not isinstance(plan_id, str) or not plan_id.strip():
        raise ValueError("plan_id must be a non-empty string")

    steps = []
    for index, decision in enumerate(_decision_rows(report), start=1):
        classification = _classification(decision.get("classification"))
        proposed_level = _permission(decision.get("permission_level"))
        blocked = (
            classification == "BLOCK"
            or proposed_level == "LEVEL_5_FORBIDDEN"
            or decision.get("blocked_by_hard_rule") is True
        )
        if blocked:
            review_action = "BLOCKED_BY_POLICY"
            requires_confirmation = False
        else:
            review_action = _REVIEW_ACTIONS[classification]
            requires_confirmation = (
                classification != "KEEP"
                or decision.get("required_confirmation") is True
            )
        steps.append(
            CleanupPlanStep(
                step_id=f"review-{index:04d}",
                target_id=_safe_target_id(decision.get("target_id"), index),
                classification=classification,
                review_action=review_action,
                proposed_execution_level=proposed_level,
                requires_user_confirmation=requires_confirmation,
                blocked=blocked,
                evidence=_evidence(decision, classification),
                execution_authorized=False,
            )
        )

    step_tuple = tuple(steps)
    return CleanupPlan(
        plan_id=plan_id.strip(),
        source_scan_id=_source_scan_id(report),
        steps=step_tuple,
        requires_user_confirmation=any(
            step.requires_user_confirmation for step in step_tuple
        ),
        execution_level=READ_ONLY_EXECUTION_LEVEL,
        mode="plan_only",
        execution_authorized=False,
    )
