"""Minimal command-line entry point for offline read-only governance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .ai import (
    DryRunPromptProvider,
    MockAIProvider,
    explain_report,
    load_report_json_file,
    write_explanation_markdown,
)
from .pipeline import (
    load_scan_json_file,
    run_readonly_scan_pipeline,
    write_pipeline_audit_jsonl,
    write_pipeline_report,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pc_cleanguard.cli",
        description="PC CleanGuard offline, read-only governance CLI",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    scan = subcommands.add_parser(
        "scan",
        help="process one explicit JSON input without executing collectors",
    )
    scan.add_argument("--input", required=True, type=Path, help="explicit input .json")
    scan.add_argument("--report", required=True, type=Path, help="output report .json")
    scan.add_argument("--audit", required=True, type=Path, help="output audit .jsonl")
    scan.add_argument("--scan-id", help="optional caller-supplied scan identifier")
    scan.add_argument(
        "--overwrite",
        action="store_true",
        help="explicitly replace existing report and audit files",
    )
    explain = subcommands.add_parser(
        "explain",
        help="explain one explicit report through an offline provider",
    )
    explain.add_argument(
        "--report", required=True, type=Path, help="explicit input report .json"
    )
    explain.add_argument(
        "--output", required=True, type=Path, help="output explanation .md"
    )
    provider_mode = explain.add_mutually_exclusive_group()
    provider_mode.add_argument(
        "--provider",
        choices=("mock",),
        help="offline provider; defaults to mock",
    )
    provider_mode.add_argument(
        "--dry-run-prompt",
        action="store_true",
        help="write the bounded prompt without a model call",
    )
    explain.add_argument(
        "--overwrite",
        action="store_true",
        help="explicitly replace an existing Markdown output",
    )
    return parser


def _run_scan(arguments: argparse.Namespace) -> dict:
    input_data = load_scan_json_file(arguments.input)
    result = run_readonly_scan_pipeline(input_data, scan_id=arguments.scan_id)
    write_pipeline_report(
        arguments.report,
        result,
        explicit_overwrite=arguments.overwrite,
    )
    write_pipeline_audit_jsonl(
        arguments.audit,
        list(result.audit_events),
        explicit_overwrite=arguments.overwrite,
    )
    return {
        "scan_id": result.scan_id,
        "normalized_counts": result.normalized_counts,
        "decisions": len(result.decisions),
        "dry_run_audit_events": len(result.audit_events),
        "report": str(arguments.report),
        "audit": str(arguments.audit),
        "execution_performed": False,
    }


def _run_explain(arguments: argparse.Namespace) -> dict:
    report = load_report_json_file(arguments.report)
    provider = (
        DryRunPromptProvider() if arguments.dry_run_prompt else MockAIProvider()
    )
    explanation = explain_report(report, provider)
    write_explanation_markdown(
        arguments.output,
        explanation,
        explicit_overwrite=arguments.overwrite,
    )
    return {
        "provider": explanation.provider,
        "report": str(arguments.report),
        "output": str(arguments.output),
        "safety_notice": explanation.safety_notice,
        "execution_authorized": explanation.execution_authorized,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "scan":
            summary = _run_scan(arguments)
        elif arguments.command == "explain":
            summary = _run_explain(arguments)
        else:  # pragma: no cover - argparse enforces the available commands.
            parser.error(f"unsupported command: {arguments.command}")
    except (FileExistsError, FileNotFoundError, OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
