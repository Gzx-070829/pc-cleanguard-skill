"""Static metadata catalog for external tools; never discovers or runs tools."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

from ..core.models import RiskLevel


_TOOL_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")


class ExternalToolType(str, Enum):
    """Supported adapter categories, not executable implementations."""

    OFFICIAL_UNINSTALLER = "official_uninstaller"
    WINGET = "winget"
    VENDOR_CLEANUP_TOOL = "vendor_cleanup_tool"
    TRUSTED_THIRD_PARTY_UNINSTALLER = "trusted_third_party_uninstaller"


@dataclass(frozen=True, slots=True)
class ExternalToolRecord:
    """Reviewable metadata required before a tool can be planned."""

    tool_id: str
    name: str
    tool_type: ExternalToolType
    official_website: str
    license: str
    supported_actions: Tuple[str, ...]
    risk_level: RiskLevel
    required_user_confirmation: bool

    def __post_init__(self) -> None:
        if not isinstance(self.tool_id, str) or not _TOOL_ID.fullmatch(self.tool_id):
            raise ValueError("tool_id must use lowercase letters, digits, _ or -")
        for field_name, value in (
            ("name", self.name),
            ("official_website", self.official_website),
            ("license", self.license),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not self.official_website.startswith("https://"):
            raise ValueError("official_website must use https")
        if not isinstance(self.tool_type, ExternalToolType):
            raise TypeError("tool_type must be an ExternalToolType")
        if not isinstance(self.risk_level, RiskLevel):
            raise TypeError("risk_level must be a RiskLevel")
        if not isinstance(self.required_user_confirmation, bool):
            raise TypeError("required_user_confirmation must be a bool")
        actions = tuple(self.supported_actions)
        if not actions or any(
            not isinstance(action, str) or not action.strip() for action in actions
        ):
            raise ValueError("supported_actions must contain non-empty strings")
        if len(set(actions)) != len(actions):
            raise ValueError("supported_actions must not contain duplicates")
        object.__setattr__(self, "supported_actions", actions)

    def to_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "tool_type": self.tool_type.value,
            "official_website": self.official_website,
            "license": self.license,
            "supported_actions": list(self.supported_actions),
            "risk_level": self.risk_level.value,
            "required_user_confirmation": self.required_user_confirmation,
        }


@dataclass(frozen=True, slots=True)
class ExternalToolCatalog:
    """Explicit tool records supplied by configuration or a trusted caller."""

    records: Tuple[ExternalToolRecord, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        records = tuple(self.records)
        if not all(isinstance(record, ExternalToolRecord) for record in records):
            raise TypeError("records must contain ExternalToolRecord objects")
        ids = [record.tool_id for record in records]
        if len(set(ids)) != len(ids):
            raise ValueError("tool catalog contains duplicate tool_id values")
        object.__setattr__(self, "records", records)

    def get(self, tool_id: str) -> Optional[ExternalToolRecord]:
        if not isinstance(tool_id, str):
            raise TypeError("tool_id must be a string")
        return next((record for record in self.records if record.tool_id == tool_id), None)

    def require(self, tool_id: str) -> ExternalToolRecord:
        record = self.get(tool_id)
        if record is None:
            raise ValueError("tool is not present in the explicit catalog")
        return record

    def to_dict(self) -> dict:
        return {"records": [record.to_dict() for record in self.records]}
