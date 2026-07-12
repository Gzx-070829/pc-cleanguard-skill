# Reputation Source Review Policy

真实来源必须有可核验 URL、标题、日期和证据摘要；无法离线确认的真实软件不得被指控。本 PR 只提交 synthetic records，不联网、不爬虫、不下载，也不采集安全厂商的专有签名、规则或检测逻辑。

监管通报的批次标签是滚动事实，不是稳定 taxonomy。MIIT APP/SDK 通报属于移动端监管证据，不是 Windows 桌面软件删除名单，最多用于 explanation/review。

`approved_for_explanation` 仅表示可向用户展示，不表示可执行。Evidence Guard 在 PR24 中对所有记录返回 execution-gating ineligible。
