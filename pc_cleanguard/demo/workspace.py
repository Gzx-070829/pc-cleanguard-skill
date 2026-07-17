"""Create verifiable synthetic files only under PC CleanGuard's temp namespace."""

from __future__ import annotations

import hashlib
import json
import secrets
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


SYNTHETIC_MANIFEST_NAME = ".pcg-synthetic-workspace.json"
_CREATED_BY = "pc_cleanguard.demo.acceptance.v0.4.1"
_OPERATIONS = ("preview", "quarantine", "restore")
_FILES = {
    "temp/acceptance.tmp": b"PC CleanGuard v0.4.1 synthetic temporary file\n",
    "cache/acceptance.cache": b"PC CleanGuard v0.4.1 synthetic cache file\n",
    "logs/acceptance.log": b"PC CleanGuard v0.4.1 synthetic log file\n",
}
_REPARSE_POINT = 0x400


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_reparse(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return True
    return path.is_symlink() or bool(attributes & _REPARSE_POINT)


def dedicated_synthetic_temp_root() -> Path:
    """Return the fixed namespace; callers cannot supply a different root."""

    temp = Path(tempfile.gettempdir()).resolve(strict=True)
    return temp / "PC-CleanGuard" / "acceptance"


def _assert_no_reparse_ancestors(path: Path) -> None:
    temp = Path(tempfile.gettempdir()).resolve(strict=True)
    try:
        relative = path.absolute().relative_to(temp)
    except ValueError as error:
        raise ValueError("synthetic path is outside the system temp root") from error
    current = temp
    for part in relative.parts:
        current = current / part
        if current.exists() and _is_reparse(current):
            raise ValueError("synthetic temp namespace traverses a reparse point")


def create_synthetic_workspace() -> dict:
    """Create a random, manifest-backed workspace containing only known bytes."""

    base = dedicated_synthetic_temp_root()
    _assert_no_reparse_ancestors(base)
    base.mkdir(parents=True, exist_ok=True)
    _assert_no_reparse_ancestors(base)
    workspace_id = uuid4().hex
    root = base / workspace_id
    root.mkdir()
    nonce = secrets.token_urlsafe(32)
    hashes = {}
    for relative, content in _FILES.items():
        destination = root / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        hashes[relative] = _sha256(destination)
    manifest = {
        "workspace_id": workspace_id,
        "nonce": nonce,
        "created_by": _CREATED_BY,
        "created_at": _now(),
        "synthetic_only": True,
        "expected_files": sorted(_FILES),
        "file_hashes": {key: hashes[key] for key in sorted(hashes)},
        "allowed_operations": list(_OPERATIONS),
        "workspace_root": str(root.resolve(strict=True)),
    }
    (root / SYNTHETIC_MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return verify_synthetic_workspace(root, nonce)


def _safe_relative(value: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("synthetic manifest paths must be non-empty strings")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or value.startswith(("\\", "/")):
        raise ValueError("synthetic manifest contains directory traversal")
    return candidate


def verify_synthetic_workspace(root: str | Path, expected_nonce: str) -> dict:
    """Fail closed unless root, nonce, entries, and hashes match the manifest."""

    if not isinstance(expected_nonce, str) or not expected_nonce:
        raise ValueError("expected nonce is required")
    candidate = Path(root).absolute()
    base = dedicated_synthetic_temp_root()
    try:
        candidate.relative_to(base)
    except ValueError as error:
        raise ValueError("synthetic workspace is outside the dedicated temp root") from error
    _assert_no_reparse_ancestors(candidate)
    if _is_reparse(candidate) or not candidate.is_dir():
        raise ValueError("synthetic workspace must be an existing non-reparse directory")
    resolved = candidate.resolve(strict=True)
    base_resolved = base.resolve(strict=True)
    if resolved == base_resolved or not resolved.is_relative_to(base_resolved):
        raise ValueError("synthetic workspace is outside the dedicated temp root")
    manifest_path = resolved / SYNTHETIC_MANIFEST_NAME
    if _is_reparse(manifest_path) or not manifest_path.is_file():
        raise ValueError("synthetic workspace manifest is missing or unsafe")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("synthetic workspace manifest is invalid") from error
    required = {
        "workspace_id", "nonce", "created_by", "created_at", "synthetic_only",
        "expected_files", "file_hashes", "allowed_operations", "workspace_root",
    }
    if set(manifest) != required:
        raise ValueError("synthetic workspace manifest fields are invalid")
    if manifest["workspace_id"] != resolved.name or manifest["created_by"] != _CREATED_BY:
        raise ValueError("synthetic workspace identity is invalid")
    if manifest["synthetic_only"] is not True or tuple(manifest["allowed_operations"]) != _OPERATIONS:
        raise ValueError("synthetic workspace permissions are invalid")
    if Path(manifest["workspace_root"]).resolve(strict=False) != resolved:
        raise ValueError("synthetic workspace root does not match manifest")
    if not secrets.compare_digest(str(manifest["nonce"]), expected_nonce):
        raise ValueError("synthetic workspace nonce mismatch")
    expected_files = manifest["expected_files"]
    hashes = manifest["file_hashes"]
    if not isinstance(expected_files, list) or not expected_files or len(expected_files) != len(set(expected_files)):
        raise ValueError("synthetic expected_files must be a unique non-empty array")
    if not isinstance(hashes, dict) or set(hashes) != set(expected_files):
        raise ValueError("synthetic file_hashes do not match expected_files")

    allowed_entries = {SYNTHETIC_MANIFEST_NAME}
    for relative in expected_files:
        safe = _safe_relative(relative)
        allowed_entries.add(safe.as_posix())
        parent = safe.parent
        while parent != Path("."):
            allowed_entries.add(parent.as_posix())
            parent = parent.parent
    for entry in resolved.rglob("*"):
        relative = entry.relative_to(resolved).as_posix()
        if _is_reparse(entry):
            raise ValueError("synthetic workspace contains a reparse point")
        if relative not in allowed_entries:
            raise ValueError("synthetic workspace contains an unregistered entry")
    for relative in expected_files:
        path = resolved / _safe_relative(relative)
        if not path.is_file() or _is_reparse(path):
            raise ValueError("synthetic expected file is missing or unsafe")
        expected_hash = hashes[relative]
        if not isinstance(expected_hash, str) or _sha256(path) != expected_hash:
            raise ValueError("synthetic file hash mismatch")
    return dict(manifest)


def synthetic_file_sha256(path: str | Path) -> str:
    return _sha256(Path(path))
