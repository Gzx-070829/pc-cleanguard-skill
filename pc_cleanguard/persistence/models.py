"""Validated, non-authorizing persistence graph primitives."""

from __future__ import annotations

NODE_TYPES = frozenset({
    "software", "installer", "startup_item", "service", "scheduled_task",
    "browser_homepage", "browser_search", "browser_extension",
    "registry_run_key", "registry_uninstall_key", "registry_browser_helper",
    "updater", "promo_component", "leftover_file", "leftover_directory",
    "temp_artifact", "unknown_component",
})
EDGE_TYPES = frozenset({
    "installed_by", "launches", "persists_via", "schedules", "registers_service",
    "modifies_browser", "leaves_artifact", "updates", "promotes",
    "related_to_publisher", "name_alias", "weak_name_overlap", "evidence_match",
    "behavior_corroborates", "requires_human_review",
})


def validate_node(node: dict) -> dict:
    if not isinstance(node, dict):
        raise TypeError("node must be a dict")
    if node.get("node_type") not in NODE_TYPES:
        raise ValueError("unsupported persistence node type")
    if not str(node.get("node_id", "")).strip() or not str(node.get("label", "")).strip():
        raise ValueError("node_id and label are required")
    if node.get("execution_authorized") is not False:
        raise ValueError("persistence nodes must be non-authorizing")
    result = dict(node)
    result.setdefault("metadata", {})
    result.setdefault("risk_level", "review")
    result.setdefault("requires_human_review", True)
    result["execution_gating_eligible"] = False
    return result

def validate_edge(edge: dict) -> dict:
    if not isinstance(edge, dict):
        raise TypeError("edge must be a dict")
    if edge.get("edge_type") not in EDGE_TYPES:
        raise ValueError("unsupported persistence edge type")
    if not all(str(edge.get(key, "")).strip() for key in ("edge_id", "source", "target", "reason")):
        raise ValueError("edge identity, endpoints, and reason are required")
    if edge.get("execution_authorized") is not False:
        raise ValueError("persistence edges must be non-authorizing")
    result = dict(edge)
    result.setdefault("confidence", "weak")
    result.setdefault("requires_human_review", True)
    result["execution_gating_eligible"] = False
    return result
