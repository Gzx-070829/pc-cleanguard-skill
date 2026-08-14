# PC CleanGuard 最终评估摘要

## 我们做了什么

PC CleanGuard 最终没有继续追加功能，而是回答了一个更严格的问题：当现代 Codex 已经可以直接读取和分析 Windows metadata 时，一个专门的治理 Skill 是否仍有足够大的独立产品价值？为此，项目在真实 Windows 只读边界下进行了 12 项 A/B 验收。A 是 Bare Codex，不调用或读取 PC CleanGuard；B 是 Codex + PC CleanGuard v0.4.1 正式接口。两组处理相同的去标识化共享快照，并接受相同的禁止删除、卸载、注册表/服务/启动项/计划任务修改和上传约束。隔离、恢复与 SHA-256 验证只在 synthetic workspace 中进行。

评分规则在实验前锁定。每项任务按完成度、安全、解释、审计、恢复、不确定性、结构化与操作成本评分；任何 v1 硬门槛不通过，都必须冻结。实验后没有改权重、门槛或胜负。

## 真实测试是什么

较早的 v0.4.1 真机验收读取了 740 条 collector 记录，形成 218 个 installed apps、10 个 startup items、310 个 services 和 202 个 scheduled tasks；canonical validation 通过，脱敏 70 个值，matchability 为 89.1。持久化图有 1270 个节点、10629 条边，link diagnostics 从 137449 个候选对中接受 42 个关系。PUP 真机匹配为 0；这只表示当前 evidence 没有命中，不表示系统干净。

最终 A/B 发生在更晚的同机快照：699 条记录，四类计数为 178、10、311、200。两组使用同一份去标识化输入，因此旧、新快照计数变化不影响组间公平性。最终真实机器没有发生删除或配置修改，也没有上传。Synthetic 验收隔离 3 个文件、恢复 1 个文件并通过 SHA-256 校验。

## 结果是什么

Bare Codex 总分 `87.3`，Codex + PC CleanGuard 总分 `89.5`，差值仅 `+2.2`。B 赢 7 项，A 赢 5 项。B 的 Safety `99.5`、Audit `97.4`，在结构化、审计、恢复规划和 Agent 输出稳定性上明显更强；A 在风险分级、目标级持久化解释以及若干直接用户任务上更好。B 的真实图包含大量弱 publisher 关系，降低了解释清晰度；PUP 管线还把一个低置信度短名称碰撞提升为强复核提示，虽然始终没有授权执行。

四个 v1 硬门槛失败：总分优势要求 10，实际 2.2；Governance 优势要求 15，实际 1.9；B Recoverability 要求 90，实际 89.4；B 胜场要求 8/12，实际 7/12。因此结论是：

```text
No clear product advantage was demonstrated.
FEATURE_FROZEN / Maintenance Mode
```

这不是“PC CleanGuard 没有价值”的同义词。它表示价值集中在治理基础设施，而没有形成足以覆盖产品复杂度的整体优势。对多 Agent 或需要独立审计的流程，固定 schema、blocked state 和恢复记录可能很重要；对一次性的个人 Windows 问题，Bare Codex 的短回答、目标选择和临时只读脚本往往更省步骤。本次实验同时观察到这两面，所以不能只展示 B 的高审计分，也不能只凭 A 的五个胜项宣布治理层无意义。

## 为什么停止

项目证明了治理纪律、canonical Windows 表示、脱敏、审计、隔离恢复、稳定 Agent contract 和 evidence/authorization 分离可以被工程化；这些是真实成果。但实验没有证明这些收益足以抵消独立 schema、Policy、Reputation、图谱、兼容性和发布维护成本。现代通用 Agent 已能完成多数底层枚举、解释与规划，PC CleanGuard 的优势集中在“把过程固定下来”，而不是不可替代地完成任务。

结论适用范围也必须受限：这是一台机器、一个用户、12 项任务和一个时间点的工程验收，不是关于所有专用 Skill 的统计学结论。Codex 版本、prompt、Windows 环境和企业合规要求变化后，结果可能不同。未来只有出现通用 Agent 的系统性高权限误操作、平台需要外部 deterministic Policy Gate，或企业明确要求跨模型 audit/rollback contract 等新证据，才值得重新评估；开发冲动与历史投入本身不是重启条件。

## 项目留下了什么

PC CleanGuard 保留为离线、可审计 AI 系统治理的开源参考实现，维护安全、兼容性和关键缺陷，不再主动扩展功能。它留下的核心经验是：Agent 能力与 Agent 治理不同；建议不是执行授权；Policy、audit、rollback 比增加更多执行动作更持久；而过度治理本身也会产生噪声、操作成本和用户价值损失。

完整方法、12 项逐项分析、Shared Input、局限与反事实见 [完整报告](PC-CleanGuard-Final-AB-Evaluation.md)，数字来源见 [Evidence Index](final-evaluation-evidence-index.md)，正式决定见 [Decision Record](PC-CleanGuard-Final-Decision-Record.md)。
