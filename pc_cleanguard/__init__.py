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

__all__ = [
    "ClassificationLabel",
    "EvidenceChain",
    "GovernanceTarget",
    "ObjectType",
    "PermissionLevel",
    "PolicyDecision",
    "RiskLevel",
    "evaluate_target",
]

__version__ = "0.1.0-pr1"
