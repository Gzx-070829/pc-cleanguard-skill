"""Run quarantine and restore acceptance only against a new synthetic workspace."""

from __future__ import annotations

import json
from pathlib import Path

from ..cleanup import (
    CleanupConfirmation,
    CleanupExecutor,
    JunkScanner,
    build_cleanup_preview,
    write_cleanup_execution_report,
)
from ..quarantine import QuarantineManager
from ..skill import write_report
from .workspace import (
    create_synthetic_workspace,
    dedicated_synthetic_temp_root,
    synthetic_file_sha256,
    verify_synthetic_workspace,
)


def _output_directory(path: str | Path) -> Path:
    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise ValueError("acceptance output must be an explicit local path")
    raw = str(path).replace("/", "\\")
    if raw.startswith("\\\\"):
        raise ValueError("acceptance output must not use UNC or network paths")
    output = Path(path)
    if output.exists():
        raise FileExistsError(f"acceptance output already exists: {output}")
    if output.is_symlink():
        raise ValueError("acceptance output must not be a symbolic link")
    return output.resolve(strict=False)


def run_demo_acceptance(
    output: str | Path,
    *,
    confirm_synthetic: bool,
) -> dict:
    """Quarantine known synthetic L1 files and restore one, never unlinking them."""

    if confirm_synthetic is not True:
        raise ValueError("demo acceptance requires --confirm-synthetic")
    destination = _output_directory(output)
    workspace = create_synthetic_workspace()
    root = Path(workspace["workspace_root"])
    verified = verify_synthetic_workspace(root, workspace["nonce"])
    destination.mkdir(parents=True)

    preview = build_cleanup_preview(JunkScanner().scan([root])).to_dict()
    preview_path = destination / "preview.json"
    result_path = destination / "execution_result.json"
    audit_path = destination / "audit.jsonl"
    write_report(preview_path, preview)

    quarantine_root = dedicated_synthetic_temp_root().parent / "quarantine" / workspace["workspace_id"]
    execution = CleanupExecutor(quarantine_root=quarantine_root).execute(
        preview,
        CleanupConfirmation(True, (root,)),
        audit_path=audit_path,
    )
    write_cleanup_execution_report(result_path, execution)
    manager = QuarantineManager(quarantine_root)
    active = [item for item in manager.list_items() if item.status == "active"]
    if not active:
        raise RuntimeError("synthetic acceptance did not quarantine any L1 file")
    restored = manager.restore_item(active[0].item_id)
    restored_path = Path(restored.original_path)
    restored_hash = synthetic_file_sha256(restored_path)
    hash_matches = restored_hash == restored.sha256 == verified["file_hashes"][restored_path.relative_to(root).as_posix()]

    audit_events = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    result = {
        "schema_version": "0.4.1",
        "workspace_id": workspace["workspace_id"],
        "workspace_root": str(root),
        "quarantine_root": str(quarantine_root),
        "manifest_verified": True,
        "registered_file_count": len(workspace["expected_files"]),
        "preview_candidate_count": preview["total_candidates"],
        "quarantine_succeeded": execution.summary["quarantined"] > 0,
        "quarantined_count": execution.summary["quarantined"],
        "restore_succeeded": restored.status == "restored" and restored_path.is_file(),
        "restored_item_id": restored.item_id,
        "restored_sha256": restored_hash,
        "restored_sha256_matches": hash_matches,
        "audit_event_count": len(audit_events),
        "audit_confirmed": bool(audit_events) and all(event.get("confirmed") is True for event in audit_events),
        "desktop_protection_bypassed": False,
        "permanent_delete_performed": False,
        "runtime_network_access": False,
        "system_modification_performed": False,
        "execution_gating_eligible_count": 0,
    }
    if not all((
        result["manifest_verified"], result["quarantine_succeeded"],
        result["restore_succeeded"], result["restored_sha256_matches"],
        result["audit_confirmed"],
    )):
        raise RuntimeError("synthetic acceptance verification failed")
    write_report(destination / "acceptance_result.json", result)
    (destination / "START_HERE.md").write_text(
        "# Synthetic Demo Acceptance\n\n"
        "专用临时空间中的合成 L1 文件已完成 preview、隔离、恢复和 SHA-256 核验。\n\n"
        "- Desktop / Documents / 代码仓库保护没有放宽。\n"
        "- 没有永久删除。\n"
        "- 没有联网或上传。\n",
        encoding="utf-8",
        newline="\n",
    )
    return result
