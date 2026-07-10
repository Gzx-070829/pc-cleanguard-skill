"""Dry-run junk candidate scanning and cleanup preview contracts."""

from .junk_rules import (
    JUNK_CATEGORIES,
    JunkCategory,
    JunkRule,
    default_junk_rules,
    match_junk_rule,
)
from .junk_scanner import (
    BlockedCandidate,
    JunkCandidate,
    JunkScanner,
    JunkScanResult,
    ScanLimits,
)
from .preview import CleanupPreview, build_cleanup_preview

__all__ = [
    "JUNK_CATEGORIES",
    "JunkCategory",
    "JunkCandidate",
    "JunkRule",
    "JunkScanner",
    "JunkScanResult",
    "ScanLimits",
    "BlockedCandidate",
    "CleanupPreview",
    "build_cleanup_preview",
    "default_junk_rules",
    "match_junk_rule",
]
