"""Normalize caller-supplied read-only Windows startup metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Mapping, Optional

from ..core.models import EvidenceChain, GovernanceTarget, ObjectType


_SOURCE = "windows_startup_metadata"


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


def _stable_id(*values: Optional[str]) -> str:
    identity = "\x1f".join(value or "" for value in values).casefold()
    return f"STARTUP_ITEM:{sha256(identity.encode('utf-8')).hexdigest()[:20]}"


@dataclass(frozen=True, slots=True)
class StartupItem:
    """Observed startup metadata; command is never an instruction to execute."""

    item_id: str
    name: str
    command: Optional[str] = field(repr=False)
    location_type: Optional[str]
    registry_path: Optional[str]
    registry_value_name: Optional[str]
    startup_folder_path: Optional[str]
    file_path: Optional[str]
    publisher: Optional[str]
    enabled_state: Optional[str]
    source: str
    collected_at: Optional[str]
    raw: dict[str, Any] = field(repr=False, compare=False)


def normalize_startup_item(raw: dict) -> Optional[StartupItem]:
    """Normalize one registry or Startup Folder record without executing it."""

    if not isinstance(raw, dict):
        raise TypeError("raw must be a dict")
    name = _text(raw, "name", "Name")
    if name is None:
        return None
    location_type = _text(raw, "location_type")
    registry_path = _text(raw, "registry_path")
    registry_value_name = _text(raw, "registry_value_name")
    startup_folder_path = _text(raw, "startup_folder_path")
    file_path = _text(raw, "file_path", "FullName")
    return StartupItem(
        item_id=_stable_id(
            name,
            location_type,
            registry_path,
            registry_value_name,
            startup_folder_path,
            file_path,
        ),
        name=name,
        command=_text(raw, "command", "Command"),
        location_type=location_type,
        registry_path=registry_path,
        registry_value_name=registry_value_name,
        startup_folder_path=startup_folder_path,
        file_path=file_path,
        publisher=_text(raw, "publisher", "Publisher"),
        enabled_state=_text(raw, "enabled_state"),
        source=_text(raw, "source") or _SOURCE,
        collected_at=_text(raw, "collected_at"),
        raw=dict(raw),
    )


def normalize_startup_items(raw_items: list[dict]) -> list[StartupItem]:
    """Normalize startup records while omitting nameless entries."""

    if not isinstance(raw_items, list):
        raise TypeError("raw_items must be a list")
    items = []
    for raw in raw_items:
        item = normalize_startup_item(raw)
        if item is not None:
            items.append(item)
    return items


def startup_item_to_governance_target(item: StartupItem) -> GovernanceTarget:
    """Construct an unclassified governance target from startup metadata."""

    if not isinstance(item, StartupItem):
        raise TypeError("item must be a StartupItem")
    references = tuple(
        value
        for value in (
            item.registry_path,
            item.registry_value_name,
            item.startup_folder_path,
            item.file_path,
        )
        if value is not None
    )
    return GovernanceTarget(
        target_id=item.item_id,
        object_type=ObjectType.STARTUP_ITEM,
        name=item.name,
        publisher=item.publisher,
        path=item.file_path or item.startup_folder_path,
        source=item.source,
        evidence_chain=EvidenceChain(
            sources=(item.source,),
            facts=("Normalized from read-only Windows startup metadata.",),
            references=references,
            confidence=0.5,
        ),
    )


def startup_item_to_scan_target_record(item: StartupItem, scan_id: str) -> dict:
    """Return fields accepted by SQLiteStateStore.insert_scan_target()."""

    if not isinstance(item, StartupItem):
        raise TypeError("item must be a StartupItem")
    if not isinstance(scan_id, str) or not scan_id.strip():
        raise ValueError("scan_id must be a non-empty string")
    return {
        "target_id": item.item_id,
        "scan_id": scan_id,
        "object_type": ObjectType.STARTUP_ITEM.value,
        "name": item.name,
        "publisher": item.publisher,
        "version": None,
        "path": item.file_path or item.startup_folder_path,
        "source": item.source,
        "first_seen": item.collected_at,
        "last_seen": item.collected_at,
        "normalized_identity": "|".join(
            value.casefold()
            for value in (item.name, item.location_type or "", item.publisher or "")
        ),
    }
