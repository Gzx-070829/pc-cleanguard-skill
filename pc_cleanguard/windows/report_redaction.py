"""Irreversibly redact identity-bearing strings from a canonical report copy."""

from __future__ import annotations

import copy
import os
import re


_EMAIL = re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[a-z0-9.-]+\.[a-z]{2,}(?![\w.-])")
_USER_PATH = re.compile(r"(?i)([a-z]:[\\/]+users[\\/]+)([^\\/]+)")
_UNC_USER_PATH = re.compile(r"(?i)^(\\\\)([^\\/]+)([\\/]+users[\\/]+)([^\\/]+)")
_JWT = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}(?![A-Za-z0-9_-])")
_TOKEN_ASSIGNMENT = re.compile(r"(?i)(\b(?:token|api[_-]?key|secret)\s*[:=]\s*)[A-Za-z0-9_./+=-]{12,}")
_DEVICE_KEYS = {"device", "device_name", "computer_name", "computername", "hostname", "host_name"}


def redact_windows_report(report: dict) -> tuple[dict, dict]:
    """Return a redacted deep copy and count-only summary; never build a map."""

    if not isinstance(report, dict):
        raise TypeError("report must be a dict")
    counts = {"user": 0, "device": 0, "email": 0, "token": 0}
    changed_fields = 0
    username = os.environ.get("USERNAME", "").strip()
    device = os.environ.get("COMPUTERNAME", "").strip()

    def substitute(value: str, key: str | None) -> str:
        nonlocal changed_fields
        original = value
        lowered_key = (key or "").casefold()
        value, amount = _EMAIL.subn("<EMAIL>", value)
        counts["email"] += amount
        if lowered_key in _DEVICE_KEYS and value and value != "<DEVICE>":
            counts["device"] += 1
            value = "<DEVICE>"
        else:
            def unc(match):
                counts["device"] += 1
                counts["user"] += 1
                return f"{match.group(1)}<DEVICE>{match.group(3)}<USER>"

            value = _UNC_USER_PATH.sub(unc, value)

            def user_path(match):
                user = match.group(2)
                if user.casefold() in {"public", "default", "all users", "<user>"}:
                    return match.group(0)
                counts["user"] += 1
                return f"{match.group(1)}<USER>"

            value = _USER_PATH.sub(user_path, value)
            if username and username.casefold() != "<user>":
                pattern = re.compile(rf"(?i)(?<![\w]){re.escape(username)}(?![\w])")
                value, amount = pattern.subn("<USER>", value)
                counts["user"] += amount
            if device and device.casefold() != "<device>":
                pattern = re.compile(rf"(?i)(?<![\w-]){re.escape(device)}(?![\w-])")
                value, amount = pattern.subn("<DEVICE>", value)
                counts["device"] += amount
        if any(term in lowered_key for term in ("token", "api_key", "apikey", "secret")) and value and value != "<TOKEN>":
            value = "<TOKEN>"
            counts["token"] += 1
        else:
            value, amount = _JWT.subn("<TOKEN>", value)
            counts["token"] += amount
            def token_assignment(match):
                counts["token"] += 1
                return match.group(1) + "<TOKEN>"
            value = _TOKEN_ASSIGNMENT.sub(token_assignment, value)
        if value != original:
            changed_fields += 1
        return value

    def walk(value, key: str | None = None):
        if isinstance(value, dict):
            return {item_key: walk(item, item_key) for item_key, item in value.items()}
        if isinstance(value, list):
            return [walk(item, key) for item in value]
        if isinstance(value, str):
            return substitute(value, key)
        return value

    redacted = walk(copy.deepcopy(report))
    summary = {
        "redacted_value_count": sum(counts.values()),
        "redacted_field_count": changed_fields,
        "redaction_counts": counts,
        "reversible_mapping_created": False,
        "original_values_recorded": False,
    }
    redacted["source_kind"] = "windows_collector_redacted"
    redacted["redaction_summary"] = summary
    return redacted, summary
