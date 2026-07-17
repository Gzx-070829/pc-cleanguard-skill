"""Validate the directory contract emitted by the read-only PowerShell collectors."""

from __future__ import annotations


COLLECTOR_NAMES = (
    "installed_apps",
    "startup_items",
    "services",
    "scheduled_tasks",
)
COLLECTOR_STATUSES = frozenset({"success", "failed", "unsupported"})


def validate_collector_manifest(manifest: dict) -> list[str]:
    """Return deterministic validation errors without executing any collector."""

    if not isinstance(manifest, dict):
        return ["manifest must be a JSON object"]
    errors: list[str] = []
    if manifest.get("schema_version") != "0.4.1":
        errors.append("schema_version must be 0.4.1")
    if manifest.get("source_kind") != "windows_powershell_collector":
        errors.append("source_kind must be windows_powershell_collector")
    if not isinstance(manifest.get("generated_at"), str) or not manifest["generated_at"].strip():
        errors.append("generated_at must be a non-empty string")
    collectors = manifest.get("collectors")
    if not isinstance(collectors, dict):
        return [*errors, "collectors must be an object"]
    for name in COLLECTOR_NAMES:
        item = collectors.get(name)
        if not isinstance(item, dict):
            errors.append(f"{name} collector status is required")
            continue
        if item.get("status") not in COLLECTOR_STATUSES:
            errors.append(f"{name}.status is invalid")
        if item.get("file") != f"{name}.json":
            errors.append(f"{name}.file must be {name}.json")
        count = item.get("record_count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            errors.append(f"{name}.record_count must be a non-negative integer")
        if item.get("status") != "success" and not str(item.get("error_code", "")).strip():
            errors.append(f"{name}.error_code is required for non-success status")
    unexpected = sorted(set(collectors) - set(COLLECTOR_NAMES))
    if unexpected:
        errors.append(f"unexpected collectors: {', '.join(unexpected)}")
    return errors
