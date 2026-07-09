"""Offline-only report explanation components for PC CleanGuard PR9."""

from .prompts import SAFETY_NOTICE, build_report_explanation_prompt
from .providers import AIProvider, DryRunPromptProvider, MockAIProvider
from .report_explainer import (
    ReportExplanation,
    explain_report,
    load_report_json_file,
    write_explanation_markdown,
)

__all__ = [
    "AIProvider",
    "DryRunPromptProvider",
    "MockAIProvider",
    "ReportExplanation",
    "SAFETY_NOTICE",
    "build_report_explanation_prompt",
    "explain_report",
    "load_report_json_file",
    "write_explanation_markdown",
]
