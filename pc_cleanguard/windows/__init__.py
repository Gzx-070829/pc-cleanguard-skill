"""Read-only Windows metadata normalization helpers."""

from .installed_apps import (
    InstalledApp,
    installed_app_to_governance_target,
    installed_app_to_scan_target_record,
    normalize_registry_app,
    normalize_registry_apps,
)

__all__ = [
    "InstalledApp",
    "installed_app_to_governance_target",
    "installed_app_to_scan_target_record",
    "normalize_registry_app",
    "normalize_registry_apps",
]
