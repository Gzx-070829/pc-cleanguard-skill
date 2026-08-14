"""Decision-bound consent validation; Agents cannot authenticate themselves."""

from __future__ import annotations

from datetime import datetime

from .models import (
    ConfirmationLevel,
    ConsentGrant,
    ConsentValidation,
    Disposition,
    GuardDecision,
    Requirement,
)
from .normalize import canonical_json, parse_timestamp


_UNTRUSTED_SOURCES = {
    "agent",
    "ai",
    "self",
    "self_asserted",
    "request_payload",
    "natural_language",
}


def validate_consent(
    decision: GuardDecision,
    grant: ConsentGrant | None,
    now: str | datetime,
) -> ConsentValidation:
    """Validate exact binding; authenticity is supplied by a trusted host/UI."""

    if not isinstance(decision, GuardDecision):
        return ConsentValidation(False, ("decision must be a GuardDecision",))
    if decision.disposition is Disposition.BLOCK:
        return ConsentValidation(False, ("consent cannot override a BLOCK decision",))
    needs_standard = Requirement.USER_CONFIRMATION in decision.requirements
    needs_high = Requirement.EXPLICIT_HIGH_RISK_CONFIRMATION in decision.requirements
    if not needs_standard and not needs_high:
        return ConsentValidation(True, (), ())
    if not isinstance(grant, ConsentGrant):
        return ConsentValidation(False, ("a trusted ConsentGrant is required",))

    errors = []
    current = parse_timestamp(now)
    issued = parse_timestamp(grant.issued_at)
    expires = parse_timestamp(grant.expires_at)
    if issued > current:
        errors.append("consent has not been issued yet")
    if expires <= current:
        errors.append("consent is expired")
    if expires <= issued:
        errors.append("consent expiry must be after issuance")
    if grant.decision_id != decision.decision_id:
        errors.append("consent is bound to a different decision")
    if grant.action_fingerprint != decision.action_fingerprint:
        errors.append("consent action fingerprint does not match")
    if tuple(grant.allowed_targets) != tuple(decision.target_fingerprints):
        errors.append("consent target set or order does not match")
    if grant.allowed_effect != decision.requested_effect:
        errors.append("consent effect does not match")
    if canonical_json(grant.allowed_scope) != canonical_json(decision.scope_snapshot):
        errors.append("consent scope differs from the evaluated scope")
    if grant.confirmation_source.casefold() in _UNTRUSTED_SOURCES:
        errors.append("Agent/self-asserted consent is not a trusted confirmation source")
    required_level = ConfirmationLevel.HIGH_RISK if needs_high else ConfirmationLevel.STANDARD
    if grant.confirmation_level.rank < required_level.rank:
        errors.append("consent confirmation level is too low for this action")

    satisfied = []
    if not errors:
        if needs_standard:
            satisfied.append(Requirement.USER_CONFIRMATION.value)
        if needs_high:
            satisfied.extend(
                (
                    Requirement.EXPLICIT_HIGH_RISK_CONFIRMATION.value,
                    Requirement.ADMIN_ACKNOWLEDGEMENT.value,
                )
            )
    return ConsentValidation(not errors, tuple(errors), tuple(satisfied))

