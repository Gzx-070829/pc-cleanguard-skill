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
]

__version__ = "0.1.0-pr4"
