"""Build non-executable plans from policy decisions.

PR2 plans are data-only review artifacts. This module performs no I/O and has
no execution layer.
"""

from __future__ import annotations

from .models import ClassificationLabel, PermissionLevel, PolicyDecision


_ACTIONS = {
    ClassificationLabel.KEEP: "REPORT_ONLY",
    ClassificationLabel.ASK_USER: "ASK_USER_CONFIRMATION",
    ClassificationLabel.SAFE_REMOVE: "PLAN_STANDARD_UNINSTALL",
    ClassificationLabel.STARTUP_OFF: "PLAN_DISABLE_STARTUP",
    ClassificationLabel.QUARANTINE: "PLAN_QUARANTINE",
    ClassificationLabel.BLOCK: "BLOCKED_BY_POLICY",
}

_ROLLBACK_METHODS = {
    ClassificationLabel.KEEP: None,
    ClassificationLabel.ASK_USER: None,
    ClassificationLabel.SAFE_REMOVE: "REVIEW_STANDARD_UNINSTALL_RECOVERY",
    ClassificationLabel.STARTUP_OFF: "RESTORE_STARTUP_CONFIGURATION",
    ClassificationLabel.QUARANTINE: "RESTORE_QUARANTINED_ITEM",
    ClassificationLabel.BLOCK: None,
}

_AUDIT_EVENT_TYPES = {
    ClassificationLabel.KEEP: "POLICY_REPORT_KEEP",
    ClassificationLabel.ASK_USER: "POLICY_REVIEW_REQUESTED",
    ClassificationLabel.SAFE_REMOVE: "POLICY_PLAN_STANDARD_UNINSTALL",
    ClassificationLabel.STARTUP_OFF: "POLICY_PLAN_DISABLE_STARTUP",
    ClassificationLabel.QUARANTINE: "POLICY_PLAN_QUARANTINE",
    ClassificationLabel.BLOCK: "POLICY_ACTION_BLOCKED",
}

_CONFIRMATION_LABELS = {
    ClassificationLabel.ASK_USER,
    ClassificationLabel.SAFE_REMOVE,
    ClassificationLabel.STARTUP_OFF,
    ClassificationLabel.QUARANTINE,
}


def _build_step(decision: PolicyDecision, index: int) -> dict:
    blocked = (
        decision.classification is ClassificationLabel.BLOCK
        or decision.permission_level is PermissionLevel.LEVEL_5_FORBIDDEN
    )
    confirmation_required = (
        decision.required_confirmation
        or decision.classification in _CONFIRMATION_LABELS
    )
    preconditions = [
        "POLICY_DECISION_PRESENT",
        "EVIDENCE_CHAIN_PRESENT",
        "AUDIT_PLAN_REQUIRED",
    ]
    if confirmation_required:
        preconditions.append("EXPLICIT_USER_CONFIRMATION_REQUIRED")
    if decision.rollback_required:
        preconditions.append("ROLLBACK_PLAN_REQUIRED")

    return {
        "step_id": f"step-{index:04d}",
        "action": _ACTIONS[decision.classification],
        "target_id": decision.target_id,
        "permission_level": decision.permission_level.value,
        "classification": decision.classification.value,
        "preconditions": preconditions,
        "confirmation_required": confirmation_required,
        "rollback_method": _ROLLBACK_METHODS[decision.classification],
        "audit_event_type": _AUDIT_EVENT_TYPES[decision.classification],
        "blocked": blocked,
        "reason": decision.reason,
    }


def build_execution_plan(decisions: list[PolicyDecision]) -> dict:
    """Organize decisions into reviewable steps without executing them."""

    if not isinstance(decisions, list):
        raise TypeError("decisions must be a list of PolicyDecision objects")
    if not all(isinstance(decision, PolicyDecision) for decision in decisions):
        raise TypeError("every decision must be a PolicyDecision")

    steps = []
    blocked_steps = []
    for index, decision in enumerate(decisions, start=1):
        step = _build_step(decision, index)
        if step["blocked"]:
            blocked_steps.append(step)
        else:
            steps.append(step)

    return {
        "mode": "report_only",
        "steps": steps,
        "blocked_steps": blocked_steps,
        "managed_mode_compatibility": False,
    }
