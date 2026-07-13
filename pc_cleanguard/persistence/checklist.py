"""Human review checklist for persistence chains."""

def build_persistence_review_checklist(graph: dict) -> list[str]:
    checks = ["核对软件名称、发布者、数字签名、版本和安装来源。", "核对启动项、服务与计划任务是否符合用户意图。", "核对浏览器主页、搜索和扩展改动是否由用户确认。", "在任何未来 L2-L4 操作前准备备份、恢复路径和审计记录。"]
    if graph.get("missing_metadata"): checks.append("补充缺失 report metadata 后重新构图。")
    return checks
