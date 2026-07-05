"""Build structured, non-destructive PC CleanGuard reports."""

from __future__ import annotations

from collections import Counter

from .execution_plan_builder import build_execution_plan
from .models import (
    ClassificationLabel,
    ObjectType,
    PolicyDecision,
    RiskLevel,
)


_RECOMMENDATIONS = {
    ClassificationLabel.KEEP: "Preserve the target and report it read-only.",
    ClassificationLabel.ASK_USER: "Ask the user for context and explicit confirmation.",
    ClassificationLabel.SAFE_REMOVE: "Review as a standard-uninstall candidate only.",
    ClassificationLabel.STARTUP_OFF: "Review as a reversible startup-disable candidate only.",
    ClassificationLabel.QUARANTINE: "Review as a reversible quarantine candidate only.",
    ClassificationLabel.BLOCK: "Do not proceed; the proposed action is blocked by policy.",
}

_WHY_NOT_MORE_AGGRESSIVE = {
    ClassificationLabel.KEEP: "The target is protected or should be preserved.",
    ClassificationLabel.ASK_USER: "Identity, intent, or evidence requires user review.",
    ClassificationLabel.SAFE_REMOVE: "The label is only a candidate and still requires confirmation and audit.",
    ClassificationLabel.STARTUP_OFF: "Only a future reversible plan is appropriate; PR2 changes nothing.",
    ClassificationLabel.QUARANTINE: "Isolation must remain reversible and PR2 moves no files.",
    ClassificationLabel.BLOCK: "BLOCK and Level 5 are absolute execution barriers.",
}

_POTENTIAL_IMPACTS = {
    ClassificationLabel.KEEP: "Modification could break a required or protected component.",
    ClassificationLabel.ASK_USER: "The impact is ambiguous until identity and user intent are confirmed.",
    ClassificationLabel.SAFE_REMOVE: "A future uninstall could remove software or dependent functionality.",
    ClassificationLabel.STARTUP_OFF: "A future startup change could alter expected login behavior.",
    ClassificationLabel.QUARANTINE: "A future isolation action could make a file temporarily unavailable.",
    ClassificationLabel.BLOCK: "The proposed action could damage protected system or user data.",
}

_CONFIRMATION_LABELS = {
    ClassificationLabel.ASK_USER,
    ClassificationLabel.SAFE_REMOVE,
    ClassificationLabel.STARTUP_OFF,
    ClassificationLabel.QUARANTINE,
}

_RISK_NOTES = [
    "PR2 does not execute cleanup.",
    "Policy decisions are not execution commands.",
    "SAFE_REMOVE is only a candidate label.",
    "BLOCK and Level 5 must never run.",
    "PR2 不执行清理；策略决策和计划都不是执行命令。",
]

_AUDIT_NOTES = [
    "This report is audit-ready but no audit event was written by PR2.",
    "Future execution must generate audit events.",
    "本报告已准备好审计字段，但 PR2 不写入审计事件。",
]


def _target_display(target_id: str) -> tuple[str, str]:
    prefix, separator, display_name = target_id.partition(":")
    known_types = {object_type.value for object_type in ObjectType}
    normalized_type = prefix.upper()
    if separator and normalized_type in known_types and display_name.strip():
        return normalized_type, display_name.strip()
    return "UNKNOWN", target_id


def _evidence_entries(decision: PolicyDecision) -> list[dict]:
    chain = decision.evidence_chain
    facts = chain.facts or (decision.reason,)
    sources = chain.sources or ("policy_decision",)
    entries = []
    for index, fact in enumerate(facts):
        source = sources[min(index, len(sources) - 1)]
        reference = chain.references[index] if index < len(chain.references) else None
        entries.append(
            {
                "source": source,
                "fact": fact,
                "reference": reference,
            }
        )
    return entries


def _finding(decision: PolicyDecision) -> dict:
    object_type, name = _target_display(decision.target_id)
    facts = decision.evidence_chain.facts or (decision.reason,)
    return {
        "target_id": decision.target_id,
        "object_type": object_type,
        "name": name,
        "publisher": None,
        "classification": decision.classification.value,
        "risk_level": decision.risk_level.value,
        "permission_level": decision.permission_level.value,
        "evidence_summary": list(facts),
        "potential_impact": _POTENTIAL_IMPACTS[decision.classification],
    }


def _recommendation(decision: PolicyDecision) -> dict:
    return {
        "target_id": decision.target_id,
        "classification": decision.classification.value,
        "risk_level": decision.risk_level.value,
        "recommendation": _RECOMMENDATIONS[decision.classification],
        "required_confirmation": (
            decision.required_confirmation
            or decision.classification in _CONFIRMATION_LABELS
        ),
        "rollback_available": decision.rollback_required,
        "why_not_more_aggressive": _WHY_NOT_MORE_AGGRESSIVE[
            decision.classification
        ],
        "evidence_chain": _evidence_entries(decision),
    }


def _summary(
    scan_id: str,
    platform: str,
    privacy_mode: str,
    decisions: list[PolicyDecision],
) -> dict:
    counts = Counter(decision.classification for decision in decisions)
    high_risk_findings = sum(
        decision.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
        for decision in decisions
    )
    return {
        "scan_id": scan_id,
        "platform": platform,
        "privacy_mode": privacy_mode,
        "total_findings": len(decisions),
        "keep_count": counts[ClassificationLabel.KEEP],
        "ask_user_count": counts[ClassificationLabel.ASK_USER],
        "safe_remove_count": counts[ClassificationLabel.SAFE_REMOVE],
        "startup_off_count": counts[ClassificationLabel.STARTUP_OFF],
        "quarantine_count": counts[ClassificationLabel.QUARANTINE],
        "block_count": counts[ClassificationLabel.BLOCK],
        "high_risk_findings": high_risk_findings,
        "ambiguous_items": counts[ClassificationLabel.ASK_USER],
        "destructive_actions_executed": False,
    }


def build_report(
    scan_id: str,
    platform: str,
    privacy_mode: str,
    decisions: list[PolicyDecision],
) -> dict:
    """Build an audit-ready report without reading or changing the system."""

    if not scan_id.strip():
        raise ValueError("scan_id must not be empty")
    if not platform.strip():
        raise ValueError("platform must not be empty")
    if not privacy_mode.strip():
        raise ValueError("privacy_mode must not be empty")
    if not isinstance(decisions, list):
        raise TypeError("decisions must be a list of PolicyDecision objects")
    if not all(isinstance(decision, PolicyDecision) for decision in decisions):
        raise TypeError("every decision must be a PolicyDecision")

    execution_plan = build_execution_plan(decisions)
    execution_plan = {
        "plan_id": f"plan:{scan_id}",
        "scan_id": scan_id,
        **execution_plan,
    }

    return {
        "summary": _summary(scan_id, platform, privacy_mode, decisions),
        "findings": [_finding(decision) for decision in decisions],
        "recommendations": [
            _recommendation(decision) for decision in decisions
        ],
        "execution_plan": execution_plan,
        "managed_mode_compatibility": {
            "status": "FUTURE_ONLY",
            "automatic_execution_allowed": False,
            "block_execution_allowed": False,
            "level_5_execution_allowed": False,
            "reason": "PR2 produces report-only plans and grants no execution authorization.",
        },
        "risk_notes": list(_RISK_NOTES),
        "audit_notes": list(_AUDIT_NOTES),
    }
