"""Small canonical SHA-256 hash chain for local governance receipts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .errors import AuditIntegrityError, GuardInputError
from .models import AuditEventType
from .normalize import (
    canonical_json,
    canonical_value,
    fingerprint,
    format_timestamp,
    require_local_path,
    utc_now,
)


GENESIS_HASH = "0" * 64
_WINDOWS_SYSTEM_PATH = re.compile(
    r"^[a-z]:\\(?:windows|program files(?: \(x86\))?|programdata|recovery|"
    r"system volume information|\$recycle\.bin)(?:\\|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    timestamp: str
    request_id: str
    decision_id: str | None
    event_type: AuditEventType | str
    payload: dict
    previous_event_hash: str
    event_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise GuardInputError("event_id must be non-empty")
        object.__setattr__(self, "timestamp", format_timestamp(self.timestamp))
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise GuardInputError("request_id must be non-empty")
        if self.decision_id is not None and (
            not isinstance(self.decision_id, str) or not self.decision_id.strip()
        ):
            raise GuardInputError("decision_id must be null or non-empty")
        try:
            object.__setattr__(self, "event_type", AuditEventType(self.event_type))
        except (TypeError, ValueError) as error:
            raise GuardInputError("unsupported audit event type") from error
        if not isinstance(self.payload, dict):
            raise GuardInputError("audit payload must be an object")
        object.__setattr__(self, "payload", canonical_value(self.payload))
        for name in ("previous_event_hash", "event_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 64 or any(
                character not in "0123456789abcdef" for character in value
            ):
                raise GuardInputError(f"{name} must be a lowercase SHA-256 digest")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AuditEvent":
        if not isinstance(data, Mapping):
            raise GuardInputError("audit event must be an object")
        expected = {
            "event_id", "timestamp", "request_id", "decision_id", "event_type",
            "payload", "previous_event_hash", "event_hash",
        }
        if set(data) != expected:
            raise GuardInputError("audit event fields do not match the stable contract")
        return cls(**dict(data))

    def hash_material(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "decision_id": self.decision_id,
            "event_type": self.event_type.value,
            "payload": self.payload,
            "previous_event_hash": self.previous_event_hash,
        }

    def to_dict(self) -> dict:
        return {**self.hash_material(), "event_hash": self.event_hash}


@dataclass(frozen=True, slots=True)
class AuditVerification:
    valid: bool
    event_count: int
    errors: tuple[str, ...]
    last_event_hash: str | None

    def __bool__(self) -> bool:
        return self.valid

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "event_count": self.event_count,
            "errors": list(self.errors),
            "last_event_hash": self.last_event_hash,
        }


def _audit_path(path: str | Path) -> Path:
    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise GuardInputError("audit path must be explicitly supplied")
    require_local_path(path, name="audit path")
    text = str(path).replace("/", "\\")
    destination = Path(path)
    resolved = str(destination.resolve(strict=False)).replace("/", "\\")
    if _WINDOWS_SYSTEM_PATH.match(text) or _WINDOWS_SYSTEM_PATH.match(resolved):
        raise GuardInputError("Windows system audit paths are not supported")
    if destination.suffix.casefold() != ".jsonl":
        raise GuardInputError("audit path must end in .jsonl")
    if destination.exists() and not destination.is_file():
        raise GuardInputError("audit path must be a regular file")
    return destination


def create_event(
    *,
    event_type: AuditEventType | str,
    request_id: str,
    decision_id: str | None,
    payload: dict,
    previous_event_hash: str = GENESIS_HASH,
    timestamp: str | None = None,
) -> AuditEvent:
    timestamp_value = format_timestamp(timestamp or utc_now())
    type_value = AuditEventType(event_type)
    seed = {
        "timestamp": timestamp_value,
        "request_id": request_id,
        "decision_id": decision_id,
        "event_type": type_value.value,
        "payload": canonical_value(payload),
        "previous_event_hash": previous_event_hash,
    }
    event_id = f"event:{fingerprint('pc-cleanguard/audit-event-id/v0.5', seed)[:24]}"
    material = {"event_id": event_id, **seed}
    event_hash = fingerprint("pc-cleanguard/audit-event/v0.5", material)
    return AuditEvent(event_hash=event_hash, **material)


def _read_events(path: Path) -> tuple[AuditEvent, ...]:
    events = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise AuditIntegrityError(f"cannot read audit chain: {error}") from error
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            raise AuditIntegrityError(f"blank audit record at line {index}")
        try:
            events.append(AuditEvent.from_dict(json.loads(line)))
        except (json.JSONDecodeError, GuardInputError) as error:
            raise AuditIntegrityError(f"invalid audit record at line {index}: {error}") from error
    return tuple(events)


def append_event(
    path: str | Path,
    *,
    event_type: AuditEventType | str,
    request_id: str,
    decision_id: str | None,
    payload: dict,
    timestamp: str | None = None,
) -> AuditEvent:
    destination = _audit_path(path)
    previous = GENESIS_HASH
    if destination.exists():
        verification = verify_audit_chain(destination)
        if not verification.valid:
            raise AuditIntegrityError("refusing to append to an invalid audit chain")
        previous = verification.last_event_hash or GENESIS_HASH
    event = create_event(
        event_type=event_type,
        request_id=request_id,
        decision_id=decision_id,
        payload=payload,
        previous_event_hash=previous,
        timestamp=timestamp,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(canonical_json(event.to_dict()) + "\n")
        stream.flush()
    return event


def verify_audit_chain(path: str | Path) -> AuditVerification:
    try:
        destination = _audit_path(path)
    except GuardInputError as error:
        return AuditVerification(False, 0, (str(error),), None)
    if not destination.is_file():
        return AuditVerification(False, 0, ("audit file does not exist",), None)
    try:
        events = _read_events(destination)
    except AuditIntegrityError as error:
        return AuditVerification(False, 0, (str(error),), None)
    if not events:
        return AuditVerification(False, 0, ("audit chain is empty",), None)
    errors = []
    previous = GENESIS_HASH
    for index, event in enumerate(events, start=1):
        if event.previous_event_hash != previous:
            errors.append(f"line {index}: previous_event_hash link mismatch")
        expected_hash = fingerprint(
            "pc-cleanguard/audit-event/v0.5", event.hash_material()
        )
        if event.event_hash != expected_hash:
            errors.append(f"line {index}: event_hash mismatch")
        previous = event.event_hash
    return AuditVerification(not errors, len(events), tuple(errors), previous)
