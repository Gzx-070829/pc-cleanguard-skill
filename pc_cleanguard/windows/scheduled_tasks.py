"""Normalize caller-supplied read-only Windows scheduled-task metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Mapping, Optional

from ..core.models import EvidenceChain, GovernanceTarget, ObjectType


_SOURCE = "windows_scheduled_task"


def _first(raw: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return None


def _text(raw: Mapping[str, Any], *keys: str) -> Optional[str]:
    value = _first(raw, *keys)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _stable_id(task_name: str, task_path: Optional[str]) -> str:
    identity = f"{task_path or ''}\x1f{task_name}".casefold()
    digest = sha256(identity.encode("utf-8")).hexdigest()[:20]
    return f"SCHEDULED_TASK:{digest}"


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    """Observed task metadata; actions_summary is never execution authority."""

    task_id: str
    task_name: str
    task_path: Optional[str]
    state: Optional[str]
    author: Optional[str]
    description: Optional[str]
    uri: Optional[str]
    actions_summary: Optional[str] = field(repr=False)
    triggers_summary: Optional[str] = field(repr=False)
    principal_user_id: Optional[str]
    run_level: Optional[str]
    source: str
    collected_at: Optional[str]
    raw: dict[str, Any] = field(repr=False, compare=False)


def normalize_scheduled_task(raw: dict) -> Optional[ScheduledTask]:
    """Normalize one task record without executing or changing its actions."""

    if not isinstance(raw, dict):
        raise TypeError("raw must be a dict")
    task_name = _text(raw, "task_name", "TaskName", "name")
    if task_name is None:
        return None
    task_path = _text(raw, "task_path", "TaskPath")
    return ScheduledTask(
        task_id=_stable_id(task_name, task_path),
        task_name=task_name,
        task_path=task_path,
        state=_text(raw, "state", "State"),
        author=_text(raw, "author", "Author"),
        description=_text(raw, "description", "Description"),
        uri=_text(raw, "uri", "URI"),
        actions_summary=_text(raw, "actions_summary"),
        triggers_summary=_text(raw, "triggers_summary"),
        principal_user_id=_text(raw, "principal_user_id"),
        run_level=_text(raw, "run_level"),
        source=_text(raw, "source") or _SOURCE,
        collected_at=_text(raw, "collected_at"),
        raw=dict(raw),
    )


def normalize_scheduled_tasks(raw_items: list[dict]) -> list[ScheduledTask]:
    """Normalize scheduled tasks while omitting nameless records."""

    if not isinstance(raw_items, list):
        raise TypeError("raw_items must be a list")
    tasks = []
    for raw in raw_items:
        task = normalize_scheduled_task(raw)
        if task is not None:
            tasks.append(task)
    return tasks


def scheduled_task_to_governance_target(task: ScheduledTask) -> GovernanceTarget:
    """Construct an unclassified governance target from task metadata."""

    if not isinstance(task, ScheduledTask):
        raise TypeError("task must be a ScheduledTask")
    return GovernanceTarget(
        target_id=task.task_id,
        object_type=ObjectType.SCHEDULED_TASK,
        name=task.task_name,
        path=task.task_path,
        source=task.source,
        evidence_chain=EvidenceChain(
            sources=(task.source,),
            facts=("Normalized from read-only Windows scheduled-task metadata.",),
            references=tuple(
                value for value in (task.task_path, task.uri) if value is not None
            ),
            confidence=0.5,
        ),
    )


def scheduled_task_to_scan_target_record(task: ScheduledTask, scan_id: str) -> dict:
    """Return fields accepted by SQLiteStateStore.insert_scan_target()."""

    if not isinstance(task, ScheduledTask):
        raise TypeError("task must be a ScheduledTask")
    if not isinstance(scan_id, str) or not scan_id.strip():
        raise ValueError("scan_id must be a non-empty string")
    return {
        "target_id": task.task_id,
        "scan_id": scan_id,
        "object_type": ObjectType.SCHEDULED_TASK.value,
        "name": task.task_name,
        "publisher": task.author,
        "version": None,
        "path": task.task_path,
        "source": task.source,
        "first_seen": task.collected_at,
        "last_seen": task.collected_at,
        "normalized_identity": "|".join(
            value.casefold() for value in (task.task_path or "", task.task_name)
        ),
    }
