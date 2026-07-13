"""Build structured PUP insight from non-authorizing reputation matches."""

SAFETY_NOTICE = (
    "此洞察不是删除授权、不是卸载授权、不是禁用授权；"
    "真实来源 evidence 仅用于解释、排序和人工复核，不是删除、卸载、禁用授权；"
    "所有不确定项需要用户确认。"
)


def build_pup_insight(matches: list[dict]) -> dict:
    if not isinstance(matches, list) or any(not isinstance(item, dict) for item in matches):
        raise TypeError("matches must be a list of objects")
    if any(item.get("execution_authorized") is not False for item in matches):
        raise ValueError("reputation matches cannot authorize execution")
    categories = sorted({category for item in matches for category in item.get("behavior_categories", ())})
    uncertain = []
    for item in matches:
        mapping = item.get("mapping_type", "unknown")
        if mapping == "analogical_behavior":
            uncertain.append(
                f"{item.get('target_id', 'unknown')}: analogical_behavior 仅为行为类比；basis={item.get('analogy_basis') or 'missing'}"
            )
        elif mapping == "related_publisher":
            uncertain.append(
                f"{item.get('target_id', 'unknown')}: publisher-level warning only，不能归因到具体软件。"
            )
        elif mapping == "name_collision_candidate":
            uncertain.append(
                f"{item.get('target_id', 'unknown')}: name collision candidate，置信度已降低并需要身份复核。"
            )
        elif item.get("false_positive_risk") != "low" or item.get("review_status") != "approved_for_explanation":
            uncertain.append(
                f"{item.get('target_id', 'unknown')}: mapping_type={mapping}, false_positive_risk={item.get('false_positive_risk', 'high')}"
            )
    mapping_counts = {
        f"{mapping}_count": sum(item.get("mapping_type") == mapping for item in matches)
        for mapping in (
            "direct_entity",
            "analogical_behavior",
            "related_publisher",
            "name_collision_candidate",
        )
    }
    return {
        "summary": {
            "matched_targets": len(matches),
            "behavior_category_count": len(categories),
            "real_source_match_count": sum(item.get("is_synthetic") is False for item in matches),
            "synthetic_match_count": sum(item.get("is_synthetic") is True for item in matches),
            **mapping_counts,
            "execution_gating_eligible_count": 0,
        },
        "suspicious_behaviors": categories,
        "matched_targets": [dict(item) for item in matches],
        "uncertainty_notes": uncertain or ["没有命中并不证明安全；仍需结合本地证据人工复核。"],
        "recommended_review": ["核对软件身份、发布者、安装来源与用户意图。", "在任何系统操作前重新经过 Policy Engine 和用户确认。"],
        "blocked_actions": ["automatic_delete", "automatic_uninstall", "automatic_disable"],
        "safety_notice": SAFETY_NOTICE,
        "next_steps_for_user": ["查看命中证据和误报风险。", "不确定时保留软件并请求人工复核。"],
        "requires_user_confirmation": True,
        "execution_authorized": False,
        "evidence_guard_applied": True,
    }

