"""Read-only Windows metadata normalization helpers."""

from .installed_apps import (
    InstalledApp,
    installed_app_to_governance_target,
    installed_app_to_scan_target_record,
    normalize_registry_app,
    normalize_registry_apps,
)
from .scheduled_tasks import (
    ScheduledTask,
    normalize_scheduled_task,
    normalize_scheduled_tasks,
    scheduled_task_to_governance_target,
    scheduled_task_to_scan_target_record,
)
from .services import (
    WindowsService,
    normalize_service,
    normalize_services,
    service_to_governance_target,
    service_to_scan_target_record,
)
from .startup_items import (
    StartupItem,
    normalize_startup_item,
    normalize_startup_items,
    startup_item_to_governance_target,
    startup_item_to_scan_target_record,
)
from .collector_ingest import load_collector_directory
from .collector_manifest import COLLECTOR_NAMES, validate_collector_manifest
from .report_builder import build_windows_canonical_report
from .report_redaction import redact_windows_report
from .report_validation import validate_windows_canonical_report, windows_report_stats

__all__ = [
    "InstalledApp",
    "installed_app_to_governance_target",
    "installed_app_to_scan_target_record",
    "normalize_registry_app",
    "normalize_registry_apps",
    "ScheduledTask",
    "normalize_scheduled_task",
    "normalize_scheduled_tasks",
    "scheduled_task_to_governance_target",
    "scheduled_task_to_scan_target_record",
    "WindowsService",
    "normalize_service",
    "normalize_services",
    "service_to_governance_target",
    "service_to_scan_target_record",
    "StartupItem",
    "normalize_startup_item",
    "normalize_startup_items",
    "startup_item_to_governance_target",
    "startup_item_to_scan_target_record",
    "COLLECTOR_NAMES",
    "load_collector_directory",
    "validate_collector_manifest",
    "build_windows_canonical_report",
    "redact_windows_report",
    "validate_windows_canonical_report",
    "windows_report_stats",
]
