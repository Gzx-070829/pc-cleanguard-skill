"""Turn machine review counts into a plain-language PUP review summary."""

from __future__ import annotations


def _strength(summary: dict) -> str:
    if summary.get("strong_review_signal_count", 0): return "强复核"
    if summary.get("moderate_review_signal_count", 0): return "中等复核"
    if summary.get("weak_name_only_signal_count", 0) or summary.get("publisher_only_signal_count", 0): return "弱线索"
    return "无命中"


def build_user_friendly_pup_report(review_pack_summary: dict) -> dict:
    if not isinstance(review_pack_summary, dict): raise TypeError("review_pack_summary must be a dict")
    strength = _strength(review_pack_summary)
    matched = review_pack_summary.get("cn_win_match_count", review_pack_summary.get("human_review_required_count", 0))
    corroborated = review_pack_summary.get("corroborated_match_count", review_pack_summary.get("strong_review_signal_count", 0) + review_pack_summary.get("moderate_review_signal_count", 0))
    return {
        "headline": f"当前产生 {matched} 条需要人工核验的 PUP 线索；当前不是自动清理。",
        "current_mode": "解释与人工复核，不执行清理",
        "signal_strength": strength,
        "found_signals": {"review_signal_count": matched, "corroborated_count": corroborated},
        "source_summary": list(review_pack_summary.get("sources", ["本地 evidence pack 中的可追溯公开来源"])),
        "behavior_corroborated": corroborated > 0,
        "why_not_direct_action": "Evidence、名称或行为 metadata 不能确认用户意图和当前实体身份，因此不能直接触发系统动作。",
        "human_checks": ["核对发布者、签名、版本与安装来源。", "检查浏览器主页/搜索/扩展、启动项、计划任务和服务是否符合预期。"],
        "false_positive_feedback": "如认为误报，请使用去标识化反馈模板提交人工复核；反馈不会自动改库。",
        "metadata_help": "补充 publisher、path、签名、版本、startup/task/service 与 behavior metadata 可提高 matchability。",
        "safety_boundaries": ["不联网、不上传、不静默删除。", "PUP 层 execution gating 始终为 0。"],
        "persistence_positioning": "这不是强力清理，而是链路治理：当前只做复核和计划，不自动卸载、禁用或修改注册表。",
        "future_execution_boundary": "未来如需处理，必须由用户确认、可回滚并留下审计记录。",
        "execution_gating_eligible_count": 0,
        "execution_authorized": False,
    }


def render_user_friendly_pup_report_markdown(report: dict) -> str:
    lines = ["# PC CleanGuard PUP 用户报告", "", report["headline"], "", f"- 线索强度：**{report['signal_strength']}**", f"- 当前模式：{report['current_mode']}", f"- 本机行为佐证：{'有' if report['behavior_corroborated'] else '尚无'}", "", "## 持久化链路治理", "", report["persistence_positioning"], report["future_execution_boundary"], "", "## 为什么不能直接操作", "", report["why_not_direct_action"], "", "## 用户可以检查", "", *[f"- {item}" for item in report["human_checks"]], "", "## 误报与补充信息", "", f"- {report['false_positive_feedback']}", f"- {report['metadata_help']}", "", "## 安全边界", "", *[f"- {item}" for item in report["safety_boundaries"]]]
    return "\n".join(lines).rstrip() + "\n"
