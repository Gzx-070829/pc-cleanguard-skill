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


def build_evidence_quality_summary(evidence_packs, *, cn_candidates=(), review_backlog=(), corroboration=None) -> dict:
    records = _flatten(evidence_packs)
    scores = [score_evidence_record_quality(item) for item in records]
    count = len(records)
    prohibited_tone=("一定是流氓","必须删除","建议卸载","软件本体定罪")
    gate_failures=[]
    if any(item.get("execution_authorized") is not False for item in records): gate_failures.append("execution_authorized_not_false")
    if any(item.get("execution_gating_eligible") is True for item in records): gate_failures.append("positive_execution_gating")
    if any(not str(item.get(field,"")).strip() for item in records for field in ("source_url","source_title")): gate_failures.append("missing_source_metadata")
    if any(item.get("mapping_type")=="installer_artifact" and not str(item.get("version_or_time_scope","")).strip() for item in records): gate_failures.append("installer_missing_time_scope")
    if any(item.get("review_status")=="approved_for_explanation" and item.get("source_type")=="user_blocklist_or_forum_list" for item in records): gate_failures.append("approved_user_blocklist")
    if any(any(term in str(item.get("evidence_summary","")) for term in prohibited_tone) for item in records): gate_failures.append("unrestrained_summary")
    result = {
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
        "cn_win_approved_count":sum(item.get("language")=="zh-CN" and item.get("entity_scope") in {"windows_desktop_software","windows_installer"} and item.get("review_status")=="approved_for_explanation" for item in records),
        "cn_win_candidate_count":len(cn_candidates),"cn_win_review_backlog_count":len(review_backlog),
        "cn_win_direct_entity_count":sum(item.get("language")=="zh-CN" and item.get("mapping_type")=="direct_entity" for item in records),
        "cn_win_installer_artifact_count":sum(item.get("language")=="zh-CN" and item.get("mapping_type")=="installer_artifact" for item in records),
        "cn_win_behavior_coverage":round(sum(bool(item.get("observed_behaviors")) for item in records)/count,3) if count else 0,
        "records_with_corroboration_hints":sum(bool(item.get("observed_behaviors")) for item in records),
        "records_without_time_scope":sum(not str(item.get("version_or_time_scope",item.get("source_date",""))).strip() for item in records),
        "records_without_second_source":sum(item.get("false_positive_risk")=="high" for item in records),
        "high_false_positive_risk_records":sum(item.get("false_positive_risk")=="high" for item in records),
        "coverage_data_gaps": [
            "为高误报风险记录补充独立第二来源。",
            "补充版本、签名、组件、分发渠道和本机行为 metadata。",
            "继续覆盖布丁系/万能五笔、浏览器主页/搜索修改链路等未充分核验方向。",
        ],
        "quality_gate_failures":gate_failures,"quality_gate_passed":not gate_failures,
    }
    if corroboration is not None: result["corroborated_match_count"]=corroboration.get("corroborated_match_count",0)
    return result


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
        f"- quality_gate_passed: `{str(summary.get('quality_gate_passed', False)).lower()}`",
        "所有线索仍需人工复核；installer artifact 只描述特定安装器、组件或渠道。",
    ]
    return "\n".join(lines).rstrip() + "\n"
