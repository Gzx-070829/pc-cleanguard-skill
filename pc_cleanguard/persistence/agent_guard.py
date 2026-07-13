"""Fail-closed guard for external Agent requests."""

from __future__ import annotations
import json

FORBIDDEN_ACTION_TERMS = (
    "delete", "remove", "uninstall", "disable", "mutation",
    "删除", "移除", "卸载", "禁用", "变更",
)
MUTATION_TERMS = (
    "edit", "modify", "change", "write", "start", "stop", "enable", "register",
    "修改", "写入", "启动", "停止", "启用", "注册",
)
SENSITIVE_OBJECT_TERMS = (
    "registry", "service", "scheduled task", "task", "browser homepage", "browser search",
    "注册表", "服务", "计划任务", "浏览器主页", "浏览器搜索",
)
ALLOWED_L0_TERMS = ("analyze", "analyse", "explain", "review", "graph", "plan", "preview", "inspect", "分析", "解释", "复核", "图谱", "计划", "预览")


def validate_agent_execution_request(request: dict) -> dict:
    if not isinstance(request, dict): raise TypeError("request must be a dict")
    text = json.dumps(request, ensure_ascii=False).lower()
    forbidden = {term for term in FORBIDDEN_ACTION_TERMS if term in text}
    mutation_terms = {term for term in MUTATION_TERMS if term in text}
    sensitive_objects = {term for term in SENSITIVE_OBJECT_TERMS if term in text}
    if mutation_terms and sensitive_objects:
        forbidden.update(mutation_terms)
        forbidden.update(sensitive_objects)
    forbidden = sorted(forbidden)
    allowed = not forbidden and any(term in text for term in ALLOWED_L0_TERMS)
    return {
        "status": "allowed_l0" if allowed else "blocked", "allowed": allowed,
        "maximum_allowed_level": "L0", "blocked_terms": forbidden,
        "reason": "L0 analysis/plan request accepted" if allowed else "fail-closed: request is unknown or asks for a persistence/system mutation",
        "agent_reason_is_execution_authorization": False, "execution_gating_eligible_count": 0,
        "execution_authorized": False, "runtime_network_access": False,
    }


def build_agent_governance_preview(report: dict, evidence_matches=None, behavior_indicators=None) -> dict:
    from .graph import build_persistence_chain_graph
    from .governance_plan import build_persistence_governance_plan
    graph = build_persistence_chain_graph(report, evidence_matches, behavior_indicators)
    plan = build_persistence_governance_plan(graph)
    return {"graph_summary": graph["risk_summary"], "governance_plan": plan, "agent_boundary_status": "L0_REVIEW_ONLY", "allowed_agent_actions": ["build graph", "explain chain", "build governance proposal"], "blocked_agent_actions": ["delete", "uninstall", "disable", "registry/service/task/browser mutation"], "execution_gating_eligible_count": 0, "execution_authorized": False, "runtime_network_access": False}
