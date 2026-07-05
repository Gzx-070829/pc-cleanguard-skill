"""Helpers for building synthetic policy targets."""

from typing import Any

from pc_cleanguard.core.models import GovernanceTarget, ObjectType


def software_target(name: str, **overrides: Any) -> GovernanceTarget:
    values = {
        "target_id": f"software:{name.casefold().replace(' ', '-')}",
        "object_type": ObjectType.SOFTWARE,
        "name": name,
    }
    values.update(overrides)
    return GovernanceTarget(**values)
