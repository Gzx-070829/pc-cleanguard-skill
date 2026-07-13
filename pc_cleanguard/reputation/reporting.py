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
    matches = insight.get("matched_targets", [])
    return "\n".join([
        "# PUP 风险洞察 / PUP Risk Insight",
        "",
        "## safety_notice",
        "",
        insight.get("safety_notice", SAFETY_NOTICE),
        "",
        f"命中目标：{insight.get('summary', {}).get('matched_targets', 0)}",
        f"真实来源命中：{insight.get('summary', {}).get('real_source_match_count', 0)}",
        f"Synthetic 命中：{insight.get('summary', {}).get('synthetic_match_count', 0)}",
        f"执行门控合格：{insight.get('summary', {}).get('execution_gating_eligible_count', 0)}",
        f"Indicator 命中：{insight.get('summary', {}).get('indicator_match_count', 0)}",
        f"高不确定性命中：{insight.get('summary', {}).get('high_uncertainty_match_count', 0)}",
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
        "## Evidence Guard details",
        "",
        *[f"- record=`{item.get('matched_record_id')}` / mapping_type=`{item.get('mapping_type')}` / entity_scope=`{item.get('entity_scope')}` / match_basis=`{item.get('match_basis')}` / indicator_type=`{item.get('matched_indicator_type')}` / indicator_value=`{item.get('matched_indicator_value')}` / target_observed=`{item.get('target_observed_value')}` / match_strength=`{item.get('match_strength')}` / source_title={item.get('source_title')} / source_date={item.get('source_date')} / source_url={item.get('source_url')} / guard_reason={'; '.join(item.get('guard_reason', []))} / why_not_execution_authorization={item.get('why_not_execution_authorization')} / human_review_checklist={'; '.join(item.get('human_review_checklist', []))}" for item in matches],
        "",
        "真实来源 evidence 仅用于解释、排序和人工复核，不是删除、卸载、禁用授权。",
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
