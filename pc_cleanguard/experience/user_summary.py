"""Turn cleanup and PUP evidence into a plain-language user summary."""


def _count(data: dict, key: str) -> int:
    value = data.get(key, 0)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def build_user_summary(
    cleanup_summary: dict,
    pup_result: dict,
    *,
    confirmed: bool,
    quarantine_root: str | None,
) -> dict:
    if not isinstance(cleanup_summary, dict) or not isinstance(pup_result, dict):
        raise TypeError("summary inputs must be dicts")
    if not isinstance(confirmed, bool):
        raise TypeError("confirmed must be bool")
    quarantined = _count(cleanup_summary, "quarantined_count")
    top_items = cleanup_summary.get("top_items", [])
    skip_reasons = sorted({
        item.get("reason", "")
        for item in top_items
        if isinstance(item, dict)
        and item.get("status") in {"skipped", "blocked"}
        and isinstance(item.get("reason"), str)
        and item.get("reason")
    })
    restore = (
        f"使用 `python -m pc_cleanguard.cli quarantine list --root {quarantine_root}` 查看条目，"
        f"再用 `python -m pc_cleanguard.cli quarantine restore --root {quarantine_root} --item-id <id>` 恢复。"
        if confirmed and quarantine_root
        else "当前是 dry-run，没有移动文件；确认隔离后可使用 quarantine restore 恢复。"
    )
    return {
        "cleanup_candidates": _count(cleanup_summary, "total_candidates"),
        "reclaimable_bytes": _count(cleanup_summary, "total_reclaimable_bytes"),
        "quarantined_count": quarantined,
        "recoverable_count": quarantined,
        "skipped_count": _count(cleanup_summary, "skipped_count"),
        "blocked_count": _count(cleanup_summary, "blocked_count"),
        "skip_reasons": skip_reasons or ["没有额外跳过原因；详见 cleanup_report.md。"],
        "pup_clue_count": _count(pup_result, "match_count"),
        "confirmed": confirmed,
        "safety_boundaries": "不静默删除；默认隔离可恢复；不联网、不上传；PUP 线索不是删除、卸载或禁用授权。",
        "next_steps": ["先阅读 cleanup_report.md 和 pup_insight.md。", "核对候选与误报风险后再决定是否确认隔离。"],
        "how_to_restore": restore,
        "execution_authorized": False,
    }


def render_user_summary_markdown(summary: dict) -> str:
    if not isinstance(summary, dict) or summary.get("execution_authorized") is not False:
        raise ValueError("user summary must be non-authorizing")
    return "\n".join([
        "# PC CleanGuard 试用摘要",
        "",
        f"- 清理候选数量：{summary['cleanup_candidates']}",
        f"- 预计可释放空间：{summary['reclaimable_bytes']} bytes",
        f"- 已隔离/可恢复：{summary['quarantined_count']}",
        f"- 已跳过：{summary['skipped_count']}",
        f"- 已阻断：{summary['blocked_count']}",
        f"- PUP 线索：{summary['pup_clue_count']}",
        "",
        "## 跳过原因",
        "",
        *[f"- {item}" for item in summary["skip_reasons"]],
        "",
        "## 安全边界",
        "",
        summary["safety_boundaries"],
        "",
        "## 下一步建议",
        "",
        *[f"- {item}" for item in summary["next_steps"]],
        "",
        "## 如何恢复",
        "",
        summary["how_to_restore"],
        "",
    ])
