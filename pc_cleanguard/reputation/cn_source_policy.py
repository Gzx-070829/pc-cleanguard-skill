"""Conservative admission decisions for offline Chinese public sources."""

from __future__ import annotations

from .cn_source_matrix import validate_cn_source


def classify_cn_source_use(source: dict) -> dict:
    source = validate_cn_source(source)
    source_class = source["source_class"]
    forced_candidate = source_class in {
        "community_multi_report", "user_blocklist_or_forum_list",
        "reputable_media_report", "historical_public_list",
    }
    can_enter_pack = (
        source_class in {"official_or_regulatory_notice", "security_vendor_public_article"}
        and source["allowed_use"] in {"explanation_only", "review_hint", "publisher_level_warning"}
    )
    if source_class == "community_multi_report" and source["cross_source_count"] < 2:
        can_enter_pack = False
    return {
        "allowed_use": source["allowed_use"],
        "forbidden_use": list(source["forbidden_use"]),
        "requires_second_source": source["requires_second_source"],
        "can_enter_evidence_pack": bool(can_enter_pack and not forced_candidate),
        "can_enter_review_queue": source_class not in {"historical_public_list", "user_blocklist_or_forum_list"},
        "can_enter_candidate_only": True,
        "execution_gating_eligible_count": 0,
        "execution_authorized": False,
    }


def build_cn_source_guard_reason(source: dict) -> list[str]:
    decision = classify_cn_source_use(source)
    reasons = ["中文公开来源只提供 candidate/review/explanation 线索，不是执行授权。"]
    source_class = source["source_class"]
    if source_class == "user_blocklist_or_forum_list":
        reasons.append("网友名单或屏蔽列表只能 candidate-only，必须找到更强的第二来源。")
    if source_class == "community_multi_report":
        reasons.append("社区多源反馈仍需人工复核，不能直接进入 approved evidence。")
    if source_class == "historical_public_list":
        reasons.append("历史榜只保留 historical context，不能成为现代 Windows 删除名单。")
    if source_class == "security_vendor_public_article":
        reasons.append("安全厂商文章只取公开行为描述，不采集签名、规则或检测逻辑。")
    if source["platform_scope"] in {"mobile_app", "mobile_sdk"}:
        reasons.append("移动端 APP/SDK 来源只能做行为类比，不能映射 Windows direct_entity。")
    if decision["requires_second_source"]:
        reasons.append("requires_second_source=true：在交叉核验前保持 candidate。")
    reasons.append("固定禁止删除、卸载、禁用和注册表修改授权。")
    return reasons


def summarize_cn_source_matrix(sources: list[dict]) -> dict:
    if not isinstance(sources, list):
        raise TypeError("sources must be a list")
    validated = [validate_cn_source(item) for item in sources]
    by_class = {
        source_class: sum(item["source_class"] == source_class for item in validated)
        for source_class in sorted({item["source_class"] for item in validated})
    }
    return {
        "cn_source_count": len(validated),
        "cn_candidate_only_count": sum(item["allowed_use"] == "candidate_only" for item in validated),
        "cn_requires_second_source_count": sum(item["requires_second_source"] for item in validated),
        "cn_historical_source_count": sum(item["source_class"] == "historical_public_list" for item in validated),
        "cn_security_vendor_public_article_count": sum(item["source_class"] == "security_vendor_public_article" for item in validated),
        "cn_user_blocklist_count": sum(item["source_class"] == "user_blocklist_or_forum_list" for item in validated),
        "by_source_class": by_class,
        "execution_gating_eligible_count": 0,
        "execution_authorized": False,
        "runtime_network_access": False,
    }


def summarize_cn_candidate_sources(candidates: list[dict]) -> dict:
    from .cn_source_matrix import validate_cn_candidate_source

    validated = [validate_cn_candidate_source(item) for item in candidates]
    return {
        "cn_candidate_source_count": len(validated),
        "cn_candidate_only_count": sum(item["candidate_status"] == "candidate_only" for item in validated),
        "cn_needs_human_review_count": sum(item["candidate_status"] == "needs_human_review" for item in validated),
        "cn_candidate_requires_second_source_count": sum(item["requires_second_source"] for item in validated),
        "execution_gating_eligible_count": 0,
        "execution_authorized": False,
        "runtime_network_access": False,
    }
