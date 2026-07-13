"""Offline validation helpers for explicitly supplied local reports."""

from .real_report_validation import validate_real_report_shape, write_real_report_validation_pack
from .no_match_report import build_no_match_report, render_no_match_report_markdown


def build_real_report_trial(*args, **kwargs):
    """Load the trial orchestrator lazily to avoid a review-pack import cycle."""
    from .trial_flow import build_real_report_trial as implementation

    return implementation(*args, **kwargs)

__all__ = ["validate_real_report_shape", "write_real_report_validation_pack", "build_no_match_report", "render_no_match_report_markdown", "build_real_report_trial"]
