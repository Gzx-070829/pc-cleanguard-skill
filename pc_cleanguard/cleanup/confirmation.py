"""Explicit confirmation and path-containment gates for L1 cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

from .junk_rules import JunkCategory


L1_ALLOWED_CATEGORIES = (
    JunkCategory.TEMP_FILE,
    JunkCategory.CACHE_FILE,
    JunkCategory.LOG_FILE,
)

_PROTECTED_NAMES = {
    "desktop",
    "documents",
    "my documents",
    "pictures",
    "photos",
    "videos",
    "source",
    "src",
    "code",
    "project",
    "projects",
    "repos",
    "repositories",
    "workspace",
    "workspaces",
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
    "代码",
    "项目",
}
_CODE_MARKERS = (
    ".git",
    ".hg",
    ".svn",
    "pyproject.toml",
    "package.json",
    "cargo.toml",
    "go.mod",
)
_BROWSER_NAMES = {
    "chrome",
    "google",
    "edge",
    "microsoft edge",
    "mozilla",
    "firefox",
    "brave-browser",
    "bravesoftware",
    "opera",
    "vivaldi",
}
_BROWSER_PROFILE_NAMES = {"user data", "profiles"}


@dataclass(frozen=True, slots=True)
class ConfirmationDecision:
    allowed: bool
    reason: str
    evidence: Tuple[dict, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise TypeError("allowed must be a bool")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        if not self.evidence or any(
            not isinstance(item, dict)
            or not isinstance(item.get("source"), str)
            or not item["source"].strip()
            or not isinstance(item.get("fact"), str)
            or not item["fact"].strip()
            for item in self.evidence
        ):
            raise ValueError("evidence must contain source/fact objects")


@dataclass(frozen=True, slots=True)
class CleanupConfirmation:
    """A caller's explicit confirmation flag and bounded local roots."""

    confirmed: bool
    allow_roots: Tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.confirmed, bool):
            raise TypeError("confirmed must be a bool")
        if isinstance(self.allow_roots, (str, Path)):
            raise TypeError("allow_roots must contain explicit directories")
        supplied = tuple(self.allow_roots)
        if not supplied:
            raise ValueError("at least one explicit allow-root is required")
        normalized = []
        seen = set()
        for raw_root in supplied:
            if not isinstance(raw_root, (str, Path)) or not str(raw_root).strip():
                raise ValueError("allow-root must be a non-empty local path")
            raw_windows = str(raw_root).replace("/", "\\")
            if raw_windows.startswith("\\\\"):
                raise ValueError("UNC, network, and device allow-roots are not allowed")
            root = Path(raw_root)
            if root.is_symlink():
                raise ValueError("symbolic-link allow-roots are not allowed")
            if not root.exists():
                raise FileNotFoundError(f"allow-root does not exist: {root}")
            if not root.is_dir():
                raise ValueError(f"allow-root must be a directory: {root}")
            resolved = root.resolve()
            if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
                raise ValueError("allow-root is too broad")
            key = str(resolved).casefold()
            if key not in seen:
                seen.add(key)
                normalized.append(resolved)
        object.__setattr__(self, "allow_roots", tuple(normalized))

    def evaluate(self, path: str | Path) -> ConfirmationDecision:
        """Re-check a candidate against current filesystem metadata."""

        if not isinstance(path, (str, Path)) or not str(path).strip():
            return self._blocked("candidate path is empty or invalid")
        candidate = Path(path)
        if candidate.is_symlink():
            return self._blocked("candidate is a symbolic link")
        if not candidate.exists():
            return self._blocked("candidate path no longer exists")
        if not candidate.is_file():
            return self._blocked("candidate is not a regular file")
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            return self._blocked("candidate metadata cannot be resolved")
        allowed_root = next(
            (
                root
                for root in self.allow_roots
                if resolved != root and resolved.is_relative_to(root)
            ),
            None,
        )
        if allowed_root is None:
            return self._blocked("candidate is outside every explicit allow-root")
        if self._contains_symbolic_link(candidate, allowed_root):
            return self._blocked("candidate path traverses a symbolic link")
        parts = {part.casefold() for part in resolved.parts}
        if parts.intersection(_PROTECTED_NAMES):
            return self._blocked("candidate is inside a protected directory")
        if parts.intersection(_BROWSER_NAMES) and parts.intersection(
            _BROWSER_PROFILE_NAMES
        ):
            return self._blocked("candidate is inside a protected browser profile")
        if self._has_code_marker(resolved.parent, allowed_root):
            return self._blocked("candidate is inside a protected code repository")
        return ConfirmationDecision(
            allowed=True,
            reason="candidate is a regular file inside an explicit allow-root",
            evidence=(
                {
                    "source": "allow_root",
                    "fact": f"candidate is contained by {allowed_root}",
                },
                {
                    "source": "path_protection",
                    "fact": "no protected directory, browser profile, or code marker matched",
                },
            ),
        )

    @staticmethod
    def _contains_symbolic_link(candidate: Path, root: Path) -> bool:
        absolute = candidate.absolute()
        try:
            relative = absolute.relative_to(root)
        except ValueError:
            return True
        current = root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                return True
        return False

    @staticmethod
    def _has_code_marker(start: Path, root: Path) -> bool:
        current = start
        while current == root or current.is_relative_to(root):
            if any((current / marker).exists() for marker in _CODE_MARKERS):
                return True
            if current == root:
                break
            current = current.parent
        return False

    @staticmethod
    def _blocked(reason: str) -> ConfirmationDecision:
        return ConfirmationDecision(
            allowed=False,
            reason=reason,
            evidence=(
                {"source": "confirmation_gate", "fact": reason},
            ),
        )
