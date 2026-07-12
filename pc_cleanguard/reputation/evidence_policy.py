"""Hard evidence-use boundaries: evidence never becomes an execution gate."""

from enum import Enum


class EvidenceUse(str, Enum):
    EXPLAIN_ONLY = "explain_only"
    REVIEW_HINT = "review_hint"
    PUBLISHER_LEVEL_WARNING = "publisher_level_warning"
    NAME_COLLISION_WARNING = "name_collision_warning"
    BLOCKED_FROM_EXECUTION = "blocked_from_execution"


def classify_evidence_use(record: dict) -> EvidenceUse:
    mapping = record.get("mapping_type")
    if mapping == "related_publisher":
        return EvidenceUse.PUBLISHER_LEVEL_WARNING
    if mapping == "name_collision_candidate":
        return EvidenceUse.NAME_COLLISION_WARNING
    if mapping == "direct_entity" and record.get("entity_scope") == "windows_desktop_software":
        return EvidenceUse.REVIEW_HINT
    return EvidenceUse.EXPLAIN_ONLY


def is_execution_gating_eligible(record: dict) -> bool:
    return False


def build_evidence_guard_reason(record: dict) -> list[str]:
    reasons = ["PR24 evidence is explanation/review/sorting/risk-hint only", "execution gating is always blocked"]
    if record.get("is_synthetic"):
        reasons.append("synthetic evidence cannot identify a real entity")
    if record.get("mapping_type") != "direct_entity":
        reasons.append(f"mapping_type={record.get('mapping_type')} is indirect")
    if record.get("entity_scope") != "windows_desktop_software":
        reasons.append(f"entity_scope={record.get('entity_scope')} is not a Windows desktop entity")
    if record.get("relation_confidence") != "high":
        reasons.append("relation confidence is not high")
    return reasons
