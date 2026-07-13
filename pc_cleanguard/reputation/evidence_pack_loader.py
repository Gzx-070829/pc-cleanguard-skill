"""Strict offline loading for orthogonal reputation evidence records."""

import json
from pathlib import Path

from .evidence_policy import is_execution_gating_eligible
from .pup_taxonomy import PUPBehaviorCategory

MAPPING_TYPES={"direct_entity","installer_artifact","related_publisher","name_collision_candidate","analogical_behavior"}
ENTITY_SCOPES={"windows_desktop_software","windows_installer","mobile_app","mobile_sdk","browser_extension","publisher_level","unknown"}
RELATION_CONFIDENCE={"low","medium","high","unknown"}
REVIEW_STATUS={"needs_human_review","approved_for_explanation"}
REQUIRED={"record_id","software_name","publisher","aliases","source_type","source_name","source_url","source_title","source_date","evidence_summary","behavior_categories","jurisdiction","language","review_status","confidence","false_positive_risk","execution_authorized","license_note","evidence_scope","mapping_type","is_synthetic","entity_scope","relation_confidence"}
PRECISION_FIELDS={"version_or_time_scope","affected_component","installer_or_bundle_artifact","distribution_channel","observed_behaviors","source_quote_summary","reviewer_notes","guard_reason"}


def validate_evidence_record(record: dict) -> dict:
    if not isinstance(record, dict) or not REQUIRED.issubset(record) or set(record)-REQUIRED-PRECISION_FIELDS-{"analogy_basis"}:
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
    if record["entity_scope"] in {"mobile_app", "mobile_sdk"} and record["mapping_type"] == "direct_entity":
        raise ValueError("mobile evidence cannot be a direct Windows entity")
    if record["mapping_type"] == "installer_artifact":
        if record["entity_scope"] != "windows_installer":
            raise ValueError("installer_artifact requires windows_installer scope")
        if not all(str(record.get(field, "")).strip() for field in (
            "installer_or_bundle_artifact", "version_or_time_scope", "affected_component"
        )):
            raise ValueError("installer_artifact requires artifact, time scope, and affected component")
        summary = str(record.get("evidence_summary", ""))
        if any(term in summary for term in ("永久属于流氓", "软件本体定罪", "必须处理", "必须删除", "建议卸载")):
            raise ValueError("installer_artifact summary must not convict the whole product")
    if record["mapping_type"] == "direct_entity" and record["entity_scope"] == "windows_desktop_software":
        if record["relation_confidence"] not in {"medium", "high"}:
            raise ValueError("Windows direct evidence requires medium or high relation confidence")
    if record["mapping_type"] == "related_publisher" and record["entity_scope"] != "publisher_level":
        raise ValueError("related_publisher evidence must remain publisher-level")
    if record["mapping_type"] == "name_collision_candidate" and record["false_positive_risk"] != "high":
        raise ValueError("name collision evidence requires high false-positive risk")
    pr29_source_types = {"security_vendor_public_article", "reputable_media_report", "vendor_public_notice", "official_or_regulatory_notice"}
    if record["source_type"] in pr29_source_types and record["language"] == "zh-CN" and record["entity_scope"] in {"windows_desktop_software", "windows_installer"} and record["is_synthetic"] is False:
        if not PRECISION_FIELDS.issubset(record):
            raise ValueError("CN Windows real evidence requires PR29 precision fields")
        if not isinstance(record["observed_behaviors"], list) or not record["observed_behaviors"]:
            raise ValueError("CN Windows real evidence requires observed behaviors")
    if record["is_synthetic"] is False:
        if record["source_type"] == "synthetic_example":
            raise ValueError("real evidence requires a public source type")
        if not all(str(record[field]).strip() for field in ("source_url", "source_title", "source_date", "evidence_summary")):
            raise ValueError("real evidence requires source URL, title, date, and summary")
        if not record["source_url"].startswith(("https://", "http://")):
            raise ValueError("real evidence requires a public source URL")
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
