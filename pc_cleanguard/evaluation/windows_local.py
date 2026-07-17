"""Evaluate one explicit redacted canonical report entirely offline."""

from __future__ import annotations

import json
from pathlib import Path

from ..persistence import (
    build_persistence_chain_graph,
    build_persistence_governance_plan,
    build_persistence_link_diagnostics,
    render_persistence_chain_markdown,
    render_persistence_governance_plan_markdown,
)
from ..pup import build_pup_review_pack
from ..reputation import load_evidence_pack
from ..skill import write_report
from ..windows import validate_windows_canonical_report, windows_report_stats
from .result import WindowsLocalEvaluationResult


def _output_directory(path: str | Path) -> Path:
    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise ValueError("evaluation output must be an explicit local path")
    raw = str(path).replace("/", "\\")
    if raw.startswith("\\\\"):
        raise ValueError("evaluation output must not use UNC or network paths")
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"evaluation output already exists: {destination}")
    if destination.is_symlink():
        raise ValueError("evaluation output must not be a symbolic link")
    return destination.resolve(strict=False)


def _text(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def _records(value) -> list[dict]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        return load_evidence_pack(value)
    if isinstance(value, list):
        return value
    raise TypeError("evidence pack must be a path or list")


def run_windows_local_evaluation(
    report: dict,
    output: str | Path,
    evidence_pack,
    *,
    cn_win_evidence_pack=None,
    include_persistence_chain: bool = False,
    include_pup_review: bool = False,
    include_evidence_quality: bool = False,
    include_user_friendly_report: bool = False,
) -> WindowsLocalEvaluationResult:
    """Consume a report only; collection and system mutation are outside this API."""

    errors = validate_windows_canonical_report(report)
    if errors:
        raise ValueError("invalid canonical Windows report: " + "; ".join(errors))
    if report.get("source_kind") != "windows_collector_redacted":
        raise ValueError("evaluation windows requires a redacted canonical report")
    destination = _output_directory(output)
    destination.mkdir(parents=True)
    stats = windows_report_stats(report)
    primary_records = _records(evidence_pack)
    cn_records = _records(cn_win_evidence_pack)

    environment = {
        "schema_version": "0.4.1",
        "platform": report["platform"],
        "source_kind": report["source_kind"],
        "privacy_mode": report["privacy_mode"],
        "collector_success_count": stats["collector_success_count"],
        "collector_failure_count": stats["collector_failure_count"],
        "collector_record_count": sum(stats[key] for key in ("software_count", "startup_count", "service_count", "scheduled_task_count")),
        "collector_execution_performed": False,
        "runtime_network_access": False,
        "uploaded": False,
        "system_modification_performed": False,
    }
    write_report(destination / "environment_summary.json", environment)
    write_report(destination / "report_validation.json", {
        "valid": True, "canonical": True, "errors": [],
        "redacted": True, "source_kind": report["source_kind"],
        "execution_authorized": False,
    })
    write_report(destination / "report_stats.json", stats)
    _text(destination / "matchability_summary.md", "\n".join([
        "# Matchability Summary", "",
        f"- score: `{stats['matchability_score']}`",
        f"- unsupported fields: `{stats['unsupported_field_count']}`",
        "- 结构可匹配不等于软件有害，也不构成执行授权。",
    ]))

    matches: list[dict] = []
    behavior: list[dict] = []
    review_summary: dict = {}
    review_dir = destination / "pup_review_pack"
    if include_pup_review:
        review_summary = build_pup_review_pack(
            report,
            primary_records,
            review_dir,
            cn_win_evidence_pack=cn_records,
            include_behavior_indicators=True,
            include_evidence_quality=include_evidence_quality,
            include_real_report_validation_summary=True,
            include_corroboration=True,
            include_coverage=include_evidence_quality,
            include_user_friendly_report=include_user_friendly_report,
            include_persistence_chain=include_persistence_chain,
        )
        matches = json.loads((review_dir / "reputation_matches.json").read_text(encoding="utf-8"))
        behavior = json.loads((review_dir / "behavior_indicators.json").read_text(encoding="utf-8"))
    else:
        review_dir.mkdir()
        _text(review_dir / "START_HERE.md", "# PUP Review\n\n未请求 PUP review；本目录不包含执行授权。")

    graph = build_persistence_chain_graph(report, matches, behavior)
    diagnostics = build_persistence_link_diagnostics(report, graph=graph)
    plan = build_persistence_governance_plan(graph)
    write_report(destination / "link_diagnostics.json", diagnostics)
    if include_persistence_chain:
        write_report(destination / "persistence_chain.json", graph)
        _text(destination / "persistence_chain.md", render_persistence_chain_markdown(graph))
        write_report(destination / "persistence_governance_plan.json", plan)
        _text(destination / "persistence_governance_plan.md", render_persistence_governance_plan_markdown(plan))

    friendly_source = review_dir / "user_friendly_summary.md"
    if friendly_source.is_file():
        friendly = friendly_source.read_text(encoding="utf-8")
    else:
        friendly = "# 用户摘要\n\n当前报告只提供离线复核线索；无 PUP 命中不代表系统绝对安全。"
    _text(destination / "user_friendly_summary.md", friendly)

    evidence_types = sorted({
        str(record.get("source_type") or record.get("mapping_type") or "unspecified")
        for record in [*primary_records, *cn_records]
        if isinstance(record, dict)
    })
    corroboration = {
        key: review_summary.get(key, 0)
        for key in ("corroborated_match_count", "strong_review_signal_count", "moderate_review_signal_count")
    }
    final = "\n".join([
        "# FINAL EVALUATION — Windows Local", "",
        f"- collectors: success `{stats['collector_success_count']}`, failed/unsupported `{stats['collector_failure_count']}`",
        f"- collector records: `{environment['collector_record_count']}`",
        "- canonical report: `true`",
        f"- redacted values: `{stats['redacted_value_count']}`",
        f"- PUP matches: `{len(matches)}`",
        f"- evidence types: `{', '.join(evidence_types) if evidence_types else 'none supplied'}`",
        f"- behavior corroboration: `{corroboration}`",
        f"- persistence nodes / edges: `{len(graph['nodes'])}` / `{len(graph['edges'])}`",
        f"- strong linked pairs: `{diagnostics['linked_pair_count']}`",
        f"- missing metadata: `{', '.join(graph['missing_metadata']) if graph['missing_metadata'] else 'none'}`",
        f"- governance plan: `{include_persistence_chain}`",
        "- execution_gating_eligible_count: `0`",
        "- execution_authorized: `false`", "",
        "## No-match value", "",
        "No-match 仍有价值：它说明当前 metadata 与 evidence 没有形成复核命中，但不代表系统绝对安全。",
        "0 edge 也是合法保守结果；请查看 link_diagnostics.json 的拒绝原因与建议 metadata。", "",
        "## 安全结论", "",
        "系统修改：未发生。本评估只读取显式 redacted report；未运行 collector、未联网、未上传、未修改注册表、未禁用服务/启动项/任务、未卸载、未永久删除真实文件。",
    ])
    _text(destination / "FINAL_EVALUATION.md", final)
    _text(destination / "START_HERE.md", "\n".join([
        "# Windows Local Evaluation", "",
        "先读 `FINAL_EVALUATION.md` 和 `user_friendly_summary.md`；技术复核再看 persistence 与 link diagnostics。",
        "本入口只消费显式 redacted canonical report，不执行 collector 或系统动作。",
    ]))
    return WindowsLocalEvaluationResult(
        output_dir=str(destination),
        collector_record_count=environment["collector_record_count"],
        pup_match_count=len(matches),
        persistence_node_count=len(graph["nodes"]),
        persistence_edge_count=len(graph["edges"]),
    )
