"""Summarize evidence coverage and data gaps without creating a verdict."""

from __future__ import annotations

from collections import Counter


MISSING_TARGETS = [
    "布丁系 / 万能五笔",
    "搜狗输入法及输入法推广组件",
    "2345 / 工具条 / 下载站安装链",
    "驱动工具 / 修复工具",
    "浏览器主页/搜索修改链路",
]


def _flatten(packs) -> list[dict]:
    records: list[dict] = []
    for pack in packs:
        if not isinstance(pack, list) or any(not isinstance(item, dict) for item in pack):
            raise TypeError("evidence_packs must contain lists of records")
        records.extend(pack)
    return records


def build_evidence_coverage_summary(evidence_packs, candidates, backlog) -> dict:
    records = _flatten(evidence_packs)
    if not isinstance(candidates, list) or not isinstance(backlog, list):
        raise TypeError("candidates and backlog must be lists")
    mapping = Counter(item.get("mapping_type", "unknown") for item in records)
    entities = Counter(item.get("entity_scope", "unknown") for item in records)
    sources = Counter(item.get("source_type", "unknown") for item in records)
    behaviors = Counter(category for item in records for category in item.get("behavior_categories", ()))
    families = Counter()
    for item in records:
        name = str(item.get("software_name", ""))
        for family, terms in {
            "input_method": ("输入法",), "archive": ("压缩", "快压"),
            "browser_or_search": ("浏览器", "搜索"), "driver_or_repair": ("驱动", "修复"),
            "installer_chain": ("安装链", "安装器", "下载站"),
        }.items():
            if any(term in name for term in terms):
                families[family] += 1
    cn_win = [item for item in records if item.get("language") == "zh-CN" and item.get("entity_scope") in {"windows_desktop_software", "windows_installer", "browser_extension", "publisher_level"}]
    approved = len(records)
    gap_count = len(MISSING_TARGETS)
    return {
        "approved_total": approved,
        "approved_cn_win_total": len(cn_win),
        "candidate_total": len(candidates),
        "backlog_total": len(backlog),
        "direct_entity_count": mapping["direct_entity"],
        "installer_artifact_count": mapping["installer_artifact"],
        "related_publisher_count": mapping["related_publisher"],
        "name_collision_count": mapping["name_collision_candidate"],
        "high_false_positive_risk_count": sum(item.get("false_positive_risk") == "high" for item in records),
        "needs_second_source_count": sum(item.get("false_positive_risk") == "high" or item.get("mapping_type") in {"related_publisher", "name_collision_candidate"} for item in records),
        "source_type_distribution": dict(sorted(sources.items())),
        "behavior_category_distribution": dict(sorted(behaviors.items())),
        "coverage_by_family": dict(sorted(families.items())),
        "coverage_by_mapping_type": dict(sorted(mapping.items())),
        "coverage_by_entity_scope": dict(sorted(entities.items())),
        "top_missing_targets": list(MISSING_TARGETS),
        "next_data_priorities": ["为缺口寻找稳定公开来源并限定版本、组件和渠道。", "优先增加第二来源和去标识化真实报告反馈。"],
        "quality_warnings": ["覆盖数量不代表本机结论。", "高误报风险记录必须人工复核。"],
        "why_coverage_is_not_blacklist": "Coverage 只描述 evidence 数据覆盖，不是黑名单，也不是系统动作授权。",
        "coverage_score": round(min(100.0, len(cn_win) / 15 * 100), 1),
        "data_gap_count": gap_count,
        "execution_gating_eligible_count": 0,
        "execution_authorized": False,
        "runtime_network_access": False,
    }


def render_evidence_coverage_markdown(summary: dict) -> str:
    if not isinstance(summary, dict):
        raise TypeError("summary must be a dict")
    lines = [
        "# Evidence Coverage Dashboard", "",
        summary["why_coverage_is_not_blacklist"], "",
        f"- approved_total: `{summary['approved_total']}`",
        f"- approved_cn_win_total: `{summary['approved_cn_win_total']}`",
        f"- candidate_total: `{summary['candidate_total']}`",
        f"- backlog_total: `{summary['backlog_total']}`",
        f"- coverage_score: `{summary['coverage_score']}`",
        f"- execution_gating_eligible_count: `0`", "",
        "## Top missing targets", "",
        *[f"- {item}" for item in summary["top_missing_targets"]], "",
        "## Next data priorities", "",
        *[f"- {item}" for item in summary["next_data_priorities"]],
    ]
    return "\n".join(lines).rstrip() + "\n"
