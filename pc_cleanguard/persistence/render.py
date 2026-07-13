"""Render review-only persistence artifacts."""

from __future__ import annotations
import re


def render_persistence_chain_markdown(graph: dict) -> str:
    risk = graph.get("risk_summary", {})
    lines = ["# 持久化链路治理 / Persistence Chain Governance", "", "本图谱是 L0 review-only 解释，不是删除、卸载、禁用或注册表修改计划。", "", f"- nodes: `{len(graph.get('nodes', ()))}`", f"- edges: `{len(graph.get('edges', ()))}`", f"- persistence_chain_score: `{risk.get('persistence_chain_score', 0)}`", f"- review_signal: `{risk.get('review_signal', 'unknown')}`", "- execution_gating_eligible_count: `0`", "", "## Nodes", ""]
    lines.extend(f"- `{n['node_type']}` **{n['label']}** (`{n['node_id']}`)" for n in graph.get("nodes", ()))
    lines.extend(["", "## Relations", ""])
    lines.extend(f"- `{e['source']}` → `{e['target']}`: `{e['edge_type']}` / `{e['confidence']}` — {e['reason']}" for e in graph.get("edges", ()))
    lines.extend(["", "## Uncertainty", "", *[f"- {n}" for n in graph.get("uncertainty_notes", ())], "", graph.get("why_not_execution_authorization", "")])
    return "\n".join(lines).rstrip() + "\n"


def render_persistence_chain_mermaid(graph: dict) -> str:
    def ident(value): return "n_" + re.sub(r"[^a-zA-Z0-9_]", "_", value)
    def label(value): return str(value).replace('"', "'").replace("\n", " ")[:80]
    lines = ["```mermaid", "flowchart LR", "  safety[\"review-only / no execution authorization\"]"]
    for node in graph.get("nodes", ()): lines.append(f"  {ident(node['node_id'])}[\"{label(node['label'])} ({node['node_type']})\"]")
    for edge in graph.get("edges", ()): lines.append(f"  {ident(edge['source'])} -->|{edge['edge_type']}| {ident(edge['target'])}")
    lines.extend(["  safety -.-> safety", "```", ""])
    return "\n".join(lines)
