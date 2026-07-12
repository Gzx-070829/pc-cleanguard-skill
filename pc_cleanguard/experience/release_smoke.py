"""Read-only release asset checks for the v0.3.0 public preview."""

from __future__ import annotations

from pathlib import Path

from .. import __version__
from ..reputation import load_seed_records


def run_release_smoke_check() -> dict:
    root = Path(__file__).resolve().parents[2]
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""
    showcase = root / "examples" / "showcase" / "v0.3"
    showcase_files = {
        "README.md", "START_HERE.md", "user_summary.md", "machine_summary.json",
        "cleanup_report.md", "pup_insight.md", "audit.jsonl", "quarantine_manifest.json",
    }
    seeds_ok = False
    try:
        seeds_ok = len(load_seed_records(root / "examples/reputation/seed_records.zh-CN.json")) >= 20
    except (OSError, TypeError, ValueError):
        seeds_ok = False
    templates = root / ".github" / "ISSUE_TEMPLATE"
    checks = {
        "version_0_3_0": __version__ == "0.3.0",
        "readme_trial_command": "trial run --root .pcg-demo --output .pcg-trial" in readme,
        "readme_restore_command": "quarantine restore --root .pcg-quarantine" in readme,
        "showcase_complete": showcase.is_dir() and all((showcase / name).is_file() for name in showcase_files),
        "seed_records_load": seeds_ok,
        "user_trial_doc": (root / "docs/v0.3-user-trial-script.md").is_file(),
        "public_preview_doc": (root / "docs/v0.3-public-preview.md").is_file(),
        "release_checklist": (root / "docs/release-v0.3.0-checklist.md").is_file(),
        "trial_feedback_template": (templates / "trial_experience_feedback.yml").is_file(),
        "pup_feedback_template": (templates / "pup_reputation_feedback.yml").is_file(),
    }
    return {
        "version": __version__,
        "checks": checks,
        "passed": all(checks.values()),
        "execution_performed": False,
        "network_accessed": False,
    }
