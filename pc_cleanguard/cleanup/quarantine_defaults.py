"""Stable default location for recoverable cleanup quarantine."""

from pathlib import Path


DEFAULT_QUARANTINE_NAME = ".pcg-quarantine"


def get_default_quarantine_root(base_path=None) -> Path:
    base = Path.cwd() if base_path is None else Path(base_path)
    return (base.resolve(strict=False) / DEFAULT_QUARANTINE_NAME).resolve(strict=False)
