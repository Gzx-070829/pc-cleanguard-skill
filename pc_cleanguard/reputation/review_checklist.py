"""Human-only review checklist for non-authorizing PUP evidence matches."""

from __future__ import annotations


SAFE_ACTIONS = (
    "review", "keep", "ask_user", "check_vendor_uninstaller",
    "check_defender_or_security_tool", "collect_more_evidence", "report_false_positive",
)
USER_CHECKS = (
    "软件是否由用户主动安装。",
    "安装包是否来自可信官方网站。",
    "是否近期随其他软件捆绑出现。",
    "是否出现异常启动项、服务或计划任务。",
    "是否修改浏览器主页、搜索或扩展。",
    "是否出现弹窗、误导安装或难以卸载行为。",
    "是否被 Microsoft Defender 或其他安全工具独立提示。",
)


def build_human_review_checklist(matches: list[dict], *, behavior_indicators: list[dict] | None = None) -> dict:
    if not isinstance(matches, list) or any(not isinstance(item, dict) for item in matches):
        raise TypeError("matches must be a list of objects")
    items = []
    for match in matches:
        items.append({
            "target_id": match.get("target_id", "unknown"),
            "matched_record_id": match.get("matched_record_id", "unknown"),
            "matched_name": match.get("matched_name", "unknown"),
            "match_basis": match.get("match_basis", "no_match"),
            "matched_indicator_type": match.get("matched_indicator_type"),
            "source_url": match.get("source_url"),
            "source_title": match.get("source_title"),
            "source_date": match.get("source_date"),
            "false_positive_risk": match.get("false_positive_risk", "high"),
            "mapping_type": match.get("mapping_type", "direct_entity"),
            "corroboration_level": match.get("corroboration_level", "no_corroboration"),
            "has_behavior_corroboration": bool(match.get("matched_behavior_indicators")),
            "is_name_or_publisher_overlap": match.get("mapping_type") in {"name_collision_candidate", "related_publisher"},
            "requires_second_source": match.get("false_positive_risk", "high") == "high" or match.get("mapping_type") in {"name_collision_candidate", "related_publisher"},
            "review_hint": match.get("review_hint", "仅供本地人工复核。"),
            "why_not_execution_authorization": match.get("why_not_execution_authorization", "人工复核线索不能授权系统动作。"),
            "checks": list(match.get("human_review_checklist") or USER_CHECKS),
            "suggested_actions": list(SAFE_ACTIONS),
            "false_positive_feedback_route": "仅生成去标识化本地模板并进入 review queue；不会自动改库或上传。",
        })
    behavior_items = []
    for indicator in behavior_indicators or ():
        if not isinstance(indicator, dict) or indicator.get("execution_gating_eligible") is not False:
            raise ValueError("behavior checklist items must remain non-authorizing")
        behavior_items.append({
            "target_id": indicator.get("target_id", "unknown"),
            "behavior_type": indicator.get("behavior_type", "unknown"),
            "observed_value": indicator.get("observed_value", "unknown"),
            "false_positive_risk": indicator.get("false_positive_risk", "high"),
            "checks": ["核对该元数据是否属于用户预期软件。", "结合发布者、来源和安全工具独立结果人工复核。"],
            "suggested_actions": list(SAFE_ACTIONS),
        })
    return {
        "items": items,
        "behavior_items": behavior_items,
        "allowed_actions": list(SAFE_ACTIONS),
        "execution_gating_eligible_count": 0,
    }


def render_human_review_checklist(checklist: dict) -> str:
    lines = ["# PUP Human Review Checklist / 人工复核清单", "", "本清单只支持保留、询问、核验和收集更多证据，不授权系统修改。", ""]
    for item in checklist.get("items", ()):
        lines.extend([
            f"## {item.get('target_id')}", "",
            f"- matched_record_id: `{item.get('matched_record_id')}`",
            f"- evidence: `{item.get('matched_name')}`",
            f"- match_basis: `{item.get('match_basis')}`",
            f"- indicator_type: `{item.get('matched_indicator_type')}`",
            f"- source_url: {item.get('source_url')}",
            f"- source_title: {item.get('source_title')}",
            f"- source_date: {item.get('source_date')}",
            f"- false_positive_risk: `{item.get('false_positive_risk')}`",
            f"- mapping_type: `{item.get('mapping_type')}`",
            f"- corroboration_level: `{item.get('corroboration_level')}`",
            f"- has_behavior_corroboration: `{str(item.get('has_behavior_corroboration')).lower()}`",
            f"- name_or_publisher_overlap: `{str(item.get('is_name_or_publisher_overlap')).lower()}`",
            f"- requires_second_source: `{str(item.get('requires_second_source')).lower()}`",
            f"- review_hint: {item.get('review_hint')}",
            f"- why_not_execution_authorization: {item.get('why_not_execution_authorization')}",
            f"- false_positive_feedback: {item.get('false_positive_feedback_route')}",
            "", "用户应检查：", "",
            *[f"- [ ] {check}" for check in item.get("checks", ())],
            "", "允许的后续建议：", "",
            *[f"- `{action}`" for action in item.get("suggested_actions", ())], "",
        ])
    if checklist.get("behavior_items"):
        lines.extend(["# Behavior Review Items / 行为线索复核", ""])
        for item in checklist["behavior_items"]:
            lines.extend([
                f"## {item.get('target_id')}", "",
                f"- behavior_type: `{item.get('behavior_type')}`",
                f"- observed_value: {item.get('observed_value')}",
                f"- false_positive_risk: `{item.get('false_positive_risk')}`",
                "", "用户应检查：", "",
                *[f"- [ ] {check}" for check in item.get("checks", ())],
                "", "允许的后续建议：", "",
                *[f"- `{action}`" for action in item.get("suggested_actions", ())], "",
            ])
    return "\n".join(lines).rstrip() + "\n"
