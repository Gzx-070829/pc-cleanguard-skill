"""Write a complete offline PUP review folder to one explicit local directory."""

from __future__ import annotations

import json
from pathlib import Path

from ..pipeline.input_loader import _validated_explicit_local_path
from ..persistence import (
    build_agent_governance_preview,
    build_persistence_chain_graph,
    build_persistence_governance_plan,
    render_persistence_chain_markdown,
    render_persistence_chain_mermaid,
    render_persistence_governance_plan_markdown,
)
from ..reputation import load_evidence_pack, render_human_review_checklist, render_pup_insight_markdown
from ..reputation import (
    build_evidence_coverage_summary,
    render_evidence_coverage_markdown,
    build_false_positive_feedback_template as build_structured_feedback_template,
    render_false_positive_feedback_markdown,
    build_evidence_quality_summary,
    render_evidence_quality_markdown,
    build_cn_source_guard_reason,
    load_cn_candidate_sources,
    load_cn_source_matrix,
    summarize_cn_candidate_sources,
    summarize_cn_source_matrix,
)
from ..reporting import build_user_friendly_pup_report, render_user_friendly_pup_report_markdown
from ..validation.real_report_validation import validate_real_report_shape
from .corroboration import render_corroboration_markdown
from .behavior_indicators import render_behavior_indicator_section
from .feedback_template import build_false_positive_feedback_template
from .intelligence import build_pup_intelligence_report
from .source_trace import build_source_trace


ARTIFACT_NAMES = (
    "START_HERE.md", "user_summary.md", "machine_summary.json", "pup_insight.md",
    "reputation_matches.json", "evidence_indicators.json", "behavior_indicators.json",
    "behavior_indicators.md", "human_review_checklist.md", "source_trace.md",
    "false_positive_feedback.md", "safety_notice.md", "cn_evidence_summary.md",
    "adversarial_safety_summary.md",
)
CN_SOURCE_ARTIFACT_NAMES = (
    "cn_source_matrix.md", "cn_candidate_sources.md", "cn_source_policy_summary.md",
)


def _validated_output_dir(path) -> Path:
    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise ValueError("output_dir must be an explicit local path")
    candidate = Path(path)
    _validated_explicit_local_path(candidate / "machine_summary.json", allowed_suffixes={".json"})
    return candidate


def _write_text(path: Path, content: str, overwrite: bool) -> None:
    with path.open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
        stream.write(content.rstrip() + "\n")


