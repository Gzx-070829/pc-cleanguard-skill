"""Four-operation facade for deterministic Windows action governance."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

from .audit import (
    GENESIS_HASH,
    AuditEvent,
    AuditEventType,
    AuditVerification,
    append_event,
    create_event,
    verify_audit_chain,
)
from .consent import validate_consent
from .errors import (
    ConsentValidationError,
    GuardInputError,
    PolicyBlockedError,
    PreconditionValidationError,
    RequirementPendingError,
    RollbackValidationError,
)
from .models import (
    ActionRequest,
    ConsentGrant,
    Disposition,
    ExecutionContract,
    GuardContext,
    GuardDecision,
    Requirement,
    RollbackContract,
    execution_contract_fingerprint_for,
)
from .normalize import format_timestamp, parse_timestamp, utc_now
from .policy import evaluate as evaluate_policy
from .preconditions import validate_preconditions
from .rollback import validate_rollback


class Guard:
    """Thin policy/consent/precondition/audit/rollback contract boundary."""

    def __init__(
        self,
        *,
        policy: dict | str | Path | None = None,
        audit_path: str | Path | None = None,
    ) -> None:
        self._policy = policy
        self._audit_path = audit_path
        self._events: list[AuditEvent] = []

    @property
    def audit_events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def _record(
        self,
        event_type: AuditEventType,
        *,
        request_id: str,
        decision_id: str | None,
        payload: dict,
        timestamp: str | None = None,
    ) -> AuditEvent:
        if self._audit_path is not None:
            event = append_event(
                self._audit_path,
                event_type=event_type,
                request_id=request_id,
                decision_id=decision_id,
                payload=payload,
                timestamp=timestamp,
            )
        else:
            previous = self._events[-1].event_hash if self._events else GENESIS_HASH
            event = create_event(
                event_type=event_type,
                request_id=request_id,
                decision_id=decision_id,
                payload=payload,
                previous_event_hash=previous,
                timestamp=timestamp,
            )
        self._events.append(event)
        return event

    def evaluate(
        self,
        request: ActionRequest | Mapping[str, Any],
        context: GuardContext | Mapping[str, Any],
    ) -> GuardDecision:
        if not isinstance(request, ActionRequest):
            request = ActionRequest.from_dict(request)
        if not isinstance(context, GuardContext):
            context = GuardContext.from_dict(context)
        decision = evaluate_policy(request, context, self._policy)
        self._record(
            AuditEventType.REQUEST_RECEIVED,
            request_id=request.request_id,
            decision_id=None,
            payload={
                "action_type": request.action_type,
                "action_fingerprint": request.action_fingerprint,
                "target_count": len(request.targets),
                "dry_run": request.dry_run,
            },
            timestamp=request.requested_at,
        )
        self._record(
            AuditEventType.DECISION_ISSUED,
            request_id=request.request_id,
            decision_id=decision.decision_id,
            payload={
                "disposition": decision.disposition.value,
                "risk_level": decision.risk_level.value,
                "requirements": [item.value for item in decision.requirements],
                "decision_fingerprint": decision.decision_fingerprint,
                "execution_authorized": False,
            },
            timestamp=decision.generated_at,
        )
        return decision

    def prepare_execution(
        self,
        *,
        decision: GuardDecision | Mapping[str, Any],
        consent: ConsentGrant | Mapping[str, Any] | None,
        rollback: RollbackContract | Mapping[str, Any] | None,
        current_context: GuardContext | Mapping[str, Any],
        now: str | datetime | None = None,
    ) -> ExecutionContract:
        if not isinstance(decision, GuardDecision):
            decision = GuardDecision.from_dict(decision)
        if consent is not None and not isinstance(consent, ConsentGrant):
            consent = ConsentGrant.from_dict(consent)
        if rollback is not None and not isinstance(rollback, RollbackContract):
            rollback = RollbackContract.from_dict(rollback)
        if not isinstance(current_context, GuardContext):
            current_context = GuardContext.from_dict(current_context)
        current = parse_timestamp(now or utc_now())

        if decision.disposition is Disposition.BLOCK:
            raise PolicyBlockedError("blocked decisions can never produce an execution contract")

        consent_result = validate_consent(decision, consent, current)
        if not consent_result.valid:
            raise ConsentValidationError("; ".join(consent_result.errors))
        if consent is not None:
            self._record(
                AuditEventType.CONSENT_RECORDED,
                request_id=decision.request_id,
                decision_id=decision.decision_id,
                payload={
                    "consent_id": consent.consent_id,
                    "confirmation_level": consent.confirmation_level.value,
                    "confirmation_source": consent.confirmation_source,
                },
                timestamp=format_timestamp(current),
            )

        preconditions_result = validate_preconditions(decision, current_context)
        self._record(
            AuditEventType.PRECONDITION_CHECKED,
            request_id=decision.request_id,
            decision_id=decision.decision_id,
            payload=preconditions_result.to_dict(),
            timestamp=format_timestamp(current),
        )
        if not preconditions_result.valid:
            raise PreconditionValidationError("; ".join(preconditions_result.errors))

        rollback_result = validate_rollback(decision, rollback, current)
        if not rollback_result.valid:
            raise RollbackValidationError("; ".join(rollback_result.errors))

        satisfied = set(consent_result.requirements_satisfied)
        satisfied.update(rollback_result.requirements_satisfied)
        if Requirement.TARGET_REVALIDATION in decision.requirements:
            satisfied.add(Requirement.TARGET_REVALIDATION.value)
        if Requirement.AUDIT in decision.requirements:
            satisfied.add(Requirement.AUDIT.value)
        # This requirement is carried as a binding executor obligation. Reporting a
        # result without a postcondition receipt is detectable by the audit chain.
        if Requirement.POSTCONDITION_VERIFY in decision.requirements:
            satisfied.add(Requirement.POSTCONDITION_VERIFY.value)

        required = {item.value for item in decision.requirements}
        pending = sorted(required - satisfied)
        if pending:
            raise RequirementPendingError(
                "requirements remain pending: " + ", ".join(pending)
            )

        expiry_candidates = [current + timedelta(minutes=5)]
        if consent is not None:
            expiry_candidates.append(parse_timestamp(consent.expires_at))
        if rollback is not None:
            expiry_candidates.append(parse_timestamp(rollback.expires_at))
        expires = min(expiry_candidates)
        if expires <= current:
            raise RequirementPendingError("execution contract would already be expired")

        material = {
            "decision_id": decision.decision_id,
            "action_fingerprint": decision.action_fingerprint,
            "authorized_targets": list(decision.target_fingerprints),
            "authorized_effect": decision.requested_effect,
            "requirements_satisfied": sorted(satisfied),
            "preconditions_snapshot": preconditions_result.snapshot,
            "expires_at": format_timestamp(expires),
            "rollback_id": rollback.rollback_id if rollback is not None else None,
        }
        contract_fingerprint = execution_contract_fingerprint_for(**material)
        contract = ExecutionContract(
            contract_id=f"contract:{contract_fingerprint[:24]}",
            decision_id=decision.decision_id,
            action_fingerprint=decision.action_fingerprint,
            authorized_targets=decision.target_fingerprints,
            authorized_effect=decision.requested_effect,
            requirements_satisfied=tuple(sorted(satisfied)),
            preconditions_snapshot=preconditions_result.snapshot,
            expires_at=format_timestamp(expires),
            execution_authorized=True,
            rollback_id=rollback.rollback_id if rollback is not None else None,
        )
        self._record(
            AuditEventType.EXECUTION_CONTRACT_ISSUED,
            request_id=decision.request_id,
            decision_id=decision.decision_id,
            payload={
                "contract_id": contract.contract_id,
                "action_fingerprint": contract.action_fingerprint,
                "expires_at": contract.expires_at,
                "execution_authorized": True,
            },
            timestamp=format_timestamp(current),
        )
        return contract

    def record_execution_result(
        self,
        *,
        contract: ExecutionContract | Mapping[str, Any],
        result: Mapping[str, Any],
        request_id: str,
        now: str | datetime | None = None,
    ) -> AuditEvent:
        if not isinstance(contract, ExecutionContract):
            contract = ExecutionContract.from_dict(contract)
        if not isinstance(result, Mapping):
            raise GuardInputError("execution result must be an object")
        if not isinstance(request_id, str) or not request_id.strip():
            raise GuardInputError("request_id must be non-empty")
        current = parse_timestamp(now or utc_now())
        if parse_timestamp(contract.expires_at) <= current:
            raise RequirementPendingError("stale execution contract cannot accept a result")
        payload = {
            "contract_id": contract.contract_id,
            "action_fingerprint": contract.action_fingerprint,
            "result": dict(result),
        }
        event = self._record(
            AuditEventType.EXECUTION_REPORTED,
            request_id=request_id,
            decision_id=contract.decision_id,
            payload=payload,
            timestamp=format_timestamp(current),
        )
        if result.get("postcondition_verified") is True:
            self._record(
                AuditEventType.POSTCONDITION_VERIFIED,
                request_id=request_id,
                decision_id=contract.decision_id,
                payload={
                    "contract_id": contract.contract_id,
                    "verified": True,
                    "details": result.get("postcondition_details", {}),
                },
                timestamp=format_timestamp(current),
            )
        return event

    def verify_audit(self, path: str | Path | None = None) -> AuditVerification:
        source = path if path is not None else self._audit_path
        if source is None:
            return AuditVerification(
                False,
                len(self._events),
                ("no persisted audit path was supplied",),
                self._events[-1].event_hash if self._events else None,
            )
        return verify_audit_chain(source)


def build_execution_contract(
    *,
    decision: GuardDecision | Mapping[str, Any],
    consent: ConsentGrant | Mapping[str, Any] | None,
    rollback: RollbackContract | Mapping[str, Any] | None,
    current_context: GuardContext | Mapping[str, Any],
    now: str | datetime | None = None,
) -> ExecutionContract:
    """Functional facade for hosts that do not need a stateful Guard instance."""

    return Guard().prepare_execution(
        decision=decision,
        consent=consent,
        rollback=rollback,
        current_context=current_context,
        now=now,
    )
