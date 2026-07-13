"""Explain review priority without producing an execution verdict."""

def score_persistence_chain(graph: dict) -> dict:
    nodes, edges = graph.get("nodes", ()), graph.get("edges", ())
    high_types = {"service", "scheduled_task", "registry_run_key", "registry_browser_helper", "browser_homepage", "browser_search"}
    high = sum(item.get("node_type") in high_types for item in nodes)
    strong = sum(item.get("confidence") == "strong" for item in edges)
    score = min(100, len(nodes) * 3 + len(edges) * 6 + strong * 5 + high * 4)
    return {
        "persistence_chain_score": score, "node_count": len(nodes), "edge_count": len(edges),
        "high_risk_node_count": high, "missing_metadata_count": len(graph.get("missing_metadata", ())),
        "review_signal": "strong_review_signal" if strong >= 3 else "moderate_review_signal" if strong else "weak_or_no_chain_signal",
        "execution_gating_eligible_count": 0, "execution_authorized": False,
    }
