# Reputation Seed Pack

`examples/reputation/seed_records.zh-CN.json` 是第一批离线、中文优先的 Reputation KB 契约数据。当前 20 条记录均为 synthetic 示例，用于验证 taxonomy、加载器、解释与排序界面，不指控任何真实软件。

加载器严格校验 PR18 八类行为、来源字段、人工复核状态以及 `execution_authorized=false`。它只读取调用方显式传入的本地 JSON，不联网、不下载，也不改变 Policy Engine 或 Cleanup Executor 的决定。

See also [Reputation source policy](reputation-source-policy.md).