def _write_json(path: Path, content, overwrite: bool) -> None:
    with path.open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
        json.dump(content, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def build_pup_review_pack(
    report: dict,
    evidence_pack,
    output_dir,
    *,
    cn_evidence_pack=None,
    cn_win_evidence_pack=None,
    cn_source_matrix=None,
    cn_candidate_sources=None,
    review_backlog=None,
    include_behavior_indicators: bool = False,
    include_evidence_quality: bool = False,
    include_real_report_validation_summary: bool = False,
    include_corroboration: bool = False,
    include_coverage: bool = False,
    include_user_friendly_report: bool = False,
    include_false_positive_template: bool = False,
    include_persistence_chain: bool = False,
    overwrite: bool = False,
) -> dict:
    if not isinstance(overwrite, bool):
        raise TypeError("overwrite must be bool")
    destination = _validated_output_dir(output_dir)
    if destination.exists() and not overwrite:
        raise FileExistsError(f"review pack output already exists: {destination}")
    if destination.exists() and not destination.is_dir():
        raise ValueError("review pack output must be a directory")
    records = load_evidence_pack(evidence_pack) if isinstance(evidence_pack, (str, Path)) else evidence_pack
    cn_records = (
        load_evidence_pack(cn_evidence_pack)
        if isinstance(cn_evidence_pack, (str, Path))
        else (cn_evidence_pack or [])
    )
    cn_win_records = (
        load_evidence_pack(cn_win_evidence_pack)
        if isinstance(cn_win_evidence_pack, (str, Path))
        else (cn_win_evidence_pack or [])
    )
    cn_sources = (
        load_cn_source_matrix(cn_source_matrix)
        if isinstance(cn_source_matrix, (str, Path))
        else (cn_source_matrix or [])
    )
    if cn_sources and cn_candidate_sources is None and isinstance(cn_source_matrix, (str, Path)):
        sibling = Path(cn_source_matrix).with_name("cn_candidate_sources.zh-CN.json")
        cn_candidate_sources = sibling if sibling.is_file() else []
    coverage_candidates = []
    if isinstance(cn_candidate_sources, (str, Path)):
        raw_candidates = json.loads(Path(cn_candidate_sources).read_text(encoding="utf-8"))
        if raw_candidates and "claimed_software_name" in raw_candidates[0]:
            coverage_candidates, cn_candidates = raw_candidates, []
        else:
            cn_candidates = load_cn_candidate_sources(cn_candidate_sources)
    else:
        cn_candidates = cn_candidate_sources or []
    backlog_records = json.loads(Path(review_backlog).read_text(encoding="utf-8")) if isinstance(review_backlog, (str, Path)) else (review_backlog or [])
    if isinstance(cn_win_evidence_pack, (str, Path)):
        data_dir = Path(cn_win_evidence_pack).parent
        candidate_path = data_dir / "cn_win_pup_evidence_candidates.zh-CN.json"
        backlog_path = data_dir / "cn_win_pup_review_backlog.zh-CN.json"
        if not coverage_candidates and candidate_path.is_file():
            coverage_candidates = json.loads(candidate_path.read_text(encoding="utf-8"))
        if not backlog_records and backlog_path.is_file():
            backlog_records = json.loads(backlog_path.read_text(encoding="utf-8"))
    source_stats = summarize_cn_source_matrix(cn_sources)
    candidate_stats = summarize_cn_candidate_sources(cn_candidates)
    intelligence = build_pup_intelligence_report(
        report,
        records,
        include_indicators=True,
        cn_evidence_pack=cn_records,
        cn_win_evidence_pack=cn_win_records,
        cn_sources=cn_sources,
        cn_candidates=cn_candidates,
        include_behavior_indicators=include_behavior_indicators,
    )
    destination.mkdir(parents=True, exist_ok=True)
    summary = {
        key: intelligence[key] for key in (
            "real_source_match_count", "synthetic_match_count", "indicator_match_count",
            "detection_family_match_count", "publisher_hint_match_count",
            "high_uncertainty_match_count", "human_review_required_count",
            "cn_real_source_count", "cn_match_count", "behavior_indicator_count",
            "cn_win_real_source_count", "cn_win_direct_entity_count",
            "cn_win_installer_artifact_count", "cn_win_match_count",
            "adversarial_guard_status",
            "execution_gating_eligible_count",
        )
    }
    if cn_sources:
        summary.update(source_stats)
        summary.update(candidate_stats)
    corroboration = intelligence.get("corroboration", {})
    quality = build_evidence_quality_summary(
        [[*records, *cn_records, *cn_win_records]], corroboration=corroboration
    )
    validation = validate_real_report_shape(report)
    summary.update({
        "evidence_quality_score": quality["evidence_quality_score"],
        "matchability_score": validation["matchability_score"],
        "high_false_positive_risk_count": quality["high_false_positive_risk_count"],
        "execution_gating_eligible_count": 0,
        "cn_win_approved_count": quality["cn_win_approved_count"],
        "quality_gate_passed": quality["quality_gate_passed"],
        "no_match_value_report_available": True,
    })
    for key in (
        "corroborated_match_count", "strong_review_signal_count",
        "moderate_review_signal_count", "weak_name_only_signal_count",
        "behavior_only_signal_count", "no_corroboration_count",
    ):
        summary[key] = corroboration.get(key, 0)
    coverage = build_evidence_coverage_summary(
        [[*records, *cn_records, *cn_win_records]], coverage_candidates, backlog_records
    )
    summary.update({
        "approved_cn_win_total": coverage["approved_cn_win_total"],
        "candidate_cn_win_total": coverage["candidate_total"],
        "backlog_cn_win_total": coverage["backlog_total"],
        "coverage_score": coverage["coverage_score"],
        "data_gap_count": coverage["data_gap_count"],
        "top_missing_targets": coverage["top_missing_targets"],
        "user_friendly_report_available": include_user_friendly_report,
        "false_positive_feedback_available": include_false_positive_template,
    })
    persistence_graph = None
    persistence_plan = None
    agent_preview = None
    if include_persistence_chain:
        persistence_graph = build_persistence_chain_graph(
            report, intelligence["matches"], intelligence["behavior_indicators"]
        )
        coverage = build_evidence_coverage_summary(
            [[*records, *cn_records, *cn_win_records]], coverage_candidates, backlog_records,
            [persistence_graph],
        )
        persistence_plan = build_persistence_governance_plan(persistence_graph)
        agent_preview = build_agent_governance_preview(
            report, intelligence["matches"], intelligence["behavior_indicators"]
        )
        risk = persistence_graph["risk_summary"]
        summary.update({
            "persistence_node_count": risk["node_count"],
            "persistence_edge_count": risk["edge_count"],
            "persistence_chain_score": risk["persistence_chain_score"],
            "persistence_high_risk_node_count": risk["high_risk_node_count"],
            "persistence_missing_metadata_count": risk["missing_metadata_count"],
            "governance_plan_available": True,
            "blocked_auto_execution_count": persistence_plan["blocked_auto_execution_count"],
            "agent_boundary_status": "L0_REVIEW_ONLY",
            "persistence_chain_coverage": coverage["persistence_chain_coverage"],
            "evidence_to_persistence_match_count": coverage["evidence_to_persistence_match_count"],
            "behavior_to_persistence_match_count": coverage["behavior_to_persistence_match_count"],
            "chain_nodes_without_evidence": coverage["chain_nodes_without_evidence"],
            "evidence_records_without_chain_fixture": coverage["evidence_records_without_chain_fixture"],
            "v04_data_readiness_score": coverage["v04_data_readiness_score"],
        })
        quality.update({
            "persistence_chain_coverage": coverage["persistence_chain_coverage"],
            "evidence_to_persistence_match_count": coverage["evidence_to_persistence_match_count"],
            "behavior_to_persistence_match_count": coverage["behavior_to_persistence_match_count"],
            "chain_nodes_without_evidence": coverage["chain_nodes_without_evidence"],
            "evidence_records_without_chain_fixture": coverage["evidence_records_without_chain_fixture"],
            "v04_data_readiness_score": coverage["v04_data_readiness_score"],
        })
    start_here = "\n".join([
        "# START HERE — PUP Intelligence Review Pack", "",
        "这是本地、离线、带来源追溯的 PUP 线索复核包。它展示命中的 evidence/indicator、匹配原因和误报风险。", "",
        f"本次命中 {len(intelligence['matches'])} 条复核线索，其中 indicator match {intelligence['indicator_match_count']} 条。", "",
        f"中文 evidence：{intelligence['cn_real_source_count']} 条批次级官方来源，命中 {intelligence['cn_match_count']} 条；这些记录不是黑名单。", "",
        f"行为线索：{intelligence['behavior_indicator_count']} 条，仅来自输入 report 元数据并进入人工复核。", "",
        "它不是删除、卸载、禁用或注册表修改授权，因为 detection family/indicator 不能确认本机实体身份与用户意图。", "",
        "请先阅读 human_review_checklist.md 与 source_trace.md，核对安装来源、发布者、签名、用户意图和安全工具独立提示。", "",
        "若认为误报，填写 false_positive_feedback.md；该文件不会自动上传。", "",
        "下一步只能保留、询问用户、核验厂商/安全工具或收集更多证据。明确禁止把本复核包当作系统修改授权。",
    ])
    if cn_win_records:
        start_here += "\n\n" + "\n".join([
            "## 中文 Windows Evidence 状态", "",
            f"- real sources: {summary['cn_win_real_source_count']}",
            f"- direct entity: {summary['cn_win_direct_entity_count']}",
            f"- installer artifact: {summary['cn_win_installer_artifact_count']}",
            "- installer artifact 只描述特定安装器、捆绑器、推广链路或组件，不代表软件本体。",
            "- related publisher 只能形成发布者级提醒；名称碰撞必须降级并显示不确定性。",
            "- 所有线索仍需核对签名、版本、渠道、用户意图并提交误报反馈；可提供去标识化 report。",
            "- 中文 Windows evidence 仍不能授权删除、卸载、禁用或注册表修改。",
        ])
    if cn_sources:
        start_here += "\n\n" + "\n".join([
            "## 中文公开来源矩阵状态", "",
            f"- 已校验公开来源：{source_stats['cn_source_count']}",
            f"- 候选来源：{candidate_stats['cn_candidate_source_count']}",
            "- 网友名单不能直接入库：它只能 candidate-only，并必须有更强第二来源。",
            "- 历史榜不能当现代删除名单：版本、时间和实体关系已经变化。",
            "- 安全厂商公开文章只取公开行为描述，不复制签名、规则库、检测逻辑或样本库。",
            "- 中文证据仍不是删除、卸载、禁用或注册表修改授权。",
        ])
    if include_corroboration:
        start_here += "\n\n" + "\n".join([
            "## 行为佐证状态", "",
            f"- 有行为佐证的 evidence 命中：{summary['corroborated_match_count']}",
            f"- strong / moderate：{summary['strong_review_signal_count']} / {summary['moderate_review_signal_count']}",
            f"- name/publisher/无佐证线索仍需核验：{summary['weak_name_only_signal_count']} / {summary['no_corroboration_count']}",
            "- 请人工核验安装来源、签名、版本、浏览器配置、启动项、计划任务与服务 metadata。",
            "- 行为佐证增强人工复核，不授权删除、卸载、禁用或修改注册表。",
        ])
    if include_user_friendly_report or include_coverage or include_false_positive_template:
        start_here += "\n\n" + "\n".join([
            "## 阅读顺序", "",
            "- 普通用户先读 user_friendly_summary.md。",
            "- 技术用户查看 evidence_coverage.md、corroboration_details.json 与 human_review_checklist.md。",
            "- Agent 使用 machine_summary.json 和结构化 JSON；自然语言解释不能成为执行授权。",
            "- strong/moderate 仍需人工核验；weak/no-match 不能形成结论。",
            "- 误报请填写本地模板；反馈不会自动改库。",
            "- 补充 publisher、签名、版本、路径和行为 metadata 可改善复核质量。",
            "- 本复核包不能触发自动清理。",
        ])
    if include_persistence_chain:
        start_here += "\n\n" + "\n".join([
            "## 持久化链路治理", "",
            "- 软件之所以看起来‘删不干净’，通常是启动项、服务、计划任务、浏览器线索、更新器和残留没有被整体复核。",
            f"- 本报告发现 {summary['persistence_node_count']} 个节点、{summary['persistence_edge_count']} 条关系。",
            "- weak_name_overlap 与 related publisher 只是弱线索，不能形成实体结论。",
            "- 当前只输出图谱和 L0-L5 治理 proposal，不自动断链。",
            "- 用户应核对身份、签名、来源、行为与恢复路径；Agent 只能请求 L0 分析和计划。",
        ])
    user_summary = "\n".join([
        "# PUP 用户摘要", "",
        f"- 真实来源命中：{intelligence['real_source_match_count']}",
        f"- Indicator 命中：{intelligence['indicator_match_count']}",
        f"- 高不确定性命中：{intelligence['high_uncertainty_match_count']}",
        f"- 需要人工复核：{intelligence['human_review_required_count']}",
        f"- 中文 evidence：{intelligence['cn_real_source_count']}",
        f"- 行为线索：{intelligence['behavior_indicator_count']}",
        f"- 对抗守卫：{intelligence['adversarial_guard_status']}",
        "- 执行门控合格：0", "", intelligence["safety_notice"],
    ])
    _write_text(destination / "START_HERE.md", start_here, overwrite)
    _write_text(destination / "user_summary.md", user_summary, overwrite)
    _write_json(destination / "machine_summary.json", {**summary, "blocked_actions": intelligence["blocked_actions"], "execution_authorized": False}, overwrite)
    insight_shape = {
        "summary": intelligence["summary"], "suspicious_behaviors": sorted({category for item in intelligence["matches"] for category in item.get("behavior_categories", ())}),
        "matched_targets": intelligence["matches"], "uncertainty_notes": intelligence["uncertainty_notes"],
        "recommended_review": intelligence["next_steps_for_user"], "blocked_actions": ["automatic_delete", "automatic_uninstall", "automatic_disable", "automatic_registry_edit"],
        "safety_notice": intelligence["safety_notice"], "next_steps_for_user": intelligence["next_steps_for_user"],
        "requires_user_confirmation": True, "execution_authorized": False,
    }
    _write_text(destination / "pup_insight.md", render_pup_insight_markdown(insight_shape), overwrite)
    _write_json(destination / "reputation_matches.json", intelligence["matches"], overwrite)
    _write_json(destination / "evidence_indicators.json", intelligence["evidence_indicators"], overwrite)
    _write_json(destination / "behavior_indicators.json", intelligence["behavior_indicators"], overwrite)
    _write_text(destination / "behavior_indicators.md", render_behavior_indicator_section(intelligence["behavior_indicators"]), overwrite)
    _write_text(destination / "human_review_checklist.md", render_human_review_checklist(intelligence["human_review_checklist"]), overwrite)
    _write_text(destination / "source_trace.md", build_source_trace(intelligence["matches"], [*records, *cn_records, *cn_win_records], cn_sources), overwrite)
    _write_text(destination / "false_positive_feedback.md", build_false_positive_feedback_template(intelligence["matches"]), overwrite)
    _write_text(destination / "safety_notice.md", f"# Safety Notice\n\n{intelligence['safety_notice']}", overwrite)
    cn_lines = [
        "# 中文 Evidence 摘要", "",
        "中文 PUP evidence 不是黑名单，只能解释、排序和支持人工复核。批次级移动端来源不能映射为 Windows 软件。", "",
        f"- checked-in CN real-source records: {len(cn_records)}",
        f"- local report matches: {intelligence['cn_match_count']}",
        "- execution_gating_eligible_count: 0", "",
    ]
    for record in cn_records:
        cn_lines.extend([
            f"- [{record.get('source_title')}]({record.get('source_url')}) — {record.get('source_date')} / `{record.get('mapping_type')}` / `{record.get('entity_scope')}`"
        ])
    _write_text(destination / "cn_evidence_summary.md", "\n".join(cn_lines), overwrite)
    guard_lines = [
        "# Adversarial Safety Summary", "",
        f"- adversarial_guard_status: {intelligence['adversarial_guard_status']}",
        "- execution_gating_eligible_count: 0",
        "- strong real evidence remains explanation/review only",
        *[f"- blocked: {action}" for action in intelligence["blocked_actions"]],
        "", "即使来源真实、实体直接、关系置信度高，也不能成为系统动作授权。",
    ]
    _write_text(destination / "adversarial_safety_summary.md", "\n".join(guard_lines), overwrite)
    extra_artifacts = 0
    if cn_win_records:
        cn_win_lines = [
            "# 中文 Windows Evidence 摘要", "",
            "这些记录是少量人工核验的公开行为 evidence，不是黑名单。installer artifact 不代表软件本体。", "",
            f"- real_source_count: `{summary['cn_win_real_source_count']}`",
            f"- direct_entity_count: `{summary['cn_win_direct_entity_count']}`",
            f"- installer_artifact_count: `{summary['cn_win_installer_artifact_count']}`",
            f"- local_match_count: `{summary['cn_win_match_count']}`",
            "- execution_gating_eligible_count: `0`", "",
        ]
        for record in cn_win_records:
            cn_win_lines.extend([
                f"## {record['software_name']}", "",
                f"- mapping_type: `{record['mapping_type']}`",
                f"- source: [{record['source_title']}]({record['source_url']}) / {record['source_date']}",
                f"- scope: {record.get('version_or_time_scope')}",
                f"- guard: {record.get('guard_reason')}", "",
            ])
        _write_text(destination / "cn_win_evidence_summary.md", "\n".join(cn_win_lines), overwrite)
        extra_artifacts += 1
    if include_evidence_quality:
        _write_text(destination / "evidence_quality.md", render_evidence_quality_markdown(quality), overwrite)
        extra_artifacts += 1
    if include_real_report_validation_summary:
        _write_text(destination / "matchability_summary.md", "\n".join([
            "# Real Report Matchability Summary", "",
            "该摘要仅检查显式输入 report 的结构，不联网、不上传、不读取额外文件。", "",
            f"- matchability_score: `{validation['matchability_score']}`",
            f"- metadata_entry_count: `{validation['metadata_entry_count']}`",
            f"- behavior_metadata_entry_count: `{validation['behavior_metadata_entry_count']}`",
            f"- pii_hint_count: `{validation['pii_hint_count']}`",
        ]), overwrite)
        extra_artifacts += 1
    if include_corroboration:
        _write_text(destination / "corroboration_summary.md", render_corroboration_markdown(corroboration), overwrite)
        _write_json(destination / "corroboration_details.json", corroboration, overwrite)
        _write_text(destination / "cn_win_evidence_quality.md", render_evidence_quality_markdown(quality), overwrite)
        match_summary = (
            f"# Match Summary\n\n发现 `{len(intelligence['matches'])}` 条复核线索；"
            "命中与佐证均不是执行授权。"
            if intelligence["matches"] else
            "# No-match Summary\n\nNo-match 不等于系统干净；只表示当前 evidence 与 metadata 未产生复核线索。"
        )
        _write_text(destination / "match_or_no_match_summary.md", match_summary, overwrite)
        extra_artifacts += 4
    if include_coverage:
        _write_text(destination / "evidence_coverage.md", render_evidence_coverage_markdown(coverage), overwrite)
        _write_text(destination / "data_gap_summary.md", "# Data Gap Summary\n\n" + "\n".join(f"- {item}" for item in coverage["top_missing_targets"]), overwrite)
        extra_artifacts += 2
    if include_user_friendly_report:
        friendly = build_user_friendly_pup_report(summary)
        _write_text(destination / "user_friendly_summary.md", render_user_friendly_pup_report_markdown(friendly), overwrite)
        extra_artifacts += 1
    if include_persistence_chain:
        _write_text(destination / "persistence_chain.md", render_persistence_chain_markdown(persistence_graph), overwrite)
        _write_json(destination / "persistence_chain.json", persistence_graph, overwrite)
        _write_text(destination / "persistence_chain_mermaid.md", render_persistence_chain_mermaid(persistence_graph), overwrite)
        _write_text(destination / "persistence_governance_plan.md", render_persistence_governance_plan_markdown(persistence_plan), overwrite)
        _write_json(destination / "persistence_governance_plan.json", persistence_plan, overwrite)
        _write_json(destination / "agent_governance_preview.json", agent_preview, overwrite)
        extra_artifacts += 6
    if include_false_positive_template:
        structured_feedback = build_structured_feedback_template(
            intelligence["matches"][0] if intelligence["matches"] else {}, {}
        )
        _write_json(destination / "false_positive_feedback_template.json", structured_feedback, overwrite)
        _write_text(destination / "false_positive_feedback_template.md", render_false_positive_feedback_markdown(structured_feedback), overwrite)
        extra_artifacts += 2
    if cn_sources:
        source_lines = [
            "# 中文公开来源矩阵", "",
            "这是一张来源准入矩阵，不是黑名单，也不提供执行授权。", "",
        ]
        for source in cn_sources:
            source_lines.extend([
                f"## {source['source_title']}", "",
                f"- source_class: `{source['source_class']}`",
                f"- source_url: {source['source_url']}",
                f"- platform_scope: `{source['platform_scope']}`",
                f"- allowed_use: `{source['allowed_use']}`",
                f"- requires_second_source: `{str(source['requires_second_source']).lower()}`",
                *[f"- guard: {reason}" for reason in build_cn_source_guard_reason(source)], "",
            ])
        candidate_lines = [
            "# 中文候选来源", "",
            "候选池只帮助人工复核；所有项目 execution_authorized=false。", "",
        ]
        for candidate in cn_candidates:
            candidate_lines.extend([
                f"## {candidate['candidate_entity']}", "",
                f"- status: `{candidate['candidate_status']}`",
                f"- source: [{candidate['source_title']}]({candidate['source_url']})",
                f"- summary: {candidate['evidence_summary']}",
                "- execution_authorized: `false`", "",
            ])
        policy_lines = [
            "# 中文来源准入策略摘要", "",
            f"- source_count: {source_stats['cn_source_count']}",
            f"- candidate_source_count: {candidate_stats['cn_candidate_source_count']}",
            f"- candidate_only_count: {candidate_stats['cn_candidate_only_count']}",
            f"- requires_second_source_count: {source_stats['cn_requires_second_source_count']}",
            "- execution_gating_eligible_count: 0", "",
            "网友名单、历史榜、单篇媒体报道和移动端类比不能直接进入 Windows 执行链。",
        ]
        _write_text(destination / "cn_source_matrix.md", "\n".join(source_lines), overwrite)
        _write_text(destination / "cn_candidate_sources.md", "\n".join(candidate_lines), overwrite)
        _write_text(destination / "cn_source_policy_summary.md", "\n".join(policy_lines), overwrite)
    artifact_count = len(ARTIFACT_NAMES) + (len(CN_SOURCE_ARTIFACT_NAMES) if cn_sources else 0) + extra_artifacts
    return {"output_dir": str(destination), "artifact_count": artifact_count, **summary, "execution_authorized": False, "runtime_network_access": False}
