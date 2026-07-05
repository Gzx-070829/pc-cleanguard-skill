"""Normalize caller-supplied Windows uninstall-registry metadata.

This module never reads the registry or invokes the PowerShell collector. An
uninstall string is retained as metadata only and is never execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Mapping, Optional

from ..core.models import EvidenceChain, GovernanceTarget, ObjectType


_SOURCE = "windows_registry_uninstall"


@dataclass(frozen=True, slots=True)
class InstalledApp:
    """Normalized installed-app metadata with no execution behavior."""

    app_id: str
    name: str
    publisher: Optional[str]
    version: Optional[str]
    install_location: Optional[str]
    install_date: Optional[str]
    uninstall_available: bool
    uninstall_string: Optional[str] = field(repr=False)
    quiet_uninstall_string: Optional[str] = field(repr=False)
    registry_source: Optional[str]
    registry_key: Optional[str]
    display_icon: Optional[str]
    estimated_size_kb: Optional[int]
    system_component: bool
    windows_installer: bool
    no_remove: bool
    no_modify: bool
    source: str
    collected_at: Optional[str]
    raw: dict[str, Any] = field(repr=False, compare=False)


def _first(raw: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return None


def _optional_text(raw: Mapping[str, Any], *keys: str) -> Optional[str]:
    value = _first(raw, *keys)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _registry_bool(raw: Mapping[str, Any], *keys: str) -> bool:
    value = _first(raw, *keys)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "on"}
    return False


def _optional_int(raw: Mapping[str, Any], *keys: str) -> Optional[int]:
    value = _first(raw, *keys)
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(str(value).strip().replace(",", ""))
    except (TypeError, ValueError):
        return None


def _app_id(
    name: str,
    publisher: Optional[str],
    version: Optional[str],
    registry_key: Optional[str],
) -> str:
    identity = "\x1f".join(
        (name, publisher or "", version or "", registry_key or "")
    ).casefold()
    return f"WINDOWS_APP:{sha256(identity.encode('utf-8')).hexdigest()[:20]}"


def normalize_registry_app(raw: dict) -> Optional[InstalledApp]:
    """Normalize one raw registry record; skip records without a display name."""

    if not isinstance(raw, dict):
        raise TypeError("raw must be a dict")

    name = _optional_text(raw, "name", "DisplayName")
    if name is None:
        return None

    publisher = _optional_text(raw, "publisher", "Publisher")
    version = _optional_text(raw, "version", "DisplayVersion")
    registry_key = _optional_text(raw, "registry_key", "PSPath")
    uninstall_string = _optional_text(raw, "uninstall_string", "UninstallString")
    quiet_uninstall_string = _optional_text(
        raw, "quiet_uninstall_string", "QuietUninstallString"
    )
    source = _optional_text(raw, "source") or _SOURCE

    return InstalledApp(
        app_id=_app_id(name, publisher, version, registry_key),
        name=name,
        publisher=publisher,
        version=version,
        install_location=_optional_text(raw, "install_location", "InstallLocation"),
        install_date=_optional_text(raw, "install_date", "InstallDate"),
        uninstall_available=uninstall_string is not None,
        uninstall_string=uninstall_string,
        quiet_uninstall_string=quiet_uninstall_string,
        registry_source=_optional_text(raw, "registry_source"),
        registry_key=registry_key,
        display_icon=_optional_text(raw, "display_icon", "DisplayIcon"),
        estimated_size_kb=_optional_int(raw, "estimated_size_kb", "EstimatedSize"),
        system_component=_registry_bool(raw, "system_component", "SystemComponent"),
        windows_installer=_registry_bool(raw, "windows_installer", "WindowsInstaller"),
        no_remove=_registry_bool(raw, "no_remove", "NoRemove"),
        no_modify=_registry_bool(raw, "no_modify", "NoModify"),
        source=source,
        collected_at=_optional_text(raw, "collected_at"),
        raw=dict(raw),
    )


def normalize_registry_apps(raw_items: list[dict]) -> list[InstalledApp]:
    """Normalize registry records while omitting nameless entries."""

    if not isinstance(raw_items, list):
        raise TypeError("raw_items must be a list")
    normalized = []
    for raw in raw_items:
        app = normalize_registry_app(raw)
        if app is not None:
            normalized.append(app)
    return normalized


def installed_app_to_governance_target(app: InstalledApp) -> GovernanceTarget:
    """Construct a policy input without classifying or authorizing the app."""

    if not isinstance(app, InstalledApp):
        raise TypeError("app must be an InstalledApp")
    return GovernanceTarget(
        target_id=app.app_id,
        object_type=ObjectType.SOFTWARE,
        name=app.name,
        publisher=app.publisher,
        version=app.version,
        path=app.install_location,
        uninstall_available=app.uninstall_available,
        source=app.source,
        evidence_chain=EvidenceChain(
            sources=(app.source,),
            facts=("Normalized from a Windows uninstall registry entry.",),
            references=tuple(
                value
                for value in (app.registry_source, app.registry_key)
                if value is not None
            ),
            confidence=0.5,
        ),
    )


def installed_app_to_scan_target_record(app: InstalledApp, scan_id: str) -> dict:
    """Return fields accepted by SQLiteStateStore.insert_scan_target()."""

    if not isinstance(app, InstalledApp):
        raise TypeError("app must be an InstalledApp")
    if not isinstance(scan_id, str) or not scan_id.strip():
        raise ValueError("scan_id must be a non-empty string")
    normalized_identity = "|".join(
        value.casefold()
        for value in (app.name, app.publisher or "", app.version or "")
    )
    return {
        "target_id": app.app_id,
        "scan_id": scan_id,
        "object_type": ObjectType.SOFTWARE.value,
        "name": app.name,
        "publisher": app.publisher,
        "version": app.version,
        "path": app.install_location,
        "source": app.source,
        "first_seen": app.collected_at,
        "last_seen": app.collected_at,
        "normalized_identity": normalized_identity,
    }
