"""Five primary offline Skill actions for the v0.5 Guard boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ..guard import (
    ActionBundle,
    Disposition,
    ExecutionContract,
    Guard,
    GuardContext,
    GuardInputError,
    evaluate_bundle,
)
from ..guard.normalize import canonical_value, fingerprint


CORE_ACTION_NAMES = (
    "evaluate_action",
    "prepare_execution",
    "evaluate_action_bundle",
    "record_execution_result",
    "verify_audit",
)


@dataclass(frozen=True, slots=True)
class GuardSkillActionResponse:
    request_id: str
    action: str
    status: str
    requires_user_confirmation: bool
    execution_level: str
    evidence: tuple[dict, ...]
    result: dict
    execution_authorized: bool = False
    schema_version: str = "0.5"

    def __post_init__(self) -> None:
        if self.action not in CORE_ACTION_NAMES:
            raise GuardInputError("unsupported Guard Skill action")
        if self.status not in {"completed", "requirements_pending", "blocked"}:
            raise GuardInputError("unsupported Guard Skill action status")
        if self.execution_authorized is not False:
            raise GuardInputError("invoking a Skill action does not execute the contract")

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "action": self.action,
            "status": self.status,
            "requires_user_confirmation": self.requires_user_confirmation,
            "execution_level": self.execution_level,
            "evidence": [canonical_value(item) for item in self.evidence],
            "execution_authorized": False,
            "result": canonical_value(self.result),
        }


def _envelope(value: Mapping[str, Any]) -> tuple[str, str, dict]:
    if not isinstance(value, Mapping):
        raise GuardInputError("Guard Skill action request must be an object")
    allowed = {"schema_version", "request_id", "action", "payload"}
    unexpected = set(value) - allowed
    if unexpected:
        raise GuardInputError(f"unexpected Guard Skill action fields: {sorted(unexpected)}")
    action = value.get("action")
    if action not in CORE_ACTION_NAMES:
        raise GuardInputError("unsupported Guard Skill action")
    payload = value.get("payload")
    if not isinstance(payload, dict):
        raise GuardInputError("Guard Skill action payload must be an object")
    schema_version = value.get("schema_version", "0.5")
    if schema_version != "0.5":
        raise GuardInputError("unsupported Guard Skill action schema version")
    request_id = value.get("request_id")
    if request_id is None:
        request_id = "guard-action:" + fingerprint(
            "pc-cleanguard/guard-skill-action/v0.5", {"action": action, "payload": payload}
        )[:24]
    if not isinstance(request_id, str) or not request_id.strip():
        raise GuardInputError("request_id must be non-empty")
    return request_id, action, payload


def _exact_payload(payload: dict, required: set[str], optional: set[str] = set()) -> None:
    missing = required - set(payload)
    unexpected = set(payload) - required - optional
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing={sorted(missing)}")
        if unexpected:
            details.append(f"unexpected={sorted(unexpected)}")
        raise GuardInputError("invalid Guard Skill payload: " + "; ".join(details))


def _response(
    *,
    request_id: str,
    action: str,
    result: dict,
    status: str = "completed",
    requires_confirmation: bool = False,
    execution_level: str = "L0",
) -> GuardSkillActionResponse:
    return GuardSkillActionResponse(
        request_id=request_id,
        action=action,
        status=status,
        requires_user_confirmation=requires_confirmation,
        execution_level=execution_level,
        evidence=(
            {
                "source": "pc_cleanguard.guard",
                "fact": "deterministic offline governance; no operation was executed",
            },
        ),
        result=result,
        execution_authorized=False,
    )


def invoke_guard_action(value: Mapping[str, Any]) -> GuardSkillActionResponse:
    request_id, action, payload = _envelope(value)

    if action == "evaluate_action":
        _exact_payload(payload, {"request", "context"})
        decision = Guard().evaluate(payload["request"], payload["context"])
        status = (
            "blocked"
            if decision.disposition is Disposition.BLOCK
            else "requirements_pending"
            if decision.disposition is Disposition.REQUIRE
            else "completed"
        )
        return _response(
            request_id=request_id,
            action=action,
            result=decision.to_dict(),
            status=status,
            requires_confirmation=decision.disposition is Disposition.REQUIRE,
            execution_level=decision.risk_level.value,
        )

    if action == "prepare_execution":
        _exact_payload(
            payload,
            {"decision", "context"},
            {"consent", "rollback", "now"},
        )
        contract = Guard().prepare_execution(
            decision=payload["decision"],
            consent=payload.get("consent"),
            rollback=payload.get("rollback"),
            current_context=payload["context"],
            now=payload.get("now"),
        )
        return _response(
            request_id=request_id,
            action=action,
            result=contract.to_dict(),
            execution_level="CONTRACT",
        )

    if action == "evaluate_action_bundle":
        _exact_payload(payload, {"bundle", "context"})
        result = evaluate_bundle(
            ActionBundle.from_dict(payload["bundle"]),
            GuardContext.from_dict(payload["context"]),
        )
        status = (
            "blocked"
            if result.disposition is Disposition.BLOCK
            else "requirements_pending"
            if result.disposition is Disposition.REQUIRE
            else "completed"
        )
        return _response(
            request_id=request_id,
            action=action,
            result=result.to_dict(),
            status=status,
            requires_confirmation=result.disposition is Disposition.REQUIRE,
            execution_level=result.risk_level.value,
        )

    if action == "record_execution_result":
        _exact_payload(
            payload,
            {"contract", "result", "request_id", "audit_path"},
            {"now"},
        )
        guard = Guard(audit_path=Path(payload["audit_path"]))
        event = guard.record_execution_result(
            contract=ExecutionContract.from_dict(payload["contract"]),
            result=payload["result"],
            request_id=payload["request_id"],
            now=payload.get("now"),
        )
        return _response(
            request_id=request_id,
            action=action,
            result=event.to_dict(),
            execution_level="RECEIPT",
        )

    if action == "verify_audit":
        _exact_payload(payload, {"path"})
        verification = Guard().verify_audit(Path(payload["path"]))
        return _response(
            request_id=request_id,
            action=action,
            result=verification.to_dict(),
            status="completed" if verification.valid else "blocked",
            execution_level="L0",
        )

    raise GuardInputError("unsupported Guard Skill action")  # pragma: no cover

