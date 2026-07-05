"""Dependency-free data contracts for PC CleanGuard PR1.

These models describe policy evidence and decisions. They do not describe or
provide an execution mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple


class ClassificationLabel(str, Enum):
    KEEP = "KEEP"
    ASK_USER = "ASK_USER"
    SAFE_REMOVE = "SAFE_REMOVE"
    STARTUP_OFF = "STARTUP_OFF"
    QUARANTINE = "QUARANTINE"
    BLOCK = "BLOCK"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PermissionLevel(str, Enum):
    LEVEL_0_READ_ONLY = "LEVEL_0_READ_ONLY"
    LEVEL_1_LOW_RISK_CLEANUP = "LEVEL_1_LOW_RISK_CLEANUP"
    LEVEL_2_REVERSIBLE = "LEVEL_2_REVERSIBLE"
    LEVEL_3_STANDARD_UNINSTALL = "LEVEL_3_STANDARD_UNINSTALL"
    LEVEL_4_HIGH_RISK_SYSTEM_MODIFICATION = (
        "LEVEL_4_HIGH_RISK_SYSTEM_MODIFICATION"
    )
    LEVEL_5_FORBIDDEN = "LEVEL_5_FORBIDDEN"


class ObjectType(str, Enum):
    SOFTWARE = "SOFTWARE"
    STARTUP_ITEM = "STARTUP_ITEM"
    SERVICE = "SERVICE"
    PROCESS = "PROCESS"
    FILE = "FILE"
    DIRECTORY = "DIRECTORY"
    REGISTRY_ENTRY = "REGISTRY_ENTRY"
    SCHEDULED_TASK = "SCHEDULED_TASK"


@dataclass(frozen=True)
class EvidenceChain:
    """Evidence available to a decision, without raw file contents."""

    sources: Tuple[str, ...] = field(default_factory=tuple)
    facts: Tuple[str, ...] = field(default_factory=tuple)
    references: Tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    @property
    def is_empty(self) -> bool:
        return not self.sources and not self.facts and not self.references

    @property
    def has_substantive_evidence(self) -> bool:
        return bool(self.facts or self.references)


@dataclass(frozen=True)
class GovernanceTarget:
    """A normalized object presented to the policy evaluator."""

    target_id: str
    object_type: ObjectType
    name: str
    publisher: Optional[str] = None
    version: Optional[str] = None
    path: Optional[str] = None
    uninstall_available: bool = False
    user_declared_core: bool = False
    source: str = "local_metadata"
    evidence_chain: EvidenceChain = field(default_factory=EvidenceChain)
    known_bloatware: bool = False
    suspicious: bool = False
    requested_classification: Optional[ClassificationLabel] = None
    community_recommendation: Optional[ClassificationLabel] = None
    online_reputation: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.target_id.strip():
            raise ValueError("target_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")


@dataclass(frozen=True)
class PolicyDecision:
    """A policy judgment. It is never an instruction to modify the system."""

    target_id: str
    classification: ClassificationLabel
    risk_level: RiskLevel
    permission_level: PermissionLevel
    allowed: bool
    reason: str
    evidence_chain: EvidenceChain
    required_confirmation: bool
    rollback_required: bool
    audit_required: bool
    blocked_by_hard_rule: bool
