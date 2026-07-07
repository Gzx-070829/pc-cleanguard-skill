"""Load explicit local JSON input without discovery or directory traversal."""

from __future__ import annotations

import json
import re
from pathlib import Path


MAX_SCAN_JSON_BYTES = 10 * 1024 * 1024

_WINDOWS_SYSTEM_PATH = re.compile(
    r"^[a-z]:\\(?:windows|program files(?: \(x86\))?|programdata|recovery|"
    r"system volume information|\$recycle\.bin)(?:\\|$)",
    re.IGNORECASE,
)
_POSIX_SYSTEM_PREFIXES = (
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/proc",
    "/root",
    "/sbin",
    "/sys",
    "/usr",
    "/var",
)


def _validated_explicit_local_path(
    path: str | Path,
    *,
    allowed_suffixes: set[str],
) -> Path:
    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise ValueError("path must be an explicit non-empty local path")
    candidate = Path(path)
    if candidate.suffix.casefold() not in allowed_suffixes:
        allowed = ", ".join(sorted(allowed_suffixes))
        raise ValueError(f"path must use one of these extensions: {allowed}")

    raw_windows = str(candidate).replace("/", "\\")
    resolved = candidate.resolve(strict=False)
    resolved_windows = str(resolved).replace("/", "\\")
    if raw_windows.startswith("\\\\") or resolved_windows.startswith("\\\\"):
        raise ValueError("UNC, network, and device paths are not allowed")
    if _WINDOWS_SYSTEM_PATH.match(raw_windows) or _WINDOWS_SYSTEM_PATH.match(
        resolved_windows
    ):
        raise ValueError("Windows system directory paths are not allowed")

    resolved_posix = resolved.as_posix()
    if any(
        resolved_posix == prefix or resolved_posix.startswith(prefix + "/")
        for prefix in _POSIX_SYSTEM_PREFIXES
    ):
        raise ValueError("system directory paths are not allowed")
    return candidate


def load_scan_json_text(text: str) -> dict:
    """Parse one JSON object supplied directly by the caller."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"invalid scan JSON at line {error.lineno}, column {error.colno}"
        ) from error
    if not isinstance(data, dict):
        raise ValueError("scan JSON root must be an object")
    return data


def load_scan_json_file(
    path: str | Path,
    *,
    max_bytes: int = MAX_SCAN_JSON_BYTES,
) -> dict:
    """Read exactly one explicit UTF-8 JSON file within the size limit."""

    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
        raise ValueError("max_bytes must be a positive integer")
    candidate = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    if not candidate.is_file():
        raise FileNotFoundError(f"scan JSON file does not exist: {candidate}")
    if candidate.stat().st_size > max_bytes:
        raise ValueError(f"scan JSON file exceeds the {max_bytes}-byte limit")

    with candidate.open("rb") as stream:
        payload = stream.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ValueError(f"scan JSON file exceeds the {max_bytes}-byte limit")
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("scan JSON file must be UTF-8") from error
    return load_scan_json_text(text)
