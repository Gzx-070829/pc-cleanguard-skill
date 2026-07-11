"""Controlled L1 file cleanup with preview, confirmation, and audit gates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Tuple

from ..core.models import RiskLevel
from ..pipeline.input_loader import (
    _validated_explicit_local_path,
    load_scan_json_file,
)
from ..protection import classify_developer_path
from .confirmation import L1_ALLOWED_CATEGORIES, CleanupConfirmation
from .execution_result import (
    CleanupExecutionAuditEvent,
    CleanupExecutionItem,
    CleanupExecutionReport,
)
from .junk_rules import JunkCategory, match_junk_rule
from .junk_scanner import JunkCandidate


_PREVIEW_FIELDS = {
    "total_candidates",
    "total_reclaimable_bytes",
    "by_category",
    "blocked_candidates",
    "requires_confirmation",
    "top_candidates",
    "warnings",
    "dry_run_only",
    "execution_authorized",
}
_CANDIDATE_FIELDS = {
    "path",
    "category",
    "size_bytes",
    "reason",
    "evidence",
    "confidence",
    "risk_level",
    "execution_level",
    "requires_user_confirmation",
    "dry_run_only",
    "execution_authorized",
}


def load_cleanup_preview_json(path: str | Path) -> dict:
    """Load and validate exactly one explicit PR14 preview JSON file."""

    return validate_cleanup_preview(load_scan_json_file(path))


def validate_cleanup_preview(preview: dict) -> dict:
    if not isinstance(preview, dict) or set(preview) != _PREVIEW_FIELDS:
        raise ValueError("input must match the PR14 cleanup preview structure")
    if preview.get("dry_run_only") is not True:
        raise ValueError("cleanup preview must have dry_run_only=true")
    if preview.get("execution_authorized") is not False:
        raise ValueError("cleanup preview cannot authorize execution")
    if not isinstance(preview.get("top_candidates"), list):
        raise TypeError("cleanup preview top_candidates must be a list")
    if not isinstance(preview.get("by_category"), dict):
        raise TypeError("cleanup preview by_category must be a dict")
    if not isinstance(preview.get("blocked_candidates"), list):
        raise TypeError("cleanup preview blocked_candidates must be a list")
    if not isinstance(preview.get("warnings"), list):
        raise TypeError("cleanup preview warnings must be a list")
    for field_name in ("total_candidates", "total_reclaimable_bytes"):
        value = preview.get(field_name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{field_name} must be a non-negative integer")
    if not isinstance(preview.get("requires_confirmation"), bool):
        raise TypeError("requires_confirmation must be a bool")
    _preview_candidates(preview)
    return preview


def _preview_candidates(preview: dict) -> Tuple[JunkCandidate, ...]:
    candidates = []
    for data in preview["top_candidates"]:
        if not isinstance(data, dict) or set(data) != _CANDIDATE_FIELDS:
            raise ValueError("preview candidate fields do not match PR14")
        try:
            candidate = JunkCandidate(
                path=data["path"],
                category=JunkCategory(data["category"]),
                size_bytes=data["size_bytes"],
                reason=data["reason"],
                evidence=tuple(data["evidence"]),
                confidence=data["confidence"],
                risk_level=RiskLevel(data["risk_level"]),
                execution_level=data["execution_level"],
                requires_user_confirmation=data["requires_user_confirmation"],
                dry_run_only=data["dry_run_only"],
                execution_authorized=data["execution_authorized"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("invalid PR14 junk candidate") from error
        candidates.append(candidate)
    return tuple(candidates)


def preflight_cleanup_artifacts(
    result_path: str | Path,
    audit_path: str | Path,
    *,
    explicit_overwrite: bool = False,
) -> tuple[Path, Path]:
    """Validate both output paths before any confirmed file change."""

    if not isinstance(explicit_overwrite, bool):
        raise TypeError("explicit_overwrite must be a bool")
    result = _validated_explicit_local_path(result_path, allowed_suffixes={".json"})
    audit = _validated_explicit_local_path(audit_path, allowed_suffixes={".jsonl"})
    if result.resolve(strict=False) == audit.resolve(strict=False):
        raise ValueError("result and audit paths must be different")
    if not explicit_overwrite:
        for path in (result, audit):
            if path.exists():
                raise FileExistsError(f"output already exists: {path}")
    return result, audit


def write_cleanup_execution_report(
    path: str | Path,
    report: CleanupExecutionReport,
    *,
    explicit_overwrite: bool = False,
) -> None:
    if not isinstance(report, CleanupExecutionReport):
        raise TypeError("report must be a CleanupExecutionReport")
    destination = _validated_explicit_local_path(path, allowed_suffixes={".json"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if explicit_overwrite else "x"
    with destination.open(mode, encoding="utf-8", newline="\n") as stream:
        json.dump(report.to_dict(), stream, ensure_ascii=False, indent=2)
        stream.write("\n")


class CleanupExecutor:
    """Execute only confirmed L1 file candidates and audit every decision."""

    def __init__(self, user_code_roots: Iterable[str | Path] = ()) -> None:
        if isinstance(user_code_roots, (str, Path)):
            raise TypeError("user_code_roots must contain explicit roots")
        supplied = tuple(user_code_roots)
        if any(
            not isinstance(root, (str, Path)) or not str(root).strip()
            for root in supplied
        ):
            raise ValueError("user code roots must be non-empty local paths")
        self._user_code_roots = tuple(
            Path(root).resolve(strict=False) for root in supplied
        )

    def execute(
        self,
        preview: dict,
        confirmation: CleanupConfirmation,
        *,
        audit_path: str | Path,
        explicit_overwrite: bool = False,
    ) -> CleanupExecutionReport:
        validate_cleanup_preview(preview)
        if not isinstance(confirmation, CleanupConfirmation):
            raise TypeError("confirmation must be CleanupConfirmation")
        if not isinstance(explicit_overwrite, bool):
            raise TypeError("explicit_overwrite must be a bool")
        destination = _validated_explicit_local_path(
            audit_path, allowed_suffixes={".jsonl"}
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        mode = "w" if explicit_overwrite else "x"
        results = []
        with destination.open(mode, encoding="utf-8", newline="\n") as audit_stream:
            for candidate in _preview_candidates(preview):
                item = self._process(candidate, confirmation)
                results.append(item)
                audit_stream.write(
                    json.dumps(
                        item.audit_event.to_dict(),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                audit_stream.flush()
        summary = self._summary(results)
        return CleanupExecutionReport(
            confirmed=confirmation.confirmed,
            allow_roots=tuple(str(root) for root in confirmation.allow_roots),
            results=tuple(results),
            audit_path=str(destination),
            summary=summary,
            mode="confirmed_l1" if confirmation.confirmed else "dry_run",
        )

    def _process(
        self,
        candidate: JunkCandidate,
        confirmation: CleanupConfirmation,
    ) -> CleanupExecutionItem:
        base_evidence = tuple(candidate.evidence)
        if candidate.category not in L1_ALLOWED_CATEGORIES:
            return self._item(
                candidate,
                confirmation,
                action="skip",
                status="skipped",
                reason="category is outside the PR15 L1 allowlist",
                bytes_reclaimed=0,
                evidence=(
                    *base_evidence,
                    {
                        "source": "l1_allowlist",
                        "fact": "candidate category is not temp, cache, or log",
                    },
                ),
            )
        developer_decision = classify_developer_path(
            candidate.path,
            user_code_roots=self._user_code_roots,
        )
        if developer_decision.protected:
            return self._item(
                candidate,
                confirmation,
                action="delete_file",
                status="blocked",
                reason=developer_decision.reason,
                bytes_reclaimed=0,
                evidence=(*base_evidence, *developer_decision.evidence),
            )
        decision = confirmation.evaluate(candidate.path)
        if not decision.allowed:
            return self._item(
                candidate,
                confirmation,
                action="delete_file",
                status="blocked",
                reason=decision.reason,
                bytes_reclaimed=0,
                evidence=(*base_evidence, *decision.evidence),
            )
        path = Path(candidate.path)
        runtime_rule = match_junk_rule(path)
        if runtime_rule is None or runtime_rule.category is not candidate.category:
            return self._item(
                candidate,
                confirmation,
                action="delete_file",
                status="blocked",
                reason="current path metadata no longer matches the preview category",
                bytes_reclaimed=0,
                evidence=(
                    *base_evidence,
                    {
                        "source": "runtime_revalidation",
                        "fact": "current category does not match preview metadata",
                    },
                ),
            )
        if not confirmation.confirmed:
            return self._item(
                candidate,
                confirmation,
                action="delete_file",
                status="would_clean",
                reason="explicit confirmation is absent; no file change was performed",
                bytes_reclaimed=0,
                evidence=(
                    *base_evidence,
                    *decision.evidence,
                    {"source": "confirmation", "fact": "confirm flag is false"},
                ),
            )
        try:
            current_size = max(0, int(path.stat(follow_symlinks=False).st_size))
            path.unlink()
        except OSError as error:
            return self._item(
                candidate,
                confirmation,
                action="delete_file",
                status="failed",
                reason=f"bounded L1 file cleanup failed: {error}",
                bytes_reclaimed=0,
                evidence=(
                    *base_evidence,
                    *decision.evidence,
                    {"source": "execution", "fact": "file operation failed"},
                ),
            )
        return self._item(
            candidate,
            confirmation,
            action="delete_file",
            status="cleaned",
            reason="confirmed L1 file cleanup completed",
            bytes_reclaimed=current_size,
            evidence=(
                *base_evidence,
                *decision.evidence,
                {
                    "source": "confirmation",
                    "fact": "confirm flag is true and all L1 gates passed",
                },
            ),
        )

    @staticmethod
    def _item(
        candidate: JunkCandidate,
        confirmation: CleanupConfirmation,
        *,
        action: str,
        status: str,
        reason: str,
        bytes_reclaimed: int,
        evidence: tuple[dict, ...],
    ) -> CleanupExecutionItem:
        method = (
            "pathlib_unlink"
            if confirmation.confirmed and status in {"cleaned", "failed"}
            else "none"
        )
        event = CleanupExecutionAuditEvent(
            path=candidate.path,
            category=candidate.category,
            action=action,
            status=status,
            reason=reason,
            bytes_reclaimed=bytes_reclaimed,
            evidence=evidence,
            confirmed=confirmation.confirmed,
            dry_run=not confirmation.confirmed,
            execution_method=method,
        )
        return CleanupExecutionItem(
            path=candidate.path,
            category=candidate.category,
            action=action,
            status=status,
            reason=reason,
            bytes_reclaimed=bytes_reclaimed,
            evidence=evidence,
            audit_event=event,
        )

    @staticmethod
    def _summary(results: list[CleanupExecutionItem]) -> dict:
        statuses = ("would_clean", "cleaned", "blocked", "skipped", "failed")
        return {
            "total_results": len(results),
            **{
                status: sum(item.status == status for item in results)
                for status in statuses
            },
            "bytes_reclaimed": sum(item.bytes_reclaimed for item in results),
            "execution_performed": any(item.status == "cleaned" for item in results),
        }
