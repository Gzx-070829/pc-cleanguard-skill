"""PC CleanGuard's non-executing safety policy foundation."""

from .core.models import (
    ClassificationLabel,
    EvidenceChain,
    GovernanceTarget,
    ObjectType,
    PermissionLevel,
    PolicyDecision,
    RiskLevel,
)
from .core.policy_engine import evaluate_target
from .core.execution_plan_builder import build_execution_plan
from .core.report_builder import build_report
from .audit import AuditEvent, JsonlAuditLogger
from .state import SCHEMA_VERSION, SQLiteStateStore
from .reputation import ReputationKnowledgeStore
from .windows import (
    InstalledApp,
    installed_app_to_governance_target,
    installed_app_to_scan_target_record,
    normalize_registry_app,
    normalize_registry_apps,
    ScheduledTask,
    normalize_scheduled_task,
    normalize_scheduled_tasks,
    scheduled_task_to_governance_target,
    scheduled_task_to_scan_target_record,
    WindowsService,
    normalize_service,
    normalize_services,
    service_to_governance_target,
    service_to_scan_target_record,
    StartupItem,
    normalize_startup_item,
    normalize_startup_items,
    startup_item_to_governance_target,
    startup_item_to_scan_target_record,
)
from .pipeline import (
    MAX_SCAN_JSON_BYTES,
    ScanPipelineInput,
    ScanPipelineResult,
    load_scan_json_file,
    load_scan_json_text,
    run_readonly_scan_pipeline,
    write_pipeline_audit_jsonl,
    write_pipeline_report,
)

__all__ = [
    "ClassificationLabel",
    "EvidenceChain",
    "GovernanceTarget",
    "ObjectType",
    "PermissionLevel",
    "PolicyDecision",
    "RiskLevel",
    "evaluate_target",
    "build_execution_plan",
    "build_report",
    "AuditEvent",
    "JsonlAuditLogger",
    "SCHEMA_VERSION",
    "SQLiteStateStore",
    "ReputationKnowledgeStore",
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
    "MAX_SCAN_JSON_BYTES",
    "ScanPipelineInput",
    "ScanPipelineResult",
    "load_scan_json_file",
    "load_scan_json_text",
    "run_readonly_scan_pipeline",
    "write_pipeline_audit_jsonl",
    "write_pipeline_report",
]

__version__ = "0.1.0-pr7"
