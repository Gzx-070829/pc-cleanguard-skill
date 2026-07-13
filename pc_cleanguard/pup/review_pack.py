"""Write a complete offline PUP review folder to one explicit local directory."""

from __future__ import annotations

import json
from pathlib import Path

from ..pipeline.input_loader import _validated_explicit_local_path
from ..reputation import load_evidence_pack, render_human_review_checklist, render_pup_insight_markdown
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
    include_behavior_indicators: bool = False,
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
    intelligence = build_pup_intelligence_report(
        report,
        records,
        include_indicators=True,
        cn_evidence_pack=cn_records,
        include_behavior_indicators=include_behavior_indicators,
    )
    destination.mkdir(parents=True, exist_ok=True)
    summary = {
        key: intelligence[key] for key in (
            "real_source_match_count", "synthetic_match_count", "indicator_match_count",
            "detection_family_match_count", "publisher_hint_match_count",
            "high_uncertainty_match_count", "human_review_required_count",
            "cn_real_source_count", "cn_match_count", "behavior_indicator_count",
            "adversarial_guard_status",
            "execution_gating_eligible_count",
        )
    }
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
    _write_text(destination / "source_trace.md", build_source_trace(intelligence["matches"], [*records, *cn_records]), overwrite)
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
    return {"output_dir": str(destination), "artifact_count": len(ARTIFACT_NAMES), **summary, "execution_authorized": False, "runtime_network_access": False}
