"""Quarantine-specific failures without destructive recovery behavior."""


class QuarantineError(RuntimeError):
    pass


class QuarantineIntegrityError(QuarantineError):
    pass
