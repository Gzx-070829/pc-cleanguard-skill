"""Render grouped source provenance for PUP review artifacts."""

from __future__ import annotations


def build_source_trace(
    matches: list[dict], evidence_pack: list[dict], cn_sources: list[dict] | None = None
) -> str:
    if not isinstance(matches, list) or not isinstance(evidence_pack, list):
        raise TypeError("matches and evidence_pack must be lists")
    records = {item.get("record_id"): item for item in evidence_pack if isinstance(item, dict)}
    grouped: dict[str, list[dict]] = {}
    for match in matches:
        grouped.setdefault(str(match.get("matched_record_id", "unknown")), []).append(match)
    lines = [
        "# Source Trace / 来源追溯", "",
        "Microsoft Security Intelligence 的 PUA detection family 是公开安全情报来源，"
        "但 detection family 不等于本机 installed app display name，也不是 PC CleanGuard 的删除授权。",
        "中文 APP/SDK 监管 evidence 保持 mobile/analogical 范围；它不是 Windows 黑名单，也不能跨平台识别本机软件。",
        "",
    ]
    for record_id, group in grouped.items():
        record = records.get(record_id, {})
        first = group[0]
        lines.extend([
            f"## {record_id}", "",
            f"- source_title: {record.get('source_title') or first.get('source_title')}",
            f"- source_url: {record.get('source_url') or first.get('source_url')}",
            f"- source_date: {record.get('source_date') or first.get('source_date')}",
            f"- source_type: {record.get('source_type')}",
            f"- mapping_type: {record.get('mapping_type') or first.get('mapping_type')}",
            f"- entity_scope: {record.get('entity_scope') or first.get('entity_scope')}",
            f"- relation_confidence: {record.get('relation_confidence') or first.get('relation_confidence')}",
            f"- evidence_summary: {record.get('evidence_summary')}",
            f"- matched_targets: {', '.join(str(item.get('target_id')) for item in group)}",
            f"- guard_reason: {'; '.join(first.get('guard_reason', []))}",
            f"- why_not_execution_authorization: {first.get('why_not_execution_authorization')}", "",
        ])
    if not grouped:
        lines.extend(["没有匹配记录；这不构成安全证明。", ""])
    if cn_sources:
        lines.extend([
            "## Chinese public-source matrix / 中文公开来源矩阵", "",
            f"- source_count: {len(cn_sources)}",
            "- matrix_role: candidate/review/explanation routing only",
            "- execution_gating_eligible_count: 0",
            "- note: 网友名单、历史榜和移动端通报不能成为 Windows 删除名单。", "",
        ])
    return "\n".join(lines).rstrip() + "\n"
