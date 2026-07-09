"""Explain an explicit report through an offline provider and write Markdown."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..pipeline import load_scan_json_file
from ..pipeline.input_loader import _validated_explicit_local_path
from .prompts import SAFETY_NOTICE, build_report_explanation_prompt
from .providers import AIProvider


@dataclass(frozen=True, slots=True)
class ReportExplanation:
    """A non-executable explanation artifact."""

    provider: str
    safety_notice: str
    prompt: str
    markdown: str
    execution_authorized: bool = False


def load_report_json_file(path: str | Path) -> dict:
    """Read exactly one explicit, validated local report JSON file."""

    return load_scan_json_file(path)


def explain_report(report: dict, provider: AIProvider) -> ReportExplanation:
    """Create an explanation without networking, credentials, or system actions."""

    if not isinstance(report, dict):
        raise TypeError("report must be a dict")
    if not hasattr(provider, "name") or not callable(
        getattr(provider, "generate", None)
    ):
        raise TypeError("provider must implement the AIProvider contract")
    prompt = build_report_explanation_prompt(report)
    markdown = provider.generate(prompt, report)
    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("provider must return non-empty Markdown")
    if SAFETY_NOTICE not in markdown:
        markdown = f"## safety_notice\n\n{SAFETY_NOTICE}\n\n{markdown}"
    return ReportExplanation(
        provider=str(provider.name),
        safety_notice=SAFETY_NOTICE,
        prompt=prompt,
        markdown=markdown,
        execution_authorized=False,
    )


def write_explanation_markdown(
    path: str | Path,
    explanation: ReportExplanation,
    *,
    explicit_overwrite: bool = False,
) -> None:
    """Write Markdown only to an explicit safe local path."""

    if not isinstance(explanation, ReportExplanation):
        raise TypeError("explanation must be a ReportExplanation")
    if not isinstance(explicit_overwrite, bool):
        raise TypeError("explicit_overwrite must be a bool")
    destination = _validated_explicit_local_path(path, allowed_suffixes={".md"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if explicit_overwrite else "x"
    with destination.open(mode, encoding="utf-8", newline="\n") as stream:
        stream.write(explanation.markdown.rstrip() + "\n")
