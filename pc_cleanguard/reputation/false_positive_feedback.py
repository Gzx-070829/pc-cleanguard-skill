"""Build and validate private-by-default false-positive review templates."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
import re


def build_false_positive_feedback_template(match: dict, report_metadata: dict) -> dict:
    if not isinstance(match, dict) or not isinstance(report_metadata, dict): raise TypeError("match and report_metadata must be dicts")
    return {
        "feedback_id": f"fp:{uuid4()}",
        "record_id": match.get("matched_record_id", match.get("record_id", "unknown")),
        "software_name": match.get("matched_name", match.get("software_name", "unknown")),
        "user_claim": "possible_false_positive",
        "installed_from": report_metadata.get("installed_from", "unknown"),
        "publisher_observed": report_metadata.get("publisher", report_metadata.get("publisher_observed", "unknown")),
        "signature_status_observed": report_metadata.get("signature_status", report_metadata.get("signature_status_observed", "unknown")),
        "version_observed": report_metadata.get("version", report_metadata.get("version_observed", "unknown")),
        "path_redacted": report_metadata.get("path_redacted", "C:/Users/<USER>/..."),
        "why_user_thinks_false_positive": "",
        "supporting_context": "",
        "privacy_redaction_confirmed": False,
        "consent_to_share_redacted_report": False,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "review_status": "review_queue_only",
        "uploaded": False,
        "runtime_network_access": False,
        "evidence_pack_modified": False,
        "execution_gating_eligible_count": 0,
        "execution_authorized": False,
    }


def validate_false_positive_feedback(feedback: dict) -> list[str]:
    if not isinstance(feedback, dict): raise TypeError("feedback must be a dict")
    errors = []
    if feedback.get("privacy_redaction_confirmed") is not True: errors.append("privacy_redaction_confirmed must be true before sharing")
    path = str(feedback.get("path_redacted", ""))
    if re.search(r"(?i)[a-z]:[/\\]users[/\\](?!<USER>)[^/\\]+", path): errors.append("path_redacted contains a real-looking username")
    if feedback.get("review_status") != "review_queue_only": errors.append("review_status must remain review_queue_only")
    if feedback.get("uploaded") is not False or feedback.get("runtime_network_access") is not False: errors.append("feedback must remain offline and not uploaded")
    if feedback.get("evidence_pack_modified") is not False: errors.append("feedback cannot modify evidence pack")
    return errors


def render_false_positive_feedback_markdown(feedback: dict) -> str:
    return "\n".join(["# False-positive Feedback / 误报反馈", "", "该模板默认保存在本地，不联网、不上传，也不会自动修改 evidence pack；只能进入人工 review queue。", "", f"- feedback_id: `{feedback.get('feedback_id')}`", f"- record_id: `{feedback.get('record_id')}`", f"- software_name: {feedback.get('software_name')}", f"- path_redacted: `{feedback.get('path_redacted')}`", f"- privacy_redaction_confirmed: `{str(feedback.get('privacy_redaction_confirmed', False)).lower()}`", "", "请补充安装来源、签名、版本、误报理由和去标识化上下文。", ""]).rstrip() + "\n"
