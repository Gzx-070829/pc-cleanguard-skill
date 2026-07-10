"""Build human-readable cleanup summaries without changing the filesystem."""

from __future__ import annotations

from pathlib import Path

from ..pipeline.input_loader import _validated_explicit_local_path
from .executor import validate_cleanup_preview


_EXECUTION_STATUSES = ("cleaned", "would_clean", "skipped", "blocked", "failed")
_SAFETY_NOTES = (
    "报告用于展示预览与执行结果，不构成新的清理授权。",
    "只有显式确认且通过 allow-root 与 L1 安全门的文件才能由现有执行器处理。",
    "crash dump、installer leftover 与目录候选不会被 L1 执行器删除。",
)


def _validated_execution_result(result: dict | None) -> dict | None:
    if result is None:
        return None
    if not isinstance(result, dict):
        raise TypeError("execution result must be a JSON object")
    if result.get("mode") not in {"dry_run", "confirmed_l1"}:
        raise ValueError("unsupported cleanup execution result mode")
    if not isinstance(result.get("results"), list):
        raise TypeError("cleanup execution results must be a list")
    for item in result["results"]:
        if not isinstance(item, dict):
            raise TypeError("cleanup execution items must be objects")
        if item.get("status") not in _EXECUTION_STATUSES:
            raise ValueError("unsupported cleanup execution status")
        if not isinstance(item.get("category"), str) or not item["category"]:
            raise ValueError("cleanup execution item category is required")
        if not isinstance(item.get("path"), str) or not item["path"]:
            raise ValueError("cleanup execution item path is required")
        reclaimed = item.get("bytes_reclaimed")
        if not isinstance(reclaimed, int) or isinstance(reclaimed, bool) or reclaimed < 0:
            raise ValueError("bytes_reclaimed must be a non-negative integer")
    return result


def build_cleanup_summary(
    preview: dict,
    execution_result: dict | None = None,
    *,
    top_limit: int = 10,
) -> dict:
    """Combine a PR14 preview and optional PR15 result into JSON-safe metrics."""

    validate_cleanup_preview(preview)
    result = _validated_execution_result(execution_result)
    if not isinstance(top_limit, int) or isinstance(top_limit, bool) or top_limit <= 0:
        raise ValueError("top_limit must be a positive integer")

    preview_identity = {
        item["path"]: item["category"] for item in preview["top_candidates"]
    }
    if result is not None and any(
        preview_identity.get(item["path"]) != item["category"]
        for item in result["results"]
    ):
        raise ValueError("execution result does not belong to this cleanup preview")

    status_counts: dict[str, int] = {}
    result_items: list[dict] = []
    if result is not None:
        result_items = result["results"]
        status_counts = {
            status: sum(item["status"] == status for item in result_items)
            for status in _EXECUTION_STATUSES
        }
    result_by_path = {item["path"]: item for item in result_items}
    combined_items = []
    preview_paths = set()
    for candidate in preview["top_candidates"]:
        preview_paths.add(candidate["path"])
        execution_item = result_by_path.get(candidate["path"], {})
        combined_items.append(
            {
                **candidate,
                "status": execution_item.get("status", "preview_candidate"),
                "bytes_reclaimed": execution_item.get("bytes_reclaimed", 0),
                "reason": execution_item.get("reason", candidate.get("reason", "")),
            }
        )
    combined_items.extend(
        item for item in result_items if item["path"] not in preview_paths
    )
    top_items = sorted(
        combined_items,
        key=lambda item: (
            -max(
                int(item.get("bytes_reclaimed", 0)),
                int(item.get("size_bytes", 0)),
            ),
            str(item.get("path", "")).casefold(),
        ),
    )[:top_limit]

    return {
        "total_candidates": preview["total_candidates"],
        "total_reclaimable_bytes": preview["total_reclaimable_bytes"],
        "cleaned_count": status_counts.get("cleaned", 0),
        "cleaned_bytes": sum(
            item["bytes_reclaimed"]
            for item in result_items
            if item["status"] == "cleaned"
        ),
        "would_clean_count": status_counts.get("would_clean", 0),
        "skipped_count": status_counts.get("skipped", 0),
        "blocked_count": status_counts.get("blocked", 0),
        "by_category": {
            category: dict(values)
            for category, values in preview["by_category"].items()
        },
        "by_status": status_counts,
        "top_items": [
            {
                "path": item["path"],
                "category": item["category"],
                "status": item["status"],
                "size_bytes": item.get("size_bytes", 0),
                "bytes_reclaimed": item.get("bytes_reclaimed", 0),
                "reason": item.get("reason", ""),
            }
            for item in top_items
        ],
        "safety_notes": list(_SAFETY_NOTES),
    }


def _format_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if size < 1024 or unit == "GiB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    raise AssertionError("unreachable")


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_cleanup_report_markdown(summary: dict) -> str:
    """Render a deterministic bilingual Markdown cleanup report."""

    required = {
        "total_candidates",
        "total_reclaimable_bytes",
        "cleaned_count",
        "cleaned_bytes",
        "would_clean_count",
        "skipped_count",
        "blocked_count",
        "by_category",
        "by_status",
        "top_items",
        "safety_notes",
    }
    if not isinstance(summary, dict) or not required.issubset(summary):
        raise ValueError("cleanup summary is incomplete")
    lines = [
        "# PC CleanGuard Cleanup Report / 清理报告",
        "",
        "> This report summarizes an explicit cleanup preview and optional L1 execution result.",
        "> 本报告仅汇总显式预览与可选的 L1 执行结果，不扩大执行权限。",
        "",
        "## Summary / 摘要",
        "",
        f"- Candidates / 候选：{summary['total_candidates']}",
        f"- Reclaimable / 可释放：{_format_bytes(summary['total_reclaimable_bytes'])}",
        f"- Cleaned / 已清理：{summary['cleaned_count']} ({_format_bytes(summary['cleaned_bytes'])})",
        f"- Would clean / 待确认：{summary['would_clean_count']}",
        f"- Skipped / 已跳过：{summary['skipped_count']}",
        f"- Blocked / 已阻断：{summary['blocked_count']}",
        "",
        "## By category / 按类别",
        "",
        "| Category | Count | Bytes |",
        "| --- | ---: | ---: |",
    ]
    for category, values in summary["by_category"].items():
        lines.append(
            f"| {_cell(category)} | {values.get('count', 0)} | {_format_bytes(values.get('size_bytes', 0))} |"
        )
    lines.extend(
        [
            "",
            "## Top items / 重点项目",
            "",
            "| Path | Category | Status | Reclaimed |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for item in summary["top_items"]:
        lines.append(
            "| {path} | {category} | {status} | {reclaimed} |".format(
                path=_cell(item["path"]),
                category=_cell(item["category"]),
                status=_cell(item["status"]),
                reclaimed=_format_bytes(item["bytes_reclaimed"]),
            )
        )
    lines.extend(["", "## Safety notes / 安全说明", ""])
    lines.extend(f"- {note}" for note in summary["safety_notes"])
    return "\n".join(lines) + "\n"


def write_cleanup_report_markdown(
    path: str | Path,
    markdown: str,
    *,
    explicit_overwrite: bool = False,
) -> Path:
    """Write Markdown to one explicit safe local path without implicit overwrite."""

    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("markdown must be non-empty")
    if not isinstance(explicit_overwrite, bool):
        raise TypeError("explicit_overwrite must be a bool")
    destination = _validated_explicit_local_path(path, allowed_suffixes={".md"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if explicit_overwrite else "x"
    with destination.open(mode, encoding="utf-8", newline="\n") as stream:
        stream.write(markdown)
    return destination
