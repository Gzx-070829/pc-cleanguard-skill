"""Software reputation knowledge base: evidence, not a blacklist."""

from .knowledge_store import ReputationKnowledgeStore
from .pup_taxonomy import (
    PUPBehaviorCategory,
    pup_behavior_label_zh,
    pup_taxonomy_records,
)
from .reputation_models import (
    EvidenceType,
    ReputationCategory,
    ReputationConflict,
    ReputationEntry,
    ReputationEvidence,
    ReputationSource,
    ReviewStatus,
    SourceType,
    SuggestedClassification,
)
from .seed_loader import load_seed_records, load_source_manifest, validate_seed_record
from .source_validation import validate_source_manifest
from .matcher import ReputationMatcher, normalize_reputation_name
from .insight import build_pup_insight
from .reporting import render_pup_insight_markdown, write_pup_insight_markdown
from .evidence_pack_loader import load_evidence_pack, validate_evidence_record, evidence_pack_stats
from .evidence_policy import EvidenceUse, classify_evidence_use, is_execution_gating_eligible, build_evidence_guard_reason
from .evidence_intake import (
    EvidenceCandidate,
    build_evidence_pack,
    build_evidence_record_from_candidate,
    load_evidence_candidates,
    validate_evidence_candidate,
    write_evidence_pack,
)
from .evidence_review import ReviewQueueItem, load_evidence_review_queue, validate_review_queue_item
from .indicators import (
    EvidenceIndicator,
    build_indicators_from_evidence,
    normalize_indicator_value,
    summarize_indicators,
    validate_indicator,
    write_indicators,
)
from .review_checklist import build_human_review_checklist, render_human_review_checklist

__all__ = [
    "EvidenceType",
    "PUPBehaviorCategory",
    "ReputationCategory",
    "ReputationConflict",
    "ReputationEntry",
    "ReputationEvidence",
    "ReputationKnowledgeStore",
    "ReputationSource",
    "ReviewStatus",
    "SourceType",
    "SuggestedClassification",
    "pup_behavior_label_zh",
    "pup_taxonomy_records",
    "load_seed_records",
    "load_source_manifest",
    "validate_seed_record",
    "validate_source_manifest",
    "ReputationMatcher",
    "normalize_reputation_name",
    "build_pup_insight",
    "render_pup_insight_markdown",
    "write_pup_insight_markdown",
    "load_evidence_pack", "validate_evidence_record", "evidence_pack_stats",
    "EvidenceUse", "classify_evidence_use", "is_execution_gating_eligible", "build_evidence_guard_reason",
    "EvidenceCandidate", "ReviewQueueItem", "load_evidence_candidates", "validate_evidence_candidate",
    "load_evidence_review_queue", "validate_review_queue_item", "build_evidence_record_from_candidate",
    "build_evidence_pack", "write_evidence_pack",
    "EvidenceIndicator", "build_indicators_from_evidence", "normalize_indicator_value",
    "summarize_indicators", "validate_indicator",
    "write_indicators",
    "build_human_review_checklist", "render_human_review_checklist",
]
