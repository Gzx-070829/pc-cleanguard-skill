"""Reversible, manifest-backed quarantine for explicit regular files."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..protection import classify_developer_path
from .errors import QuarantineIntegrityError
from .manifest import QuarantineItem, QuarantineManifest, validated_evidence


_PROTECTED_PARTS = {
    "windows", "program files", "program files (x86)", "programdata",
    "documents", "desktop", "pictures", "photos", "videos",
    "recovery", "system volume information", "$recycle.bin",
    "文档", "桌面", "图片", "照片", "视频",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_root(path: str | Path) -> Path:
    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise ValueError("quarantine root must be an explicit local path")
    raw = str(path).replace("/", "\\")
    if raw.startswith("\\\\"):
        raise ValueError("UNC and network quarantine roots are not allowed")
    root = Path(path)
    if root.is_symlink():
        raise ValueError("symbolic-link quarantine roots are not allowed")
    resolved = root.resolve(strict=False)
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        raise ValueError("quarantine root is too broad")
    if {part.casefold() for part in resolved.parts}.intersection(_PROTECTED_PARTS):
        raise ValueError("quarantine root is protected")
    if classify_developer_path(resolved).protected:
        raise ValueError("quarantine root is developer protected")
    return resolved


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class QuarantineManager:
    def __init__(self, root: str | Path) -> None:
        self.root = _safe_root(root)
        self.files_root = self.root / "files"
        self.manifest_path = self.root / "manifest.json"
        if not self.manifest_path.is_file():
            raise FileNotFoundError("quarantine manifest does not exist")
        self._manifest = self._load()
        if Path(self._manifest.root).resolve(strict=False) != self.root:
            raise ValueError("quarantine manifest root mismatch")

    @classmethod
    def create_quarantine(cls, root: str | Path) -> "QuarantineManager":
        destination = _safe_root(root)
        if destination.exists() and not destination.is_dir():
            raise ValueError("quarantine root must be a directory")
        if destination.exists() and any(destination.iterdir()):
            if not (destination / "manifest.json").is_file():
                raise FileExistsError("non-empty quarantine root has no manifest")
            return cls(destination)
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "files").mkdir(exist_ok=True)
        manifest = QuarantineManifest(root=str(destination), items=(), updated_at=_now())
        cls._write_manifest(destination / "manifest.json", manifest)
        return cls(destination)

    @staticmethod
    def _write_manifest(path: Path, manifest: QuarantineManifest) -> None:
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        temporary.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        temporary.replace(path)

    def _load(self) -> QuarantineManifest:
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("invalid quarantine manifest") from error
        return QuarantineManifest.from_dict(data)

    def _save(self, manifest: QuarantineManifest) -> None:
        self._write_manifest(self.manifest_path, manifest)
        self._manifest = manifest

    def list_items(self) -> list[QuarantineItem]:
        self._manifest = self._load()
        return list(self._manifest.items)

    def get_item(self, item_id: str) -> QuarantineItem:
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError("item_id must be non-empty")
        for item in self.list_items():
            if item.item_id == item_id:
                return item
        raise KeyError(f"unknown quarantine item: {item_id}")

    def quarantine_file(self, path: str | Path, reason: str, evidence) -> QuarantineItem:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be non-empty")
        source = Path(path)
        if source.is_symlink() or not source.exists() or not source.is_file():
            raise ValueError("quarantine input must be an existing regular file")
        source = source.resolve(strict=True)
        if source == self.root or source.is_relative_to(self.root):
            raise ValueError("cannot quarantine an item already inside quarantine")
        if classify_developer_path(source).protected:
            raise ValueError("developer-protected files cannot be quarantined")
        if {part.casefold() for part in source.parts}.intersection(_PROTECTED_PARTS):
            raise ValueError("protected user or system files cannot be quarantined")
        evidence_items = validated_evidence(evidence)
        stat = source.stat(follow_symlinks=False)
        item_id = str(uuid4())
        destination = self.files_root / f"{item_id}.bin"
        item = QuarantineItem(
            item_id=item_id,
            original_path=str(source),
            quarantine_path=str(destination),
            sha256=_sha256(source),
            size_bytes=max(0, int(stat.st_size)),
            original_mtime=float(stat.st_mtime),
            reason=reason.strip(),
            evidence=evidence_items,
            created_at=_now(),
        )
        source.replace(destination)
        manifest = QuarantineManifest(
            root=str(self.root),
            items=(*self._manifest.items, item),
            updated_at=_now(),
        )
        try:
            self._save(manifest)
        except Exception:
            destination.replace(source)
            raise
        return item

    def restore_item(self, item_id: str) -> QuarantineItem:
        item = self.get_item(item_id)
        if item.status != "active":
            raise ValueError("quarantine item is not active")
        source = Path(item.quarantine_path)
        destination = Path(item.original_path)
        if destination.exists():
            raise FileExistsError(f"restore destination exists: {destination}")
        if not destination.parent.is_dir():
            raise FileNotFoundError("restore destination parent does not exist")
        if not source.is_file() or source.is_symlink():
            raise QuarantineIntegrityError("quarantine payload is unavailable")
        if source.stat().st_size != item.size_bytes or _sha256(source) != item.sha256:
            raise QuarantineIntegrityError("quarantine payload integrity mismatch")
        source.replace(destination)
        restored = replace(item, status="restored", restored_at=_now())
        items = tuple(restored if current.item_id == item_id else current for current in self._manifest.items)
        manifest = QuarantineManifest(root=str(self.root), items=items, updated_at=_now())
        try:
            self._save(manifest)
        except Exception:
            destination.replace(source)
            raise
        return restored
