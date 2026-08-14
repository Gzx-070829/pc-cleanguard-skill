# PC CleanGuard Final Decision Record

## Decision

PC CleanGuard 的最终决策为：

```text
FEATURE_FROZEN / Maintenance Mode
```

不发布 `v1.0.0`，停止主动功能开发。冻结不等于代码无法运行，也不等于工程失败；它表示现有证据不足以证明继续把 PC CleanGuard 作为独立大型 Windows AI Skill 进行产品化扩张具有足够高的边际价值。

## 为什么冻结

最终实验在相同安全边界下比较了 Bare Codex 与 Codex + PC CleanGuard。12 项任务的总分是 A `87.3`、B `89.5`，B 领先 `2.2`；Governance 是 `87.7` 对 `89.6`，仅领先 `1.9`。B 赢 `7 / 12`，Recoverability 为 `89.4`。虽然 B 的 Safety `99.5`、Audit `97.4`，并在 Shared Input 的结构化、审计、恢复规划、Agent 输出稳定性上有明显优势，但四个硬条件没有通过：总分优势不足 `10`、Governance 优势不足 `15`、Recoverability 未达到 `90`、胜场未达到 `8 / 12`。

因此，机器 scorecard 给出 `NO CLEAR PRODUCT ADVANTAGE`，自动对应 `FEATURE_FROZEN`。完整证据见 [Evidence Index](final-evaluation-evidence-index.md) 与 [完整 A/B 报告](PC-CleanGuard-Final-AB-Evaluation.md)。

冻结不是因为某个测试崩溃，也不是因为 B 发生安全事故。两组 Critical Failure 都为零，真实系统没有被修改，B 在审计和安全上明显更强。真正未通过的是“相对于现代通用 Agent 的净产品价值”这一更高标准。若只问 PC CleanGuard 是否能运行、是否能生成报告、是否能阻断危险请求，答案是肯定的；若问这些能力是否足以支撑一个持续扩张的独立大型 Skill，当前答案是否定的。Decision Record 必须保留这一区分，避免以后把冻结误解成工程失败，也避免把工程成功重新包装成产品胜出。

## 依据是什么

直接依据包括锁定 rubric、机器生成 scorecard、A/B command logs、A 的 12 项 task result、B 的 canonical evaluation、link diagnostics、PUP Review Pack、Agent guards、TEMP preview、synthetic acceptance，以及较早 v0.4.1 真机验收用于背景对照的 collector stats。最终 A/B 使用较晚的共享快照；较早 740 条记录与最终 699 条记录被明确分开。旧快照的 0 PUP match 和最终快照的 1 条低置信度 review match 也没有合并叙述。所有关键数值均能定位到原始 artifact，关键数字 `source_not_found` 为零。

## 谁做了决定

决定主体不是实验结束后的单次主观判断，而是项目方在实验前锁定的自动决策规则。实验执行者负责运行两组、保存产物、按既定公式录入维度分数并执行门槛；规则本身决定是否允许 v1。项目投入、历史版本数量和希望继续开发的意愿不参与判定。

## 门槛何时锁定

评分维度、权重、单项胜负、Shared Input 的“明显优势”定义、Critical Failure 和 v1 的全部硬门槛在首个 A/B 结果生成前写入 `docs/final-ab-evaluation-rubric.md`。锁定文件的 SHA-256 为 `398d416de2640841275da17ab66c9ce51eeb16fde7faf6df24f78f14a41a893b`，本次报告阶段复核后未变化。

```text
No thresholds were changed after observing the result.
```

本报告没有重算分数、改变 A/B 权重、删除 A 的胜项、挑选更有利的 run，也没有修改产品后重新比较。较早 v0.4.1 验收与最终 A/B 使用不同快照；报告分别呈现，未将差异用于改变分数。

决策也没有因为 B 在 Audit 上领先 27 分就豁免其余条件。预注册规则要求所有门槛同时成立，目的是防止单一强项掩盖用户价值、解释质量、恢复性或操作成本。反过来，A 赢得五项也不被解释为 B 没有任何价值；它只说明 B 的优势分布不足以支持 v1。

## Maintenance Scope

冻结后允许的工作仅包括关键安全问题、严重兼容性问题、会破坏现有数据或审计链的缺陷，以及事实性文档修正。不以维护名义增加清理范围、卸载器、注册表/服务/任务修改、在线 Reputation、上传、后台服务或新的大型治理架构。

## Reopen Criteria

只有出现可验证的新外部条件时，才重新评估主动开发：

1. 通用 Agent 在 Windows 高权限操作中持续出现系统性、不可接受且仅靠平台约束无法解决的误操作；
2. Agent 平台明确需要独立 deterministic Policy Gate；
3. 企业部署提出独立 audit、rollback、审批和职责分离契约；
4. 跨模型大规模部署需要一致的治理接口，并有实际采用方；
5. OS Agent 生态出现稳定标准接口，使治理层的集成和维护成本显著下降。

“又想到新功能”或“已经投入很多”不构成 reopen 依据。重启时必须建立新的研究问题、新的预注册门槛和新的真实环境数据，不能把本次冻结结果改写为胜出。

## Record Status

- Engineering verdict: successful reference implementation.
- Product differentiation: insufficiently demonstrated.
- Research value: strong.
- Future feature development: not justified by current evidence.
- Maintenance: security, compatibility and critical bug fixes only.
