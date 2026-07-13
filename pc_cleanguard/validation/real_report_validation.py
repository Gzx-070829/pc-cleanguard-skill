"""Validate whether one caller-supplied report is useful for offline PUP review."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..pipeline.input_loader import _validated_explicit_local_path


GROUPS = ("installed_apps", "startup_items", "services", "scheduled_tasks")
METADATA_FIELDS = {"publisher", "Publisher", "display_name", "DisplayName", "software_name", "name", "path", "install_location", "InstallLocation", "path_name", "command", "task_name"}
BEHAVIOR_FIELDS = {"behavior_metadata", "actions_summary", "triggers_summary"}


def _walk(value, prefix="report"):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, f"{prefix}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{prefix}[{index}]")
    elif isinstance(value, str):
        yield prefix, value


def validate_real_report_shape(report: dict) -> dict:
    if not isinstance(report, dict):
        raise TypeError("report must be a dict")
    groups_present = {name: isinstance(report.get(name), list) and bool(report.get(name)) for name in GROUPS}
    entries = [item for name in GROUPS for item in report.get(name, ()) if isinstance(item, dict)]
    metadata_count = sum(any(field in item and item[field] not in (None, "") for field in METADATA_FIELDS) for item in entries)
    behavior_count = sum(any(field in item and item[field] not in (None, "", []) for field in BEHAVIOR_FIELDS) for item in entries)
    pii_hints = []
    patterns = (re.compile(r"(?i)[a-z]:[/\\]users[/\\][^/\\]+"), re.compile(r"(?i)\\\\[^\\]+\\"))
    for location, value in _walk(report):
        if any(pattern.search(value) for pattern in patterns) or any(term in location.casefold() for term in ("username", "device_name", "hostname")):
            pii_hints.append({"field": location, "reason": "可能包含用户名、设备名或用户路径；分享前请去标识化。"})
    supported = set(GROUPS) | {"targets", "scan_id", "normalized_counts", "decisions", "report", "fixture_metadata", "fixture_notice", "synthetic_but_realistic"}
    unsupported = sorted(set(report) - supported)
    group_score = sum(groups_present.values()) / len(GROUPS)
    metadata_score = min(1.0, metadata_count / max(1, len(entries)))
    behavior_score = min(1.0, behavior_count / max(1, len(entries)))
    matchability_score = round(100 * (0.5 * group_score + 0.35 * metadata_score + 0.15 * behavior_score), 1)
    return {
        "groups_present": groups_present,
        "entry_count": len(entries),
        "metadata_entry_count": metadata_count,
        "behavior_metadata_entry_count": behavior_count,
        "pii_hints": pii_hints,
        "pii_hint_count": len(pii_hints),
        "unsupported_fields": unsupported,
        "matchability_score": matchability_score,
        "runtime_network_access": False,
        "uploaded": False,
        "execution_authorized": False,
    }


def _write(path: Path, content: str, overwrite: bool) -> None:
    with path.open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
        stream.write(content.rstrip() + "\n")


def write_real_report_validation_pack(report: dict, output_dir, *, overwrite: bool = False) -> dict:
    if not isinstance(overwrite, bool):
        raise TypeError("overwrite must be bool")
    destination = Path(output_dir)
    _validated_explicit_local_path(destination / "report_shape_summary.json", allowed_suffixes={".json"})
    if destination.exists() and not overwrite:
        raise FileExistsError(f"validation output already exists: {destination}")
    if destination.exists() and not destination.is_dir():
        raise ValueError("validation output must be a directory")
    destination.mkdir(parents=True, exist_ok=True)
    summary = validate_real_report_shape(report)
    _write(destination / "START_HERE.md", "# Real Machine Report Validation\n\n本地离线检查显式输入的 report；不上传、不联网、不读取额外文件。", overwrite)
    with (destination / "report_shape_summary.json").open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2); stream.write("\n")
    pii = ["# PII 去标识化清单", "", "分享报告前请删除或泛化用户名、设备名、用户目录、token 和精确安装路径。", ""]
    pii.extend(f"- {item['field']}: {item['reason']}" for item in summary["pii_hints"])
    _write(destination / "pii_redaction_checklist.md", "\n".join(pii), overwrite)
    _write(destination / "matchability_summary.md", f"# Matchability Summary\n\n- matchability_score: `{summary['matchability_score']}`\n- metadata entries: `{summary['metadata_entry_count']}`\n- behavior metadata entries: `{summary['behavior_metadata_entry_count']}`", overwrite)
    _write(destination / "unsupported_fields.md", "# Unsupported Fields\n\n" + ("\n".join(f"- `{item}`" for item in summary["unsupported_fields"]) or "- none"), overwrite)
    _write(destination / "next_steps.md", "# Next Steps\n\n1. 本地核对软件身份、发布者和安装来源。\n2. 分享前完成去标识化。\n3. 将 evidence 命中视为人工复核线索，而非系统动作授权。", overwrite)
    return {"output_dir": str(destination), "artifact_count": 6, **summary}
