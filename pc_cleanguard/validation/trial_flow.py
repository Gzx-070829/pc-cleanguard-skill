"""Orchestrate one explicit local report through the offline review experience."""

from __future__ import annotations
import json
from pathlib import Path

from ..pipeline.input_loader import _validated_explicit_local_path
from ..pup.review_pack import build_pup_review_pack
from ..reputation import build_evidence_quality_summary, load_evidence_pack, render_evidence_quality_markdown
from .real_report_validation import validate_real_report_shape
from .no_match_report import build_no_match_report, render_no_match_report_markdown

def _records(value):
    if isinstance(value,(str,Path)): return load_evidence_pack(value)
    if isinstance(value,list): return value
    raise TypeError("evidence pack must be path or list")

def _text(path:Path,value:str,overwrite:bool):
    with path.open("w" if overwrite else "x",encoding="utf-8",newline="\n") as stream: stream.write(value.rstrip()+"\n")

def _json(path:Path,value,overwrite:bool):
    with path.open("w" if overwrite else "x",encoding="utf-8",newline="\n") as stream: json.dump(value,stream,ensure_ascii=False,indent=2); stream.write("\n")

def build_real_report_trial(report:dict,output_dir,evidence_pack,*,cn_win_evidence_pack=None,cn_source_matrix=None,include_behavior_indicators=False,include_evidence_quality=False,overwrite=False)->dict:
    if not isinstance(report,dict): raise TypeError("report must be dict")
    destination=Path(output_dir); _validated_explicit_local_path(destination/"report_shape_summary.json",allowed_suffixes={".json"})
    if destination.exists() and not overwrite: raise FileExistsError(f"trial output already exists: {destination}")
    if destination.exists() and not destination.is_dir(): raise ValueError("trial output must be directory")
    destination.mkdir(parents=True,exist_ok=True)
    primary=_records(evidence_pack); cnwin=_records(cn_win_evidence_pack) if cn_win_evidence_pack is not None else []
    shape=validate_real_report_shape(report)
    review=build_pup_review_pack(report,primary,destination/"pup_review_pack",cn_win_evidence_pack=cnwin,cn_source_matrix=cn_source_matrix,include_behavior_indicators=include_behavior_indicators,include_evidence_quality=include_evidence_quality,include_real_report_validation_summary=True,include_corroboration=True,overwrite=overwrite)
    quality=build_evidence_quality_summary([primary,cnwin])
    _text(destination/"START_HERE.md","# Real Report Trial\n\n本地离线验证、PUP 复核、quality 与 match/no-match 说明；不上传、不修改系统。",overwrite)
    _json(destination/"report_shape_summary.json",shape,overwrite)
    _text(destination/"pii_redaction_checklist.md","# PII Redaction\n\n分享前替换用户名、设备名、邮箱、token 与完整路径：`C:\\Users\\<USER>\\...`、`<DEVICE>`、`<EMAIL>`、`<TOKEN>`。",overwrite)
    _text(destination/"matchability_summary.md",f"# Matchability\n\n- score: `{shape['matchability_score']}`\n- PII hints: `{shape['pii_hint_count']}`",overwrite)
    _text(destination/"evidence_quality.md",render_evidence_quality_markdown(quality),overwrite)
    if review.get("cn_win_match_count",0):
        _text(destination/"match_report.md",f"# Match Report\n\n产生 {review['cn_win_match_count']} 条中文 Windows 人工复核线索；不是执行授权。",overwrite); report_kind="match"
    else:
        no_match=build_no_match_report(report,[primary,cnwin],shape); _text(destination/"no_match_report.md",render_no_match_report_markdown(no_match),overwrite); report_kind="no_match"
    _text(destination/"next_steps.md","# Next Steps\n\n核对发布者、签名、版本、安装来源和行为 metadata；必要时提交去标识化反馈。",overwrite)
    _text(destination/"safety_notice.md","# Safety Notice\n\nEvidence、corroboration 和 no-match 都不是删除、卸载、禁用或注册表修改授权。",overwrite)
    return {"output_dir":str(destination),"report_kind":report_kind,"matchability_score":shape["matchability_score"],"quality_gate_passed":quality["quality_gate_passed"],"execution_gating_eligible_count":0,"execution_authorized":False,"runtime_network_access":False}
