"""Safe, explicit demo experiences for PC CleanGuard."""

from .cleanup_demo import (
    init_cleanup_demo,
    quickstart_cleanup_demo,
    run_cleanup_demo,
)
from .acceptance import run_demo_acceptance
from .workspace import (
    SYNTHETIC_MANIFEST_NAME,
    create_synthetic_workspace,
    dedicated_synthetic_temp_root,
    verify_synthetic_workspace,
)

__all__ = [
    "init_cleanup_demo", "quickstart_cleanup_demo", "run_cleanup_demo",
    "run_demo_acceptance", "SYNTHETIC_MANIFEST_NAME",
    "create_synthetic_workspace", "dedicated_synthetic_temp_root",
    "verify_synthetic_workspace",
]
