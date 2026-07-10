"""Recommend trusted external-tool review paths without executing anything."""

from __future__ import annotations

from typing import Tuple

from .catalog import ExternalToolCatalog, ExternalToolType
from .recommendation import (
    READ_ONLY_EXECUTION_LEVEL,
    ExternalToolRecommendation,
    validated_evidence,
)
from .tool_matcher import ToolMatcher
from .trust_policy import ToolTrustPolicy


_AI_NOTES = {
    ExternalToolType.OFFICIAL_UNINSTALLER: (
        "Show the official uninstaller as a review option; do not launch it."
    ),
    ExternalToolType.WINGET: (
        "Show the package-manager option only; do not generate or run a command."
    ),
    ExternalToolType.VENDOR_CLEANUP_TOOL: (
        "Show the explicitly associated vendor tool; never download it automatically."
    ),
    ExternalToolType.TRUSTED_THIRD_PARTY_UNINSTALLER: (
        "Present this only as a secondary review option, never as the default."
    ),
}


class ToolRecommender:
    """Combine metadata matching with explicit allowlist trust decisions."""

    def __init__(
        self,
        catalog: ExternalToolCatalog,
        trust_policy: ToolTrustPolicy,
        matcher: ToolMatcher | None = None,
    ) -> None:
        if not isinstance(catalog, ExternalToolCatalog):
            raise TypeError("catalog must be an ExternalToolCatalog")
        if not isinstance(trust_policy, ToolTrustPolicy):
            raise TypeError("trust_policy must be a ToolTrustPolicy")
        if matcher is not None and not isinstance(matcher, ToolMatcher):
            raise TypeError("matcher must be a ToolMatcher")
        self._catalog = catalog
        self._trust_policy = trust_policy
        self._matcher = matcher or ToolMatcher()

    def recommend(
        self,
        cleanup_plan: dict,
        *,
        governance_decisions: list[dict] | tuple[dict, ...] = (),
        evidence: list[dict] | tuple[dict, ...] = (),
        installed_apps: list[dict] | tuple[dict, ...] = (),
    ) -> Tuple[ExternalToolRecommendation, ...]:
        if not isinstance(cleanup_plan, dict):
            raise TypeError("cleanup_plan must be a dict")
        if (
            cleanup_plan.get("mode") != "plan_only"
            or cleanup_plan.get("execution_level") != READ_ONLY_EXECUTION_LEVEL
            or cleanup_plan.get("execution_authorized") is not False
        ):
            raise ValueError("cleanup_plan must remain a non-executing Level 0 plan")
        caller_evidence = self._optional_evidence(evidence)
        recommendations = []
        for record in self._catalog.records:
            match = self._matcher.match(
                record,
                cleanup_plan,
                governance_decisions=governance_decisions,
                installed_apps=installed_apps,
            )
            if match is None:
                continue
            trust = self._trust_policy.evaluate(record)
            notes = _AI_NOTES[record.tool_type]
            if not trust.trusted:
                notes += " This tool is untrusted and the recommendation is blocked."
            recommendations.append(
                ExternalToolRecommendation(
                    tool_id=record.tool_id,
                    tool_name=record.name,
                    tool_type=record.tool_type,
                    matched_reason=match.matched_reason,
                    matched_target_ids=match.target_ids,
                    evidence=(
                        *match.evidence,
                        *trust.evidence,
                        *caller_evidence,
                    ),
                    confidence=match.confidence,
                    risk_level=record.risk_level,
                    execution_level=READ_ONLY_EXECUTION_LEVEL,
                    requires_user_confirmation=True,
                    plan_only=True,
                    blocked_if_untrusted=True,
                    trusted=trust.trusted,
                    blocked=not trust.trusted,
                    notes_for_ai=notes,
                    execution_authorized=False,
                )
            )
        return tuple(recommendations)

    @staticmethod
    def _optional_evidence(
        evidence: list[dict] | tuple[dict, ...],
    ) -> tuple[dict, ...]:
        if not isinstance(evidence, (list, tuple)):
            raise TypeError("evidence must be a list or tuple")
        if not evidence:
            return ()
        return validated_evidence(evidence)
