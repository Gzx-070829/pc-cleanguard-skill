"""Link only metadata already present in an explicit report."""

from __future__ import annotations
import hashlib
import re

from .models import validate_edge, validate_node

COLLECTIONS = {
    "installed_apps": ("software", ("display_name", "name"), ("install_location", "path")),
    "installers": ("installer", ("display_name", "name"), ("path", "command")),
    "startup_items": ("startup_item", ("name", "display_name"), ("command", "path")),
    "services": ("service", ("display_name", "name"), ("path_name", "command")),
    "scheduled_tasks": ("scheduled_task", ("task_name", "name"), ("actions_summary", "command")),
    "browser_settings": ("unknown_component", ("name", "type", "value"), ("value", "path")),
    "registry_clues": ("unknown_component", ("name", "type", "value"), ("value", "path")),
    "updaters": ("updater", ("name", "display_name"), ("path", "command")),
    "promo_components": ("promo_component", ("name", "display_name"), ("path", "command")),
    "leftovers": ("leftover_file", ("name", "path", "type"), ("path",)),
    "temp_artifacts": ("temp_artifact", ("name", "path"), ("path",)),
}


def _first(item, keys, default="unknown"):
    return next((str(item[key]) for key in keys if str(item.get(key, "")).strip()), default)


def _normalized(value):
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(value).lower())


def _identifier(prefix, value, index):
    supplied = str(value.get("target_id") or value.get("node_id") or "").strip()
    if supplied: return supplied
    digest = hashlib.sha256(f"{prefix}|{index}|{value}".encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{digest}"


def _edge(source, target, edge_type, confidence, reason, index):
    return validate_edge({
        "edge_id": f"edge:{index}:{source['node_id']}:{target['node_id']}",
        "source": source["node_id"], "target": target["node_id"],
        "edge_type": edge_type, "confidence": confidence, "reason": reason,
        "requires_human_review": True, "execution_authorized": False,
    })


def link_persistence_nodes(report_targets: dict) -> dict:
    if not isinstance(report_targets, dict): raise TypeError("report_targets must be a dict")
    nodes, sources = [], []
    for collection, (default_type, label_keys, path_keys) in COLLECTIONS.items():
        for index, item in enumerate(report_targets.get(collection, ()) or ()):
            if not isinstance(item, dict): continue
            node_type = str(item.get("type", default_type))
            if collection == "browser_settings" and node_type not in {"browser_homepage", "browser_search", "browser_extension"}: node_type = "unknown_component"
            if collection == "registry_clues" and node_type not in {"registry_run_key", "registry_uninstall_key", "registry_browser_helper"}: node_type = "unknown_component"
            if collection == "leftovers" and node_type not in {"leftover_file", "leftover_directory"}: node_type = "leftover_file"
            label = _first(item, label_keys)
            node = validate_node({
                "node_id": _identifier(node_type, item, index), "node_type": node_type,
                "label": label, "metadata": dict(item), "risk_level": "review",
                "requires_human_review": True, "execution_authorized": False,
            })
            nodes.append(node)
            sources.append((collection, node, _first(item, path_keys, "")))
    edges = []
    software = [(c, n, p) for c, n, p in sources if n["node_type"] == "software"]
    for left_index, (_, left, _) in enumerate(software):
        left_publisher = _normalized(left["metadata"].get("publisher", ""))
        for _, right, _ in software[left_index + 1:]:
            if left_publisher and left_publisher == _normalized(right["metadata"].get("publisher", "")):
                edges.append(_edge(left, right, "related_to_publisher", "weak", "same publisher is only a review clue", len(edges)))
    relation = {"startup_item": "persists_via", "service": "registers_service", "scheduled_task": "schedules", "browser_homepage": "modifies_browser", "browser_search": "modifies_browser", "browser_extension": "modifies_browser", "registry_run_key": "persists_via", "registry_uninstall_key": "persists_via", "registry_browser_helper": "persists_via", "updater": "updates", "promo_component": "promotes", "leftover_file": "leaves_artifact", "leftover_directory": "leaves_artifact", "installer": "installed_by"}
    for _, app, app_path in software:
        app_name = _normalized(app["label"])
        app_path_norm = _normalized(app_path)
        for _, other, other_path in sources:
            if other is app or other["node_type"] == "software": continue
            other_text = _normalized(f"{other['label']} {other_path}")
            if app_path_norm and len(app_path_norm) >= 5 and app_path_norm in other_text:
                edges.append(_edge(app, other, relation.get(other["node_type"], "requires_human_review"), "strong", "explicit report path proximity", len(edges)))
            elif app_name and len(app_name) >= 4 and app_name in other_text:
                edges.append(_edge(app, other, "weak_name_overlap", "weak", "normalized name overlap requires identity review", len(edges)))
    return {"nodes": nodes, "edges": edges, "missing_metadata": _missing_metadata(report_targets), "runtime_registry_read": False, "runtime_browser_scan": False}


def _missing_metadata(report):
    missing = []
    for field in ("installed_apps", "startup_items", "services", "scheduled_tasks", "browser_settings", "registry_clues", "leftovers"):
        if field not in report: missing.append(field)
    return missing
