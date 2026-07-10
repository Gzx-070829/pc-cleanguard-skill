"""Create and run a bounded cleanup demo through the production safety gates."""

from __future__ import annotations

import json
from pathlib import Path

from ..cleanup import (
    BlockedCandidate,
    CleanupConfirmation,
    CleanupExecutor,
    JunkScanner,
    JunkScanResult,
    build_cleanup_preview,
    build_cleanup_summary,
    render_cleanup_report_markdown,
    write_cleanup_execution_report,
    write_cleanup_report_markdown,
)
from ..cleanup.junk_rules import JunkCategory
from ..skill import write_report


_MARKER_NAME = ".pc-cleanguard-demo.json"
_MARKER_FORMAT = "pc_cleanguard_cleanup_demo"
_PROTECTED_PARTS = {
    "desktop",
    "documents",
    "my documents",
    "pictures",
    "photos",
    "videos",
    "windows",
    "program files",
    "program files (x86)",
    "programdata",
    "recovery",
    "system volume information",
    "$recycle.bin",
    "桌面",
    "文档",
    "图片",
    "照片",
    "视频",
}
_DEMO_FILES = {
    "temp/example.tmp": b"PC CleanGuard demo temporary data\n",
    "cache/example.cache": b"PC CleanGuard demo cache data\n",
    "logs/example.log": b"PC CleanGuard demo log entry\n",
    "dumps/example.dmp": b"PC CleanGuard synthetic crash dump marker\n",
    "installers/example.old": b"PC CleanGuard synthetic installer leftover\n",
}


def _explicit_demo_root(path: str | Path) -> Path:
    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise ValueError("demo root must be an explicit non-empty local path")
    raw = str(path).replace("/", "\\")
    if raw.startswith("\\\\"):
        raise ValueError("UNC, network, and device demo roots are not allowed")
    candidate = Path(path)
    if candidate.is_symlink():
        raise ValueError("symbolic-link demo roots are not allowed")
    resolved = candidate.resolve(strict=False)
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        raise ValueError("demo root is too broad")
    if {part.casefold() for part in resolved.parts}.intersection(_PROTECTED_PARTS):
        raise ValueError("demo root is inside a protected directory")
    current = resolved
    while current != Path(current.anchor):
        if current.exists() and current.is_symlink():
            raise ValueError("demo root traverses a symbolic link")
        current = current.parent
    return resolved


def _marker_payload(root: Path) -> dict:
    marker = root / _MARKER_NAME
    if not marker.is_file() or marker.is_symlink():
        raise ValueError("demo root was not created by PC CleanGuard demo init")
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("demo root marker is invalid") from error
    if payload != {
        "format": _MARKER_FORMAT,
        "schema_version": "0.2",
        "root": str(root),
    }:
        raise ValueError("demo root marker does not match this explicit root")
    return payload


