"""Validation for external rollback contracts and plans."""

from __future__ import annotations

from datetime import datetime

from .models import (
    GuardDecision,
    GuardRiskLevel,
    Requirement,
    RollbackContract,
    RollbackValidation,
)
from .normalize import parse_timestamp


def validate_rollback(
    decision: GuardDecision,
    rollback: RollbackContract | None,
    now: str | datetime,
) -> RollbackValidation:
    if not isinstance(decision, GuardDecision):
        return RollbackValidation(False, True, ("decision must be a GuardDecision",))
    required = decision.risk_level in {
        GuardRiskLevel.L2,
        GuardRiskLevel.L3,
        GuardRiskLevel.L4,
    }
    if not required:
        return RollbackValidation(True, False, (), ())
    if not isinstance(rollback, RollbackContract):
        return RollbackValidation(False, True, ("a bound rollback contract is required",))

    errors = []
    if rollback.decision_id != decision.decision_id:
        errors.append("rollback contract is bound to a different decision")
    if rollback.action_fingerprint != decision.action_fingerprint:
        errors.append("rollback action fingerprint does not match")
    if parse_timestamp(rollback.expires_at) <= parse_timestamp(now):
        errors.append("rollback contract is expired")
    if decision.risk_level in {GuardRiskLevel.L2, GuardRiskLevel.L4} and not rollback.reversible:
        errors.append("L2/L4 rollback contract must be reversible")
    if Requirement.BACKUP in decision.requirements:
        if not rollback.backup_required or not rollback.backup_reference:
            errors.append("high-risk action requires a referenced backup")

    satisfied = []
    if not errors:
        if Requirement.ROLLBACK_CONTRACT in decision.requirements:
            satisfied.append(Requirement.ROLLBACK_CONTRACT.value)
        if Requirement.ROLLBACK_PLAN in decision.requirements:
            satisfied.append(Requirement.ROLLBACK_PLAN.value)
        if Requirement.BACKUP in decision.requirements:
            satisfied.append(Requirement.BACKUP.value)
    return RollbackValidation(not errors, True, tuple(errors), tuple(satisfied))

