"""Write pipeline artifacts only to explicit safe local paths."""

from __future__ import annotations

import json
from pathlib import Path

from ..audit import AuditEvent
from .input_loader import _validated_explicit_local_path
from .scan_pipeline import ScanPipelineResult


def _open_mode(explicit_overwrite: bool) -> str:
    if not isinstance(explicit_overwrite, bool):
        raise TypeError("explicit_overwrite must be a bool")
    return "w" if explicit_overwrite else "x"


def write_pipeline_report(
    path: str | Path,
    result: ScanPipelineResult,
    *,
    explicit_overwrite: bool = False,
) -> None:
    """Write one UTF-8 JSON report; default to exclusive creation."""

    if not isinstance(result, ScanPipelineResult):
        raise TypeError("result must be a ScanPipelineResult")
    mode = _open_mode(explicit_overwrite)
    destination = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open(mode, encoding="utf-8", newline="\n") as stream:
        json.dump(result.to_dict(), stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def write_pipeline_audit_jsonl(
    path: str | Path,
    events: list[AuditEvent],
    *,
    explicit_overwrite: bool = False,
) -> None:
    """Write validated dry-run events as UTF-8 JSONL without implicit overwrite."""

    if not isinstance(events, list) or not all(
        isinstance(event, AuditEvent) for event in events
    ):
        raise TypeError("events must be a list of AuditEvent objects")
    for event in events:
        event.validate_pr3()
        if event.dry_run is not True:
            raise ValueError("pipeline audit events must remain dry-run")

    mode = _open_mode(explicit_overwrite)
    destination = _validated_explicit_local_path(path, allowed_suffixes={".jsonl"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open(mode, encoding="utf-8", newline="\n") as stream:
        for event in events:
            serialized = json.dumps(
                event.to_dict(), ensure_ascii=False, separators=(",", ":")
            )
            stream.write(serialized + "\n")
