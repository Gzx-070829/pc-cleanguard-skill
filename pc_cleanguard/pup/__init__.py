"""User-facing, non-executing PUP inspection."""

from .inspector import inspect_pup_risk
from .intelligence import build_pup_intelligence_report, build_safety_notice
from .review_pack import build_pup_review_pack
from .source_trace import build_source_trace
from .feedback_template import build_false_positive_feedback_template
from .behavior_indicators import (
    BehaviorIndicator,
    build_behavior_indicators_from_report,
    render_behavior_indicator_section,
    summarize_behavior_indicators,
    validate_behavior_indicator,
    write_behavior_indicators,
)
from .corroboration import build_pup_corroboration, score_match_corroboration, render_corroboration_markdown

__all__ = [
    "inspect_pup_risk", "build_pup_intelligence_report", "build_pup_review_pack",
    "build_source_trace", "build_false_positive_feedback_template", "build_safety_notice",
    "BehaviorIndicator", "build_behavior_indicators_from_report",
    "render_behavior_indicator_section", "summarize_behavior_indicators",
    "validate_behavior_indicator", "write_behavior_indicators",
    "build_pup_corroboration", "score_match_corroboration", "render_corroboration_markdown",
]
