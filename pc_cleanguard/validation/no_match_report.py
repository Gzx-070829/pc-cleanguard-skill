"""Build useful, non-authorizing explanations when local evidence produces no match."""

from __future__ import annotations

from ..pup.behavior_indicators import build_behavior_indicators_from_report

GROUPS=("installed_apps","startup_items","services","scheduled_tasks")

def build_no_match_report(report: dict, evidence_packs: list[list[dict]], matchability_summary: dict) -> dict:
    if not isinstance(report,dict) or not isinstance(evidence_packs,list): raise TypeError("report must be dict and evidence_packs list")
    counts={name:len(report.get(name,())) if isinstance(report.get(name,()),list) else 0 for name in GROUPS}
    records=[item for pack in evidence_packs for item in pack]
    missing=[]
    apps=report.get("installed_apps",())
    if not apps or any(not (item.get("publisher") or item.get("Publisher")) for item in apps if isinstance(item,dict)): missing.append("publisher")
    if not apps or any(not (item.get("path") or item.get("install_location") or item.get("InstallLocation")) for item in apps if isinstance(item,dict)): missing.append("path/install_location")
    for name in ("startup_items","scheduled_tasks","services"):
        if not report.get(name): missing.append(name+" metadata")
    if not any(isinstance(item,dict) and item.get("behavior_metadata") for item in apps): missing.append("behavior metadata")
    return {"scanned_target_counts":counts,"enabled_evidence_packs":len(evidence_packs),"evidence_record_counts":[len(pack) for pack in evidence_packs],
        "cn_win_evidence_count":sum(item.get("language")=="zh-CN" and item.get("entity_scope") in {"windows_desktop_software","windows_installer"} for item in records),
        "behavior_indicator_count":len(build_behavior_indicators_from_report(report)),"unsupported_fields":matchability_summary.get("unsupported_fields",[]),"missing_metadata":missing,
        "why_no_match":["当前 evidence 名称、别名、发布者和报告元数据未形成可审计复核线索。"],
        "how_to_improve_matchability":["补充 publisher、签名、版本与 path metadata。","补充 startup/task/service metadata 和经过核验的 behavior metadata。"],
        "safety_boundaries_still_active":["不联网、不上传、不静默删除。","PUP 层 execution gating 保持为 0。"],
        "next_steps_for_user":["核对报告是否完整并先完成去标识化。","必要时使用可信安全工具独立检查。"],
        "matchability_score":matchability_summary.get("matchability_score",0),"execution_gating_eligible_count":0,"execution_authorized":False}

def render_no_match_report_markdown(report: dict) -> str:
    lines=["# No-match 价值报告","","No-match 不等于系统干净；它只表示当前 evidence 与 report metadata 下没有产生复核线索。","",
        f"- scanned_target_counts: `{report.get('scanned_target_counts',{})}`",f"- enabled_evidence_packs: `{report.get('enabled_evidence_packs',0)}`",f"- behavior_indicator_count: `{report.get('behavior_indicator_count',0)}`",f"- matchability_score: `{report.get('matchability_score',0)}`","","## 缺失 metadata","",*[f"- {x}" for x in report.get("missing_metadata",())],"","## 如何改进","",*[f"- {x}" for x in report.get("how_to_improve_matchability",())],"","## 安全边界仍然生效","",*[f"- {x}" for x in report.get("safety_boundaries_still_active",())]]
    return "\n".join(lines).rstrip()+"\n"
