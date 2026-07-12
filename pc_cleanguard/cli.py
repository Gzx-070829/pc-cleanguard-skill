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
from .quarantine import QuarantineManager
from .pup import inspect_pup_risk
from .reputation import (
    ReputationMatcher,
    build_pup_insight,
    load_seed_records,
    render_pup_insight_markdown,
    write_pup_insight_markdown,
)
from .skill import invoke_skill_action, write_report
from .experience import run_user_trial


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
    execute.add_argument(
        "--quarantine-root",
        type=Path,
        help="move confirmed L1 files into this explicit quarantine root",
    )
    execute.add_argument(
        "--permanent",
        action="store_true",
        help="expert-only permanent L1 deletion; requires a second acknowledgement",
    )
    execute.add_argument(
        "--i-understand-permanent-delete",
        action="store_true",
        help="second acknowledgement required with --permanent",
    )
    safe = clean_commands.add_parser(
        "safe",
        help="preview, safely execute, audit, and report explicit paths",
    )
    safe.add_argument("--path", dest="paths", required=True, action="append", type=Path)
    safe.add_argument("--output", required=True, type=Path)
    safe.add_argument("--confirm", action="store_true")
    safe.add_argument("--quarantine-root", type=Path)
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
    quarantine = subcommands.add_parser(
        "quarantine",
        help="add, list, or restore explicit regular-file quarantine items",
    )
    quarantine_commands = quarantine.add_subparsers(
        dest="quarantine_command", required=True
    )
    quarantine_add = quarantine_commands.add_parser("add")
    quarantine_add.add_argument("--root", required=True, type=Path)
    quarantine_add.add_argument("--path", required=True, type=Path)
    quarantine_add.add_argument("--reason", required=True)
    quarantine_list = quarantine_commands.add_parser("list")
    quarantine_list.add_argument("--root", required=True, type=Path)
    quarantine_restore = quarantine_commands.add_parser("restore")
    quarantine_restore.add_argument("--root", required=True, type=Path)
    quarantine_restore.add_argument("--item-id", required=True)
    reputation = subcommands.add_parser("reputation", help="offline reputation evidence matching")
    reputation_commands = reputation.add_subparsers(dest="reputation_command", required=True)
    reputation_match = reputation_commands.add_parser("match")
    reputation_match.add_argument("--input", required=True, type=Path)
    reputation_match.add_argument("--seed", required=True, type=Path)
    reputation_match.add_argument("--output", required=True, type=Path)
    reputation_insight = reputation_commands.add_parser("insight")
    reputation_insight.add_argument("--matches", required=True, type=Path)
    reputation_insight.add_argument("--output", required=True, type=Path)
    pup = subcommands.add_parser("pup", help="inspect PUP evidence without execution")
    pup_commands = pup.add_subparsers(dest="pup_command", required=True)
    pup_inspect = pup_commands.add_parser("inspect")
    pup_inspect.add_argument("--input", required=True, type=Path)
    pup_inspect.add_argument("--seed", required=True, type=Path)
    pup_inspect.add_argument("--output", required=True, type=Path)
    trial = subcommands.add_parser("trial", help="run the bounded five-minute product trial")
    trial_commands = trial.add_subparsers(dest="trial_command", required=True)
    trial_run = trial_commands.add_parser("run")
    trial_run.add_argument("--root", required=True, type=Path)
    trial_run.add_argument("--output", required=True, type=Path)
    trial_run.add_argument("--confirm", action="store_true")
    trial_run.add_argument("--quarantine-root", type=Path)
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
    report = CleanupExecutor(
        quarantine_root=arguments.quarantine_root,
        permanent=arguments.permanent,
        permanent_delete_acknowledged=arguments.i_understand_permanent_delete,
    ).execute(
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


def _run_cleanup_safe(arguments: argparse.Namespace) -> dict:
    if arguments.confirm and arguments.quarantine_root is None:
        raise ValueError("clean safe --confirm requires --quarantine-root")
    output = Path(arguments.output).resolve(strict=False)
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True)
    preview = build_cleanup_preview(JunkScanner().scan(arguments.paths)).to_dict()
    preview_path = output / "preview.json"
    result_path = output / "result.json"
    audit_path = output / "audit.jsonl"
    report_path = output / "cleanup_report.md"
    summary_path = output / "summary.json"
    write_report(preview_path, preview)
    execution = CleanupExecutor(quarantine_root=arguments.quarantine_root).execute(
        preview,
        CleanupConfirmation(arguments.confirm, tuple(arguments.paths)),
        audit_path=audit_path,
    )
    write_cleanup_execution_report(result_path, execution)
    summary = build_cleanup_summary(preview, execution.to_dict())
    write_cleanup_report_markdown(
        report_path,
        render_cleanup_report_markdown(summary),
    )
    response = {
        "paths": [str(path) for path in arguments.paths],
        "output": str(output),
        "mode": execution.mode,
        "confirmed": execution.confirmed,
        **execution.summary,
    }
    write_report(summary_path, response)
    return response


