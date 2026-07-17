"""Offline evaluation entry points."""

from .result import WindowsLocalEvaluationResult
from .windows_local import run_windows_local_evaluation

__all__ = ["WindowsLocalEvaluationResult", "run_windows_local_evaluation"]
