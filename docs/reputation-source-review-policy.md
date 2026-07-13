# Reputation Source Review Policy

真实来源必须有可核验 URL、标题、日期和证据摘要；无法确认的真实软件不得被指控。PR25 只在开发期人工核验公开页面，并提交 5 条 Microsoft Security Intelligence detection-family 记录；运行时不联网、不爬虫、不下载，也不采集安全厂商的专有签名、规则或检测逻辑。

监管通报的批次标签是滚动事实，不是稳定 taxonomy。MIIT APP/SDK 通报属于移动端监管证据，不是 Windows 桌面软件删除名单，最多用于 explanation/review。

`approved_for_explanation` 仅表示可向用户展示，不表示可执行。Evidence Guard 在 PR24 中对所有记录返回 execution-gating ineligible。

人工核验必须检查 `mapping_type`、`entity_scope`、`is_synthetic` 与 `relation_confidence`。页面描述只允许克制转述；涉及特定版本、安装器或 detection family 时必须保留限定。source date 缺失时写 `unknown` 并在 review notes 解释原因。证据不足就拒绝或要求更多证据。
