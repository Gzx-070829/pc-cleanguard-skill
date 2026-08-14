"""Read-only release asset checks for the current public preview."""

from __future__ import annotations

from pathlib import Path

from .. import __version__
from ..reputation import load_seed_records


def run_release_smoke_check() -> dict:
    root = Path(__file__).resolve().parents[2]
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""
    showcase = root / "examples" / "showcase" / "v0.4.0"
    showcase_files = {
        "README.md", "START_HERE.md", "user_friendly_summary.md", "machine_summary.json",
        "persistence_chain.md", "persistence_chain_mermaid.md", "persistence_governance_plan.md",
        "agent_governance_preview.json", "evidence_coverage.md", "evidence_quality.md",
        "corroboration_summary.md", "no_match_report.md", "false_positive_feedback_template.md", "safety_notice.md",
    }
    seeds_ok = False
    try:
        seeds_ok = len(load_seed_records(root / "examples/reputation/seed_records.zh-CN.json")) >= 20
    except (OSError, TypeError, ValueError):
        seeds_ok = False
    templates = root / ".github" / "ISSUE_TEMPLATE"
    checks = {
        "version_0_4_2": __version__ == "0.4.2",
        "readme_trial_command": "trial run --root .pcg-demo --output .pcg-trial" in readme,
        "readme_restore_command": "quarantine restore --root .pcg-quarantine" in readme,
        "showcase_complete": showcase.is_dir() and all((showcase / name).is_file() for name in showcase_files),
        "seed_records_load": seeds_ok,
        "user_trial_doc": (root / "docs/v0.3-user-trial-script.md").is_file(),
        "final_ab_evaluation": (root / "docs/PC-CleanGuard-Final-AB-Evaluation.md").is_file(),
        "final_decision_record": (root / "docs/PC-CleanGuard-Final-Decision-Record.md").is_file(),
        "final_evaluation_summary": (root / "docs/PC-CleanGuard-Final-Evaluation-Summary.md").is_file(),
        "final_evidence_index": (root / "docs/final-evaluation-evidence-index.md").is_file(),
        "final_machine_result": (root / "examples/final-evaluation/final_result.json").is_file(),
        "windows_quickstart": (root / "docs/windows-real-machine-quickstart.md").is_file(),
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
