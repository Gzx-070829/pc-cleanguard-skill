"""Append-only JSONL storage for explicit PR3 dry-run audit paths."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .audit_models import AuditEvent


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


class JsonlAuditLogger:
    """Append and read dry-run events at a caller-supplied local path."""

    def __init__(self, log_path: str | Path):
        if not isinstance(log_path, (str, Path)) or not str(log_path).strip():
            raise ValueError("log_path must be an explicit non-empty path")
        self.log_path = Path(log_path)
        if self.log_path.suffix.casefold() != ".jsonl":
            raise ValueError("log_path must use the .jsonl extension")
        self._validate_log_path()

    def _validate_log_path(self) -> None:
        raw_path = str(self.log_path).replace("/", "\\")
        resolved = self.log_path.resolve(strict=False)
        resolved_windows = str(resolved).replace("/", "\\")
        if raw_path.startswith("\\\\") or resolved_windows.startswith("\\\\"):
            raise ValueError("network and device paths are not allowed")
        if _WINDOWS_SYSTEM_PATH.match(raw_path) or _WINDOWS_SYSTEM_PATH.match(
            resolved_windows
        ):
            raise ValueError("system directory log paths are not allowed")

        resolved_posix = resolved.as_posix()
        if any(
            resolved_posix == prefix or resolved_posix.startswith(prefix + "/")
            for prefix in _POSIX_SYSTEM_PREFIXES
        ):
            raise ValueError("system directory log paths are not allowed")

    def append_event(self, event: AuditEvent) -> None:
        """Append one validated event as one UTF-8 JSON line."""

        if not isinstance(event, AuditEvent):
            raise TypeError("event must be an AuditEvent")
        self._validate_log_path()
        event.validate_pr3()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(
            event.to_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        separator = "\n" if self._needs_line_separator() else ""
        with self.log_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(separator + serialized + "\n")

    def _needs_line_separator(self) -> bool:
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return False
        with self.log_path.open("rb") as stream:
            stream.seek(-1, 2)
            return stream.read(1) not in {b"\n", b"\r"}

    def read_events(self) -> list[dict]:
        """Read all JSONL events without modifying the log."""

        self._validate_log_path()
        if not self.log_path.exists():
            return []
        events = []
        with self.log_path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise ValueError(
                        f"audit line {line_number} must contain a JSON object"
                    )
                events.append(event)
        return events
