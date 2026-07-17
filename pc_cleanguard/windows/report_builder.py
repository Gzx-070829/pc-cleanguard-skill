"""Build the existing report shape from read-only Windows collector records."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .collector_manifest import COLLECTOR_NAMES
from .installed_apps import normalize_registry_apps
from .scheduled_tasks import normalize_scheduled_tasks as _normalize_scheduled_tasks
from .services import normalize_services as _normalize_services
from .startup_items import normalize_startup_items as _normalize_startup_items


_SUPPORTED_FIELDS = {
    "installed_apps": {
        "name", "DisplayName", "publisher", "Publisher", "version", "DisplayVersion",
        "install_location", "InstallLocation", "install_date", "InstallDate",
        "uninstall_string", "UninstallString", "quiet_uninstall_string", "QuietUninstallString",
        "registry_source", "registry_key", "PSPath", "display_icon", "DisplayIcon",
        "estimated_size_kb", "EstimatedSize", "system_component", "SystemComponent",
        "windows_installer", "WindowsInstaller", "no_remove", "NoRemove", "no_modify",
        "NoModify", "source", "collected_at",
    },
    "startup_items": {
        "item_id", "name", "Name", "command", "Command", "location_type",
        "registry_path", "registry_value_name", "startup_folder_path", "file_path",
        "FullName", "publisher", "Publisher", "enabled_state", "source", "collected_at",
    },
    "services": {
        "service_name", "Name", "display_name", "DisplayName", "status", "Status",
        "start_type", "StartMode", "state", "State", "path_name", "PathName",
        "process_id", "ProcessId", "service_type", "ServiceType", "start_name",
        "StartName", "description", "Description", "source", "collected_at",
    },
    "scheduled_tasks": {
        "task_name", "TaskName", "name", "task_path", "TaskPath", "state", "State",
        "author", "Author", "description", "Description", "uri", "URI",
        "actions_summary", "triggers_summary", "principal_user_id", "run_level",
        "source", "collected_at",
    },
}


def _unsupported(raw: dict, collection: str) -> list[str]:
    return sorted(set(raw) - _SUPPORTED_FIELDS[collection])


def normalize_installed_apps(records: list[dict]) -> list[dict]:
    apps = normalize_registry_apps(records)
    result = []
    for app in apps:
        unknown = _unsupported(app.raw, "installed_apps")
        result.append({
            "target_id": app.app_id, "app_id": app.app_id, "name": app.name,
            "display_name": app.name, "publisher": app.publisher, "version": app.version,
            "path": app.install_location, "install_location": app.install_location,
            "install_date": app.install_date, "uninstall_available": app.uninstall_available,
            "uninstall_string": app.uninstall_string,
            "quiet_uninstall_string": app.quiet_uninstall_string,
            "registry_source": app.registry_source, "registry_key": app.registry_key,
            "display_icon": app.display_icon, "estimated_size_kb": app.estimated_size_kb,
            "system_component": app.system_component, "windows_installer": app.windows_installer,
            "no_remove": app.no_remove, "no_modify": app.no_modify,
            "source": app.source, "collected_at": app.collected_at,
            "unsupported_fields": unknown,
        })
    return result


def normalize_startup_items(records: list[dict]) -> list[dict]:
    result = []
    for item in _normalize_startup_items(records):
        unknown = _unsupported(item.raw, "startup_items")
        result.append({
            "target_id": item.item_id, "item_id": item.item_id, "name": item.name,
            "command": item.command, "path": item.file_path or item.startup_folder_path,
            "location_type": item.location_type, "registry_path": item.registry_path,
            "registry_value_name": item.registry_value_name,
            "startup_folder_path": item.startup_folder_path, "file_path": item.file_path,
            "publisher": item.publisher, "enabled_state": item.enabled_state,
            "source": item.source, "collected_at": item.collected_at,
            "unsupported_fields": unknown,
        })
    return result


def normalize_services(records: list[dict]) -> list[dict]:
    result = []
    for service in _normalize_services(records):
        unknown = _unsupported(service.raw, "services")
        result.append({
            "target_id": service.service_id, "service_id": service.service_id,
            "name": service.display_name or service.service_name,
            "service_name": service.service_name, "display_name": service.display_name,
            "status": service.status, "start_type": service.start_type, "state": service.state,
            "path": service.path_name, "path_name": service.path_name,
            "process_id": service.process_id, "service_type": service.service_type,
            "start_name": service.start_name, "description": service.description,
            "source": service.source, "collected_at": service.collected_at,
            "unsupported_fields": unknown,
        })
    return result


def normalize_scheduled_tasks(records: list[dict]) -> list[dict]:
    result = []
    for task in _normalize_scheduled_tasks(records):
        unknown = _unsupported(task.raw, "scheduled_tasks")
        result.append({
            "target_id": task.task_id, "task_id": task.task_id, "name": task.task_name,
            "task_name": task.task_name, "path": task.task_path, "task_path": task.task_path,
            "state": task.state, "author": task.author, "publisher": task.author,
            "description": task.description, "uri": task.uri,
            "actions_summary": task.actions_summary, "triggers_summary": task.triggers_summary,
            "principal_user_id": task.principal_user_id, "run_level": task.run_level,
            "source": task.source, "collected_at": task.collected_at,
            "unsupported_fields": unknown,
        })
    return result


_NORMALIZERS = {
    "installed_apps": normalize_installed_apps,
    "startup_items": normalize_startup_items,
    "services": normalize_services,
    "scheduled_tasks": normalize_scheduled_tasks,
}
_IDENTITY_FIELDS = {
    "installed_apps": ("name", "DisplayName"),
    "startup_items": ("name", "Name"),
    "services": ("service_name", "Name", "display_name", "DisplayName"),
    "scheduled_tasks": ("task_name", "TaskName", "name"),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_windows_canonical_report(collections: dict) -> dict:
    """Combine four metadata families; collected commands remain inert strings."""

    if not isinstance(collections, dict):
        raise TypeError("collections must be a dict")
    raw = collections.get("collections", collections)
    if not isinstance(raw, dict):
        raise TypeError("collections.collections must be a dict")
    status = collections.get("collector_status")
    if status is None:
        status = {
            name: {"status": "success", "record_count": len(raw.get(name, ()) or ())}
            for name in COLLECTOR_NAMES
        }
    if not isinstance(status, dict):
        raise TypeError("collector_status must be a dict")
    normalized = {}
    unsupported_fields = []
    unsupported_records = []
    normalized_status = {}
    for name in COLLECTOR_NAMES:
        records = raw.get(name, []) or []
        if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
            raise ValueError(f"{name} must contain objects")
        values = _NORMALIZERS[name](records)
        normalized[name] = values
        for index, value in enumerate(values):
            for field in value.get("unsupported_fields", ()):
                unsupported_fields.append({"collector": name, "record_index": index, "field": field})
        if len(values) < len(records):
            for index, record in enumerate(records):
                if not any(str(record.get(field, "")).strip() for field in _IDENTITY_FIELDS[name]):
                    unsupported_records.append({
                        "collector": name, "record_index": index,
                        "reason": "record lacked the minimum identity required by the existing model",
                        "fields": sorted(record),
                    })
        item_status = dict(status.get(name, {"status": "failed", "record_count": len(records), "error_code": "missing_manifest_status"}))
        item_status["normalized_count"] = len(values)
        normalized_status[name] = item_status
    states = [item.get("status") for item in normalized_status.values()]
    collection_state = "complete" if all(state == "success" for state in states) else "partial"
    if not any(state == "success" for state in states):
        collection_state = "failed"
    manifest = collections.get("manifest", {})
    timestamp = manifest.get("generated_at") if isinstance(manifest, dict) else None
    timestamp = timestamp if isinstance(timestamp, str) and timestamp.strip() else _now()
    scan_id = f"windows:{uuid4()}"
    return {
        "schema_version": "0.4.1",
        "report_id": scan_id,
        "scan_id": scan_id,
        "timestamp": timestamp,
        "platform": "Windows",
        "privacy_mode": "offline",
        "source_kind": "windows_collector_raw",
        "collection_state": collection_state,
        "collector_status": normalized_status,
        "installed_apps": normalized["installed_apps"],
        "startup_items": normalized["startup_items"],
        "services": normalized["services"],
        "scheduled_tasks": normalized["scheduled_tasks"],
        "processes": [],
        "collection_errors": list(collections.get("collection_errors", ()) or ()),
        "unsupported_collectors": [name for name, item in normalized_status.items() if item.get("status") == "unsupported"],
        "unsupported_fields": unsupported_fields,
        "unsupported_records": unsupported_records,
        "redaction_summary": {"redacted_value_count": 0, "redaction_counts": {}, "reversible_mapping_created": False},
        "execution_gating_eligible_count": 0,
        "execution_authorized": False,
        "runtime_network_access": False,
        "system_modification_performed": False,
    }
