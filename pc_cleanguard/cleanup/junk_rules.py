"""Metadata-only rules for identifying dry-run junk candidates."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Tuple

from ..core.models import RiskLevel


class JunkCategory(str, Enum):
    TEMP_FILE = "temp_file"
    CACHE_FILE = "cache_file"
    LOG_FILE = "log_file"
    CRASH_DUMP = "crash_dump"
    INSTALLER_LEFTOVER = "installer_leftover"
    EMPTY_DIRECTORY_CANDIDATE = "empty_directory_candidate"


JUNK_CATEGORIES = tuple(category.value for category in JunkCategory)


@dataclass(frozen=True, slots=True)
class JunkRule:
    """One explainable filename or directory-metadata classification rule."""

    category: JunkCategory
    reason: str
    confidence: float
    risk_level: RiskLevel
    extensions: Tuple[str, ...] = ()
    directory_markers: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.category, JunkCategory):
            raise TypeError("category must be a JunkCategory")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        if (
            not isinstance(self.confidence, (int, float))
            or isinstance(self.confidence, bool)
            or not 0.0 < float(self.confidence) <= 1.0
        ):
            raise ValueError("confidence must be greater than 0 and at most 1")
        if not isinstance(self.risk_level, RiskLevel):
            raise TypeError("risk_level must be a RiskLevel")
        extensions = tuple(item.casefold() for item in self.extensions)
        markers = tuple(item.casefold() for item in self.directory_markers)
        if any(not item.startswith(".") for item in extensions):
            raise ValueError("extensions must start with a dot")
        if any(not item for item in markers):
            raise ValueError("directory markers must not be empty")
        object.__setattr__(self, "extensions", extensions)
        object.__setattr__(self, "directory_markers", markers)
        object.__setattr__(self, "confidence", float(self.confidence))

    def matches(self, path: Path, *, is_empty_directory: bool = False) -> bool:
        if self.category is JunkCategory.EMPTY_DIRECTORY_CANDIDATE:
            return is_empty_directory
        if is_empty_directory:
            return False
        suffix_match = path.suffix.casefold() in self.extensions
        parent_parts = {part.casefold() for part in path.parent.parts}
        marker_match = bool(parent_parts.intersection(self.directory_markers))
        return suffix_match or marker_match


def default_junk_rules() -> Tuple[JunkRule, ...]:
    """Return deterministic PR14 rules in classification-priority order."""

    return (
        JunkRule(
            category=JunkCategory.CRASH_DUMP,
            reason="file extension indicates crash-dump metadata",
            confidence=0.90,
            risk_level=RiskLevel.LOW,
            extensions=(".dmp", ".dump", ".mdmp"),
        ),
        JunkRule(
            category=JunkCategory.INSTALLER_LEFTOVER,
            reason="file extension indicates a possible installer leftover",
            confidence=0.65,
            risk_level=RiskLevel.MEDIUM,
            extensions=(".msi", ".msp"),
        ),
        JunkRule(
            category=JunkCategory.TEMP_FILE,
            reason="file extension indicates temporary data",
            confidence=0.85,
            risk_level=RiskLevel.LOW,
            extensions=(".tmp", ".temp"),
        ),
        JunkRule(
            category=JunkCategory.LOG_FILE,
            reason="file extension indicates log data",
            confidence=0.75,
            risk_level=RiskLevel.LOW,
            extensions=(".log", ".trace"),
        ),
        JunkRule(
            category=JunkCategory.CACHE_FILE,
            reason="path or extension indicates cached data",
            confidence=0.75,
            risk_level=RiskLevel.LOW,
            extensions=(".cache",),
            directory_markers=(
                "cache",
                "caches",
                ".cache",
                "code cache",
                "gpucache",
                "__pycache__",
            ),
        ),
        JunkRule(
            category=JunkCategory.EMPTY_DIRECTORY_CANDIDATE,
            reason="directory is empty and is only a review candidate",
            confidence=0.50,
            risk_level=RiskLevel.MEDIUM,
        ),
    )


def match_junk_rule(
    path: str | Path,
    *,
    is_empty_directory: bool = False,
    rules: Iterable[JunkRule] | None = None,
) -> JunkRule | None:
    """Return the first metadata rule that matches a path."""

    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise ValueError("path must be non-empty")
    if not isinstance(is_empty_directory, bool):
        raise TypeError("is_empty_directory must be a bool")
    selected = tuple(default_junk_rules() if rules is None else rules)
    if not all(isinstance(rule, JunkRule) for rule in selected):
        raise TypeError("rules must contain JunkRule objects")
    candidate = Path(path)
    return next(
        (
            rule
            for rule in selected
            if rule.matches(candidate, is_empty_directory=is_empty_directory)
        ),
        None,
    )