def _run_quarantine(arguments: argparse.Namespace) -> dict:
    if arguments.quarantine_command == "add":
        manager = QuarantineManager.create_quarantine(arguments.root)
        item = manager.quarantine_file(
            arguments.path,
            reason=arguments.reason,
            evidence=(
                {"source": "cli_explicit_request", "fact": "caller supplied path and reason"},
            ),
        )
        return item.to_dict()
    manager = QuarantineManager(arguments.root)
    if arguments.quarantine_command == "list":
        return {"root": str(manager.root), "items": [item.to_dict() for item in manager.list_items()]}
    if arguments.quarantine_command == "restore":
        return manager.restore_item(arguments.item_id).to_dict()
    raise ValueError("unsupported quarantine command")


def _run_reputation(arguments: argparse.Namespace) -> dict:
    if arguments.reputation_command == "match":
        report = load_scan_json_file(arguments.input)
        matches = ReputationMatcher(load_seed_records(arguments.seed)).match(report)
        payload = {"matches": matches, "match_count": len(matches), "execution_authorized": False}
        write_report(arguments.output, payload)
        return {"output": str(arguments.output), **payload}
    if arguments.reputation_command == "insight":
        payload = load_scan_json_file(arguments.matches)
        matches = payload.get("matches") if isinstance(payload, dict) else None
        insight = build_pup_insight(matches)
        write_pup_insight_markdown(arguments.output, render_pup_insight_markdown(insight))
        return {"output": str(arguments.output), "matched_targets": len(matches), "execution_authorized": False}
    raise ValueError("unsupported reputation command")


def _run_pup(arguments: argparse.Namespace) -> dict:
    result = inspect_pup_risk(load_scan_json_file(arguments.input), arguments.seed)
    write_pup_insight_markdown(arguments.output, result["markdown"])
    return {"output": str(arguments.output), "match_count": result["match_count"], "execution_authorized": False}


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
                "quarantined_count",
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
        elif arguments.command == "clean" and arguments.clean_command == "safe":
            summary = _run_cleanup_safe(arguments)
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
        elif arguments.command == "quarantine":
            summary = _run_quarantine(arguments)
        elif arguments.command == "reputation":
            summary = _run_reputation(arguments)
        elif arguments.command == "pup" and arguments.pup_command == "inspect":
            summary = _run_pup(arguments)
        elif arguments.command == "trial" and arguments.trial_command == "run":
            summary = run_user_trial(
                arguments.root,
                arguments.output,
                confirm=arguments.confirm,
                quarantine_root=arguments.quarantine_root,
            )
        else:  # pragma: no cover - argparse enforces the available commands.
            parser.error(f"unsupported command: {arguments.command}")
    except (FileExistsError, FileNotFoundError, KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