def init_cleanup_demo(
    root: str | Path,
    *,
    force: bool = False,
) -> dict:
    """Create deterministic synthetic junk only inside an explicit safe root."""

    if not isinstance(force, bool):
        raise TypeError("force must be a bool")
    destination = _explicit_demo_root(root)
    if destination.exists():
        if not destination.is_dir():
            raise ValueError("demo root must be a directory")
        if not force:
            raise FileExistsError(f"demo root already exists: {destination}")
        _marker_payload(destination)
    else:
        destination.mkdir(parents=True)

    marker = {
        "format": _MARKER_FORMAT,
        "schema_version": "0.2",
        "root": str(destination),
    }
    (destination / _MARKER_NAME).write_text(
        json.dumps(marker, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (destination / "README.txt").write_text(
        "PC CleanGuard cleanup demo directory.\n"
        "此目录只包含由 demo init 创建的合成测试垃圾。\n"
        "默认运行仅预览；--confirm 也只允许现有 L1 安全门处理本目录文件。\n",
        encoding="utf-8",
        newline="\n",
    )
    for relative, content in _DEMO_FILES.items():
        target = destination / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    (destination / "empty").mkdir(exist_ok=True)
    return {
        "root": str(destination),
        "created_files": sorted(_DEMO_FILES),
        "marker": str(destination / _MARKER_NAME),
        "safe_demo_only": True,
    }


def _explicit_output_root(path: str | Path, demo_root: Path) -> Path:
    output = _explicit_demo_root(path)
    if output == demo_root or output.is_relative_to(demo_root):
        raise ValueError("demo output must be outside the cleanup demo root")
    if output.exists():
        raise FileExistsError(f"demo output already exists: {output}")
    return output


def _bounded_demo_scan(root: Path) -> JunkScanResult:
    """Keep only unchanged init-generated candidates eligible for demo execution."""

    scanned = JunkScanner().scan([root])
    allowed = []
    blocked = list(scanned.blocked_candidates)
    warnings = list(scanned.warnings)
    for candidate in scanned.candidates:
        path = Path(candidate.path)
        try:
            relative = path.resolve(strict=True).relative_to(root).as_posix()
        except (OSError, ValueError):
            relative = ""
        expected = _DEMO_FILES.get(relative)
        is_known_empty = (
            relative == "empty"
            and candidate.category is JunkCategory.EMPTY_DIRECTORY_CANDIDATE
        )
        matches_manifest = is_known_empty
        if expected is not None:
            try:
                matches_manifest = path.read_bytes() == expected
            except OSError:
                matches_manifest = False
        if matches_manifest:
            allowed.append(candidate)
            continue
        reason = "candidate is not an unchanged file from the cleanup demo manifest"
        blocked.append(
            BlockedCandidate(
                path=str(path),
                reason=reason,
                evidence=({"source": "demo_manifest", "fact": reason},),
            )
        )
        warnings.append(f"blocked demo candidate: {path}: {reason}")
    return JunkScanResult(
        explicit_paths=scanned.explicit_paths,
        candidates=tuple(allowed),
        blocked_candidates=tuple(blocked),
        scanned_files=scanned.scanned_files,
        scanned_bytes=scanned.scanned_bytes,
        warnings=tuple(warnings),
    )


def run_cleanup_demo(
    root: str | Path,
    output: str | Path,
    *,
    confirm: bool = False,
) -> dict:
    """Run preview, PR15 execution, audit, and reporting for a marked demo root."""

    if not isinstance(confirm, bool):
        raise TypeError("confirm must be a bool")
    demo_root = _explicit_demo_root(root)
    if not demo_root.is_dir():
        raise FileNotFoundError(f"demo root does not exist: {demo_root}")
    _marker_payload(demo_root)
    output_root = _explicit_output_root(output, demo_root)
    output_root.mkdir(parents=True)

    preview_path = output_root / "preview.json"
    result_path = output_root / "dry_run_result.json"
    audit_path = output_root / "audit.jsonl"
    report_path = output_root / "cleanup_report.md"

    preview = build_cleanup_preview(_bounded_demo_scan(demo_root)).to_dict()
    write_report(preview_path, preview)
    confirmation = CleanupConfirmation(confirm, (demo_root,))
    execution = CleanupExecutor().execute(
        preview,
        confirmation,
        audit_path=audit_path,
    )
    write_cleanup_execution_report(result_path, execution)
    summary = build_cleanup_summary(preview, execution.to_dict())
    write_cleanup_report_markdown(
        report_path,
        render_cleanup_report_markdown(summary),
    )
    return {
        "root": str(demo_root),
        "output": str(output_root),
        "preview": str(preview_path),
        "result": str(result_path),
        "audit": str(audit_path),
        "report": str(report_path),
        "confirmed": confirm,
        "execution_performed": execution.summary["execution_performed"],
        "next_step": (
            "Review cleanup_report.md and the audit JSONL."
            if confirm
            else "Review cleanup_report.md; rerun in a fresh output path with --confirm only if desired."
        ),
        "summary": summary,
    }


def quickstart_cleanup_demo(root: str | Path, output: str | Path) -> dict:
    """Initialize a new demo root and run the complete loop in dry-run mode."""

    demo_root = _explicit_demo_root(root)
    if demo_root.exists():
        raise FileExistsError(f"demo root already exists: {demo_root}")
    output_root = _explicit_output_root(output, demo_root)
    initialized = init_cleanup_demo(demo_root)
    result = run_cleanup_demo(demo_root, output_root, confirm=False)
    return {
        **result,
        "quickstart": True,
        "initialized": initialized["safe_demo_only"],
    }
