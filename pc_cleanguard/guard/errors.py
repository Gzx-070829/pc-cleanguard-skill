"""Fail-closed exceptions exposed by the deterministic Guard boundary."""


class GuardError(Exception):
    """Base class for expected Guard failures."""


class GuardInputError(GuardError, ValueError):
    """A caller supplied an invalid contract."""


class PolicyBlockedError(GuardError):
    """Policy issued a hard block that no consent can override."""


class RequirementPendingError(GuardError):
    """One or more deterministic requirements remain unsatisfied."""


class ConsentValidationError(RequirementPendingError):
    """A consent grant is absent, invalid, stale, or too weak."""


class PreconditionValidationError(RequirementPendingError):
    """Current target facts no longer satisfy the evaluated snapshot."""


class RollbackValidationError(RequirementPendingError):
    """A required rollback contract is absent or insufficient."""


class AuditIntegrityError(GuardError):
    """A hash-chained audit record is malformed or inconsistent."""

