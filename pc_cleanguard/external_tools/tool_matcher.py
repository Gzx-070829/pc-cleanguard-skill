"""Evidence-based matching between cleanup candidates and cataloged tool types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .catalog import ExternalToolRecord, ExternalToolType
from .recommendation import validated_evidence


@dataclass(frozen=True, slots=True)
class ToolMatch:
    matched_reason: str
    target_ids: Tuple[str, ...]
    evidence: Tuple[dict, ...]
    confidence: float


_ACTION_COMPATIBILITY = {
    ExternalToolType.OFFICIAL_UNINSTALLER: {"standard_uninstall"},
    ExternalToolType.WINGET: {"package_uninstall", "standard_uninstall"},
    ExternalToolType.VENDOR_CLEANUP_TOOL: {"vendor_cleanup"},
    ExternalToolType.TRUSTED_THIRD_PARTY_UNINSTALLER: {
        "review_uninstall",
        "standard_uninstall",
    },
}


class ToolMatcher:
    """Match metadata only; it does not inspect the system or run a tool."""

    def match(
        self,
        record: ExternalToolRecord,
        cleanup_plan: dict,
        *,
        governance_decisions: list[dict] | tuple[dict, ...] = (),
        installed_apps: list[dict] | tuple[dict, ...] = (),
    ) -> ToolMatch | None:
        if not isinstance(record, ExternalToolRecord):
            raise TypeError("record must be an ExternalToolRecord")
        if not isinstance(cleanup_plan, dict):
            raise TypeError("cleanup_plan must be a dict")
        if not _ACTION_COMPATIBILITY[record.tool_type].intersection(
            record.supported_actions
        ):
            return None
        steps = cleanup_plan.get("steps")
        if not isinstance(steps, list):
            raise ValueError("cleanup_plan.steps must be a list")
        decisions = self._rows(governance_decisions, "governance_decisions")
        apps = self._rows(installed_apps, "installed_apps")
        decision_by_target = {
            item.get("target_id"): item
            for item in decisions
            if isinstance(item.get("target_id"), str)
        }
        app_by_target = {
            item.get("target_id"): item
            for item in apps
            if isinstance(item.get("target_id"), str)
        }

        eligible: list[dict] = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            target_id = step.get("target_id")
            decision = decision_by_target.get(target_id, {})
            if (
                step.get("blocked") is True
                or step.get("classification") == "BLOCK"
                or step.get("review_action") != "REVIEW_REMOVAL_CANDIDATE"
                or decision.get("blocked_by_hard_rule") is True
                or decision.get("permission_level") == "LEVEL_5_FORBIDDEN"
                or decision.get("classification") == "BLOCK"
            ):
                continue
            if isinstance(target_id, str) and target_id.strip():
                eligible.append(step)

        if record.tool_type is ExternalToolType.WINGET:
            eligible = [
                step
                for step in eligible
                if self._nonempty(app_by_target.get(step["target_id"], {}).get("package_id"))
            ]
            reason = "package metadata includes a package ID suitable for a winget review"
            confidence = 0.85
        elif record.tool_type is ExternalToolType.VENDOR_CLEANUP_TOOL:
            eligible = [
                step
                for step in eligible
                if app_by_target.get(step["target_id"], {}).get(
                    "vendor_cleanup_tool_id"
                )
                == record.tool_id
            ]
            reason = "installed-app metadata explicitly names this vendor cleanup tool"
            confidence = 0.80
        elif record.tool_type is ExternalToolType.OFFICIAL_UNINSTALLER:
            reason = "official uninstaller is the preferred review path for a software candidate"
            confidence = 0.90
        else:
            reason = "trusted third-party uninstaller is available for secondary review only"
            confidence = 0.55

        if not eligible:
            return None
        evidence: list[dict] = [
            {
                "source": "cleanup_plan",
                "fact": f"matched {len(eligible)} unblocked removal candidate(s)",
            }
        ]
        for step in eligible:
            step_evidence = step.get("evidence")
            if isinstance(step_evidence, list):
                evidence.extend(item for item in step_evidence if isinstance(item, dict))
        if record.tool_type is ExternalToolType.WINGET:
            evidence.append(
                {"source": "installed_app_metadata", "fact": "package ID is present"}
            )
        elif record.tool_type is ExternalToolType.VENDOR_CLEANUP_TOOL:
            evidence.append(
                {
                    "source": "installed_app_metadata",
                    "fact": "vendor tool association is explicit",
                }
            )
        return ToolMatch(
            matched_reason=reason,
            target_ids=tuple(step["target_id"] for step in eligible),
            evidence=validated_evidence(evidence),
            confidence=confidence,
        )

    @staticmethod
    def _rows(value: list[dict] | tuple[dict, ...], name: str) -> tuple[dict, ...]:
        if not isinstance(value, (list, tuple)) or any(
            not isinstance(item, dict) for item in value
        ):
            raise TypeError(f"{name} must contain dict objects")
        return tuple(value)

    @staticmethod
    def _nonempty(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip())
