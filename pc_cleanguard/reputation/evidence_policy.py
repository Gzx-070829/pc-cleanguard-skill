"""Hard evidence-use boundaries: evidence never becomes an execution gate."""

from enum import Enum


class EvidenceUse(str, Enum):
    EXPLAIN_ONLY = "explain_only"
    REVIEW_HINT = "review_hint"
    PUBLISHER_LEVEL_WARNING = "publisher_level_warning"
    NAME_COLLISION_WARNING = "name_collision_warning"
    BLOCKED_FROM_EXECUTION = "blocked_from_execution"


EVIDENCE_BLOCKED_ACTIONS = (
    "no_delete_authorization",
    "no_uninstall_authorization",
    "no_disable_authorization",
    "no_registry_edit_authorization",
)


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


def evidence_guard_status(records: list[dict]) -> dict:
    """Return a fail-closed summary for even the strongest reviewed evidence."""

    if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
        raise TypeError("records must be a list of evidence objects")
    if any(item.get("execution_authorized") is not False for item in records):
        raise ValueError("evidence cannot authorize execution")
    eligible = sum(is_execution_gating_eligible(item) for item in records)
    if eligible:
        raise ValueError("evidence execution gating must remain disabled")
    return {
        "status": "enforced",
        "record_count": len(records),
        "execution_gating_eligible_count": 0,
        "allowed_uses": sorted({classify_evidence_use(item).value for item in records}),
        "blocked_actions": list(EVIDENCE_BLOCKED_ACTIONS),
    }


def build_evidence_guard_reason(record: dict) -> list[str]:
    reasons = ["evidence is explanation/review/sorting/risk-hint only", "execution gating is always blocked"]
    if record.get("is_synthetic"):
        reasons.append("synthetic evidence cannot identify a real entity")
    if record.get("mapping_type") != "direct_entity":
        reasons.append(f"mapping_type={record.get('mapping_type')} is indirect")
    if record.get("entity_scope") != "windows_desktop_software":
        reasons.append(f"entity_scope={record.get('entity_scope')} is not a Windows desktop entity")
    if record.get("relation_confidence") != "high":
        reasons.append("relation confidence is not high")
    return reasons
