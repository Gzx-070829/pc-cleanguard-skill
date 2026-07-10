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
from .confirmation import (
    L1_ALLOWED_CATEGORIES,
    CleanupConfirmation,
    ConfirmationDecision,
)
from .execution_result import (
    L1_EXECUTION_LEVEL,
    CleanupExecutionAuditEvent,
    CleanupExecutionItem,
    CleanupExecutionReport,
)
from .executor import (
    CleanupExecutor,
    load_cleanup_preview_json,
    preflight_cleanup_artifacts,
    validate_cleanup_preview,
    write_cleanup_execution_report,
)
from .reporting import (
    build_cleanup_summary,
    render_cleanup_report_markdown,
    write_cleanup_report_markdown,
)

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
    "L1_ALLOWED_CATEGORIES",
    "CleanupConfirmation",
    "ConfirmationDecision",
    "L1_EXECUTION_LEVEL",
    "CleanupExecutionAuditEvent",
    "CleanupExecutionItem",
    "CleanupExecutionReport",
    "CleanupExecutor",
    "load_cleanup_preview_json",
    "preflight_cleanup_artifacts",
    "validate_cleanup_preview",
    "write_cleanup_execution_report",
    "build_cleanup_summary",
    "render_cleanup_report_markdown",
    "write_cleanup_report_markdown",
    "default_junk_rules",
    "match_junk_rule",
]
