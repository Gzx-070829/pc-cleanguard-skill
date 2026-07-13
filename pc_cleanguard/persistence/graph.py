"""Build a deterministic L0 persistence chain graph from caller data."""

from __future__ import annotations
from datetime import datetime, timezone
import hashlib

from .linker import link_persistence_nodes
from .models import validate_edge, validate_node
from .risk import score_persistence_chain


def _now(): return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_persistence_chain_graph(report: dict, evidence_matches=None, behavior_indicators=None) -> dict:
    if not isinstance(report, dict): raise TypeError("report must be a dict")
    evidence_matches = list(evidence_matches or ())
    behavior_indicators = list(behavior_indicators or ())
    linked = link_persistence_nodes(report)
    nodes, edges = list(linked["nodes"]), list(linked["edges"])
    known = {item["node_id"] for item in nodes}
    for index, match in enumerate(evidence_matches):
        target = str(match.get("target_id", "unknown"))
        if target not in known: continue
        evidence_id = f"evidence:{match.get('matched_record_id', index)}"
        nodes.append(validate_node({"node_id": evidence_id, "node_type": "unknown_component", "label": str(match.get("source_title") or match.get("matched_record_id") or "Evidence"), "metadata": dict(match), "risk_level": "review", "requires_human_review": True, "execution_authorized": False}))
        mapping = match.get("mapping_type")
        edge_type = "weak_name_overlap" if mapping in {"related_publisher", "name_collision_candidate"} else "evidence_match"
        edges.append(validate_edge({"edge_id": f"evidence-edge:{index}", "source": evidence_id, "target": target, "edge_type": edge_type, "confidence": "weak" if edge_type == "weak_name_overlap" else "review", "reason": "evidence metadata supports review only", "requires_human_review": True, "execution_authorized": False}))
    for index, indicator in enumerate(behavior_indicators):
        target = str(indicator.get("target_id", "unknown"))
        if target not in known: continue
        behavior_id = f"behavior:{index}:{target}"
        nodes.append(validate_node({"node_id": behavior_id, "node_type": "unknown_component", "label": str(indicator.get("behavior_type", "behavior clue")), "metadata": dict(indicator), "risk_level": "review", "requires_human_review": True, "execution_authorized": False}))
        edges.append(validate_edge({"edge_id": f"behavior-edge:{index}", "source": behavior_id, "target": target, "edge_type": "behavior_corroborates", "confidence": "review", "reason": "caller-supplied behavior metadata corroborates review only", "requires_human_review": True, "execution_authorized": False}))
    source_report_id = str(report.get("report_id") or report.get("scan_id") or "explicit-report")
    graph_id = "pcg:" + hashlib.sha256(source_report_id.encode("utf-8")).hexdigest()[:16]
    graph = {
        "schema_version": "0.4.0", "graph_id": graph_id, "source_report_id": source_report_id,
        "nodes": nodes, "edges": edges, "evidence_matches": evidence_matches,
        "behavior_indicators": behavior_indicators, "corroboration_summary": _corroboration(edges),
        "missing_metadata": linked["missing_metadata"], "uncertainty_notes": _uncertainty(linked, evidence_matches),
        "why_not_execution_authorization": "Persistence graph relations explain review clues; they do not prove user intent or authorize system mutation.",
        "generated_at": _now(), "execution_gating_eligible_count": 0, "execution_authorized": False,
        "runtime_registry_read": False, "runtime_browser_scan": False, "runtime_network_access": False,
    }
    graph["risk_summary"] = score_persistence_chain(graph)
    return graph


def _corroboration(edges):
    return {"evidence_to_persistence_match_count": sum(e["edge_type"] == "evidence_match" for e in edges), "behavior_to_persistence_match_count": sum(e["edge_type"] == "behavior_corroborates" for e in edges), "execution_gating_eligible_count": 0}


def _uncertainty(linked, matches):
    notes = [f"missing report metadata: {field}" for field in linked["missing_metadata"]]
    if not linked["edges"]: notes.append("No strong persistence relation was found in current report metadata.")
    if not matches: notes.append("No evidence match was supplied; no-match does not mean the system is clean.")
    return notes
