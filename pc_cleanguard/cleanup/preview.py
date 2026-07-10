"""Build a JSON-safe cleanup preview from metadata-only scan results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .junk_rules import JUNK_CATEGORIES
from .junk_scanner import BlockedCandidate, JunkCandidate, JunkScanResult


@dataclass(frozen=True, slots=True)
class CleanupPreview:
    """A dry-run summary that cannot authorize cleanup execution."""

    total_candidates: int
    total_reclaimable_bytes: int
    by_category: dict
    blocked_candidates: Tuple[BlockedCandidate, ...]
    requires_confirmation: bool
    top_candidates: Tuple[JunkCandidate, ...]
    warnings: Tuple[str, ...]
    dry_run_only: bool = True
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        for field_name, value in (
            ("total_candidates", self.total_candidates),
            ("total_reclaimable_bytes", self.total_reclaimable_bytes),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if not isinstance(self.by_category, dict):
            raise TypeError("by_category must be a dict")
        if not all(
            isinstance(item, BlockedCandidate) for item in self.blocked_candidates
        ):
            raise TypeError("blocked_candidates must contain BlockedCandidate objects")
        if not all(isinstance(item, JunkCandidate) for item in self.top_candidates):
            raise TypeError("top_candidates must contain JunkCandidate objects")
        if not all(isinstance(item, str) and item for item in self.warnings):
            raise ValueError("warnings must contain non-empty strings")
        if not isinstance(self.requires_confirmation, bool):
            raise TypeError("requires_confirmation must be a bool")
        if self.dry_run_only is not True or self.execution_authorized is not False:
            raise ValueError("cleanup previews cannot authorize execution")

    def to_dict(self) -> dict:
        return {
            "total_candidates": self.total_candidates,
            "total_reclaimable_bytes": self.total_reclaimable_bytes,
            "by_category": {
                category: dict(summary)
                for category, summary in self.by_category.items()
            },
            "blocked_candidates": [
                item.to_dict() for item in self.blocked_candidates
            ],
            "requires_confirmation": self.requires_confirmation,
            "top_candidates": [item.to_dict() for item in self.top_candidates],
            "warnings": list(self.warnings),
            "dry_run_only": True,
            "execution_authorized": False,
        }


def build_cleanup_preview(
    scan_result: JunkScanResult,
    *,
    top_limit: int = 20,
) -> CleanupPreview:
    """Summarize candidates and protected paths without changing the system."""

    if not isinstance(scan_result, JunkScanResult):
        raise TypeError("scan_result must be a JunkScanResult")
    if not isinstance(top_limit, int) or isinstance(top_limit, bool) or top_limit <= 0:
        raise ValueError("top_limit must be a positive integer")
    category_summary = {
        category: {"count": 0, "size_bytes": 0} for category in JUNK_CATEGORIES
    }
    for candidate in scan_result.candidates:
        summary = category_summary[candidate.category.value]
        summary["count"] += 1
        summary["size_bytes"] += candidate.size_bytes
    ordered = tuple(
        sorted(
            scan_result.candidates,
            key=lambda item: (-item.size_bytes, item.path.casefold()),
        )
    )
    warnings = list(scan_result.warnings)
    if len(ordered) > top_limit:
        warnings.append(
            f"top candidate limit applied; showing {top_limit} of {len(ordered)}"
        )
    return CleanupPreview(
        total_candidates=len(scan_result.candidates),
        total_reclaimable_bytes=sum(
            candidate.size_bytes for candidate in scan_result.candidates
        ),
        by_category=category_summary,
        blocked_candidates=scan_result.blocked_candidates,
        requires_confirmation=bool(scan_result.candidates),
        top_candidates=ordered[:top_limit],
        warnings=tuple(warnings),
        dry_run_only=True,
        execution_authorized=False,
    )
