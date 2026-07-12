"""Orchestrate a bounded five-minute local trial without permanent deletion."""

from __future__ import annotations

import json
from pathlib import Path

from ..demo import init_cleanup_demo, run_cleanup_demo
from ..pup import inspect_pup_risk
from ..reputation import write_pup_insight_markdown
from .user_summary import build_user_summary, render_user_summary_markdown


def _write(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text.rstrip() + "\n")


def run_user_trial(
    root: str | Path,
    output: str | Path,
    *,
    confirm: bool = False,
    quarantine_root: str | Path | None = None,
) -> dict:
    if not isinstance(confirm, bool):
        raise TypeError("confirm must be bool")
    if confirm and quarantine_root is None:
        raise ValueError("confirmed trial requires an explicit quarantine_root")
    if not confirm and quarantine_root is not None:
        raise ValueError("quarantine_root requires confirm=true")
    demo_root = Path(root).resolve(strict=False)
    output_root = Path(output).resolve(strict=False)
    init_cleanup_demo(demo_root)
    cleanup = run_cleanup_demo(
        demo_root,
        output_root,
        confirm=confirm,
        quarantine_root=quarantine_root,
    )

    project_root = Path(__file__).resolve().parents[2]
    seed_path = project_root / "examples" / "reputation" / "seed_records.zh-CN.json"
    synthetic_report = {
        "targets": [{
            "target_id": "trial:synthetic-app-11",
            "object_type": "SOFTWARE",
            "name": "Example Synthetic App 11",
            "source": "pc_cleanguard_trial",
        }]
    }
    _write(output_root / "pup_demo_report.json", json.dumps(synthetic_report, ensure_ascii=False, indent=2))
    pup = inspect_pup_risk(synthetic_report, seed_path)
    write_pup_insight_markdown(output_root / "pup_insight.md", pup["markdown"])

    user_summary = build_user_summary(
        cleanup["summary"],
        pup,
        confirmed=confirm,
        quarantine_root=str(Path(quarantine_root).resolve(strict=False)) if quarantine_root is not None else None,
    )
    machine = {
        **user_summary,
        "root": str(demo_root),
        "output": str(output_root),
        "cleanup_report": str(output_root / "cleanup_report.md"),
        "pup_insight": str(output_root / "pup_insight.md"),
        "audit": cleanup["audit"],
        "quarantine_manifest": str(Path(quarantine_root).resolve(strict=False) / "manifest.json") if quarantine_root is not None else None,
        "execution_performed": cleanup["execution_performed"],
    }
    _write(output_root / "user_summary.md", render_user_summary_markdown(user_summary))
    _write(output_root / "machine_summary.json", json.dumps(machine, ensure_ascii=False, indent=2))
    _write(output_root / "START_HERE.md", """# START HERE

1. 打开 `user_summary.md` 查看人类可读结论。
2. 打开 `cleanup_report.md` 查看清理候选、跳过与阻断项。
3. 打开 `pup_insight.md` 查看 synthetic PUP 线索和误报提醒。
4. 查看 `audit.jsonl` 核对每个 dry-run 或隔离事件。

默认试用不修改候选文件；确认试用只进入可恢复隔离区。PUP 线索不是删除、卸载或禁用授权。不联网、不上传、不静默删除。
""")
    return {"confirmed": confirm, "execution_performed": cleanup["execution_performed"], "machine_summary": machine, "output": str(output_root)}
