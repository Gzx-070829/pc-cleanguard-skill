"""Dry-run-only audit event data contract for PC CleanGuard PR3."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import UUID, uuid4

from ..core.models import ClassificationLabel, PermissionLevel, RiskLevel


_ALLOWED_RESULTS = {"planned", "simulated", "blocked", "refused", "skipped"}
_ALLOWED_EXECUTION_METHODS = {
    "none",
    "dry_run",
    "policy_engine",
    "report_builder",
}


def _new_event_id() -> str:
    return str(uuid4())


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """An audit record for a plan, simulation, refusal, or policy block."""

    action: str
    target_id: str
    target_name: str
    classification: ClassificationLabel
    risk_level: RiskLevel
    permission_level: PermissionLevel
    reason: str
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)
    result: str = "planned"
    event_id: str = field(default_factory=_new_event_id)
    timestamp: str = field(default_factory=_utc_timestamp)
    actor: str = "pc-cleanguard-skill"
    mode: str = "safe"
    approved_by: Optional[str] = None
    execution_method: str = "none"
    command_summary: None = None
    rollback_available: bool = False
    rollback_method: Optional[str] = None
    schema_version: str = "0.1"
    scan_id: Optional[str] = None
    plan_id: Optional[str] = None
    dry_run: bool = True
    policy_decision_id: Optional[str] = None
    rulepack_version: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        self.validate_pr3()

    def validate_pr3(self) -> None:
        """Reject values that would claim or enable real execution in PR3."""

        try:
            UUID(self.event_id)
        except (TypeError, ValueError, AttributeError) as error:
            raise ValueError("event_id must be a UUID string") from error

        try:
            parsed_timestamp = datetime.fromisoformat(
                self.timestamp.replace("Z", "+00:00")
            )
        except (TypeError, ValueError, AttributeError) as error:
            raise ValueError("timestamp must be a valid ISO 8601 string") from error
        if parsed_timestamp.tzinfo is None or parsed_timestamp.utcoffset() is None:
            raise ValueError("timestamp must include a timezone or UTC Z")

        for name, value in (
            ("action", self.action),
            ("target_id", self.target_id),
            ("target_name", self.target_name),
            ("reason", self.reason),
            ("actor", self.actor),
            ("schema_version", self.schema_version),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if not isinstance(self.classification, ClassificationLabel):
            raise ValueError("classification must be a ClassificationLabel")
        if not isinstance(self.risk_level, RiskLevel):
            raise ValueError("risk_level must be a RiskLevel")
        if not isinstance(self.permission_level, PermissionLevel):
            raise ValueError("permission_level must be a PermissionLevel")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs):
            raise ValueError("evidence_refs must contain non-empty strings")
        if self.dry_run is not True:
            raise ValueError("PR3 audit events must have dry_run=True")
        if self.mode != "safe":
            raise ValueError("PR3 audit events must use mode='safe'")
        if self.result not in _ALLOWED_RESULTS:
            raise ValueError("result is not allowed for PR3 dry-run audit events")
        if self.execution_method not in _ALLOWED_EXECUTION_METHODS:
            raise ValueError("execution_method is not allowed for PR3")
        if self.command_summary is not None:
            raise ValueError("command_summary must be null in PR3")

    def to_dict(self) -> dict:
        """Return a JSON-serializable dictionary aligned with the PR3 schema."""

        self.validate_pr3()
        return {
            "schema_version": self.schema_version,
            "scan_id": self.scan_id,
            "plan_id": self.plan_id,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "mode": self.mode,
            "action": self.action,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "classification": self.classification.value,
            "risk_level": self.risk_level.value,
            "permission_level": self.permission_level.value,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
            "approved_by": self.approved_by,
            "execution_method": self.execution_method,
            "command_summary": self.command_summary,
            "result": self.result,
            "rollback_available": self.rollback_available,
            "rollback_method": self.rollback_method,
            "dry_run": self.dry_run,
            "policy_decision_id": self.policy_decision_id,
            "rulepack_version": self.rulepack_version,
        }
