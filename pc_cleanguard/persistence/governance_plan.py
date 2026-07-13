"""Build proposal-only governance plans; never execute them."""

from __future__ import annotations
from datetime import datetime, timezone
import hashlib

from .checklist import build_persistence_review_checklist
from .levels import GOVERNANCE_LEVELS


def build_persistence_governance_plan(graph: dict) -> dict:
    if not isinstance(graph, dict): raise TypeError("graph must be a dict")
    graph_id = str(graph.get("graph_id", "unknown"))
    levels = [{"level": level, "description": description, "execution_authorized": False} for level, description in GOVERNANCE_LEVELS.items()]
    proposed = [{"step_id": "review-chain", "level": "L0", "action": "review persistence graph and evidence", "proposal_only": True, "execution_authorized": False}]
    node_types = {n.get("node_type") for n in graph.get("nodes", ())}
    if node_types & {"leftover_file", "leftover_directory"}: proposed.append({"step_id": "quarantine-proposal", "level": "L2", "action": "prepare reversible quarantine proposal", "proposal_only": True, "execution_authorized": False})
    if "software" in node_types: proposed.append({"step_id": "uninstaller-proposal", "level": "L3", "action": "ask user to inspect an official uninstaller", "proposal_only": True, "execution_authorized": False})
    if node_types & {"service", "scheduled_task", "registry_run_key", "registry_browser_helper", "browser_homepage", "browser_search", "browser_extension"}: proposed.append({"step_id": "system-governance-proposal", "level": "L4", "action": "draft backup-first system governance review", "proposal_only": True, "execution_authorized": False})
    blocked = [
        {"level": "L5", "action": action, "reason": "automatic persistence mutation is forbidden", "execution_authorized": False}
        for action in ("PUP evidence triggered delete", "AI language triggered uninstall", "silent disable", "registry change without backup")
    ]
    return {
        "schema_version": "0.4.0", "plan_id": "plan:" + hashlib.sha256(graph_id.encode()).hexdigest()[:16], "graph_id": graph_id,
        "levels": levels, "proposed_steps": proposed, "blocked_steps": blocked,
        "required_backups": ["future L2-L4 proposals require a verified restore path", "registry/service/task/browser proposals require backup design"],
        "required_user_confirmations": ["explicit scope confirmation", "strong confirmation for every future reversible or high-risk action"],
        "rollback_requirements": ["record original state", "verify restore before any future mutation"],
        "audit_requirements": ["record evidence, level, confirmation, proposed action, and outcome"],
        "human_review_checklist": build_persistence_review_checklist(graph),
        "why_not_auto_execute": "Graph relations and AI explanations are review evidence, not execution authorization; this version does not execute persistence changes.",
        "agent_execution_boundary": "L0_REVIEW_ONLY", "blocked_auto_execution_count": len(blocked),
        "execution_gating_eligible_count": 0, "execution_authorized": False,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def render_persistence_governance_plan_markdown(plan: dict) -> str:
    lines = ["# 持久化链路治理计划 / Governance Plan", "", "这是分级治理 proposal，不自动执行，不是卸载、禁用或注册表修改命令。", "", "## L0-L5", ""]
    lines.extend(f"- **{x['level']}** — {x['description']}" for x in plan.get("levels", ()))
    lines.extend(["", "## Proposed review steps", ""])
    lines.extend(f"- `{x['level']}` {x['action']} (proposal-only)" for x in plan.get("proposed_steps", ()))
    lines.extend(["", "## Blocked automatic steps", ""])
    lines.extend(f"- `{x['action']}` — {x['reason']}" for x in plan.get("blocked_steps", ()))
    lines.extend(["", "- execution_gating_eligible_count: `0`", "", plan.get("why_not_auto_execute", "")])
    return "\n".join(lines).rstrip() + "\n"
