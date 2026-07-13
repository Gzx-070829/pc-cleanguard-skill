"""Offline evidence-quality scoring; never an execution decision."""

from __future__ import annotations

from collections.abc import Iterable


def score_evidence_record_quality(record: dict) -> dict:
    if not isinstance(record, dict):
        raise TypeError("record must be a dict")
    source_fields = ("source_url", "source_title", "source_date", "evidence_summary", "license_note")
    source_completeness = sum(bool(str(record.get(field, "")).strip()) for field in source_fields) / len(source_fields)
    entity_clarity = 1.0 if record.get("entity_scope") in {"windows_desktop_software", "windows_installer"} and record.get("relation_confidence") in {"medium", "high"} else 0.5
    mapping_precision = {"direct_entity": 1.0, "installer_artifact": 0.9, "related_publisher": 0.5, "name_collision_candidate": 0.25, "analogical_behavior": 0.35}.get(record.get("mapping_type"), 0.0)
    time_scope_clarity = 1.0 if str(record.get("version_or_time_scope", record.get("source_date", ""))).strip() else 0.0
    execution_safety = 1.0 if record.get("execution_authorized") is False else 0.0
    review_status_quality = 1.0 if record.get("review_status") == "approved_for_explanation" else 0.6
    behavior_coverage = min(1.0, len(record.get("behavior_categories", ())) / 3)
    false_positive_risk = record.get("false_positive_risk", "high")
    false_positive_risk_quality = {"low": 1.0, "medium": 0.7, "high": 0.4}.get(false_positive_risk, 0.0)
    quality = round(100 * sum((source_completeness, entity_clarity, mapping_precision, time_scope_clarity, false_positive_risk_quality, execution_safety, review_status_quality, behavior_coverage)) / 8, 1)
    return {
        "record_id": record.get("record_id"),
        "source_completeness": round(source_completeness, 3),
        "entity_clarity": entity_clarity,
        "mapping_precision": mapping_precision,
        "time_scope_clarity": time_scope_clarity,
        "false_positive_risk": false_positive_risk,
        "false_positive_risk_quality": false_positive_risk_quality,
        "review_status_quality": review_status_quality,
        "execution_safety": execution_safety,
        "cn_windows_direct_coverage": record.get("language") == "zh-CN" and record.get("mapping_type") == "direct_entity" and record.get("entity_scope") == "windows_desktop_software",
        "behavior_coverage": round(behavior_coverage, 3),
        "needs_more_review": record.get("review_status") != "approved_for_explanation" or false_positive_risk == "high",
        "quality_score": quality,
    }


def _flatten(evidence_packs: Iterable) -> list[dict]:
    records: list[dict] = []
    for pack in evidence_packs:
        if not isinstance(pack, list) or any(not isinstance(item, dict) for item in pack):
            raise TypeError("evidence_packs must contain lists of records")
        records.extend(pack)
    return records


def build_evidence_quality_summary(evidence_packs) -> dict:
    records = _flatten(evidence_packs)
    scores = [score_evidence_record_quality(item) for item in records]
    count = len(records)
    return {
        "total_records": count,
        "real_records": sum(item.get("is_synthetic") is False for item in records),
        "synthetic_records": sum(item.get("is_synthetic") is True for item in records),
        "cn_windows_direct_records": sum(item.get("language") == "zh-CN" and item.get("mapping_type") == "direct_entity" and item.get("entity_scope") == "windows_desktop_software" for item in records),
        "installer_artifact_records": sum(item.get("mapping_type") == "installer_artifact" for item in records),
        "related_publisher_records": sum(item.get("mapping_type") == "related_publisher" for item in records),
        "name_collision_records": sum(item.get("mapping_type") == "name_collision_candidate" for item in records),
        "approved_for_explanation_count": sum(item.get("review_status") == "approved_for_explanation" for item in records),
        "needs_human_review_count": sum(item.get("review_status") == "needs_human_review" for item in records),
        "execution_gating_eligible_count": 0,
        "high_false_positive_risk_count": sum(item.get("false_positive_risk") == "high" for item in records),
        "records_missing_time_scope": sum(not str(item.get("version_or_time_scope", item.get("source_date", ""))).strip() for item in records),
        "records_requiring_second_source": sum(item.get("false_positive_risk") == "high" or item.get("mapping_type") in {"related_publisher", "name_collision_candidate"} for item in records),
        "needs_more_review_count": sum(item["needs_more_review"] for item in scores),
        "evidence_quality_score": round(sum(item["quality_score"] for item in scores) / count, 1) if count else 0.0,
        "record_scores": scores,
        "execution_authorized": False,
    }


def render_evidence_quality_markdown(summary: dict) -> str:
    if not isinstance(summary, dict):
        raise TypeError("summary must be a dict")
    lines = [
        "# Evidence 数据质量 Dashboard", "",
        "这是 evidence 数据质量与覆盖面报告，不是黑名单，也不是删除、卸载、禁用或注册表修改授权。", "",
        f"- total_records: `{summary['total_records']}`",
        f"- real_records: `{summary['real_records']}`",
        f"- cn_windows_direct_records: `{summary['cn_windows_direct_records']}`",
        f"- installer_artifact_records: `{summary['installer_artifact_records']}`",
        f"- evidence_quality_score: `{summary['evidence_quality_score']}`",
        f"- high_false_positive_risk_count: `{summary['high_false_positive_risk_count']}`",
        f"- records_requiring_second_source: `{summary['records_requiring_second_source']}`",
        f"- execution_gating_eligible_count: `{summary['execution_gating_eligible_count']}`", "",
        "所有线索仍需人工复核；installer artifact 只描述特定安装器、组件或渠道。",
    ]
    return "\n".join(lines).rstrip() + "\n"
