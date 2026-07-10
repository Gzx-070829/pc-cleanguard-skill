"""External-tool planning foundation for v0.2 PR12; never executes tools."""

from .catalog import ExternalToolCatalog, ExternalToolRecord, ExternalToolType
from .invocation_plan import (
    ExternalToolInvocationPlan,
    build_external_tool_invocation_plan,
)
from .trust_policy import ToolTrustDecision, ToolTrustPolicy

__all__ = [
    "ExternalToolCatalog",
    "ExternalToolInvocationPlan",
    "ExternalToolRecord",
    "ExternalToolType",
    "ToolTrustDecision",
    "ToolTrustPolicy",
    "build_external_tool_invocation_plan",
]
