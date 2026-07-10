"""Structured external-tool recommendations that never authorize execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from ..core.models import RiskLevel
from .catalog import ExternalToolType


READ_ONLY_EXECUTION_LEVEL = "LEVEL_0_READ_ONLY"


def validated_evidence(evidence: Tuple[dict, ...] | list[dict]) -> Tuple[dict, ...]:
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
class ExternalToolRecommendation:
    """A user-confirmed, Level 0 suggestion with no invocation material."""

    tool_id: str
    tool_name: str
    tool_type: ExternalToolType
    matched_reason: str
    matched_target_ids: Tuple[str, ...]
    evidence: Tuple[dict, ...]
    confidence: float
    risk_level: RiskLevel
    execution_level: str
    requires_user_confirmation: bool
    plan_only: bool
    blocked_if_untrusted: bool
    trusted: bool
    blocked: bool
    notes_for_ai: str
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        for field_name, value in (
            ("tool_id", self.tool_id),
            ("tool_name", self.tool_name),
            ("matched_reason", self.matched_reason),
            ("notes_for_ai", self.notes_for_ai),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not isinstance(self.tool_type, ExternalToolType):
            raise TypeError("tool_type must be an ExternalToolType")
        if not isinstance(self.risk_level, RiskLevel):
            raise TypeError("risk_level must be a RiskLevel")
        targets = tuple(self.matched_target_ids)
        if not targets or any(
            not isinstance(target_id, str) or not target_id.strip()
            for target_id in targets
        ):
            raise ValueError("matched_target_ids must contain non-empty strings")
        if len(set(targets)) != len(targets):
            raise ValueError("matched_target_ids must not contain duplicates")
        if (
            not isinstance(self.confidence, (int, float))
            or isinstance(self.confidence, bool)
            or not 0.0 <= float(self.confidence) <= 1.0
        ):
            raise ValueError("confidence must be between 0 and 1")
        if self.execution_level != READ_ONLY_EXECUTION_LEVEL:
            raise ValueError("recommendations are restricted to Level 0")
        if self.requires_user_confirmation is not True:
            raise ValueError("recommendations always require user confirmation")
        if self.plan_only is not True or self.execution_authorized is not False:
            raise ValueError("recommendations cannot authorize execution")
        if self.blocked_if_untrusted is not True:
            raise ValueError("recommendations must be blocked if untrusted")
        if self.blocked != (not self.trusted):
            raise ValueError("blocked state must match the trust decision")
        object.__setattr__(self, "matched_target_ids", targets)
        object.__setattr__(self, "evidence", validated_evidence(self.evidence))
        object.__setattr__(self, "confidence", float(self.confidence))

    def to_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "tool_type": self.tool_type.value,
            "matched_reason": self.matched_reason,
            "matched_target_ids": list(self.matched_target_ids),
            "evidence": [dict(item) for item in self.evidence],
            "confidence": self.confidence,
            "risk_level": self.risk_level.value,
            "execution_level": READ_ONLY_EXECUTION_LEVEL,
            "requires_user_confirmation": True,
            "plan_only": True,
            "blocked_if_untrusted": True,
            "trusted": self.trusted,
            "blocked": self.blocked,
            "notes_for_ai": self.notes_for_ai,
            "execution_authorized": False,
        }
