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
]
