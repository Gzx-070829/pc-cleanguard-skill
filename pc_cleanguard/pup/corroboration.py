"""Correlate evidence matches with caller-supplied behavior metadata for review only."""

from __future__ import annotations


def score_match_corroboration(match: dict, behavior_indicators: list[dict]) -> dict:
    if not isinstance(match, dict) or not isinstance(behavior_indicators, list):
        raise TypeError("match must be dict and behavior_indicators must be list")
    related = [item for item in behavior_indicators if isinstance(item, dict) and item.get("target_id") == match.get("target_id")]
    mapping = match.get("mapping_type", "direct_entity")
    kinds = {item.get("behavior_type") for item in related}
    if mapping == "related_publisher": level, score = "publisher_only_signal", 20
    elif mapping == "name_collision_candidate": level, score = "weak_name_only_signal", 25
    elif mapping == "installer_artifact" and kinds & {"bundled_installer_trace", "startup_persistence", "scheduled_task_persistence"}: level, score = "moderate_review_signal", 65
    elif mapping == "direct_entity" and related: level, score = "strong_review_signal", 80
    elif related: level, score = "moderate_review_signal", 50
    else: level, score = "no_corroboration", 10
    return {
        "target_id": match.get("target_id"), "matched_record_id": match.get("matched_record_id"),
        "mapping_type": mapping, "corroboration_level": level, "corroboration_score": score,
        "matched_behavior_indicators": related,
        "missing_behavior_indicators": [] if related else ["publisher/path/startup/task/service/browser/behavior metadata"],
        "required_human_checks": ["核对发布者、签名、版本和安装来源。", "核对浏览器、启动项、计划任务和服务是否符合用户预期。"],
        "source_trace": {"source_url": match.get("source_url"), "source_title": match.get("source_title"), "source_date": match.get("source_date")},
        "review_next_step": "对照来源范围与本机 metadata；缺少第二来源或身份不一致时降级并提交误报反馈。",
        "false_positive_risk_after_corroboration": "high" if mapping in {"related_publisher","name_collision_candidate"} or not related else "medium",
        "why_still_not_execution_authorization": "行为佐证只增强人工复核，不确认用户意图，也不授权删除、卸载、禁用或注册表修改。",
        "uncertainty_notes": [] if related else ["没有同一 target 的行为元数据佐证；名称或 indicator 命中需要更多证据。"],
        "execution_authorized": False, "execution_gating_eligible": False,
    }


def build_pup_corroboration(matches: list[dict], behavior_indicators: list[dict]) -> dict:
    if not isinstance(matches, list) or not isinstance(behavior_indicators, list): raise TypeError("matches and behavior_indicators must be lists")
    details=[score_match_corroboration(item,behavior_indicators) for item in matches]
    matched_targets={item.get("target_id") for item in matches}
    behavior_only=[item for item in behavior_indicators if item.get("target_id") not in matched_targets]
    levels=("strong_review_signal","moderate_review_signal","weak_name_only_signal","publisher_only_signal","no_corroboration")
    result={f"{level}_count":sum(item["corroboration_level"]==level for item in details) for level in levels}
    return {
        "details":details,"behavior_only_signals":behavior_only,"corroborated_match_count":sum(bool(item["matched_behavior_indicators"]) for item in details),
        **result,"behavior_only_signal_count":len(behavior_only),"no_match_count":int(not matches),
        "execution_gating_eligible_count":0,"execution_authorized":False,
    }


def render_corroboration_markdown(corroboration: dict) -> str:
    lines=["# PUP 行为佐证 / Corroboration","","行为佐证只增强人工复核，不是 PUP 定罪或系统动作授权。",""]
    for key in ("corroborated_match_count","strong_review_signal_count","moderate_review_signal_count","weak_name_only_signal_count","publisher_only_signal_count","behavior_only_signal_count","no_corroboration_count"):
        lines.append(f"- {key}: `{corroboration.get(key,0)}`")
    lines.extend(["- execution_gating_eligible_count: `0`",""])
    for item in corroboration.get("details",()): lines.extend([f"## {item['target_id']}","",f"- level: `{item['corroboration_level']}`",f"- score: `{item['corroboration_score']}`",f"- source: {item.get('source_trace', {}).get('source_title') or '未提供'}",f"- next: {item.get('review_next_step')}",f"- safety: {item['why_still_not_execution_authorization']}",""])
    return "\n".join(lines).rstrip()+"\n"
