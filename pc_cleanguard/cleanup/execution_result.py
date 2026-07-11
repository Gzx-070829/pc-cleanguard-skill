"""Structured results and audit events for controlled L1 cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Tuple
from uuid import uuid4

from .junk_rules import JunkCategory


L1_EXECUTION_LEVEL = "LEVEL_1_LOW_RISK_CLEANUP"
_STATUSES = {"would_clean", "cleaned", "quarantined", "blocked", "skipped", "failed"}
_ACTIONS = {"delete_file", "quarantine_file", "skip"}
_METHODS = {"none", "pathlib_unlink", "pathlib_replace"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _validated_evidence(evidence: Iterable[dict]) -> Tuple[dict, ...]:
    items = tuple(evidence)
    if not items or any(
        not isinstance(item, dict)
        or not isinstance(item.get("source"), str)
        or not item["source"].strip()
        or not isinstance(item.get("fact"), str)
        or not item["fact"].strip()
        for item in items
    ):
        raise ValueError("evidence must contain source/fact objects")
    return tuple(
        {"source": item["source"].strip(), "fact": item["fact"].strip()}
        for item in items
    )


@dataclass(frozen=True, slots=True)
class CleanupExecutionAuditEvent:
    path: str
    category: JunkCategory
    action: str
    status: str
    reason: str
    bytes_reclaimed: int
    evidence: Tuple[dict, ...]
    confirmed: bool
    dry_run: bool
    execution_method: str
    event_id: str = ""
    timestamp: str = ""
    actor: str = "pc-cleanguard-skill"
    execution_level: str = L1_EXECUTION_LEVEL

    def __post_init__(self) -> None:
        if not self.event_id:
            object.__setattr__(self, "event_id", str(uuid4()))
        if not self.timestamp:
            object.__setattr__(self, "timestamp", _utc_now())
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError("path must be a non-empty string")
        if not isinstance(self.category, JunkCategory):
            raise TypeError("category must be a JunkCategory")
        if self.action not in _ACTIONS:
            raise ValueError("unsupported cleanup action")
        if self.status not in _STATUSES:
            raise ValueError("unsupported cleanup status")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        if (
            not isinstance(self.bytes_reclaimed, int)
            or isinstance(self.bytes_reclaimed, bool)
            or self.bytes_reclaimed < 0
        ):
            raise ValueError("bytes_reclaimed must be a non-negative integer")
        if not isinstance(self.confirmed, bool) or not isinstance(self.dry_run, bool):
            raise TypeError("confirmed and dry_run must be bool values")
        if self.execution_method not in _METHODS:
            raise ValueError("unsupported execution method")
        if self.execution_level != L1_EXECUTION_LEVEL:
            raise ValueError("cleanup execution events are restricted to L1")
        if self.status == "would_clean" and self.dry_run is not True:
            raise ValueError("would_clean audit events must be dry-run")
        if self.status == "cleaned":
            if not self.confirmed or self.dry_run:
                raise ValueError("cleaned status requires confirmed real execution")
            if self.execution_method != "pathlib_unlink":
                raise ValueError("cleaned status requires the bounded file method")
        if self.status == "quarantined":
            if not self.confirmed or self.dry_run:
                raise ValueError("quarantined status requires confirmed execution")
            if self.action != "quarantine_file" or self.execution_method != "pathlib_replace":
                raise ValueError("quarantined status requires the quarantine method")
        if self.status != "cleaned" and self.bytes_reclaimed != 0:
            raise ValueError("only cleaned results may report reclaimed bytes")
        object.__setattr__(self, "evidence", _validated_evidence(self.evidence))

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "path": self.path,
            "category": self.category.value,
            "action": self.action,
            "status": self.status,
            "reason": self.reason,
            "bytes_reclaimed": self.bytes_reclaimed,
            "evidence": [dict(item) for item in self.evidence],
            "confirmed": self.confirmed,
            "dry_run": self.dry_run,
            "execution_method": self.execution_method,
            "execution_level": L1_EXECUTION_LEVEL,
        }


@dataclass(frozen=True, slots=True)
class CleanupExecutionItem:
    path: str
    category: JunkCategory
    action: str
    status: str
    reason: str
    bytes_reclaimed: int
    evidence: Tuple[dict, ...]
    audit_event: CleanupExecutionAuditEvent

    def __post_init__(self) -> None:
        if not isinstance(self.audit_event, CleanupExecutionAuditEvent):
            raise TypeError("audit_event must be a CleanupExecutionAuditEvent")
        if (
            self.path != self.audit_event.path
            or self.category is not self.audit_event.category
            or self.action != self.audit_event.action
            or self.status != self.audit_event.status
            or self.reason != self.audit_event.reason
            or self.bytes_reclaimed != self.audit_event.bytes_reclaimed
        ):
            raise ValueError("item fields must match the audit event")
        object.__setattr__(self, "evidence", _validated_evidence(self.evidence))

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "category": self.category.value,
            "action": self.action,
            "status": self.status,
            "reason": self.reason,
            "bytes_reclaimed": self.bytes_reclaimed,
            "evidence": [dict(item) for item in self.evidence],
            "audit_event": self.audit_event.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class CleanupExecutionReport:
    confirmed: bool
    allow_roots: Tuple[str, ...]
    results: Tuple[CleanupExecutionItem, ...]
    audit_path: str
    summary: dict
    mode: str
    execution_level: str = L1_EXECUTION_LEVEL
    schema_version: str = "0.2"

    def __post_init__(self) -> None:
        if self.mode not in {"dry_run", "confirmed_l1", "confirmed_l1_quarantine"}:
            raise ValueError("unsupported cleanup execution mode")
        if self.mode != "dry_run" and not self.confirmed:
            raise ValueError("confirmed cleanup mode requires explicit confirmation")
        if self.execution_level != L1_EXECUTION_LEVEL:
            raise ValueError("cleanup reports are restricted to L1")
        if not self.allow_roots or any(not item for item in self.allow_roots):
            raise ValueError("allow_roots must contain explicit paths")
        if not all(isinstance(item, CleanupExecutionItem) for item in self.results):
            raise TypeError("results must contain CleanupExecutionItem objects")
        if not isinstance(self.summary, dict):
            raise TypeError("summary must be a dict")

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "confirmed": self.confirmed,
            "execution_level": L1_EXECUTION_LEVEL,
            "allow_roots": list(self.allow_roots),
            "audit_path": self.audit_path,
            "summary": dict(self.summary),
            "results": [item.to_dict() for item in self.results],
        }
