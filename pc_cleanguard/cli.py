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
    get_default_quarantine_root,
    JunkScanner,
    build_cleanup_preview,
    build_cleanup_summary,
    load_cleanup_preview_json,
    preflight_cleanup_artifacts,
    render_cleanup_report_markdown,
    write_cleanup_execution_report,
    write_cleanup_report_markdown,
)
from .demo import (
    init_cleanup_demo,
    quickstart_cleanup_demo,
    run_cleanup_demo,
    run_demo_acceptance,
)
from .pipeline import (
    load_scan_json_file,
    run_readonly_scan_pipeline,
    write_pipeline_audit_jsonl,
    write_pipeline_report,
)
from .quarantine import QuarantineManager
from .persistence import (
    build_agent_governance_preview,
    build_persistence_chain_graph,
    build_persistence_governance_plan,
    render_persistence_chain_markdown,
    render_persistence_governance_plan_markdown,
    validate_agent_execution_request,
)
from .pup import (
    build_pup_corroboration,
    build_behavior_indicators_from_report,
    build_pup_review_pack,
    inspect_pup_risk,
    summarize_behavior_indicators,
    write_behavior_indicators,
    render_corroboration_markdown,
)
from .reputation import (
    ReputationMatcher,
    build_pup_insight,
    load_seed_records,
    render_pup_insight_markdown,
    write_pup_insight_markdown,
    load_evidence_pack,
    evidence_pack_stats,
    build_evidence_pack,
    load_evidence_candidates,
    load_evidence_review_queue,
    write_evidence_pack,
    build_indicators_from_evidence,
    summarize_indicators,
    write_indicators,
    build_human_review_checklist,
    render_human_review_checklist,
    load_cn_candidate_sources,
    load_cn_source_matrix,
    summarize_cn_candidate_sources,
    summarize_cn_source_matrix,
    build_evidence_quality_summary,
    render_evidence_quality_markdown,
    build_evidence_coverage_summary,
    render_evidence_coverage_markdown,
    build_false_positive_feedback_template,
)
from .reporting import build_user_friendly_pup_report, render_user_friendly_pup_report_markdown
from .validation import (
    build_no_match_report,
    build_real_report_trial,
    render_no_match_report_markdown,
    write_real_report_validation_pack,
)
from .skill import invoke_skill_action, write_report
from .experience import run_release_smoke_check, run_user_trial
from .evaluation import run_windows_local_evaluation
from .windows import (
    build_windows_canonical_report,
    load_collector_directory,
    redact_windows_report,
    validate_windows_canonical_report,
    windows_report_stats,
)
from .guard import (
    ActionBundle,
    Disposition,
    Guard,
    GuardContext,
    GuardInputError,
    PolicyBlockedError,
    RequirementPendingError,
    evaluate_bundle,
    load_policy_pack,
)
from .guard.normalize import require_local_path
from . import __version__


