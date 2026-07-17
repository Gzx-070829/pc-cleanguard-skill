"""Load explicit PowerShell collector artifacts without running their commands."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from .collector_manifest import COLLECTOR_NAMES, validate_collector_manifest


_MAX_FILE_BYTES = 64 * 1024 * 1024


def _load_json(path: Path):
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"collector artifact is missing: {path.name}")
    if path.stat().st_size > _MAX_FILE_BYTES:
        raise ValueError(f"collector artifact exceeds {_MAX_FILE_BYTES} bytes: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"collector artifact is not valid UTF-8 JSON: {path.name}") from error


def _explicit_directory(path: str | Path) -> Path:
    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise ValueError("collector directory must be an explicit local path")
    raw = str(path).replace("/", "\\")
    if raw.startswith("\\\\"):
        raise ValueError("UNC, network, and device collector directories are not allowed")
    candidate = Path(path)
    if candidate.is_symlink():
        raise ValueError("symbolic-link collector directories are not allowed")
    if not candidate.is_dir():
        raise FileNotFoundError(f"collector directory does not exist: {candidate}")
    return candidate.resolve(strict=True)


def load_collector_directory(path: str | Path) -> dict:
    """Read one explicit collector directory and preserve partial failure state."""

    root = _explicit_directory(path)
    manifest = _load_json(root / "collector_manifest.json")
    errors = validate_collector_manifest(manifest)
    if errors:
        raise ValueError("invalid collector manifest: " + "; ".join(errors))
    status = deepcopy(manifest["collectors"])
    collections: dict[str, list[dict]] = {}
    collection_errors = []
    errors_path = root / "collector_errors.json"
    if errors_path.exists():
        loaded_errors = _load_json(errors_path)
        if not isinstance(loaded_errors, list) or not all(isinstance(item, dict) for item in loaded_errors):
            raise ValueError("collector_errors.json must contain an array of objects")
        collection_errors.extend(deepcopy(loaded_errors))

    for name in COLLECTOR_NAMES:
        item = status[name]
        artifact = root / item["file"]
        try:
            records = _load_json(artifact)
            if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
                raise ValueError(f"{artifact.name} must contain an array of objects")
        except (FileNotFoundError, ValueError) as error:
            records = []
            if item["status"] == "success":
                item["status"] = "failed"
                item["error_code"] = "invalid_collector_artifact"
                collection_errors.append(
                    {"collector": name, "error_code": "invalid_collector_artifact", "message": str(error)}
                )
        if item["status"] == "success" and item["record_count"] != len(records):
            item["status"] = "failed"
            item["error_code"] = "record_count_mismatch"
            collection_errors.append(
                {"collector": name, "error_code": "record_count_mismatch", "message": "manifest count does not match JSON array"}
            )
        collections[name] = deepcopy(records)
    return {
        "manifest": deepcopy(manifest),
        "collections": collections,
        "collector_status": status,
        "collection_errors": collection_errors,
        "source_directory": str(root),
    }
