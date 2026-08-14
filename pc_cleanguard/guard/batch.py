"""Maximum-restriction aggregation for multi-action bundles."""

from __future__ import annotations

from .models import (
    ActionBundle,
    BatchDecision,
    Disposition,
    GuardContext,
    Requirement,
)


def evaluate_bundle(bundle: ActionBundle, context: GuardContext, *, guard=None) -> BatchDecision:
    if not isinstance(bundle, ActionBundle):
        bundle = ActionBundle.from_dict(bundle)
    if not isinstance(context, GuardContext):
        context = GuardContext.from_dict(context)
    if guard is None:
        from .guard import Guard

        guard = Guard()
    decisions = tuple(guard.evaluate(action, context) for action in bundle.actions)
    disposition = max((item.disposition for item in decisions), key=lambda item: item.rank)
    risk_level = max((item.risk_level for item in decisions), key=lambda item: item.rank)
    requirements = tuple(
        sorted(
            {requirement for item in decisions for requirement in item.requirements},
            key=lambda item: item.value,
        )
    )
    blocked = tuple(
        item.request_id for item in decisions if item.disposition is Disposition.BLOCK
    )
    # Rollback runs in reverse dependency order after a partial external failure.
    rollback_order = tuple(reversed(bundle.dependency_order))
    return BatchDecision(
        bundle_id=bundle.bundle_id,
        disposition=disposition,
        risk_level=risk_level,
        requirements=requirements,
        child_decisions=decisions,
        blocked_action_ids=blocked,
        dependency_order=bundle.dependency_order,
        rollback_order=rollback_order,
        execution_authorized=False,
    )