LEGACY_COMPATIBILITY_WARNING = (
    "warning: Legacy compatibility interface. Not part of the v0.5 Guard Core."
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pc_cleanguard.cli",
        description=(
            "PC CleanGuard deterministic Windows Agent governance CLI. "
            "Legacy / Compatibility commands remain available below."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"PC CleanGuard Skill {__version__}",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    guard = subcommands.add_parser(
        "guard",
        help="PRIMARY: deterministic policy, consent, precondition, audit, and rollback contracts",
    )
    guard_commands = guard.add_subparsers(dest="guard_command", required=True)

    guard_evaluate = guard_commands.add_parser(
        "evaluate", help="evaluate one structured ActionRequest deterministically"
    )
    evaluate_input = guard_evaluate.add_mutually_exclusive_group(required=True)
    evaluate_input.add_argument("--request", type=Path)
    evaluate_input.add_argument("--stdin", action="store_true")
    guard_evaluate.add_argument("--context", type=Path)
    guard_evaluate.add_argument("--output", type=Path)
    guard_evaluate.add_argument("--overwrite", action="store_true")
    guard_evaluate.add_argument("--json", action="store_true")

    guard_prepare = guard_commands.add_parser(
        "prepare", help="issue an ExecutionContract after every required gate"
    )
    prepare_input = guard_prepare.add_mutually_exclusive_group(required=True)
    prepare_input.add_argument("--decision", type=Path)
    prepare_input.add_argument("--stdin", action="store_true")
    guard_prepare.add_argument("--context", type=Path)
    guard_prepare.add_argument("--consent", type=Path)
    guard_prepare.add_argument("--rollback", type=Path)
    guard_prepare.add_argument("--output", type=Path)
    guard_prepare.add_argument("--overwrite", action="store_true")
    guard_prepare.add_argument("--json", action="store_true")

    guard_audit = guard_commands.add_parser(
        "audit", help="verify local tamper-evident audit receipts"
    )
    guard_audit_commands = guard_audit.add_subparsers(
        dest="guard_audit_command", required=True
    )
    guard_audit_verify = guard_audit_commands.add_parser("verify")
    guard_audit_verify.add_argument("--input", required=True, type=Path)
    guard_audit_verify.add_argument("--json", action="store_true")

    guard_batch = guard_commands.add_parser(
        "batch", help="evaluate a multi-action bundle with maximum restriction"
    )
    guard_batch_commands = guard_batch.add_subparsers(
        dest="guard_batch_command", required=True
    )
    guard_batch_evaluate = guard_batch_commands.add_parser("evaluate")
    batch_input = guard_batch_evaluate.add_mutually_exclusive_group(required=True)
    batch_input.add_argument("--input", type=Path)
    batch_input.add_argument("--stdin", action="store_true")
    guard_batch_evaluate.add_argument("--context", type=Path)
    guard_batch_evaluate.add_argument("--output", type=Path)
    guard_batch_evaluate.add_argument("--overwrite", action="store_true")
    guard_batch_evaluate.add_argument("--json", action="store_true")

    guard_doctor = guard_commands.add_parser(
        "doctor", help="run offline Guard Core dependency and policy checks"
    )
    guard_doctor.add_argument("--json", action="store_true")

    guard_benchmark = guard_commands.add_parser(
        "benchmark", help="run the fixed governance acceptance suite"
    )
    guard_benchmark.add_argument("--suite", required=True, type=Path)
    guard_benchmark.add_argument("--output", required=True, type=Path)
    guard_benchmark.add_argument("--json", action="store_true")

    windows = subcommands.add_parser(
        "windows", help="Legacy / Compatibility: ingest read-only Windows artifacts"
    )
    windows_commands = windows.add_subparsers(dest="windows_command", required=True)
    windows_report = windows_commands.add_parser(
        "report", help="build, validate, or summarize a canonical Windows report"
    )
    windows_report_commands = windows_report.add_subparsers(
        dest="windows_report_command", required=True
    )
    windows_build = windows_report_commands.add_parser("build")
    windows_build.add_argument("--collector-dir", required=True, type=Path)
    windows_build.add_argument("--output", required=True, type=Path)
    windows_build.add_argument("--raw-output", type=Path)
    windows_build.add_argument(
        "--i-understand-local-sensitive-data", action="store_true"
    )
    windows_build.add_argument("--validation-output", type=Path)
    windows_build.add_argument("--overwrite", action="store_true")
    windows_validate = windows_report_commands.add_parser("validate")
    windows_validate.add_argument("--input", required=True, type=Path)
    windows_validate.add_argument("--output", required=True, type=Path)
    windows_validate.add_argument("--overwrite", action="store_true")
    windows_stats = windows_report_commands.add_parser("stats")
    windows_stats.add_argument("--input", required=True, type=Path)
    windows_stats.add_argument("--output", required=True, type=Path)
    windows_stats.add_argument("--overwrite", action="store_true")
    evaluation = subcommands.add_parser(
        "evaluation", help="evaluate an explicit redacted report entirely offline"
    )
    evaluation_commands = evaluation.add_subparsers(
        dest="evaluation_command", required=True
    )
    evaluation_windows = evaluation_commands.add_parser("windows")
    evaluation_windows.add_argument("--report", required=True, type=Path)
    evaluation_windows.add_argument("--output", required=True, type=Path)
    evaluation_windows.add_argument("--evidence-pack", required=True, type=Path)
    evaluation_windows.add_argument("--cn-win-evidence-pack", type=Path)
    evaluation_windows.add_argument("--include-persistence-chain", action="store_true")
    evaluation_windows.add_argument("--include-pup-review", action="store_true")
    evaluation_windows.add_argument("--include-evidence-quality", action="store_true")
    evaluation_windows.add_argument("--include-user-friendly-report", action="store_true")
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
        help="Legacy / Compatibility: bounded cleanup preview and execution",
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
    demo_acceptance = demo_commands.add_parser(
        "acceptance",
        help="verify quarantine and restore in a dedicated synthetic temp workspace",
    )
    demo_acceptance.add_argument("--output", required=True, type=Path)
    demo_acceptance.add_argument("--confirm-synthetic", action="store_true")
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
    reputation = subcommands.add_parser(
        "reputation", help="Legacy / Compatibility: offline reputation evidence matching"
    )
    reputation_commands = reputation.add_subparsers(dest="reputation_command", required=True)
    reputation_match = reputation_commands.add_parser("match")
    reputation_match.add_argument("--input", required=True, type=Path)
    reputation_match.add_argument("--seed", required=True, type=Path)
    reputation_match.add_argument("--output", required=True, type=Path)
    reputation_insight = reputation_commands.add_parser("insight")
    reputation_insight.add_argument("--matches", required=True, type=Path)
    reputation_insight.add_argument("--output", required=True, type=Path)
    evidence = reputation_commands.add_parser("evidence")
    evidence_commands = evidence.add_subparsers(dest="evidence_command", required=True)
    for evidence_command in ("validate", "stats", "cn-validate", "cn-stats"):
        evidence_parser = evidence_commands.add_parser(evidence_command)
        evidence_parser.add_argument("--input", required=True, type=Path)
    evidence_intake = evidence_commands.add_parser("intake")
    evidence_intake_commands = evidence_intake.add_subparsers(
        dest="evidence_flow_command", required=True
    )
    evidence_intake_validate = evidence_intake_commands.add_parser("validate")
    evidence_intake_validate.add_argument("--input", required=True, type=Path)
    evidence_review = evidence_commands.add_parser("review")
    evidence_review_commands = evidence_review.add_subparsers(
        dest="evidence_flow_command", required=True
    )
    evidence_review_validate = evidence_review_commands.add_parser("validate")
    evidence_review_validate.add_argument("--input", required=True, type=Path)
    evidence_build = evidence_commands.add_parser("build")
    evidence_build.add_argument("--candidates", required=True, type=Path)
    evidence_build.add_argument("--reviews", required=True, type=Path)
    evidence_build.add_argument("--output", required=True, type=Path)
    evidence_indicators = evidence_commands.add_parser("indicators")
    evidence_indicators.add_argument("--input", required=True, type=Path)
    evidence_indicators.add_argument("--output", required=True, type=Path)
    evidence_indicators.add_argument("--overwrite", action="store_true")
    evidence_indicator_stats = evidence_commands.add_parser("indicators-stats")
    evidence_indicator_stats.add_argument("--input", required=True, type=Path)
    evidence_quality = evidence_commands.add_parser("quality")
    evidence_quality.add_argument("--inputs", required=True, nargs="+", type=Path)
    evidence_quality.add_argument("--output", required=True, type=Path)
    evidence_quality.add_argument("--overwrite", action="store_true")
    evidence_coverage = evidence_commands.add_parser("coverage")
    evidence_coverage.add_argument("--inputs", required=True, nargs="+", type=Path)
    evidence_coverage.add_argument("--candidates", required=True, type=Path)
    evidence_coverage.add_argument("--backlog", required=True, type=Path)
    evidence_coverage.add_argument("--output", required=True, type=Path)
    evidence_coverage.add_argument("--overwrite", action="store_true")
    cn_source = reputation_commands.add_parser("cn-source")
    cn_source_commands = cn_source.add_subparsers(dest="cn_source_command", required=True)
    for cn_source_command in ("validate", "stats"):
        cn_source_parser = cn_source_commands.add_parser(cn_source_command)
        cn_source_parser.add_argument("--input", required=True, type=Path)
    cn_source_candidates = cn_source_commands.add_parser("candidates")
    cn_source_candidates.add_argument("--input", required=True, type=Path)
    cn_source_candidates.add_argument("--output", required=True, type=Path)
    cn_source_candidates.add_argument("--overwrite", action="store_true")
    pup = subcommands.add_parser(
        "pup", help="Legacy / Compatibility: inspect PUP evidence without execution"
    )
    pup_commands = pup.add_subparsers(dest="pup_command", required=True)
    pup_inspect = pup_commands.add_parser("inspect")
    pup_inspect.add_argument("--input", required=True, type=Path)
    pup_source = pup_inspect.add_mutually_exclusive_group(required=True)
    pup_source.add_argument("--seed", type=Path)
    pup_source.add_argument("--evidence-pack", type=Path)
    pup_inspect.add_argument("--output", required=True, type=Path)
    pup_inspect.add_argument("--include-indicators", action="store_true")
    pup_inspect.add_argument("--human-review-checklist", type=Path)
    pup_review_pack = pup_commands.add_parser("review-pack")
    pup_review_pack.add_argument("--input", required=True, type=Path)
    pup_review_pack.add_argument("--evidence-pack", required=True, type=Path)
    pup_review_pack.add_argument("--cn-evidence-pack", type=Path)
    pup_review_pack.add_argument("--cn-win-evidence-pack", type=Path)
    pup_review_pack.add_argument("--cn-source-matrix", type=Path)
    pup_review_pack.add_argument("--output", required=True, type=Path)
    pup_review_pack.add_argument("--include-indicators", action="store_true")
    pup_review_pack.add_argument("--human-review-checklist", action="store_true")
    pup_review_pack.add_argument("--source-trace", action="store_true")
    pup_review_pack.add_argument("--feedback-template", action="store_true")
    pup_review_pack.add_argument("--overwrite", action="store_true")
    pup_review_pack.add_argument("--include-behavior-indicators", action="store_true")
    pup_review_pack.add_argument("--include-evidence-quality", action="store_true")
    pup_review_pack.add_argument("--include-real-report-validation-summary", action="store_true")
    pup_review_pack.add_argument("--include-corroboration", action="store_true")
    pup_review_pack.add_argument("--include-coverage", action="store_true")
    pup_review_pack.add_argument("--include-user-friendly-report", action="store_true")
    pup_review_pack.add_argument("--include-false-positive-template", action="store_true")
    pup_review_pack.add_argument("--include-persistence-chain", action="store_true")
    pup_corroborate = pup_commands.add_parser("corroborate")
    pup_corroborate.add_argument("--matches", required=True, type=Path)
    pup_corroborate.add_argument("--behavior-indicators", required=True, type=Path)
    pup_corroborate.add_argument("--output", required=True, type=Path)
    pup_corroborate.add_argument("--overwrite", action="store_true")
    pup_behavior = pup_commands.add_parser("behavior")
    pup_behavior.add_argument("--input", required=True, type=Path)
    pup_behavior.add_argument("--output", required=True, type=Path)
    pup_behavior.add_argument("--overwrite", action="store_true")
    validate = subcommands.add_parser("validate", help="validate explicit local artifacts offline")
    validate_commands = validate.add_subparsers(dest="validate_command", required=True)
    validate_report = validate_commands.add_parser("report")
    validate_report.add_argument("--input", required=True, type=Path)
    validate_report.add_argument("--output", required=True, type=Path)
    validate_report.add_argument("--overwrite", action="store_true")
    trial = subcommands.add_parser(
        "trial", help="Legacy / Compatibility: run the bounded five-minute product trial"
    )
    trial_commands = trial.add_subparsers(dest="trial_command", required=True)
    trial_run = trial_commands.add_parser("run")
    trial_run.add_argument("--root", required=True, type=Path)
    trial_run.add_argument("--output", required=True, type=Path)
    trial_run.add_argument("--confirm", action="store_true")
    trial_run.add_argument("--quarantine-root", type=Path)
    trial_report = trial_commands.add_parser("report")
    trial_report.add_argument("--input", required=True, type=Path)
    trial_report.add_argument("--output", required=True, type=Path)
    trial_report.add_argument("--evidence-pack", required=True, type=Path)
    trial_report.add_argument("--cn-win-evidence-pack", type=Path)
    trial_report.add_argument("--cn-source-matrix", type=Path)
    trial_report.add_argument("--include-behavior-indicators", action="store_true")
    trial_report.add_argument("--include-evidence-quality", action="store_true")
    trial_report.add_argument("--include-coverage", action="store_true")
    trial_report.add_argument("--include-user-friendly-report", action="store_true")
    trial_report.add_argument("--include-persistence-chain", action="store_true")
    trial_report.add_argument("--overwrite", action="store_true")
    validation = subcommands.add_parser("validation", help="explain local validation results")
    validation_commands = validation.add_subparsers(dest="validation_command", required=True)
    validation_no_match = validation_commands.add_parser("no-match")
    validation_no_match.add_argument("--input", required=True, type=Path)
    validation_no_match.add_argument("--output", required=True, type=Path)
    validation_no_match.add_argument("--overwrite", action="store_true")
    report = subcommands.add_parser("report", help="render user-facing local reports")
    report_commands = report.add_subparsers(dest="report_command", required=True)
    report_user = report_commands.add_parser("user-friendly")
    report_user.add_argument("--review-pack", required=True, type=Path)
    report_user.add_argument("--output", required=True, type=Path)
    report_user.add_argument("--overwrite", action="store_true")
    feedback = subcommands.add_parser("feedback", help="build local feedback templates")
    feedback_commands = feedback.add_subparsers(dest="feedback_command", required=True)
    feedback_fp = feedback_commands.add_parser("false-positive-template")
    feedback_fp.add_argument("--match", required=True, type=Path)
    feedback_fp.add_argument("--output", required=True, type=Path)
    feedback_fp.add_argument("--overwrite", action="store_true")
    persistence = subcommands.add_parser(
        "persistence",
        help="Legacy / Compatibility: build offline persistence-chain review artifacts",
    )
    persistence_commands = persistence.add_subparsers(dest="persistence_command", required=True)
    persistence_graph = persistence_commands.add_parser("graph")
    persistence_graph.add_argument("--input", required=True, type=Path)
    persistence_graph.add_argument("--output", required=True, type=Path)
    persistence_graph.add_argument("--json-output", required=True, type=Path)
    persistence_graph.add_argument("--overwrite", action="store_true")
    persistence_plan = persistence_commands.add_parser("plan")
    persistence_plan.add_argument("--graph", required=True, type=Path)
    persistence_plan.add_argument("--output", required=True, type=Path)
    persistence_plan.add_argument("--json-output", required=True, type=Path)
    persistence_plan.add_argument("--overwrite", action="store_true")
    agent = subcommands.add_parser("agent", help="build and validate L0 Agent governance requests")
    agent_commands = agent.add_subparsers(dest="agent_command", required=True)
    agent_preview = agent_commands.add_parser("governance-preview")
    agent_preview.add_argument("--input", required=True, type=Path)
    agent_preview.add_argument("--output", required=True, type=Path)
    agent_preview.add_argument("--overwrite", action="store_true")
    agent_validate = agent_commands.add_parser("validate-request")
    agent_validate.add_argument("--input", required=True, type=Path)
    agent_validate.add_argument("--output", required=True, type=Path)
    agent_validate.add_argument("--overwrite", action="store_true")
    doctor = subcommands.add_parser("doctor", help="run read-only project checks")
    doctor_commands = doctor.add_subparsers(dest="doctor_command", required=True)
    doctor_commands.add_parser("release-check", help="verify local v0.4.0 release assets")
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


def _preflight_windows_outputs(paths: list[Path], *, overwrite: bool) -> None:
    resolved = [path.resolve(strict=False) for path in paths]
    if len({str(path).casefold() for path in resolved}) != len(resolved):
        raise ValueError("Windows report output paths must be different")
    if not overwrite:
        for path in paths:
            if path.exists():
                raise FileExistsError(f"output already exists: {path}")


def _run_windows_report(arguments: argparse.Namespace) -> dict:
    if arguments.windows_report_command == "build":
        if arguments.raw_output is not None and not arguments.i_understand_local_sensitive_data:
            raise ValueError(
                "raw output may contain sensitive local metadata; pass --i-understand-local-sensitive-data"
            )
        destinations = [arguments.output]
        if arguments.raw_output is not None:
            destinations.append(arguments.raw_output)
        if arguments.validation_output is not None:
            destinations.append(arguments.validation_output)
        _preflight_windows_outputs(destinations, overwrite=arguments.overwrite)
        loaded = load_collector_directory(arguments.collector_dir)
        raw_report = build_windows_canonical_report(loaded)
        redacted_report, _ = redact_windows_report(raw_report)
        errors = validate_windows_canonical_report(redacted_report)
        if errors:
            raise ValueError("canonical report validation failed: " + "; ".join(errors))
        stats = windows_report_stats(redacted_report)
        write_report(arguments.output, redacted_report, explicit_overwrite=arguments.overwrite)
        if arguments.raw_output is not None:
            write_report(arguments.raw_output, raw_report, explicit_overwrite=arguments.overwrite)
        if arguments.validation_output is not None:
            write_report(
                arguments.validation_output,
                {"valid": True, "errors": [], "stats": stats},
                explicit_overwrite=arguments.overwrite,
            )
        return {
            "output": str(arguments.output),
            "raw_output_written": arguments.raw_output is not None,
            "validation_output": str(arguments.validation_output) if arguments.validation_output else None,
            **{key: stats[key] for key in (
                "software_count", "startup_count", "service_count",
                "scheduled_task_count", "redacted_value_count", "matchability_score",
                "persistence_input_ready",
            )},
            "system_modification_performed": False,
            "runtime_network_access": False,
        }
    report = load_scan_json_file(arguments.input)
    _preflight_windows_outputs([arguments.output], overwrite=arguments.overwrite)
    if arguments.windows_report_command == "validate":
        errors = validate_windows_canonical_report(report)
        payload = {
            "valid": not errors,
            "errors": errors,
            "stats": windows_report_stats(report),
            "execution_authorized": False,
        }
        write_report(arguments.output, payload, explicit_overwrite=arguments.overwrite)
        return {"output": str(arguments.output), "valid": not errors, "error_count": len(errors)}
    if arguments.windows_report_command == "stats":
        payload = windows_report_stats(report)
        write_report(arguments.output, payload, explicit_overwrite=arguments.overwrite)
        return {"output": str(arguments.output), **payload}
    raise ValueError("unsupported Windows report command")


def _run_windows_evaluation(arguments: argparse.Namespace) -> dict:
    report = load_scan_json_file(arguments.report)
    result = run_windows_local_evaluation(
        report,
        arguments.output,
        arguments.evidence_pack,
        cn_win_evidence_pack=arguments.cn_win_evidence_pack,
        include_persistence_chain=arguments.include_persistence_chain,
        include_pup_review=arguments.include_pup_review,
        include_evidence_quality=arguments.include_evidence_quality,
        include_user_friendly_report=arguments.include_user_friendly_report,
    )
    return result.to_dict()


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
    quarantine_root = arguments.quarantine_root
    uses_default_quarantine = arguments.confirm and quarantine_root is None and not arguments.permanent
    if uses_default_quarantine:
        quarantine_root = get_default_quarantine_root()
    report = CleanupExecutor(
        quarantine_root=quarantine_root,
        permanent=arguments.permanent,
        permanent_delete_acknowledged=arguments.i_understand_permanent_delete,
        using_default_quarantine=uses_default_quarantine,
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
    quarantine_root = arguments.quarantine_root
    uses_default_quarantine = arguments.confirm and quarantine_root is None
    if uses_default_quarantine:
        quarantine_root = get_default_quarantine_root()
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
    execution = CleanupExecutor(quarantine_root=quarantine_root, using_default_quarantine=uses_default_quarantine).execute(
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
        "quarantine_root": str(quarantine_root) if quarantine_root is not None else None,
        "default_quarantine_root": uses_default_quarantine,
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
    if arguments.reputation_command == "cn-source":
        if arguments.cn_source_command in {"validate", "stats"}:
            sources = load_cn_source_matrix(arguments.input)
            result = summarize_cn_source_matrix(sources)
            return {"valid": True, **result}
        candidates = load_cn_candidate_sources(arguments.input)
        result = summarize_cn_candidate_sources(candidates)
        payload = {
            **result,
            "candidates": candidates,
            "execution_gating_eligible_count": 0,
            "execution_authorized": False,
            "runtime_network_access": False,
        }
        write_report(arguments.output, payload, explicit_overwrite=arguments.overwrite)
        return {"output": str(arguments.output), **result}
    if arguments.reputation_command == "evidence":
        if arguments.evidence_command == "coverage":
            records = [load_evidence_pack(path) for path in arguments.inputs]
            candidates = json.loads(arguments.candidates.read_text(encoding="utf-8"))
            backlog = json.loads(arguments.backlog.read_text(encoding="utf-8"))
            summary = build_evidence_coverage_summary(records, candidates, backlog)
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            with arguments.output.open("w" if arguments.overwrite else "x", encoding="utf-8", newline="\n") as stream:
                stream.write(render_evidence_coverage_markdown(summary))
            return {"output": str(arguments.output), **summary}
        if arguments.evidence_command == "quality":
            records = [load_evidence_pack(path) for path in arguments.inputs]
            summary = build_evidence_quality_summary(records)
            destination = arguments.output
            from .pipeline.input_loader import _validated_explicit_local_path
            _validated_explicit_local_path(destination, allowed_suffixes={".md"})
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("w" if arguments.overwrite else "x", encoding="utf-8", newline="\n") as stream:
                stream.write(render_evidence_quality_markdown(summary))
            return {"output": str(destination), **summary}
        if arguments.evidence_command == "intake":
            candidates = load_evidence_candidates(arguments.input)
            return {
                "valid": True,
                "candidate_count": len(candidates),
                "runtime_network_access": False,
                "execution_authorized": False,
            }
        if arguments.evidence_command == "review":
            reviews = load_evidence_review_queue(arguments.input)
            return {
                "valid": True,
                "review_count": len(reviews),
                "runtime_network_access": False,
                "execution_authorized": False,
            }
        if arguments.evidence_command == "build":
            candidates = load_evidence_candidates(arguments.candidates)
            reviews = load_evidence_review_queue(arguments.reviews)
            records = build_evidence_pack(candidates, reviews)
            destination = write_evidence_pack(arguments.output, records)
            return {
                "output": str(destination),
                "record_count": len(records),
                **evidence_pack_stats(records),
                "runtime_network_access": False,
                "execution_authorized": False,
            }
        if arguments.evidence_command in {"indicators", "indicators-stats"}:
            records = load_evidence_pack(arguments.input)
            indicators = [
                item for record in records for item in build_indicators_from_evidence(record)
            ]
            stats = summarize_indicators(indicators)
            if arguments.evidence_command == "indicators":
                destination = write_indicators(
                    arguments.output, indicators, overwrite=arguments.overwrite
                )
                return {"output": str(destination), **stats, "execution_authorized": False}
            return {**stats, "execution_authorized": False}
        records = load_evidence_pack(arguments.input)
        stats = evidence_pack_stats(records)
        result = {"valid": True, "record_count": len(records), **stats, "execution_authorized": False}
        if arguments.evidence_command in {"cn-validate", "cn-stats"}:
            if any(item["language"] != "zh-CN" for item in records):
                raise ValueError("CN evidence pack requires language=zh-CN")
            result["cn_real_source_count"] = sum(item["is_synthetic"] is False for item in records)
            result["runtime_network_access"] = False
        return result
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
    if arguments.pup_command == "corroborate":
        matches_payload = json.loads(arguments.matches.read_text(encoding="utf-8"))
        behavior_payload = json.loads(arguments.behavior_indicators.read_text(encoding="utf-8"))
        matches = matches_payload.get("matches", matches_payload) if isinstance(matches_payload, dict) else matches_payload
        indicators = behavior_payload.get("behavior_indicators", behavior_payload) if isinstance(behavior_payload, dict) else behavior_payload
        result = build_pup_corroboration(matches, indicators)
        with arguments.output.open("w" if arguments.overwrite else "x", encoding="utf-8", newline="\n") as stream:
            stream.write(render_corroboration_markdown(result))
        return {"output": str(arguments.output), **{key: value for key, value in result.items() if key.endswith("_count")}, "execution_authorized": False}
    if arguments.pup_command == "behavior":
        indicators = build_behavior_indicators_from_report(load_scan_json_file(arguments.input))
        destination = write_behavior_indicators(
            arguments.output, indicators, overwrite=arguments.overwrite
        )
        return {
            "output": str(destination),
            **summarize_behavior_indicators(indicators),
            "execution_authorized": False,
            "runtime_network_access": False,
        }
    if arguments.pup_command == "review-pack":
        return build_pup_review_pack(
            load_scan_json_file(arguments.input),
            arguments.evidence_pack,
            arguments.output,
            cn_evidence_pack=arguments.cn_evidence_pack,
            cn_win_evidence_pack=arguments.cn_win_evidence_pack,
            cn_source_matrix=arguments.cn_source_matrix,
            include_behavior_indicators=arguments.include_behavior_indicators,
            include_evidence_quality=arguments.include_evidence_quality,
            include_real_report_validation_summary=arguments.include_real_report_validation_summary,
            include_corroboration=arguments.include_corroboration,
            include_coverage=arguments.include_coverage,
            include_user_friendly_report=arguments.include_user_friendly_report,
            include_false_positive_template=arguments.include_false_positive_template,
            include_persistence_chain=arguments.include_persistence_chain,
            overwrite=arguments.overwrite,
        )
    source = arguments.evidence_pack or arguments.seed
    result = inspect_pup_risk(
        load_scan_json_file(arguments.input), source,
        evidence_pack=arguments.evidence_pack is not None,
        include_indicators=arguments.include_indicators,
    )
    write_pup_insight_markdown(arguments.output, result["markdown"])
    if arguments.human_review_checklist is not None:
        write_pup_insight_markdown(
            arguments.human_review_checklist,
            render_human_review_checklist(build_human_review_checklist(result["matches"])),
        )
    return {"output": str(arguments.output), "match_count": result["match_count"], "execution_authorized": False}


def _write_markdown(path: Path, value: str, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
        stream.write(value.rstrip() + "\n")


def _run_persistence(arguments: argparse.Namespace) -> dict:
    if arguments.persistence_command == "graph":
        graph = build_persistence_chain_graph(load_scan_json_file(arguments.input))
        _write_markdown(arguments.output, render_persistence_chain_markdown(graph), arguments.overwrite)
        write_report(arguments.json_output, graph, explicit_overwrite=arguments.overwrite)
        return {"output": str(arguments.output), "json_output": str(arguments.json_output), **graph["risk_summary"], "execution_authorized": False}
    graph = load_scan_json_file(arguments.graph)
    plan = build_persistence_governance_plan(graph)
    _write_markdown(arguments.output, render_persistence_governance_plan_markdown(plan), arguments.overwrite)
    write_report(arguments.json_output, plan, explicit_overwrite=arguments.overwrite)
    return {"output": str(arguments.output), "json_output": str(arguments.json_output), "blocked_auto_execution_count": plan["blocked_auto_execution_count"], "execution_authorized": False}


def _run_agent(arguments: argparse.Namespace) -> dict:
    payload = load_scan_json_file(arguments.input)
    result = build_agent_governance_preview(payload) if arguments.agent_command == "governance-preview" else validate_agent_execution_request(payload)
    write_report(arguments.output, result, explicit_overwrite=arguments.overwrite)
    return {"output": str(arguments.output), **result}


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


def _guard_json_file(path: Path, *, name: str) -> dict:
    if not isinstance(path, Path):
        raise GuardInputError(f"{name} path is required")
    require_local_path(path, name=f"{name} path")
    if path.suffix.casefold() != ".json" or not path.is_file():
        raise GuardInputError(f"{name} must be an explicit existing .json file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GuardInputError(f"unable to read {name}: {error}") from error
    if not isinstance(value, dict):
        raise GuardInputError(f"{name} must contain a JSON object")
    return value


def _guard_stdin_envelope() -> dict:
    try:
        value = json.load(sys.stdin)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise GuardInputError(f"stdin must contain one JSON object: {error}") from error
    if not isinstance(value, dict):
        raise GuardInputError("stdin must contain one JSON object")
    return value


def _write_guard_json(path: Path | None, value: dict, *, overwrite: bool) -> None:
    if path is None:
        return
    require_local_path(path, name="Guard output path")
    if path.suffix.casefold() != ".json":
        raise GuardInputError("Guard output path must end in .json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")


def _guard_doctor_result() -> dict:
    guard_root = Path(__file__).resolve().parent / "guard"
    forbidden = (
        "subprocess", "requests", "httpx", "socket", "urllib", "openai",
        "anthropic", "powershell", "os.system",
    )
    legacy_imports = (
        "from ..pup", "from ..reputation", "from ..persistence", "from ..cleanup",
        "from ..windows",
    )
    dangerous_hits = []
    legacy_dependency_hits = []
    modules = sorted(guard_root.glob("*.py"))
    for path in modules:
        source = path.read_text(encoding="utf-8").casefold()
        for token in forbidden:
            if token in source:
                dangerous_hits.append({"file": path.name, "token": token})
        for token in legacy_imports:
            if token in source:
                legacy_dependency_hits.append({"file": path.name, "token": token})
    policy = load_policy_pack()
    schema_root = Path(__file__).resolve().parents[1] / "schemas" / "guard"
    schema_count = len(list(schema_root.glob("*.schema.json")))
    healthy = not dangerous_hits and not legacy_dependency_hits and schema_count == 8
    return {
        "healthy": healthy,
        "version": __version__,
        "platform": "windows",
        "guard_module_count": len(modules),
        "core_schema_count": schema_count,
        "policy_id": policy["policy_id"],
        "policy_version": policy["version"],
        "policy_rule_count": len(policy["rules"]),
        "dangerous_import_hits": dangerous_hits,
        "legacy_dependency_hits": legacy_dependency_hits,
        "network_dependency": False,
        "llm_dependency": False,
        "executor_dependency": False,
    }


def _run_guard(arguments: argparse.Namespace) -> tuple[dict, int]:
    if arguments.guard_command == "evaluate":
        if arguments.stdin:
            envelope = _guard_stdin_envelope()
            if set(envelope) != {"request", "context"}:
                raise GuardInputError("stdin evaluate envelope requires request and context")
            request_data = envelope["request"]
            context_data = envelope["context"]
        else:
            request_data = _guard_json_file(arguments.request, name="request")
            context_data = _guard_json_file(arguments.context, name="context")
        decision = Guard().evaluate(request_data, context_data)
        payload = decision.to_dict()
        _write_guard_json(arguments.output, payload, overwrite=arguments.overwrite)
        code = 3 if decision.disposition is Disposition.BLOCK else 4 if decision.disposition is Disposition.REQUIRE else 0
        return payload, code

    if arguments.guard_command == "prepare":
        if arguments.stdin:
            envelope = _guard_stdin_envelope()
            required = {"decision", "context"}
            allowed = required | {"consent", "rollback", "now"}
            if not required.issubset(envelope) or set(envelope) - allowed:
                raise GuardInputError("stdin prepare envelope requires decision/context and only optional consent/rollback/now")
            decision_data = envelope["decision"]
            context_data = envelope["context"]
            consent_data = envelope.get("consent")
            rollback_data = envelope.get("rollback")
            now = envelope.get("now")
        else:
            decision_data = _guard_json_file(arguments.decision, name="decision")
            context_data = _guard_json_file(arguments.context, name="context")
            consent_data = _guard_json_file(arguments.consent, name="consent") if arguments.consent is not None else None
            rollback_data = _guard_json_file(arguments.rollback, name="rollback") if arguments.rollback is not None else None
            now = None
        contract = Guard().prepare_execution(
            decision=decision_data,
            consent=consent_data,
            rollback=rollback_data,
            current_context=context_data,
            now=now,
        )
        payload = contract.to_dict()
        _write_guard_json(arguments.output, payload, overwrite=arguments.overwrite)
        return payload, 0

    if arguments.guard_command == "audit" and arguments.guard_audit_command == "verify":
        verification = Guard().verify_audit(arguments.input)
        return verification.to_dict(), 0 if verification.valid else 5

    if arguments.guard_command == "batch" and arguments.guard_batch_command == "evaluate":
        if arguments.stdin:
            envelope = _guard_stdin_envelope()
            if set(envelope) != {"bundle", "context"}:
                raise GuardInputError("stdin batch envelope requires bundle and context")
            bundle_data = envelope["bundle"]
            context_data = envelope["context"]
        else:
            bundle_data = _guard_json_file(arguments.input, name="bundle")
            context_data = _guard_json_file(arguments.context, name="context")
        result = evaluate_bundle(
            ActionBundle.from_dict(bundle_data), GuardContext.from_dict(context_data)
        )
        payload = result.to_dict()
        _write_guard_json(arguments.output, payload, overwrite=arguments.overwrite)
        code = 3 if result.disposition is Disposition.BLOCK else 4 if result.disposition is Disposition.REQUIRE else 0
        return payload, code

    if arguments.guard_command == "doctor":
        payload = _guard_doctor_result()
        return payload, 0 if payload["healthy"] else 5

    if arguments.guard_command == "benchmark":
        from .guard.benchmark import run_benchmark

        payload = run_benchmark(arguments.suite, arguments.output)
        return payload, 0 if payload["failed"] == 0 else 5

    raise GuardInputError("unsupported Guard command")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    parser = _parser()
    arguments = parser.parse_args(argv)
    if arguments.command == "guard":
        try:
            payload, exit_code = _run_guard(arguments)
        except PolicyBlockedError as error:
            print(f"error: {error}", file=sys.stderr)
            return 3
        except RequirementPendingError as error:
            print(f"error: {error}", file=sys.stderr)
            return 4
        except (FileExistsError, FileNotFoundError, GuardInputError, KeyError, OSError, TypeError, ValueError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        except Exception as error:  # pragma: no cover - final fail-closed boundary.
            print(f"internal validation error: {error}", file=sys.stderr)
            return 5
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return exit_code
    print(LEGACY_COMPATIBILITY_WARNING, file=sys.stderr)
    try:
        if arguments.command == "windows" and arguments.windows_command == "report":
            summary = _run_windows_report(arguments)
        elif arguments.command == "evaluation" and arguments.evaluation_command == "windows":
            summary = _run_windows_evaluation(arguments)
        elif arguments.command == "scan":
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
        elif arguments.command == "demo" and arguments.demo_command == "acceptance":
            summary = run_demo_acceptance(
                arguments.output,
                confirm_synthetic=arguments.confirm_synthetic,
            )
        elif arguments.command == "quarantine":
            summary = _run_quarantine(arguments)
        elif arguments.command == "reputation":
            summary = _run_reputation(arguments)
        elif arguments.command == "pup":
            summary = _run_pup(arguments)
        elif arguments.command == "persistence":
            summary = _run_persistence(arguments)
        elif arguments.command == "agent":
            summary = _run_agent(arguments)
        elif arguments.command == "validate" and arguments.validate_command == "report":
            summary = write_real_report_validation_pack(
                load_scan_json_file(arguments.input), arguments.output, overwrite=arguments.overwrite
            )
        elif arguments.command == "trial" and arguments.trial_command == "run":
            summary = run_user_trial(
                arguments.root,
                arguments.output,
                confirm=arguments.confirm,
                quarantine_root=arguments.quarantine_root,
            )
        elif arguments.command == "trial" and arguments.trial_command == "report":
            summary = build_real_report_trial(
                load_scan_json_file(arguments.input), arguments.output, arguments.evidence_pack,
                cn_win_evidence_pack=arguments.cn_win_evidence_pack,
                cn_source_matrix=arguments.cn_source_matrix,
                include_behavior_indicators=arguments.include_behavior_indicators,
                include_evidence_quality=arguments.include_evidence_quality,
                include_coverage=arguments.include_coverage,
                include_user_friendly_report=arguments.include_user_friendly_report,
                include_persistence_chain=arguments.include_persistence_chain,
                overwrite=arguments.overwrite,
            )
        elif arguments.command == "validation" and arguments.validation_command == "no-match":
            report = load_scan_json_file(arguments.input)
            value_report = build_no_match_report(report, [], {})
            with arguments.output.open("w" if arguments.overwrite else "x", encoding="utf-8", newline="\n") as stream:
                stream.write(render_no_match_report_markdown(value_report))
            summary = {"output": str(arguments.output), "execution_authorized": False, "runtime_network_access": False}
        elif arguments.command == "report" and arguments.report_command == "user-friendly":
            machine = load_scan_json_file(arguments.review_pack / "machine_summary.json")
            friendly = build_user_friendly_pup_report(machine)
            with arguments.output.open("w" if arguments.overwrite else "x", encoding="utf-8", newline="\n") as stream:
                stream.write(render_user_friendly_pup_report_markdown(friendly))
            summary = {"output": str(arguments.output), "execution_gating_eligible_count": 0, "execution_authorized": False}
        elif arguments.command == "feedback" and arguments.feedback_command == "false-positive-template":
            payload = json.loads(arguments.match.read_text(encoding="utf-8"))
            if isinstance(payload, dict): payload = payload.get("matches", payload)
            match = payload[0] if isinstance(payload, list) and payload else payload
            template = build_false_positive_feedback_template(match or {}, {})
            write_report(arguments.output, template, explicit_overwrite=arguments.overwrite)
            summary = {"output": str(arguments.output), "review_status": template["review_status"], "execution_authorized": False}
        elif arguments.command == "doctor" and arguments.doctor_command == "release-check":
            summary = run_release_smoke_check()
        else:  # pragma: no cover - argparse enforces the available commands.
            parser.error(f"unsupported command: {arguments.command}")
    except (FileExistsError, FileNotFoundError, KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
