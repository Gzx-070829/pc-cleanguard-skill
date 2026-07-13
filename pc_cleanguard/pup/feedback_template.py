"""Create a local false-positive feedback worksheet without uploading it."""

from __future__ import annotations


def build_false_positive_feedback_template(matches: list[dict]) -> str:
    if not isinstance(matches, list):
        raise TypeError("matches must be a list")
    lines = [
        "# False Positive Feedback / 误报反馈模板", "",
        "这是本地模板，不会自动上传。请在分享前移除路径、账户名或其他隐私信息。", "",
    ]
    for match in matches:
        lines.extend([
            f"## {match.get('target_id', 'unknown')}", "",
            f"- 命中的软件/启动项/服务/任务：{match.get('target_observed_value')}",
            f"- matched_record_id：{match.get('matched_record_id')}",
            f"- source 是否匹配：{match.get('source_url')}",
            "- 用户为什么认为是误报：",
            "- 是否来自官网：",
            "- 是否为用户主动安装：",
            "- 是否存在名称相似但不同实体：",
            "- 是否应降级为 name_collision_candidate：",
            "- 是否应降低 relation_confidence：",
            "- 是否应移除 alias/indicator：",
            "- 是否应保留为 explanation-only：", "",
        ])
    if not matches:
        lines.extend(["当前没有匹配项。", ""])
    return "\n".join(lines).rstrip() + "\n"
