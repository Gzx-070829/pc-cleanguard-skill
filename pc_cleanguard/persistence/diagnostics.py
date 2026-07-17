"""Explain accepted and rejected persistence link candidates without weakening links."""

from __future__ import annotations

import re

from .linker import link_persistence_nodes


def _normalized(value) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(value or "").casefold())


def _path(item: dict, *keys: str) -> str:
    return next((str(item[key]) for key in keys if str(item.get(key, "")).strip()), "")


def build_persistence_link_diagnostics(report: dict, *, graph: dict | None = None) -> dict:
    """Describe why structural pairs linked or remained separate."""

    if not isinstance(report, dict):
        raise TypeError("report must be a dict")
    linked = link_persistence_nodes(report)
    graph_edges = list((graph or {}).get("edges", linked["edges"]))
    nodes = list((graph or {}).get("nodes", linked["nodes"]))
    by_id = {node["node_id"]: node for node in nodes if isinstance(node, dict) and node.get("node_id")}
    software = [node for node in nodes if node.get("node_type") == "software"]
    nonsoftware = [node for node in nodes if node.get("node_type") != "software" and not str(node.get("node_id", "")).startswith(("evidence:", "behavior:"))]
    candidate_pair_count = len(software) * len(nonsoftware) + (len(software) * (len(software) - 1) // 2)

    strong_edges = [
        edge for edge in graph_edges
        if edge.get("confidence") == "strong"
        and edge.get("source") in by_id and edge.get("target") in by_id
    ]
    linked_pairs = {(edge["source"], edge["target"]) for edge in strong_edges}
    counters = {
        "linked_by_exact_path": 0,
        "linked_by_executable_root": 0,
        "linked_by_command_path": 0,
        "linked_by_alias": 0,
        "linked_by_publisher": 0,
    }
    for edge in strong_edges:
        left = by_id[edge["source"]]
        right = by_id[edge["target"]]
        left_meta, right_meta = left.get("metadata", {}), right.get("metadata", {})
        app_path = _normalized(_path(left_meta, "install_location", "path"))
        other_path = _normalized(_path(right_meta, "command", "actions_summary", "path_name", "path", "file_path"))
        if edge.get("edge_type") == "name_alias":
            counters["linked_by_alias"] += 1
        elif app_path and other_path and app_path == other_path:
            counters["linked_by_exact_path"] += 1
        elif right.get("node_type") in {"startup_item", "scheduled_task"}:
            counters["linked_by_command_path"] += 1
        else:
            counters["linked_by_executable_root"] += 1

    rejected_publisher_only = 0
    for index, left in enumerate(software):
        publisher = _normalized(left.get("metadata", {}).get("publisher"))
        if not publisher:
            continue
        for right in software[index + 1:]:
            if publisher == _normalized(right.get("metadata", {}).get("publisher")):
                rejected_publisher_only += 1
    rejected_weak_name = sum(edge.get("edge_type") == "weak_name_overlap" for edge in graph_edges)
    rejected_missing_metadata = 0
    for app in software:
        app_meta = app.get("metadata", {})
        app_path = _path(app_meta, "install_location", "path")
        for other in nonsoftware:
            other_meta = other.get("metadata", {})
            other_path = _path(other_meta, "command", "actions_summary", "path_name", "path", "file_path")
            if not app_path or not other_path:
                rejected_missing_metadata += 1
    linked_node_ids = {node_id for pair in linked_pairs for node_id in pair}
    unlinked_nodes = [
        {"node_id": node["node_id"], "node_type": node["node_type"], "label": node["label"]}
        for node in nodes
        if node.get("node_id") not in linked_node_ids
        and not str(node.get("node_id", "")).startswith(("evidence:", "behavior:"))
    ]
    recommendations = []
    if any(not _path(node.get("metadata", {}), "install_location", "path") for node in software):
        recommendations.append("executable_path")
    if any(not _path(node.get("metadata", {}), "command", "actions_summary", "path_name", "path", "file_path") for node in nonsoftware):
        recommendations.append("startup_service_task_command_path")
    recommendations.extend(("publisher_signature", "package_or_product_identity"))
    recommendations = list(dict.fromkeys(recommendations))
    linked_pair_count = len(linked_pairs)
    return {
        "candidate_pair_count": candidate_pair_count,
        "linked_pair_count": linked_pair_count,
        "rejected_pair_count": max(0, candidate_pair_count - linked_pair_count),
        **counters,
        "rejected_publisher_only": rejected_publisher_only,
        "rejected_weak_name": rejected_weak_name,
        "rejected_missing_metadata": rejected_missing_metadata,
        "unlinked_nodes": unlinked_nodes,
        "recommended_metadata": recommendations,
        "zero_edge_explanation": (
            "No strong structural path relation was present; zero edges is a valid conservative result."
            if linked_pair_count == 0 else ""
        ),
        "threshold_lowered": False,
        "execution_gating_eligible_count": 0,
        "execution_authorized": False,
    }
