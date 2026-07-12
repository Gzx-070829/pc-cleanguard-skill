# Reputation 来源策略 / Source Policy

Reputation KB 是证据层，不是黑名单，也不是执行授权。记录只可用于解释、排序和风险提示；任何单一来源都不能触发删除、卸载或禁用。

允许的来源类型包括公开监管通报、公开厂商行为文章、社区报告和 synthetic example。公开内容仅手工整理行为描述与必要元数据，不复制或推导专有安全厂商的签名库、检测库、规则库、样本库或检测逻辑。

PR20 不联网、不下载、不爬取网站。无法确认可靠来源时必须使用 `Example` / `Synthetic` 名称和 placeholder URL，避免对真实软件作未经核实的指控。社区报告默认需要人工复核。

Every record fixes `execution_authorized=false`. Approval for explanation means only that evidence may be shown to a user; it never grants cleanup authority.
