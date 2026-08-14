"""Canonical JSON, timestamps, and fingerprints for Guard contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .errors import GuardInputError


def canonical_value(value: Any) -> Any:
    """Return a JSON-compatible value with stable container ordering."""

    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return canonical_value(value.to_dict())
    if is_dataclass(value):
        return canonical_value(asdict(value))
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise GuardInputError("contract object keys must be strings")
        return {key: canonical_value(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [canonical_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            raise GuardInputError("non-finite numbers are not valid contract values")
        return value
    raise GuardInputError(f"unsupported contract value type: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def fingerprint(namespace: str, value: Any) -> str:
    if not isinstance(namespace, str) or not namespace.strip():
        raise GuardInputError("fingerprint namespace must be non-empty")
    material = f"{namespace.strip()}\n{canonical_json(value)}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def parse_timestamp(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as error:
            raise GuardInputError("timestamp must be ISO-8601") from error
    else:
        raise GuardInputError("timestamp must be a non-empty ISO-8601 value")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise GuardInputError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def format_timestamp(value: str | datetime) -> str:
    return parse_timestamp(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_local_path(value: Any, *, name: str) -> None:
    """Reject UNC/device paths before pathlib can trigger network filesystem I/O."""

    if not isinstance(value, (str, bytes)) and not hasattr(value, "__fspath__"):
        raise GuardInputError(f"{name} must be an explicit local path")
    text = str(value).strip().replace("/", "\\")
    if not text or text.startswith("\\\\"):
        raise GuardInputError(f"{name} must be an explicit local non-UNC path")


def normalized_windows_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuardInputError("path must be a non-empty string")
    path = value.strip().replace("/", "\\")
    while "\\\\" in path[2:]:
        path = path.replace("\\\\", "\\")
    return path


def json_object(value: Any, *, name: str) -> dict:
    if not isinstance(value, dict):
        raise GuardInputError(f"{name} must be an object")
    return canonical_value(value)
