"""Bounded, metadata-only scanning of caller-supplied local directories."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Tuple

from ..core.models import RiskLevel
from .junk_rules import JunkCategory, JunkRule, default_junk_rules, match_junk_rule


READ_ONLY_EXECUTION_LEVEL = "LEVEL_0_READ_ONLY"

_PROTECTED_DIRECTORY_NAMES = {
    "desktop",
    "documents",
    "my documents",
    "pictures",
    "videos",
    "photos",
    "source",
    "src",
    "code",
    "project",
    "projects",
    "repos",
    "repositories",
    "workspace",
    "workspaces",
    "桌面",
    "文档",
    "图片",
    "照片",
    "视频",
    "代码",
    "项目",
}
_SYSTEM_DIRECTORY_NAMES = {
    "windows",
    "program files",
    "program files (x86)",
    "programdata",
    "recovery",
    "system volume information",
    "$recycle.bin",
}
_CODE_MARKERS = {
    ".git",
    ".hg",
    ".svn",
    "pyproject.toml",
    "package.json",
    "cargo.toml",
    "go.mod",
}


def _validated_evidence(evidence: Iterable[dict]) -> Tuple[dict, ...]:
    items = tuple(evidence)
    if not items or any(
        not isinstance(item, dict)
        or not isinstance(item.get("source"), str)
        or not item["source"].strip()
        or not isinstance(item.get("fact"), str)
        or not item["fact"].strip()
        for item in items
    ):
        raise ValueError("evidence must contain source/fact objects")
    return tuple(
        {"source": item["source"].strip(), "fact": item["fact"].strip()}
        for item in items
    )


@dataclass(frozen=True, slots=True)
class JunkCandidate:
    """A confirmation-required metadata finding, never a deletion instruction."""

    path: str
    category: JunkCategory
    size_bytes: int
    reason: str
    evidence: Tuple[dict, ...]
    confidence: float
    risk_level: RiskLevel
    execution_level: str = READ_ONLY_EXECUTION_LEVEL
    requires_user_confirmation: bool = True
    dry_run_only: bool = True
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError("path must be a non-empty string")
        if not isinstance(self.category, JunkCategory):
            raise TypeError("category must be a JunkCategory")
        if (
            not isinstance(self.size_bytes, int)
            or isinstance(self.size_bytes, bool)
            or self.size_bytes < 0
        ):
            raise ValueError("size_bytes must be a non-negative integer")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        if (
            not isinstance(self.confidence, (int, float))
            or isinstance(self.confidence, bool)
            or not 0.0 <= float(self.confidence) <= 1.0
        ):
            raise ValueError("confidence must be between 0 and 1")
        if not isinstance(self.risk_level, RiskLevel):
            raise TypeError("risk_level must be a RiskLevel")
        if self.execution_level != READ_ONLY_EXECUTION_LEVEL:
            raise ValueError("junk candidates are restricted to Level 0")
        if self.requires_user_confirmation is not True:
            raise ValueError("junk candidates always require user confirmation")
        if self.dry_run_only is not True or self.execution_authorized is not False:
            raise ValueError("junk candidates cannot authorize execution")
        object.__setattr__(self, "evidence", _validated_evidence(self.evidence))
        object.__setattr__(self, "confidence", float(self.confidence))

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "category": self.category.value,
            "size_bytes": self.size_bytes,
            "reason": self.reason,
            "evidence": [dict(item) for item in self.evidence],
            "confidence": self.confidence,
            "risk_level": self.risk_level.value,
            "execution_level": READ_ONLY_EXECUTION_LEVEL,
            "requires_user_confirmation": True,
            "dry_run_only": True,
            "execution_authorized": False,
        }


@dataclass(frozen=True, slots=True)
class BlockedCandidate:
    path: str
    reason: str
    evidence: Tuple[dict, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError("path must be a non-empty string")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        object.__setattr__(self, "evidence", _validated_evidence(self.evidence))

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "reason": self.reason,
            "evidence": [dict(item) for item in self.evidence],
            "blocked": True,
        }


@dataclass(frozen=True, slots=True)
class ScanLimits:
    max_files: int = 10_000
    max_total_size_bytes: int = 10 * 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        for name, value in (
            ("max_files", self.max_files),
            ("max_total_size_bytes", self.max_total_size_bytes),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class JunkScanResult:
    explicit_paths: Tuple[str, ...]
    candidates: Tuple[JunkCandidate, ...]
    blocked_candidates: Tuple[BlockedCandidate, ...]
    scanned_files: int
    scanned_bytes: int
    warnings: Tuple[str, ...]


@dataclass(slots=True)
class _ScanState:
    candidates: list[JunkCandidate] = field(default_factory=list)
    blocked: list[BlockedCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    scanned_files: int = 0
    scanned_bytes: int = 0
    stopped: bool = False


class JunkScanner:
    """Scan only explicit local directories using names and stat metadata."""

    def __init__(
        self,
        limits: ScanLimits | None = None,
        rules: Iterable[JunkRule] | None = None,
    ) -> None:
        self._limits = limits or ScanLimits()
        if not isinstance(self._limits, ScanLimits):
            raise TypeError("limits must be ScanLimits")
        self._rules = tuple(default_junk_rules() if rules is None else rules)
        if not self._rules or not all(
            isinstance(rule, JunkRule) for rule in self._rules
        ):
            raise TypeError("rules must contain JunkRule objects")

    def scan(self, paths: Iterable[str | Path]) -> JunkScanResult:
        if isinstance(paths, (str, Path)):
            raise TypeError("paths must be an iterable of explicit directories")
        supplied = tuple(paths)
        if not supplied:
            raise ValueError("at least one explicit scan path is required")
        roots = self._validated_roots(supplied)
        state = _ScanState()
        selected_roots: list[Path] = []
        for root in sorted(roots, key=lambda item: (len(item.parts), str(item).casefold())):
            if any(root == selected or root.is_relative_to(selected) for selected in selected_roots):
                state.warnings.append(f"skipped overlapping explicit path: {root}")
                continue
            selected_roots.append(root)
            if self._root_is_broad_or_protected(root):
                self._block(state, root, "explicit path is protected or too broad")
                continue
            self._walk(root, state)
            if state.stopped:
                break
        return JunkScanResult(
            explicit_paths=tuple(str(path) for path in selected_roots),
            candidates=tuple(state.candidates),
            blocked_candidates=tuple(state.blocked),
            scanned_files=state.scanned_files,
            scanned_bytes=state.scanned_bytes,
            warnings=tuple(state.warnings),
        )

    @staticmethod
    def _validated_roots(paths: tuple[str | Path, ...]) -> tuple[Path, ...]:
        roots = []
        seen = set()
        for raw_path in paths:
            if not isinstance(raw_path, (str, Path)) or not str(raw_path).strip():
                raise ValueError("scan paths must be explicit non-empty local paths")
            raw = str(raw_path).replace("/", "\\")
            if raw.startswith("\\\\"):
                raise ValueError("UNC, network, and device paths are not allowed")
            path = Path(raw_path)
            if path.is_symlink():
                raise ValueError(f"symbolic-link scan paths are not allowed: {path}")
            if not path.exists():
                raise FileNotFoundError(f"scan path does not exist: {path}")
            if not path.is_dir():
                raise ValueError(f"scan path must be a directory: {path}")
            resolved = path.resolve()
            key = str(resolved).casefold()
            if key not in seen:
                seen.add(key)
                roots.append(resolved)
        return tuple(roots)

    @staticmethod
    def _root_is_broad_or_protected(path: Path) -> bool:
        if path == Path(path.anchor) or path == Path.home().resolve():
            return True
        names = {part.casefold() for part in path.parts}
        return bool(names.intersection(_PROTECTED_DIRECTORY_NAMES | _SYSTEM_DIRECTORY_NAMES))

    def _walk(self, directory: Path, state: _ScanState) -> None:
        if state.stopped:
            return
        try:
            entries = sorted(directory.iterdir(), key=lambda item: item.name.casefold())
        except OSError as error:
            self._block(state, directory, f"directory metadata is unavailable: {error}")
            return
        names = {entry.name.casefold() for entry in entries}
        directory_name = directory.name.casefold()
        if directory_name in _PROTECTED_DIRECTORY_NAMES:
            self._block(state, directory, "personal or code directory is protected")
            return
        if directory_name in _SYSTEM_DIRECTORY_NAMES:
            self._block(state, directory, "system directory is protected")
            return
        if names.intersection(_CODE_MARKERS):
            self._block(state, directory, "code repository marker detected")
            return
        if not entries:
            self._add_empty_directory(directory, state)
            return
        for entry in entries:
            if state.stopped:
                return
            try:
                if entry.is_symlink():
                    state.warnings.append(f"skipped symbolic link: {entry}")
                    continue
                if entry.is_dir():
                    self._walk(entry, state)
                elif entry.is_file():
                    self._scan_file(entry, state)
            except OSError as error:
                state.warnings.append(f"skipped unavailable metadata: {entry}: {error}")

    def _scan_file(self, path: Path, state: _ScanState) -> None:
        if state.scanned_files >= self._limits.max_files:
            state.warnings.append("file count limit reached; scan stopped")
            state.stopped = True
            return
        metadata = path.stat(follow_symlinks=False)
        size = max(0, int(metadata.st_size))
        if state.scanned_bytes + size > self._limits.max_total_size_bytes:
            state.warnings.append("total size limit reached; scan stopped")
            state.stopped = True
            return
        state.scanned_files += 1
        state.scanned_bytes += size
        rule = match_junk_rule(path, rules=self._rules)
        if rule is not None:
            state.candidates.append(self._candidate(path, size, metadata.st_mtime, rule))

    def _add_empty_directory(self, path: Path, state: _ScanState) -> None:
        rule = match_junk_rule(path, is_empty_directory=True, rules=self._rules)
        if rule is None:
            return
        metadata = path.stat(follow_symlinks=False)
        state.candidates.append(self._candidate(path, 0, metadata.st_mtime, rule))

    @staticmethod
    def _candidate(
        path: Path,
        size: int,
        modified_time: float,
        rule: JunkRule,
    ) -> JunkCandidate:
        extension = path.suffix.casefold() or "<none>"
        return JunkCandidate(
            path=str(path),
            category=rule.category,
            size_bytes=size,
            reason=rule.reason,
            evidence=(
                {
                    "source": "filesystem_metadata",
                    "fact": (
                        f"size_bytes={size}; mtime_epoch={modified_time:.3f}; "
                        f"extension={extension}"
                    ),
                },
                {"source": "junk_rule", "fact": rule.reason},
            ),
            confidence=rule.confidence,
            risk_level=rule.risk_level,
            execution_level=READ_ONLY_EXECUTION_LEVEL,
            requires_user_confirmation=True,
            dry_run_only=True,
            execution_authorized=False,
        )

    @staticmethod
    def _block(state: _ScanState, path: Path, reason: str) -> None:
        state.blocked.append(
            BlockedCandidate(
                path=str(path),
                reason=reason,
                evidence=(
                    {"source": "path_protection", "fact": reason},
                ),
            )
        )
        state.warnings.append(f"blocked path: {path}: {reason}")
