"""Normalize caller-supplied read-only Windows service metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Mapping, Optional

from ..core.models import EvidenceChain, GovernanceTarget, ObjectType


_SOURCE = "windows_cim_service"


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


def _integer(raw: Mapping[str, Any], *keys: str) -> Optional[int]:
    value = _first(raw, *keys)
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _stable_id(service_name: str) -> str:
    digest = sha256(service_name.casefold().encode("utf-8")).hexdigest()[:20]
    return f"SERVICE:{digest}"


@dataclass(frozen=True, slots=True)
class WindowsService:
    """Observed service metadata; path_name is never executable authority."""

    service_id: str
    service_name: str
    display_name: Optional[str]
    status: Optional[str]
    start_type: Optional[str]
    state: Optional[str]
    path_name: Optional[str] = field(repr=False)
    process_id: Optional[int]
    service_type: Optional[str]
    start_name: Optional[str]
    description: Optional[str]
    source: str
    collected_at: Optional[str]
    raw: dict[str, Any] = field(repr=False, compare=False)


def normalize_service(raw: dict) -> Optional[WindowsService]:
    """Normalize one Win32_Service record without changing the service."""

    if not isinstance(raw, dict):
        raise TypeError("raw must be a dict")
    service_name = _text(raw, "service_name", "Name")
    display_name = _text(raw, "display_name", "DisplayName")
    if service_name is None and display_name is None:
        return None
    service_name = service_name or display_name
    return WindowsService(
        service_id=_stable_id(service_name),
        service_name=service_name,
        display_name=display_name,
        status=_text(raw, "status", "Status"),
        start_type=_text(raw, "start_type", "StartMode"),
        state=_text(raw, "state", "State"),
        path_name=_text(raw, "path_name", "PathName"),
        process_id=_integer(raw, "process_id", "ProcessId"),
        service_type=_text(raw, "service_type", "ServiceType"),
        start_name=_text(raw, "start_name", "StartName"),
        description=_text(raw, "description", "Description"),
        source=_text(raw, "source") or _SOURCE,
        collected_at=_text(raw, "collected_at"),
        raw=dict(raw),
    )


def normalize_services(raw_items: list[dict]) -> list[WindowsService]:
    """Normalize service records while omitting records without identity."""

    if not isinstance(raw_items, list):
        raise TypeError("raw_items must be a list")
    services = []
    for raw in raw_items:
        service = normalize_service(raw)
        if service is not None:
            services.append(service)
    return services


def service_to_governance_target(service: WindowsService) -> GovernanceTarget:
    """Construct an unclassified governance target from service metadata."""

    if not isinstance(service, WindowsService):
        raise TypeError("service must be a WindowsService")
    return GovernanceTarget(
        target_id=service.service_id,
        object_type=ObjectType.SERVICE,
        name=service.display_name or service.service_name,
        path=service.path_name,
        source=service.source,
        evidence_chain=EvidenceChain(
            sources=(service.source,),
            facts=("Normalized from read-only Win32_Service metadata.",),
            references=(service.service_name,),
            confidence=0.5,
        ),
    )


def service_to_scan_target_record(service: WindowsService, scan_id: str) -> dict:
    """Return fields accepted by SQLiteStateStore.insert_scan_target()."""

    if not isinstance(service, WindowsService):
        raise TypeError("service must be a WindowsService")
    if not isinstance(scan_id, str) or not scan_id.strip():
        raise ValueError("scan_id must be a non-empty string")
    return {
        "target_id": service.service_id,
        "scan_id": scan_id,
        "object_type": ObjectType.SERVICE.value,
        "name": service.display_name or service.service_name,
        "publisher": None,
        "version": None,
        "path": service.path_name,
        "source": service.source,
        "first_seen": service.collected_at,
        "last_seen": service.collected_at,
        "normalized_identity": "|".join(
            value.casefold()
            for value in (service.service_name, service.display_name or "")
        ),
    }
