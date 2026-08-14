"""Stable, JSON-friendly contracts for the v0.5 deterministic Guard Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from .errors import GuardInputError
from .normalize import (
    canonical_value,
    fingerprint,
    format_timestamp,
    json_object,
    normalized_windows_path,
)


def _text(value: Any, name: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise GuardInputError(f"{name} must be a non-empty string")
    return value.strip()


def _bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise GuardInputError(f"{name} must be a bool")
    return value


def _enum(enum_type, value, name):
    try:
        return value if isinstance(value, enum_type) else enum_type(value)
    except (TypeError, ValueError) as error:
        raise GuardInputError(f"invalid {name}: {value!r}") from error


def _reject_unknown(data: Mapping[str, Any], allowed: set[str], name: str) -> None:
    unexpected = set(data) - allowed
    if unexpected:
        raise GuardInputError(f"unexpected {name} fields: {sorted(unexpected)}")


def _string_tuple(value: Any, name: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise GuardInputError(f"{name} must be an array of strings")
    items = tuple(_text(item, f"{name} item") for item in value)
    if not allow_empty and not items:
        raise GuardInputError(f"{name} must not be empty")
    if len(set(items)) != len(items):
        raise GuardInputError(f"{name} must not contain duplicates")
    return items


class Disposition(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE = "REQUIRE"
    BLOCK = "BLOCK"

    @property
    def rank(self) -> int:
        return {self.ALLOW: 0, self.REQUIRE: 1, self.BLOCK: 2}[self]


class GuardRiskLevel(str, Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"

    @property
    def rank(self) -> int:
        return int(self.value[1:])


RiskLevel = GuardRiskLevel


class Requirement(str, Enum):
    USER_CONFIRMATION = "USER_CONFIRMATION"
    BACKUP = "BACKUP"
    ROLLBACK_CONTRACT = "ROLLBACK_CONTRACT"
    ROLLBACK_PLAN = "ROLLBACK_PLAN"
    TARGET_REVALIDATION = "TARGET_REVALIDATION"
    POSTCONDITION_VERIFY = "POSTCONDITION_VERIFY"
    ADMIN_ACKNOWLEDGEMENT = "ADMIN_ACKNOWLEDGEMENT"
    AUDIT = "AUDIT"
    EXPLICIT_HIGH_RISK_CONFIRMATION = "EXPLICIT_HIGH_RISK_CONFIRMATION"


class PreconditionName(str, Enum):
    TARGET_EXISTS = "TARGET_EXISTS"
    TARGET_TYPE_MATCH = "TARGET_TYPE_MATCH"
    HASH_MATCH = "HASH_MATCH"
    SIZE_MATCH = "SIZE_MATCH"
    MTIME_MATCH = "MTIME_MATCH"
    PATH_SCOPE_MATCH = "PATH_SCOPE_MATCH"
    NOT_REPARSE_POINT = "NOT_REPARSE_POINT"
    NOT_PROTECTED = "NOT_PROTECTED"
    BACKUP_PRESENT = "BACKUP_PRESENT"
    ROLLBACK_READY = "ROLLBACK_READY"


class ConfirmationLevel(str, Enum):
    STANDARD = "STANDARD"
    HIGH_RISK = "HIGH_RISK"

    @property
    def rank(self) -> int:
        return 1 if self is self.STANDARD else 2


class AuditEventType(str, Enum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    DECISION_ISSUED = "DECISION_ISSUED"
    CONSENT_RECORDED = "CONSENT_RECORDED"
    PRECONDITION_CHECKED = "PRECONDITION_CHECKED"
    EXECUTION_CONTRACT_ISSUED = "EXECUTION_CONTRACT_ISSUED"
    EXECUTION_REPORTED = "EXECUTION_REPORTED"
    POSTCONDITION_VERIFIED = "POSTCONDITION_VERIFIED"
    ROLLBACK_REQUESTED = "ROLLBACK_REQUESTED"
    ROLLBACK_REPORTED = "ROLLBACK_REPORTED"


def decision_fingerprint_for(
    *,
    request_id: str,
    action_fingerprint: str,
    target_fingerprints: Sequence[str],
    requested_effect: str,
    scope_snapshot: dict,
    preconditions_snapshot: dict,
    policy_version: str,
    disposition: Disposition | str,
    risk_level: GuardRiskLevel | str,
    requirements: Sequence[Requirement | str],
    matched_rules: Sequence[str],
    blocked_reasons: Sequence[str],
    generated_at: str,
) -> str:
    disposition_value = disposition.value if isinstance(disposition, Disposition) else disposition
    risk_value = risk_level.value if isinstance(risk_level, GuardRiskLevel) else risk_level
    requirement_values = sorted(
        item.value if isinstance(item, Requirement) else item for item in requirements
    )
    return fingerprint(
        "pc-cleanguard/decision/v0.5",
        {
            "request_id": request_id,
            "action_fingerprint": action_fingerprint,
            "target_fingerprints": list(target_fingerprints),
            "requested_effect": requested_effect,
            "scope_snapshot": scope_snapshot,
            "preconditions_snapshot": preconditions_snapshot,
            "policy_version": policy_version,
            "disposition": disposition_value,
            "risk_level": risk_value,
            "requirements": requirement_values,
            "matched_rules": list(matched_rules),
            "blocked_reasons": list(blocked_reasons),
            "generated_at": format_timestamp(generated_at),
        },
    )


def execution_contract_fingerprint_for(
    *,
    decision_id: str,
    action_fingerprint: str,
    authorized_targets: Sequence[str],
    authorized_effect: str,
    requirements_satisfied: Sequence[str],
    preconditions_snapshot: dict,
    expires_at: str,
    rollback_id: str | None,
) -> str:
    return fingerprint(
        "pc-cleanguard/execution-contract/v0.5",
        {
            "decision_id": decision_id,
            "action_fingerprint": action_fingerprint,
            "authorized_targets": list(authorized_targets),
            "authorized_effect": authorized_effect,
            "requirements_satisfied": sorted(requirements_satisfied),
            "preconditions_snapshot": preconditions_snapshot,
            "expires_at": format_timestamp(expires_at),
            "rollback_id": rollback_id,
        },
    )


@dataclass(frozen=True, slots=True)
class ActionTarget:
    target_type: str
    identifier: str
    path: str | None = None
    metadata: dict = field(default_factory=dict)
    observed_state: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_type", _text(self.target_type, "target_type"))
        object.__setattr__(self, "identifier", _text(self.identifier, "identifier"))
        if self.path is not None:
            object.__setattr__(self, "path", normalized_windows_path(self.path))
        object.__setattr__(self, "metadata", json_object(self.metadata, name="metadata"))
        object.__setattr__(
            self, "observed_state", json_object(self.observed_state, name="observed_state")
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ActionTarget":
        if not isinstance(data, Mapping):
            raise GuardInputError("action target must be an object")
        allowed = {"target_type", "identifier", "path", "metadata", "observed_state"}
        if set(data) - allowed:
            raise GuardInputError("unexpected action target fields")
        return cls(
            target_type=data.get("target_type"),
            identifier=data.get("identifier"),
            path=data.get("path"),
            metadata=dict(data.get("metadata", {})),
            observed_state=dict(data.get("observed_state", {})),
        )

    def to_dict(self) -> dict:
        return {
            "target_type": self.target_type,
            "identifier": self.identifier,
            "path": self.path,
            "metadata": canonical_value(self.metadata),
            "observed_state": canonical_value(self.observed_state),
        }

    @property
    def target_fingerprint(self) -> str:
        return fingerprint("pc-cleanguard/target/v0.5", self.to_dict())


@dataclass(frozen=True, slots=True)
class RiskSignal:
    source: str
    signal_type: str
    severity: GuardRiskLevel | str
    reason: str
    requirements: tuple[Requirement | str, ...] = ()
    block: bool = False
    trusted: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _text(self.source, "signal source"))
        object.__setattr__(self, "signal_type", _text(self.signal_type, "signal_type"))
        object.__setattr__(self, "severity", _enum(GuardRiskLevel, self.severity, "severity"))
        object.__setattr__(self, "reason", _text(self.reason, "signal reason"))
        object.__setattr__(
            self,
            "requirements",
            tuple(_enum(Requirement, item, "signal requirement") for item in self.requirements),
        )
        _bool(self.block, "block")
        _bool(self.trusted, "trusted")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RiskSignal":
        if not isinstance(data, Mapping):
            raise GuardInputError("risk signal must be an object")
        _reject_unknown(
            data,
            {"source", "signal_type", "severity", "reason", "requirements", "block", "trusted", "execution_authorized"},
            "risk signal",
        )
        if data.get("execution_authorized", False) is not False:
            raise GuardInputError("risk signals cannot authorize execution")
        return cls(
            source=data.get("source"),
            signal_type=data.get("signal_type"),
            severity=data.get("severity"),
            reason=data.get("reason"),
            requirements=tuple(data.get("requirements", ())),
            block=data.get("block", False),
            trusted=data.get("trusted", False),
        )

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "signal_type": self.signal_type,
            "severity": self.severity.value,
            "reason": self.reason,
            "requirements": [item.value for item in self.requirements],
            "block": self.block,
            "trusted": self.trusted,
            "execution_authorized": False,
        }


@dataclass(frozen=True, slots=True)
class ActionRequest:
    request_id: str
    action_type: str
    targets: tuple[ActionTarget, ...]
    parameters: dict
    requested_effect: str
    requested_at: str
    agent_id: str
    agent_reason: str = ""
    evidence_refs: tuple[Any, ...] = ()
    dry_run: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", _text(self.request_id, "request_id"))
        object.__setattr__(self, "action_type", _text(self.action_type, "action_type"))
        targets = tuple(
            item if isinstance(item, ActionTarget) else ActionTarget.from_dict(item)
            for item in self.targets
        )
        if not targets:
            raise GuardInputError("targets must contain at least one target")
        if len({item.target_fingerprint for item in targets}) != len(targets):
            raise GuardInputError("targets must not contain duplicates")
        object.__setattr__(self, "targets", targets)
        object.__setattr__(self, "parameters", json_object(self.parameters, name="parameters"))
        object.__setattr__(self, "requested_effect", _text(self.requested_effect, "requested_effect"))
        object.__setattr__(self, "requested_at", format_timestamp(self.requested_at))
        object.__setattr__(self, "agent_id", _text(self.agent_id, "agent_id"))
        if not isinstance(self.agent_reason, str):
            raise GuardInputError("agent_reason must be a string")
        object.__setattr__(self, "agent_reason", self.agent_reason.strip())
        object.__setattr__(self, "evidence_refs", tuple(canonical_value(self.evidence_refs)))
        _bool(self.dry_run, "dry_run")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ActionRequest":
        if not isinstance(data, Mapping):
            raise GuardInputError("action request must be an object")
        allowed = {
            "request_id", "action_type", "targets", "parameters", "requested_effect",
            "requested_at", "agent_id", "agent_reason", "evidence_refs", "dry_run",
        }
        unexpected = set(data) - allowed
        if unexpected:
            raise GuardInputError(f"unexpected action request fields: {sorted(unexpected)}")
        return cls(
            request_id=data.get("request_id"),
            action_type=data.get("action_type"),
            targets=tuple(data.get("targets", ())),
            parameters=dict(data.get("parameters", {})),
            requested_effect=data.get("requested_effect"),
            requested_at=data.get("requested_at"),
            agent_id=data.get("agent_id"),
            agent_reason=data.get("agent_reason", ""),
            evidence_refs=tuple(data.get("evidence_refs", ())),
            dry_run=data.get("dry_run", False),
        )

    def action_material(self) -> dict:
        """Authorization material deliberately excludes prose and evidence claims."""

        return {
            "action_type": self.action_type,
            "targets": [item.to_dict() for item in self.targets],
            "parameters": self.parameters,
            "requested_effect": self.requested_effect,
            "dry_run": self.dry_run,
        }

    @property
    def action_fingerprint(self) -> str:
        return fingerprint("pc-cleanguard/action/v0.5", self.action_material())

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "action_type": self.action_type,
            "targets": [item.to_dict() for item in self.targets],
            "parameters": canonical_value(self.parameters),
            "requested_effect": self.requested_effect,
            "requested_at": self.requested_at,
            "agent_id": self.agent_id,
            "agent_reason": self.agent_reason,
            "evidence_refs": canonical_value(self.evidence_refs),
            "dry_run": self.dry_run,
        }


@dataclass(frozen=True, slots=True)
class GuardContext:
    platform: str
    scope: dict
    target_facts: dict
    protected_status: dict
    developer_status: dict
    system_status: dict
    user_policy: dict
    preconditions: dict
    risk_signals: tuple[RiskSignal, ...] = ()

    def __post_init__(self) -> None:
        platform = _text(self.platform, "platform").casefold()
        if platform != "windows":
            raise GuardInputError("v0.5 Guard supports platform=windows only")
        object.__setattr__(self, "platform", platform)
        for name in (
            "scope", "target_facts", "protected_status", "developer_status",
            "system_status", "user_policy", "preconditions",
        ):
            object.__setattr__(self, name, json_object(getattr(self, name), name=name))
        object.__setattr__(
            self,
            "risk_signals",
            tuple(
                item if isinstance(item, RiskSignal) else RiskSignal.from_dict(item)
                for item in self.risk_signals
            ),
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GuardContext":
        if not isinstance(data, Mapping):
            raise GuardInputError("guard context must be an object")
        allowed = {
            "platform", "scope", "target_facts", "protected_status", "developer_status",
            "system_status", "user_policy", "preconditions", "risk_signals",
        }
        unexpected = set(data) - allowed
        if unexpected:
            raise GuardInputError(f"unexpected guard context fields: {sorted(unexpected)}")
        return cls(
            platform=data.get("platform"),
            scope=dict(data.get("scope", {})),
            target_facts=dict(data.get("target_facts", {})),
            protected_status=dict(data.get("protected_status", {})),
            developer_status=dict(data.get("developer_status", {})),
            system_status=dict(data.get("system_status", {})),
            user_policy=dict(data.get("user_policy", {})),
            preconditions=dict(data.get("preconditions", {})),
            risk_signals=tuple(data.get("risk_signals", ())),
        )

    @property
    def scope_fingerprint(self) -> str:
        return fingerprint("pc-cleanguard/scope/v0.5", self.scope)

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "scope": canonical_value(self.scope),
            "target_facts": canonical_value(self.target_facts),
            "protected_status": canonical_value(self.protected_status),
            "developer_status": canonical_value(self.developer_status),
            "system_status": canonical_value(self.system_status),
            "user_policy": canonical_value(self.user_policy),
            "preconditions": canonical_value(self.preconditions),
            "risk_signals": [item.to_dict() for item in self.risk_signals],
        }


@dataclass(frozen=True, slots=True)
class GuardDecision:
    decision_id: str
    request_id: str
    disposition: Disposition | str
    risk_level: GuardRiskLevel | str
    requirements: tuple[Requirement | str, ...]
    matched_rules: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    explanation: str
    decision_fingerprint: str
    execution_authorized: bool
    generated_at: str
    action_fingerprint: str
    target_fingerprints: tuple[str, ...]
    requested_effect: str
    scope_snapshot: dict
    preconditions_snapshot: dict
    policy_version: str = "windows-default/0.5"

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _text(self.decision_id, "decision_id"))
        object.__setattr__(self, "request_id", _text(self.request_id, "request_id"))
        object.__setattr__(self, "disposition", _enum(Disposition, self.disposition, "disposition"))
        object.__setattr__(self, "risk_level", _enum(GuardRiskLevel, self.risk_level, "risk_level"))
        requirements = tuple(
            _enum(Requirement, item, "requirement") for item in self.requirements
        )
        requirements = tuple(sorted(set(requirements), key=lambda item: item.value))
        object.__setattr__(self, "requirements", requirements)
        object.__setattr__(self, "matched_rules", _string_tuple(self.matched_rules, "matched_rules", allow_empty=False))
        object.__setattr__(self, "blocked_reasons", _string_tuple(self.blocked_reasons, "blocked_reasons"))
        object.__setattr__(self, "explanation", _text(self.explanation, "explanation"))
        for name in ("decision_fingerprint", "action_fingerprint"):
            value = _text(getattr(self, name), name)
            if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                raise GuardInputError(f"{name} must be a lowercase SHA-256 digest")
            object.__setattr__(self, name, value)
        if self.execution_authorized is not False:
            raise GuardInputError("a GuardDecision is never execution authorization")
        object.__setattr__(self, "generated_at", format_timestamp(self.generated_at))
        object.__setattr__(self, "target_fingerprints", _string_tuple(self.target_fingerprints, "target_fingerprints", allow_empty=False))
        object.__setattr__(self, "requested_effect", _text(self.requested_effect, "requested_effect"))
        object.__setattr__(self, "scope_snapshot", json_object(self.scope_snapshot, name="scope_snapshot"))
        object.__setattr__(self, "preconditions_snapshot", json_object(self.preconditions_snapshot, name="preconditions_snapshot"))
        object.__setattr__(self, "policy_version", _text(self.policy_version, "policy_version"))
        if self.disposition is Disposition.BLOCK and not self.blocked_reasons:
            raise GuardInputError("blocked decisions require blocked_reasons")
        if self.disposition is Disposition.ALLOW and self.risk_level is not GuardRiskLevel.L0:
            raise GuardInputError("only L0 decisions may be directly ALLOW")
        expected = decision_fingerprint_for(
            request_id=self.request_id,
            action_fingerprint=self.action_fingerprint,
            target_fingerprints=self.target_fingerprints,
            requested_effect=self.requested_effect,
            scope_snapshot=self.scope_snapshot,
            preconditions_snapshot=self.preconditions_snapshot,
            policy_version=self.policy_version,
            disposition=self.disposition,
            risk_level=self.risk_level,
            requirements=self.requirements,
            matched_rules=self.matched_rules,
            blocked_reasons=self.blocked_reasons,
            generated_at=self.generated_at,
        )
        if self.decision_fingerprint != expected:
            raise GuardInputError("GuardDecision fingerprint does not match its fields")
        if self.decision_id != f"decision:{expected[:24]}":
            raise GuardInputError("GuardDecision ID does not match its fingerprint")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GuardDecision":
        if not isinstance(data, Mapping):
            raise GuardInputError("guard decision must be an object")
        _reject_unknown(
            data,
            {
                "decision_id", "request_id", "disposition", "risk_level", "requirements",
                "matched_rules", "blocked_reasons", "explanation", "decision_fingerprint",
                "execution_authorized", "generated_at", "action_fingerprint",
                "target_fingerprints", "requested_effect", "scope_snapshot",
                "preconditions_snapshot", "policy_version",
            },
            "guard decision",
        )
        return cls(
            decision_id=data.get("decision_id"),
            request_id=data.get("request_id"),
            disposition=data.get("disposition"),
            risk_level=data.get("risk_level"),
            requirements=tuple(data.get("requirements", ())),
            matched_rules=tuple(data.get("matched_rules", ())),
            blocked_reasons=tuple(data.get("blocked_reasons", ())),
            explanation=data.get("explanation"),
            decision_fingerprint=data.get("decision_fingerprint"),
            execution_authorized=data.get("execution_authorized", False),
            generated_at=data.get("generated_at"),
            action_fingerprint=data.get("action_fingerprint"),
            target_fingerprints=tuple(data.get("target_fingerprints", ())),
            requested_effect=data.get("requested_effect"),
            scope_snapshot=dict(data.get("scope_snapshot", {})),
            preconditions_snapshot=dict(data.get("preconditions_snapshot", {})),
            policy_version=data.get("policy_version", "windows-default/0.5"),
        )

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "disposition": self.disposition.value,
            "risk_level": self.risk_level.value,
            "requirements": [item.value for item in self.requirements],
            "matched_rules": list(self.matched_rules),
            "blocked_reasons": list(self.blocked_reasons),
            "explanation": self.explanation,
            "decision_fingerprint": self.decision_fingerprint,
            "execution_authorized": False,
            "generated_at": self.generated_at,
            "action_fingerprint": self.action_fingerprint,
            "target_fingerprints": list(self.target_fingerprints),
            "requested_effect": self.requested_effect,
            "scope_snapshot": canonical_value(self.scope_snapshot),
            "preconditions_snapshot": canonical_value(self.preconditions_snapshot),
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True, slots=True)
class ConsentGrant:
    consent_id: str
    decision_id: str
    action_fingerprint: str
    allowed_targets: tuple[str, ...]
    allowed_effect: str
    issued_at: str
    expires_at: str
    confirmation_level: ConfirmationLevel | str
    confirmation_source: str
    allowed_scope: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("consent_id", "decision_id", "action_fingerprint"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "allowed_targets", _string_tuple(self.allowed_targets, "allowed_targets", allow_empty=False))
        object.__setattr__(self, "allowed_effect", _text(self.allowed_effect, "allowed_effect"))
        object.__setattr__(self, "issued_at", format_timestamp(self.issued_at))
        object.__setattr__(self, "expires_at", format_timestamp(self.expires_at))
        object.__setattr__(self, "confirmation_level", _enum(ConfirmationLevel, self.confirmation_level, "confirmation_level"))
        object.__setattr__(self, "confirmation_source", _text(self.confirmation_source, "confirmation_source"))
        object.__setattr__(self, "allowed_scope", json_object(self.allowed_scope, name="allowed_scope"))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConsentGrant":
        if not isinstance(data, Mapping):
            raise GuardInputError("consent grant must be an object")
        _reject_unknown(
            data,
            {
                "consent_id", "decision_id", "action_fingerprint", "allowed_targets",
                "allowed_effect", "allowed_scope", "issued_at", "expires_at",
                "confirmation_level", "confirmation_source",
            },
            "consent grant",
        )
        return cls(
            consent_id=data.get("consent_id"),
            decision_id=data.get("decision_id"),
            action_fingerprint=data.get("action_fingerprint"),
            allowed_targets=tuple(data.get("allowed_targets", ())),
            allowed_effect=data.get("allowed_effect"),
            issued_at=data.get("issued_at"),
            expires_at=data.get("expires_at"),
            confirmation_level=data.get("confirmation_level"),
            confirmation_source=data.get("confirmation_source"),
            allowed_scope=dict(data.get("allowed_scope", {})),
        )

    def to_dict(self) -> dict:
        return {
            "consent_id": self.consent_id,
            "decision_id": self.decision_id,
            "action_fingerprint": self.action_fingerprint,
            "allowed_targets": list(self.allowed_targets),
            "allowed_effect": self.allowed_effect,
            "allowed_scope": canonical_value(self.allowed_scope),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "confirmation_level": self.confirmation_level.value,
            "confirmation_source": self.confirmation_source,
        }


@dataclass(frozen=True, slots=True)
class RollbackContract:
    rollback_id: str
    decision_id: str
    action_fingerprint: str
    reversible: bool
    backup_required: bool
    backup_reference: str | None
    rollback_steps: tuple[str, ...]
    verification_steps: tuple[str, ...]
    expires_at: str

    def __post_init__(self) -> None:
        for name in ("rollback_id", "decision_id", "action_fingerprint"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        _bool(self.reversible, "reversible")
        _bool(self.backup_required, "backup_required")
        object.__setattr__(self, "backup_reference", _text(self.backup_reference, "backup_reference", optional=True))
        if self.backup_required and self.backup_reference is None:
            raise GuardInputError("backup_required contracts need backup_reference")
        object.__setattr__(self, "rollback_steps", _string_tuple(self.rollback_steps, "rollback_steps", allow_empty=False))
        object.__setattr__(self, "verification_steps", _string_tuple(self.verification_steps, "verification_steps", allow_empty=False))
        object.__setattr__(self, "expires_at", format_timestamp(self.expires_at))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RollbackContract":
        if not isinstance(data, Mapping):
            raise GuardInputError("rollback contract must be an object")
        _reject_unknown(
            data,
            {
                "rollback_id", "decision_id", "action_fingerprint", "reversible",
                "backup_required", "backup_reference", "rollback_steps",
                "verification_steps", "expires_at",
            },
            "rollback contract",
        )
        return cls(
            rollback_id=data.get("rollback_id"),
            decision_id=data.get("decision_id"),
            action_fingerprint=data.get("action_fingerprint"),
            reversible=data.get("reversible"),
            backup_required=data.get("backup_required"),
            backup_reference=data.get("backup_reference"),
            rollback_steps=tuple(data.get("rollback_steps", ())),
            verification_steps=tuple(data.get("verification_steps", ())),
            expires_at=data.get("expires_at"),
        )

    def to_dict(self) -> dict:
        return {
            "rollback_id": self.rollback_id,
            "decision_id": self.decision_id,
            "action_fingerprint": self.action_fingerprint,
            "reversible": self.reversible,
            "backup_required": self.backup_required,
            "backup_reference": self.backup_reference,
            "rollback_steps": list(self.rollback_steps),
            "verification_steps": list(self.verification_steps),
            "expires_at": self.expires_at,
        }


@dataclass(frozen=True, slots=True)
class ExecutionContract:
    contract_id: str
    decision_id: str
    action_fingerprint: str
    authorized_targets: tuple[str, ...]
    authorized_effect: str
    requirements_satisfied: tuple[str, ...]
    preconditions_snapshot: dict
    expires_at: str
    execution_authorized: bool = True
    rollback_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("contract_id", "decision_id", "action_fingerprint"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "authorized_targets", _string_tuple(self.authorized_targets, "authorized_targets", allow_empty=False))
        object.__setattr__(self, "authorized_effect", _text(self.authorized_effect, "authorized_effect"))
        object.__setattr__(self, "requirements_satisfied", _string_tuple(self.requirements_satisfied, "requirements_satisfied"))
        object.__setattr__(self, "preconditions_snapshot", json_object(self.preconditions_snapshot, name="preconditions_snapshot"))
        object.__setattr__(self, "expires_at", format_timestamp(self.expires_at))
        if self.execution_authorized is not True:
            raise GuardInputError("ExecutionContract must represent completed authorization gates")
        object.__setattr__(self, "rollback_id", _text(self.rollback_id, "rollback_id", optional=True))
        expected = execution_contract_fingerprint_for(
            decision_id=self.decision_id,
            action_fingerprint=self.action_fingerprint,
            authorized_targets=self.authorized_targets,
            authorized_effect=self.authorized_effect,
            requirements_satisfied=self.requirements_satisfied,
            preconditions_snapshot=self.preconditions_snapshot,
            expires_at=self.expires_at,
            rollback_id=self.rollback_id,
        )
        if self.contract_id != f"contract:{expected[:24]}":
            raise GuardInputError("ExecutionContract ID does not match its fields")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionContract":
        if not isinstance(data, Mapping):
            raise GuardInputError("execution contract must be an object")
        _reject_unknown(
            data,
            {
                "contract_id", "decision_id", "action_fingerprint", "authorized_targets",
                "authorized_effect", "requirements_satisfied", "preconditions_snapshot",
                "expires_at", "execution_authorized", "rollback_id",
            },
            "execution contract",
        )
        return cls(
            contract_id=data.get("contract_id"),
            decision_id=data.get("decision_id"),
            action_fingerprint=data.get("action_fingerprint"),
            authorized_targets=tuple(data.get("authorized_targets", ())),
            authorized_effect=data.get("authorized_effect"),
            requirements_satisfied=tuple(data.get("requirements_satisfied", ())),
            preconditions_snapshot=dict(data.get("preconditions_snapshot", {})),
            expires_at=data.get("expires_at"),
            execution_authorized=data.get("execution_authorized", True),
            rollback_id=data.get("rollback_id"),
        )

    def to_dict(self) -> dict:
        return {
            "contract_id": self.contract_id,
            "decision_id": self.decision_id,
            "action_fingerprint": self.action_fingerprint,
            "authorized_targets": list(self.authorized_targets),
            "authorized_effect": self.authorized_effect,
            "requirements_satisfied": list(self.requirements_satisfied),
            "preconditions_snapshot": canonical_value(self.preconditions_snapshot),
            "expires_at": self.expires_at,
            "execution_authorized": True,
            "rollback_id": self.rollback_id,
        }


@runtime_checkable
class ExecutorProtocol(Protocol):
    """External executor boundary; the Guard provides no implementation."""

    def execute(self, contract: ExecutionContract) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True, slots=True)
class ActionBundle:
    bundle_id: str
    actions: tuple[ActionRequest, ...]
    dependency_order: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "bundle_id", _text(self.bundle_id, "bundle_id"))
        actions = tuple(
            item if isinstance(item, ActionRequest) else ActionRequest.from_dict(item)
            for item in self.actions
        )
        if not actions:
            raise GuardInputError("action bundle must contain actions")
        identifiers = tuple(item.request_id for item in actions)
        if len(set(identifiers)) != len(identifiers):
            raise GuardInputError("bundle action request IDs must be unique")
        object.__setattr__(self, "actions", actions)
        order = _string_tuple(self.dependency_order, "dependency_order", allow_empty=False)
        if set(order) != set(identifiers) or len(order) != len(identifiers):
            raise GuardInputError("dependency_order must contain every action exactly once")
        object.__setattr__(self, "dependency_order", order)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ActionBundle":
        if not isinstance(data, Mapping):
            raise GuardInputError("action bundle must be an object")
        _reject_unknown(data, {"bundle_id", "actions", "dependency_order"}, "action bundle")
        return cls(
            bundle_id=data.get("bundle_id"),
            actions=tuple(data.get("actions", ())),
            dependency_order=tuple(data.get("dependency_order", ())),
        )

    def to_dict(self) -> dict:
        return {
            "bundle_id": self.bundle_id,
            "actions": [item.to_dict() for item in self.actions],
            "dependency_order": list(self.dependency_order),
        }


@dataclass(frozen=True, slots=True)
class ConsentValidation:
    valid: bool
    errors: tuple[str, ...]
    requirements_satisfied: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.valid

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "requirements_satisfied": list(self.requirements_satisfied),
        }


@dataclass(frozen=True, slots=True)
class PreconditionValidation:
    valid: bool
    checked: tuple[str, ...]
    failed_checks: tuple[str, ...]
    errors: tuple[str, ...]
    snapshot: dict

    def __bool__(self) -> bool:
        return self.valid

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "checked": list(self.checked),
            "failed_checks": list(self.failed_checks),
            "errors": list(self.errors),
            "snapshot": canonical_value(self.snapshot),
        }


@dataclass(frozen=True, slots=True)
class RollbackValidation:
    valid: bool
    required: bool
    errors: tuple[str, ...]
    requirements_satisfied: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.valid

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "required": self.required,
            "errors": list(self.errors),
            "requirements_satisfied": list(self.requirements_satisfied),
        }


@dataclass(frozen=True, slots=True)
class BatchDecision:
    bundle_id: str
    disposition: Disposition
    risk_level: GuardRiskLevel
    requirements: tuple[Requirement, ...]
    child_decisions: tuple[GuardDecision, ...]
    blocked_action_ids: tuple[str, ...]
    dependency_order: tuple[str, ...]
    rollback_order: tuple[str, ...]
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if self.execution_authorized is not False:
            raise GuardInputError("batch decisions cannot authorize execution")

    def to_dict(self) -> dict:
        return {
            "bundle_id": self.bundle_id,
            "disposition": self.disposition.value,
            "risk_level": self.risk_level.value,
            "requirements": [item.value for item in self.requirements],
            "child_decisions": [item.to_dict() for item in self.child_decisions],
            "blocked_action_ids": list(self.blocked_action_ids),
            "dependency_order": list(self.dependency_order),
            "rollback_order": list(self.rollback_order),
            "execution_authorized": False,
        }
