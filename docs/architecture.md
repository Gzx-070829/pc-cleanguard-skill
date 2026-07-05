# Architecture

> English summary: The Policy Engine is an independent safety brake; the future Execution Layer may consume decisions but may not make policy.

## 分层

1. **Discovery / Normalization（未来）**：只读采集元数据，形成稳定 target identity。
2. **Evidence Layer**：保存本地事实、规则来源、冲突与置信度。
3. **Policy Engine（PR1）**：硬规则优先，输出分类、风险、权限、确认、回滚与审计要求。
4. **Recommendation / Planning（Schema）**：把决策组织成非执行建议与计划。
5. **Execution Layer（未来）**：只能消费已批准决策，不能自行分类或提升权限。
6. **Audit / Restore（未来）**：记录批准、执行结果与恢复信息。

PR1 只实现第 3 层最小模型以及其他层的数据契约，不读取系统状态，不执行命令。

## 安全门

任何未来执行必须依次通过身份完整性、硬规则、证据充分性、分类、权限上限、用户确认、回滚可用性和审计准备检查。任一失败都停止或降级。
