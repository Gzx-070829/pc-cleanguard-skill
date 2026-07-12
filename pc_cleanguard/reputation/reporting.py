"""Markdown rendering for user-visible PUP insights."""

from pathlib import Path

from .insight import SAFETY_NOTICE
from ..pipeline.input_loader import _validated_explicit_local_path


def render_pup_insight_markdown(insight: dict) -> str:
    if not isinstance(insight, dict) or insight.get("execution_authorized") is not False:
        raise ValueError("insight must be a non-authorizing object")
    behaviors = insight.get("suspicious_behaviors", [])
    uncertainty = insight.get("uncertainty_notes", [])
    reviews = insight.get("recommended_review", [])
    return "\n".join([
        "# PUP 风险洞察 / PUP Risk Insight",
        "",
        "## safety_notice",
        "",
        insight.get("safety_notice", SAFETY_NOTICE),
        "",
        f"命中目标：{insight.get('summary', {}).get('matched_targets', 0)}",
        "",
        "## 可疑行为类别",
        "",
        *([f"- `{item}`" for item in behaviors] or ["- 未发现 seed 命中；这不等于安全证明。"]),
        "",
        "## 不确定性",
        "",
        *[f"- {item}" for item in uncertainty],
        "",
        "## 建议人工复核",
        "",
        *[f"- {item}" for item in reviews],
        "",
        "AI 和 Reputation KB 均不能提供删除、卸载或禁用授权。",
        "",
    ])


def write_pup_insight_markdown(path: str | Path, markdown: str, *, explicit_overwrite: bool = False) -> None:
    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("markdown must be non-empty")
    destination = _validated_explicit_local_path(path, allowed_suffixes={".md"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if explicit_overwrite else "x"
    with destination.open(mode, encoding="utf-8", newline="\n") as stream:
        stream.write(markdown.rstrip() + "\n")
