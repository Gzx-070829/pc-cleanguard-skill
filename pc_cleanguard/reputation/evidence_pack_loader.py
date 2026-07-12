"""Strict offline loading for orthogonal reputation evidence records."""

import json
from pathlib import Path

from .evidence_policy import is_execution_gating_eligible
from .pup_taxonomy import PUPBehaviorCategory

MAPPING_TYPES={"direct_entity","related_publisher","name_collision_candidate","analogical_behavior"}
ENTITY_SCOPES={"windows_desktop_software","mobile_app","mobile_sdk","browser_extension","publisher_level","unknown"}
RELATION_CONFIDENCE={"low","medium","high","unknown"}
REVIEW_STATUS={"needs_human_review","approved_for_explanation"}
REQUIRED={"record_id","software_name","publisher","aliases","source_type","source_name","source_url","source_title","source_date","evidence_summary","behavior_categories","jurisdiction","language","review_status","confidence","false_positive_risk","execution_authorized","license_note","evidence_scope","mapping_type","is_synthetic","entity_scope","relation_confidence"}


def validate_evidence_record(record: dict) -> dict:
    if not isinstance(record, dict) or not REQUIRED.issubset(record) or set(record)-REQUIRED-{"analogy_basis"}:
        raise ValueError("evidence record fields do not match PR24 schema")
    if record["execution_authorized"] is not False:
        raise ValueError("evidence cannot authorize execution")
    if record["mapping_type"] not in MAPPING_TYPES or record["mapping_type"] == "synthetic_example":
        raise ValueError("invalid mapping_type")
    if type(record["is_synthetic"]) is not bool:
        raise ValueError("is_synthetic must be bool")
    if record["entity_scope"] not in ENTITY_SCOPES or record["relation_confidence"] not in RELATION_CONFIDENCE:
        raise ValueError("invalid evidence relation scope")
    if record["review_status"] not in REVIEW_STATUS:
        raise ValueError("invalid evidence review status")
    taxonomy={item.value for item in PUPBehaviorCategory}
    if not record["behavior_categories"] or not set(record["behavior_categories"]).issubset(taxonomy):
        raise ValueError("invalid behavior categories")
    if record["mapping_type"] == "analogical_behavior" and not str(record.get("analogy_basis", "")).strip():
        raise ValueError("analogical_behavior requires analogy_basis")
    is_miit = "miit" in record["source_name"].casefold() or "工信" in record["source_name"]
    if is_miit:
        if record["entity_scope"] not in {"mobile_app","mobile_sdk"} or record["mapping_type"] not in {"analogical_behavior","related_publisher"} or record["is_synthetic"] is not False or not str(record.get("analogy_basis", "")).strip():
            raise ValueError("MIIT APP/SDK evidence must remain mobile and analogical/publisher-level")
    return record


def load_evidence_pack(path) -> list[dict]:
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,list): raise ValueError("evidence pack must be an array")
    records=[validate_evidence_record(item) for item in data]
    if len({item["record_id"] for item in records}) != len(records): raise ValueError("duplicate record_id")
    return records


def evidence_pack_stats(records: list[dict]) -> dict:
    return {
        **{f"{kind}_count":sum(r["mapping_type"]==kind for r in records) for kind in MAPPING_TYPES},
        "synthetic_count":sum(r["is_synthetic"] for r in records),
        "real_source_count":sum(not r["is_synthetic"] for r in records),
        "execution_gating_eligible_count":sum(is_execution_gating_eligible(r) for r in records),
    }
