"""Explicit allowlist policy for non-executing external-tool planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .catalog import ExternalToolRecord, ExternalToolType


@dataclass(frozen=True, slots=True)
class ToolTrustDecision:
    """A policy result; it never grants authority to launch a tool."""

    tool_id: str
    trusted: bool
    reason: str
    evidence: Tuple[dict, ...]

    def to_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "trusted": self.trusted,
            "reason": self.reason,
            "evidence": [dict(item) for item in self.evidence],
            "execution_authorized": False,
        }


@dataclass(frozen=True, slots=True)
class ToolTrustPolicy:
    """Trust only exact allowlisted IDs and approved adapter categories."""

    allowlisted_tool_ids: Tuple[str, ...] = field(default_factory=tuple)
    allowed_tool_types: Tuple[ExternalToolType, ...] = field(
        default_factory=lambda: tuple(ExternalToolType)
    )

    def __post_init__(self) -> None:
        tool_ids = tuple(self.allowlisted_tool_ids)
        if any(not isinstance(tool_id, str) or not tool_id.strip() for tool_id in tool_ids):
            raise ValueError("allowlisted_tool_ids must contain non-empty strings")
        if len(set(tool_ids)) != len(tool_ids):
            raise ValueError("allowlisted_tool_ids must not contain duplicates")
        types = tuple(self.allowed_tool_types)
        if not types or not all(isinstance(tool_type, ExternalToolType) for tool_type in types):
            raise ValueError("allowed_tool_types must contain ExternalToolType values")
        if len(set(types)) != len(types):
            raise ValueError("allowed_tool_types must not contain duplicates")
        object.__setattr__(self, "allowlisted_tool_ids", tool_ids)
        object.__setattr__(self, "allowed_tool_types", types)

    def evaluate(self, record: ExternalToolRecord) -> ToolTrustDecision:
        if not isinstance(record, ExternalToolRecord):
            raise TypeError("record must be an ExternalToolRecord")
        if record.tool_type not in self.allowed_tool_types:
            return ToolTrustDecision(
                tool_id=record.tool_id,
                trusted=False,
                reason="tool type is not allowed by policy",
                evidence=(
                    {
                        "source": "tool_trust_policy",
                        "fact": "tool type is outside the approved adapter categories",
                    },
                ),
            )
        if record.tool_id not in self.allowlisted_tool_ids:
            return ToolTrustDecision(
                tool_id=record.tool_id,
                trusted=False,
                reason="tool is not on the explicit allowlist",
                evidence=(
                    {
                        "source": "tool_trust_policy",
                        "fact": "exact tool ID is absent from the allowlist",
                    },
                ),
            )
        return ToolTrustDecision(
            tool_id=record.tool_id,
            trusted=True,
            reason="tool is explicitly allowlisted for planning only",
            evidence=(
                {
                    "source": "tool_trust_policy",
                    "fact": "exact tool ID and type are allowlisted",
                },
            ),
        )
