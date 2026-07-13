"""Build a local, source-traceable PUP intelligence review report."""

from __future__ import annotations

from pathlib import Path

from ..reputation import (
    ReputationMatcher,
    build_human_review_checklist,
    build_indicators_from_evidence,
    build_pup_insight,
    evidence_guard_status,
    load_evidence_pack,
)
from .behavior_indicators import build_behavior_indicators_from_report


BLOCKED_ACTIONS = [
    "no_delete_authorization",
    "no_uninstall_authorization",
    "no_disable_authorization",
    "no_registry_edit_authorization",
]


def build_safety_notice() -> str:
    return (
        "真实来源 evidence 和 indicator match 仅用于解释、排序和人工复核，"
        "不是删除、卸载、禁用或注册表修改授权。Review Pack 在本地离线生成，"
        "不联网、不上传，也不替代 Microsoft Defender 或其他安全工具。"
    )


def _records(value) -> list[dict]:
    if isinstance(value, (str, Path)):
        return load_evidence_pack(value)
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise TypeError("evidence_pack must be a path or list of records")
    return value


def build_pup_intelligence_report(
    report: dict,
    evidence_pack,
    include_indicators: bool = True,
    *,
    cn_evidence_pack=None,
    include_behavior_indicators: bool = False,
) -> dict:
    if not isinstance(report, dict):
        raise TypeError("report must be a dict")
    if not isinstance(include_indicators, bool):
        raise TypeError("include_indicators must be bool")
    if not isinstance(include_behavior_indicators, bool):
        raise TypeError("include_behavior_indicators must be bool")
    primary_records = _records(evidence_pack)
    cn_records = _records(cn_evidence_pack) if cn_evidence_pack is not None else []
    records = [*primary_records, *cn_records]
    indicators = [item for record in records for item in build_indicators_from_evidence(record)] if include_indicators else []
    matches = ReputationMatcher(records, include_indicators=include_indicators).match(report)
    insight = build_pup_insight(matches)
    counts = insight["summary"]
    behavior_indicators = build_behavior_indicators_from_report(report) if include_behavior_indicators else []
    cn_record_ids = {item["record_id"] for item in cn_records}
    cn_match_count = sum(item.get("matched_record_id") in cn_record_ids for item in matches)
    guard = evidence_guard_status(records)
    uncertainty_notes = list(insight["uncertainty_notes"])
    uncertainty_notes.extend(
        f"{item['target_id']}: behavior_type={item['behavior_type']} 误伤风险高，只能人工复核。"
        for item in behavior_indicators
        if item["false_positive_risk"] == "high"
    )
    return {
        "summary": {
            **counts,
            "cn_real_source_count": len(cn_records),
            "cn_match_count": cn_match_count,
            "behavior_indicator_count": len(behavior_indicators),
            "adversarial_guard_status": guard["status"],
        },
        "risk_overview": {
            strength: sum(match.get("match_strength") == strength for match in matches)
            for strength in ("exact", "strong", "medium", "weak", "informational")
        },
        "real_source_match_count": counts["real_source_match_count"],
        "synthetic_match_count": counts["synthetic_match_count"],
        "direct_entity_count": counts["direct_entity_count"],
        "analogical_behavior_count": counts["analogical_behavior_count"],
        "related_publisher_count": counts["related_publisher_count"],
        "name_collision_candidate_count": counts["name_collision_candidate_count"],
        "indicator_match_count": counts["indicator_match_count"],
        "detection_family_match_count": counts["detection_family_match_count"],
        "publisher_hint_match_count": counts["publisher_hint_match_count"],
        "high_uncertainty_match_count": counts["high_uncertainty_match_count"],
        "human_review_required_count": counts["human_review_required_count"],
        "cn_real_source_count": len(cn_records),
        "cn_match_count": cn_match_count,
        "behavior_indicator_count": len(behavior_indicators),
        "adversarial_guard_status": guard["status"],
        "execution_gating_eligible_count": 0,
        "matches": matches,
        "evidence_indicators": indicators,
        "behavior_indicators": behavior_indicators,
        "human_review_checklist": build_human_review_checklist(
            matches, behavior_indicators=behavior_indicators
        ),
        "uncertainty_notes": uncertainty_notes,
        "blocked_actions": list(BLOCKED_ACTIONS),
        "safety_notice": build_safety_notice(),
        "next_steps_for_user": [
            "先查看 source_url、match_basis、false_positive_risk 与人工复核清单。",
            "核对本地软件身份与用户安装意图；证据不足时保留并收集更多证据。",
            "若名称或实体不一致，提交本地 false-positive feedback 模板供人工修订。",
        ],
        "execution_authorized": False,
        "runtime_network_access": False,
    }
