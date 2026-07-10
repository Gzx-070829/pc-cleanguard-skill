"""Command-line entry point for offline governance and controlled L1 cleanup."""

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
from .cleanup import (
    CleanupConfirmation,
    CleanupExecutor,
    JunkScanner,
    build_cleanup_preview,
    build_cleanup_summary,
    load_cleanup_preview_json,
    preflight_cleanup_artifacts,
    render_cleanup_report_markdown,
    write_cleanup_execution_report,
    write_cleanup_report_markdown,
)
from .demo import init_cleanup_demo, quickstart_cleanup_demo, run_cleanup_demo
from .pipeline import (
    load_scan_json_file,
    run_readonly_scan_pipeline,
    write_pipeline_audit_jsonl,
    write_pipeline_report,
)
from .skill import invoke_skill_action, write_report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pc_cleanguard.cli",
        description="PC CleanGuard offline governance CLI with controlled L1 cleanup",
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
    tools = subcommands.add_parser(
        "tools",
        help="build offline external-tool recommendations without execution",
    )
    tool_commands = tools.add_subparsers(dest="tools_command", required=True)
    recommend = tool_commands.add_parser(
        "recommend",
        help="recommend cataloged tools from an explicit cleanup-plan input",
    )
    recommend.add_argument(
        "--input",
        required=True,
        type=Path,
        help="explicit recommendation request .json",
    )
    recommend.add_argument(
        "--output",
        required=True,
        type=Path,
        help="output recommendations .json",
    )
    recommend.add_argument(
        "--overwrite",
        action="store_true",
        help="explicitly replace an existing recommendations file",
    )
    clean = subcommands.add_parser(
        "clean",
        help="build dry-run cleanup previews from explicit local paths",
    )
    clean_commands = clean.add_subparsers(dest="clean_command", required=True)
    preview = clean_commands.add_parser(
        "preview",
        help="scan explicit directories and write a non-executing preview",
    )
    preview.add_argument(
        "--path",
        dest="paths",
        required=True,
        action="append",
        type=Path,
        help="explicit local directory; may be supplied multiple times",
    )
    preview.add_argument(
        "--output",
        required=True,
        type=Path,
        help="output cleanup preview .json",
    )
    preview.add_argument(
        "--overwrite",
        action="store_true",
        help="explicitly replace an existing preview file",
    )
    execute = clean_commands.add_parser(
        "execute",
        help="dry-run or explicitly confirm bounded L1 file cleanup",
    )
    execute.add_argument(
        "--preview",
        required=True,
        type=Path,
        help="explicit PR14 cleanup preview .json",
    )
    execute.add_argument(
        "--allow-root",
        dest="allow_roots",
        required=True,
        action="append",
        type=Path,
        help="explicit cleanup root; may be supplied multiple times",
    )
    execute.add_argument(
        "--result",
        required=True,
        type=Path,
        help="output cleanup execution result .json",
    )
    execute.add_argument(
        "--audit",
        required=True,
        type=Path,
        help="output cleanup execution audit .jsonl",
    )
    execute.add_argument(
        "--confirm",
        action="store_true",
        help="explicitly permit L1 file cleanup after all gates pass",
    )
    execute.add_argument(
        "--overwrite",
        action="store_true",
        help="explicitly replace existing result and audit artifacts",
    )
    report = clean_commands.add_parser(
        "report",
        help="render a Markdown summary from explicit preview and result JSON",
    )
    report.add_argument(
        "--preview",
        required=True,
        type=Path,
        help="explicit PR14 cleanup preview .json",
    )
    report.add_argument(
        "--result",
        required=True,
        type=Path,
        help="explicit PR15 cleanup execution result .json",
    )
    report.add_argument(
        "--output",
        required=True,
        type=Path,
        help="output cleanup report .md",
    )
    report.add_argument(
        "--overwrite",
        action="store_true",
        help="explicitly replace an existing Markdown report",
    )
    demo = subcommands.add_parser(
        "demo",
        help="create and run a bounded synthetic cleanup experience",
    )
    demo_commands = demo.add_subparsers(dest="demo_command", required=True)
    demo_init = demo_commands.add_parser(
        "init-cleanup",
        help="create synthetic junk under one explicit safe demo root",
    )
    demo_init.add_argument(
        "--root",
        required=True,
        type=Path,
        help="explicit demo directory to create",
    )
    demo_init.add_argument(
        "--force",
        action="store_true",
        help="refresh only a root already marked by demo init",
    )
    demo_run = demo_commands.add_parser(
        "run-cleanup",
        help="run preview, controlled execution, audit, and report for a demo root",
    )
    demo_run.add_argument(
        "--root",
        required=True,
        type=Path,
        help="explicit root previously created by demo init-cleanup",
    )
    demo_run.add_argument(
        "--output",
        required=True,
        type=Path,
        help="new explicit directory for demo artifacts",
    )
    demo_run.add_argument(
        "--confirm",
        action="store_true",
        help="confirm only L1 files inside the marked demo root",
    )
    demo_quickstart = demo_commands.add_parser(
        "quickstart",
        help="initialize a synthetic demo and run the full loop in dry-run mode",
    )
    demo_quickstart.add_argument(
        "--root",
        required=True,
        type=Path,
        help="new explicit safe demo directory",
    )
    demo_quickstart.add_argument(
        "--output",
        required=True,
        type=Path,
        help="new explicit directory for dry-run artifacts",
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


def _run_tools_recommend(arguments: argparse.Namespace) -> dict:
    payload = load_scan_json_file(arguments.input)
    response = invoke_skill_action(
        {"action": "recommend_external_tools", "payload": payload}
    )
    write_report(
        arguments.output,
        response.result,
        explicit_overwrite=arguments.overwrite,
    )
    return {
        "input": str(arguments.input),
        "output": str(arguments.output),
        "recommendations": response.result["recommendation_count"],
        "trusted": response.result["trusted_count"],
        "blocked": response.result["blocked_count"],
        "execution_authorized": False,
    }


def _run_cleanup_preview(arguments: argparse.Namespace) -> dict:
    scan_result = JunkScanner().scan(arguments.paths)
    preview = build_cleanup_preview(scan_result)
    serialized = preview.to_dict()
    write_report(
        arguments.output,
        serialized,
        explicit_overwrite=arguments.overwrite,
    )
    return {
        "paths": [str(path) for path in arguments.paths],
        "output": str(arguments.output),
        "total_candidates": preview.total_candidates,
        "total_reclaimable_bytes": preview.total_reclaimable_bytes,
        "blocked_candidates": len(preview.blocked_candidates),
        "requires_confirmation": preview.requires_confirmation,
        "dry_run_only": True,
        "execution_authorized": False,
    }


def _run_cleanup_execute(arguments: argparse.Namespace) -> dict:
    preview = load_cleanup_preview_json(arguments.preview)
    confirmation = CleanupConfirmation(
        arguments.confirm,
        tuple(arguments.allow_roots),
    )
    result_path, audit_path = preflight_cleanup_artifacts(
        arguments.result,
        arguments.audit,
        explicit_overwrite=arguments.overwrite,
    )
    report = CleanupExecutor().execute(
        preview,
        confirmation,
        audit_path=audit_path,
        explicit_overwrite=arguments.overwrite,
    )
    write_cleanup_execution_report(
        result_path,
        report,
        explicit_overwrite=arguments.overwrite,
    )
    return {
        "preview": str(arguments.preview),
        "result": str(result_path),
        "audit": str(audit_path),
        "confirmed": report.confirmed,
        "mode": report.mode,
        **report.summary,
    }


def _run_cleanup_report(arguments: argparse.Namespace) -> dict:
    preview = load_cleanup_preview_json(arguments.preview)
    execution_result = load_scan_json_file(arguments.result)
    summary = build_cleanup_summary(preview, execution_result)
    write_cleanup_report_markdown(
        arguments.output,
        render_cleanup_report_markdown(summary),
        explicit_overwrite=arguments.overwrite,
    )
    return {
        "preview": str(arguments.preview),
        "result": str(arguments.result),
        "output": str(arguments.output),
        **{
            key: summary[key]
            for key in (
                "total_candidates",
                "total_reclaimable_bytes",
                "cleaned_count",
                "cleaned_bytes",
                "would_clean_count",
                "skipped_count",
                "blocked_count",
            )
        },
        "report_only": True,
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
        elif arguments.command == "tools" and arguments.tools_command == "recommend":
            summary = _run_tools_recommend(arguments)
        elif arguments.command == "clean" and arguments.clean_command == "preview":
            summary = _run_cleanup_preview(arguments)
        elif arguments.command == "clean" and arguments.clean_command == "execute":
            summary = _run_cleanup_execute(arguments)
        elif arguments.command == "clean" and arguments.clean_command == "report":
            summary = _run_cleanup_report(arguments)
        elif arguments.command == "demo" and arguments.demo_command == "init-cleanup":
            summary = init_cleanup_demo(arguments.root, force=arguments.force)
        elif arguments.command == "demo" and arguments.demo_command == "run-cleanup":
            summary = run_cleanup_demo(
                arguments.root,
                arguments.output,
                confirm=arguments.confirm,
            )
        elif arguments.command == "demo" and arguments.demo_command == "quickstart":
            summary = quickstart_cleanup_demo(arguments.root, arguments.output)
        else:  # pragma: no cover - argparse enforces the available commands.
            parser.error(f"unsupported command: {arguments.command}")
    except (FileExistsError, FileNotFoundError, OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
