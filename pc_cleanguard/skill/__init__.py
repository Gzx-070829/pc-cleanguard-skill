"""AI-callable, non-executing action interface for PC CleanGuard PR10."""

from .actions import (
    ACTION_NAMES,
    SkillActionRequest,
    SkillActionResponse,
    build_cleanup_plan,
    explain_report,
    invoke_skill_action,
    scan_from_json,
    write_audit,
    write_report,
)
from .cleanup_plan import (
    CleanupPlan,
    CleanupPlanStep,
    READ_ONLY_EXECUTION_LEVEL,
    build_cleanup_plan_from_report,
)

__all__ = [
    "ACTION_NAMES",
    "CleanupPlan",
    "CleanupPlanStep",
    "READ_ONLY_EXECUTION_LEVEL",
    "SkillActionRequest",
    "SkillActionResponse",
    "build_cleanup_plan",
    "build_cleanup_plan_from_report",
    "explain_report",
    "invoke_skill_action",
    "scan_from_json",
    "write_audit",
    "write_report",
]
