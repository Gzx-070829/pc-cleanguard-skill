"""Evidence-oriented reputation data contracts, never execution verdicts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ReputationCategory(str, Enum):
    POSSIBLE_PUP = "POSSIBLE_PUP"
    ADWARE = "ADWARE"
    BUNDLED_SOFTWARE = "BUNDLED_SOFTWARE"
    FAKE_OPTIMIZER = "FAKE_OPTIMIZER"
    BROWSER_HIJACKER_CANDIDATE = "BROWSER_HIJACKER_CANDIDATE"
    VENDOR_BLOATWARE = "VENDOR_BLOATWARE"
    PREINSTALLED_BLOATWARE = "PREINSTALLED_BLOATWARE"
    DUPLICATE_UTILITY = "DUPLICATE_UTILITY"
    UNKNOWN_REPUTATION = "UNKNOWN_REPUTATION"


class SuggestedClassification(str, Enum):
    ASK_USER = "ASK_USER"
    STARTUP_OFF = "STARTUP_OFF"
    SAFE_REMOVE_CANDIDATE = "SAFE_REMOVE_CANDIDATE"
    QUARANTINE_CANDIDATE = "QUARANTINE_CANDIDATE"


class SourceType(str, Enum):
    OFFICIAL_VENDOR = "OFFICIAL_VENDOR"
    SECURITY_VENDOR = "SECURITY_VENDOR"
    CURATED_RULEPACK = "CURATED_RULEPACK"
    COMMUNITY_REPORT = "COMMUNITY_REPORT"
    USER_LOCAL = "USER_LOCAL"
    AI_ASSESSMENT = "AI_ASSESSMENT"
    UNKNOWN = "UNKNOWN"


class ReviewStatus(str, Enum):
    DRAFT = "DRAFT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REVIEWED = "REVIEWED"
    DEPRECATED = "DEPRECATED"
    DISPUTED = "DISPUTED"
    EMERGENCY_WARNING = "EMERGENCY_WARNING"


class EvidenceType(str, Enum):
    STARTUP_BEHAVIOR = "STARTUP_BEHAVIOR"
    BUNDLED_INSTALL = "BUNDLED_INSTALL"
    BROWSER_INJECTION = "BROWSER_INJECTION"
    ADS_OR_POPUPS = "ADS_OR_POPUPS"
    MISLEADING_CLAIM = "MISLEADING_CLAIM"
    REAPPEARANCE_AFTER_REMOVAL = "REAPPEARANCE_AFTER_REMOVAL"
    HIGH_BACKGROUND_USAGE = "HIGH_BACKGROUND_USAGE"
    SECURITY_VENDOR_SIGNAL = "SECURITY_VENDOR_SIGNAL"
    COMMUNITY_REPORT = "COMMUNITY_REPORT"
    OFFICIAL_VENDOR_INFO = "OFFICIAL_VENDOR_INFO"
    KNOWN_UNINSTALLER = "KNOWN_UNINSTALLER"
    FALSE_POSITIVE_NOTE = "FALSE_POSITIVE_NOTE"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_confidence(value: float) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError("confidence must be numeric")
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class ReputationSource:
    source_id: str
    source_name: str
    source_type: SourceType
    trust_tier: str
    created_at: str
    updated_at: str
    homepage: Optional[str] = None
    license: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        for name in (
            "source_id",
            "source_name",
            "trust_tier",
            "created_at",
            "updated_at",
        ):
            _require_text(name, getattr(self, name))
        if not isinstance(self.source_type, SourceType):
            raise ValueError("source_type must be a SourceType")


@dataclass(frozen=True, slots=True)
class ReputationEntry:
    entry_id: str
    canonical_name: str
    category: ReputationCategory
    suggested_classification: SuggestedClassification
    confidence: float
    severity: str
    false_positive_risk: str
    review_status: ReviewStatus
    first_seen: str
    last_updated: str
    publisher: Optional[str] = None
    rulepack_version: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        for name in (
            "entry_id",
            "canonical_name",
            "severity",
            "false_positive_risk",
            "first_seen",
            "last_updated",
        ):
            _require_text(name, getattr(self, name))
        if not isinstance(self.category, ReputationCategory):
            raise ValueError("category must be a ReputationCategory")
        if not isinstance(self.suggested_classification, SuggestedClassification):
            raise ValueError(
                "suggested_classification must be a non-authorizing candidate"
            )
        if not isinstance(self.review_status, ReviewStatus):
            raise ValueError("review_status must be a ReviewStatus")
        _require_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class ReputationEvidence:
    evidence_id: str
    entry_id: str
    source_id: str
    evidence_type: EvidenceType
    summary: str
    confidence: float
    captured_at: str
    observed_behavior: Optional[str] = None
    version_range: Optional[str] = None
    path_pattern: Optional[str] = None
    startup_indicator: Optional[str] = None
    service_indicator: Optional[str] = None
    network_reputation_summary: Optional[str] = None
    source_reference: Optional[str] = None
    license_note: Optional[str] = None

    def __post_init__(self) -> None:
        for name in (
            "evidence_id",
            "entry_id",
            "source_id",
            "summary",
            "captured_at",
        ):
            _require_text(name, getattr(self, name))
        if not isinstance(self.evidence_type, EvidenceType):
            raise ValueError("evidence_type must be an EvidenceType")
        _require_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class ReputationConflict:
    conflict_id: str
    entry_id: str
    conflict_type: str
    requires_user_context: bool
    created_at: str
    positive_summary: Optional[str] = None
    negative_summary: Optional[str] = None
    resolution_note: Optional[str] = None

    def __post_init__(self) -> None:
        for name in ("conflict_id", "entry_id", "conflict_type", "created_at"):
            _require_text(name, getattr(self, name))
        if not isinstance(self.requires_user_context, bool):
            raise ValueError("requires_user_context must be a bool")
