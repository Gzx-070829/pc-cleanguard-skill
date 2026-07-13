# PUP Human Review Checklist

Checklist 为每个 match 展示 target、evidence、match basis、indicator type、source URL/title/date、误报风险和不能成为执行授权的原因。

用户应核对：是否主动安装、是否来自可信官网、是否随其他软件捆绑出现、是否存在异常启动项/服务/任务、是否修改浏览器主页/搜索/扩展、是否有弹窗或难以卸载行为，以及 Microsoft Defender 或其他安全工具是否独立提示。

允许的建议仅限 `review`、`keep`、`ask_user`、`check_vendor_uninstaller`、`check_defender_or_security_tool`、`collect_more_evidence` 和 `report_false_positive`。Checklist 不输出系统修改指令。

PR27 把 behavior indicators 作为独立 `behavior_items` 加入清单。启动项、服务、任务或 installer 名称只是输入报告中的观察值，必须核对用户意图、发布者、来源和安全工具独立结果，不能自动触发系统修改。

PR28 复核还必须检查 source class、平台范围、时间/版本范围、第二来源要求和实体映射边界。网友名单不是 evidence pack，历史榜不是现代 verdict，Behavior Indicator 不是 PUP 定罪；任何线索都不能触发自动执行。
