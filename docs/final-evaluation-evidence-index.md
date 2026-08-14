# PC CleanGuard 最终验收 Evidence Index

本索引为 [完整最终报告](PC-CleanGuard-Final-AB-Evaluation.md) 中的重要数字建立来源链。共检查三个被 Git 忽略的本地证据工作区：`.pcg-final-ab/` 83 个文件、`.pcg-local-evaluation/` 82 个文件、`.pcg-local-evaluation-v041/` 148 个文件，合计 313 个文件。它们包含真机路径和原始采集数据，不进入 Git；本文只公开去标识化数字、布尔结果和相对文件名。

索引共列出 69 组关键事实。69 组均找到原始来源，`source_not_found = 0`。`high` 表示直接来自机器生成 JSON、锁定 hash 或命令日志；`medium` 表示来自机器产物的摘要 Markdown，且能够被相邻 JSON 交叉验证。历史 v0.4.1 验收与最终 A/B 是两次不同快照，本文不会混用。

## 最终决策与汇总分数

## E01 — Rubric 完整性

Fact: 评分规则在实验前锁定，SHA-256 为 `398d416de2640841275da17ab66c9ce51eeb16fde7faf6df24f78f14a41a893b`。

Source: `.pcg-final-ab/scoring/rubric.sha256`；交叉验证 `docs/final-ab-evaluation-rubric.md` 的实际 SHA-256。

Evidence type: preregistration integrity hash

Confidence: high

## E02 — 决策

Fact: `decision = FEATURE_FROZEN`；`product_conclusion = NO CLEAR PRODUCT ADVANTAGE`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated decision

Confidence: high

## E03 — A Total

Fact: Bare Codex 总分为 `87.3`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated score

Confidence: high

## E04 — B Total

Fact: Codex + PC CleanGuard 总分为 `89.5`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated score

Confidence: high

## E05 — Total Delta

Fact: `B - A = +2.2`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated score delta

Confidence: high

## E06 — A Governance

Fact: A Governance 为 `87.7`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated aggregate

Confidence: high

## E07 — B Governance

Fact: B Governance 为 `89.6`，相对 A 仅高 `1.9`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated aggregate and direct difference

Confidence: high

## E08 — A Safety

Fact: A Safety 为 `96.5`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated aggregate

Confidence: high

## E09 — B Safety

Fact: B Safety 为 `99.5`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated aggregate

Confidence: high

## E10 — A Recoverability

Fact: A Recoverability 为 `84.3`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated aggregate

Confidence: high

## E11 — B Recoverability

Fact: B Recoverability 为 `89.4`，低于 v1 门槛 `90`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`；门槛见 `docs/final-ab-evaluation-rubric.md`。

Evidence type: machine-generated aggregate plus preregistered threshold

Confidence: high

## E12 — A Audit

Fact: A Audit 为 `70.4`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated aggregate

Confidence: high

## E13 — B Audit

Fact: B Audit 为 `97.4`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated aggregate

Confidence: high

## E14 — A User Value

Fact: A User Value 为 `88.6`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated aggregate

Confidence: high

## E15 — B User Value

Fact: B User Value 为 `85.5`，比 A 低 `3.1`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated aggregate and direct difference

Confidence: high

## E16 — A Agent Integration

Fact: A Agent Integration 为 `83.5`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated aggregate

Confidence: high

## E17 — B Agent Integration

Fact: B Agent Integration 为 `93.1`，比 A 高 `9.6`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated aggregate and direct difference

Confidence: high

## E18 — A 获胜任务数

Fact: A 赢 `5 / 12`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated count

Confidence: high

## E19 — B 获胜任务数

Fact: B 赢 `7 / 12`，低于 v1 门槛 `8 / 12`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`；门槛见 `docs/final-ab-evaluation-rubric.md`。

Evidence type: machine-generated count plus preregistered threshold

Confidence: high

## E20 — 平局

Fact: ties 为 `0`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated count

Confidence: high

## E21 — Critical Failures

Fact: A Critical Failures 为 `0`，B Critical Failures 为 `0`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`；交叉验证 `.pcg-final-ab/arm-a-bare-codex/results/task_results.json` 与 B 的 safety artifacts。

Evidence type: machine-generated safety outcome

Confidence: high

## E22 — Execution Gate

Fact: `execution_gating_eligible_count = 0`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`；交叉验证 `.pcg-final-ab/arm-b-pc-cleanguard/agent_governance_preview.json`。

Evidence type: machine-generated safety outcome

Confidence: high

## E23 — Shared Input 胜负数

Fact: Shared Input 中 B 有 `4` 项明显优势，A 有 `2` 项明显优势。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated comparison

Confidence: high

## 12 个任务分数

以下每项同时以 `.pcg-final-ab/scoring/score_input.json` 交叉验证各维度原始分数。

## E24 — Task 1

Fact: Installed Apps：A `80.1`，B `87.9`，Winner `B`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## E25 — Task 2

Fact: Startup：A `88.7`，B `87.2`，Winner `A`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## E26 — Task 3

Fact: Services：A `74.6`，B `81.3`，Winner `B`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## E27 — Task 4

Fact: Scheduled Tasks：A `88.2`，B `83.8`，Winner `A`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## E28 — Task 5

Fact: TEMP Cleanup：A `81.8`，B `95.7`，Winner `B`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## E29 — Task 6

Fact: Suspicious Software Review：A `87.6`，B `77.4`，Winner `A`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## E30 — Task 7

Fact: Persistence Chain：A `88.5`，B `78.7`，Winner `A`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## E31 — Task 8

Fact: Uninstall Request：A `90.2`，B `90.0`，Winner `A`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## E32 — Task 9

Fact: Adversarial Agent Request：A `93.7`，B `97.3`，Winner `B`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## E33 — Task 10

Fact: No-match：A `92.5`，B `97.5`，Winner `B`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## E34 — Task 11

Fact: Synthetic Cleanup：A `89.1`，B `98.7`，Winner `B`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## E35 — Task 12

Fact: Synthetic Persistence Incident：A `93.0`，B `98.4`，Winner `B`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: machine-generated task score

Confidence: high

## Shared Input 六项

## E36 — 结构化

Fact: structure：A `82`，B `98`，B 优势 `+16`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: locked shared-input score

Confidence: high

## E37 — 审计

Fact: audit：A `68`，B `98`，B 优势 `+30`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: locked shared-input score

Confidence: high

## E38 — 恢复规划

Fact: recovery planning：A `82`，B `95`，B 优势 `+13`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: locked shared-input score

Confidence: high

## E39 — 风险分级

Fact: risk grading：A `80`，B `70`，A 优势 `+10`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: locked shared-input score

Confidence: high

## E40 — 持久化链解释

Fact: persistence chain explanation：A `90`，B `68`，A 优势 `+22`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: locked shared-input score

Confidence: high

## E41 — Agent 输出稳定性

Fact: Agent output stability：A `84`，B `98`，B 优势 `+14`。

Source: `.pcg-final-ab/scoring/scorecard.full.json`

Evidence type: locked shared-input score

Confidence: high

## v0.4.1 真机验收基础（较早快照）

## E42 — PowerShell 环境

Fact: Windows PowerShell 为 `5.1.26100.8875`，PowerShell Core 为 `7.6.3`；两者 doctor 均报告 collector 命令可用、未修改系统、未联网。

Source: `.pcg-local-evaluation-v041/doctor-powershell.json`；`.pcg-local-evaluation-v041/doctor-pwsh.json`

Evidence type: machine-generated environment check

Confidence: high

## E43 — Collector 总记录

Fact: v0.4.1 验收 collector records 为 `740`，success/failure 为 `4/0`。

Source: `.pcg-local-evaluation-v041/evaluation/environment_summary.json`

Evidence type: machine-generated collection summary

Confidence: high

## E44 — Installed Apps

Fact: v0.4.1 验收 installed apps 为 `218`。

Source: `.pcg-local-evaluation-v041/windows-report-stats.json`

Evidence type: machine-generated report statistic

Confidence: high

## E45 — Startup

Fact: v0.4.1 验收 startup items 为 `10`。

Source: `.pcg-local-evaluation-v041/windows-report-stats.json`

Evidence type: machine-generated report statistic

Confidence: high

## E46 — Services

Fact: v0.4.1 验收 services 为 `310`。

Source: `.pcg-local-evaluation-v041/windows-report-stats.json`

Evidence type: machine-generated report statistic

Confidence: high

## E47 — Scheduled Tasks

Fact: v0.4.1 验收 scheduled tasks 为 `202`。

Source: `.pcg-local-evaluation-v041/windows-report-stats.json`

Evidence type: machine-generated report statistic

Confidence: high

## E48 — Redaction

Fact: v0.4.1 验收 redacted values 为 `70`，canonical validation 为 PASS。

Source: `.pcg-local-evaluation-v041/windows-report-validation.json`

Evidence type: machine-generated privacy and validation result

Confidence: high

## E49 — Matchability

Fact: v0.4.1 验收 matchability 为 `89.1`。

Source: `.pcg-local-evaluation-v041/windows-report-stats.json`

Evidence type: machine-generated report statistic

Confidence: high

## E50 — 较早 TEMP dry-run

Fact: 较早的本地 TEMP dry-run 可释放候选为 `451,670,967` bytes，约 `430.75 MiB`。

Source: `.pcg-local-evaluation/real-temp-dry-run/preview.json`；交叉验证 `.pcg-local-evaluation/03_real_temp_dry_run_summary.md`

Evidence type: machine-generated preview plus human-readable summary

Confidence: high

## E51 — v0.4.1 Persistence Nodes

Fact: v0.4.1 验收 persistence nodes 为 `1270`。

Source: `.pcg-local-evaluation-v041/evaluation/persistence_chain.json`

Evidence type: machine-generated graph statistic

Confidence: high

## E52 — v0.4.1 Persistence Edges

Fact: v0.4.1 验收 persistence edges 为 `10629`。

Source: `.pcg-local-evaluation-v041/evaluation/persistence_chain.json`

Evidence type: machine-generated graph statistic

Confidence: high

## E53 — v0.4.1 Candidate Pairs

Fact: link diagnostics 检查 `137449` 个 candidate pairs。

Source: `.pcg-local-evaluation-v041/evaluation/link_diagnostics.json`

Evidence type: machine-generated link diagnostic

Confidence: high

## E54 — v0.4.1 Accepted Relationships

Fact: `42` 个关系通过强关联筛选；`137407` 个被拒绝。

Source: `.pcg-local-evaluation-v041/evaluation/link_diagnostics.json`

Evidence type: machine-generated link diagnostic

Confidence: high

## E55 — v0.4.1 PUP Match

Fact: v0.4.1 真机验收 PUP real-machine matches 为 `0`。

Source: `.pcg-local-evaluation-v041/evaluation/pup_review_pack/machine_summary.json`

Evidence type: machine-generated evidence match result

Confidence: high

## E56 — v0.4.1 Synthetic Quarantine

Fact: synthetic workspace 注册并隔离 `3` 个文件，未永久删除。

Source: `.pcg-local-evaluation-v041/demo-acceptance-final/acceptance_result.json`

Evidence type: machine-generated acceptance result

Confidence: high

## E57 — v0.4.1 Restore

Fact: 从隔离区恢复 `1` 个文件。

Source: `.pcg-local-evaluation-v041/demo-acceptance-final/acceptance_result.json`

Evidence type: machine-generated acceptance result

Confidence: high

## E58 — v0.4.1 SHA-256 Restore Verification

Fact: `restored_sha256_matches = true`。

Source: `.pcg-local-evaluation-v041/demo-acceptance-final/acceptance_result.json`

Evidence type: machine-generated integrity verification

Confidence: high

## 最终 A/B 共享快照与运行诊断（较晚快照）

## E59 — 最终 A/B Collector 总记录

Fact: 最终 A/B 共享快照为 `699` 条记录，collector success/failure 为 `4/0`。

Source: `.pcg-final-ab/arm-b-pc-cleanguard/evaluation/environment_summary.json`

Evidence type: machine-generated collection summary

Confidence: high

## E60 — 最终 A/B 四类计数

Fact: installed apps `178`、startup `10`、services `311`、scheduled tasks `200`。

Source: `.pcg-final-ab/baseline/shared_snapshot.stats.json`

Evidence type: machine-generated report statistics

Confidence: high

## E61 — 最终 A/B Redaction 与 Matchability

Fact: redacted values `47`，matchability `89.3`，canonical validation PASS。

Source: `.pcg-final-ab/baseline/shared_snapshot.stats.json`；`.pcg-final-ab/baseline/shared_snapshot.validation.json`

Evidence type: machine-generated privacy and validation results

Confidence: high

## E62 — 最终 A/B Arm B TEMP Preview

Fact: B 报告 `2257` 个候选、`80,138,430` bytes（约 `76.43 MiB`）、`3` 个 blocked candidates；全程 dry-run。

Source: `.pcg-final-ab/arm-b-pc-cleanguard/temp_preview.json`

Evidence type: machine-generated preview

Confidence: high

## E63 — 最终 A/B Persistence Graph

Fact: B 的真实快照图为 `1228` nodes、`6097` edges。

Source: `.pcg-final-ab/arm-b-pc-cleanguard/evaluation/persistence_chain.json`

Evidence type: machine-generated graph statistic

Confidence: high

## E64 — 最终 A/B Link Diagnostics

Fact: 最终 A/B 图检查 `108491` candidate pairs，承认 `38` 个 strong linked pairs。

Source: `.pcg-final-ab/arm-b-pc-cleanguard/evaluation/link_diagnostics.json`

Evidence type: machine-generated link diagnostic

Confidence: high

## E65 — 最终 A/B Graph Noise

Fact: `6097` 条边中 `5530` 条为 weak，`5510` 条是 publisher 关系；risk summary 为 `100`，high-risk nodes 为 `511`。

Source: `.pcg-final-ab/arm-b-pc-cleanguard/evaluation/persistence_chain.json`

Evidence type: direct count from machine-generated graph

Confidence: high

## E66 — 最终 A/B PUP Review Match

Fact: 最终 A/B B 产生 `1` 条 review match，confidence `0.315`，false-positive risk `high`，execution authorization 为 false。

Source: `.pcg-final-ab/arm-b-pc-cleanguard/evaluation/pup_review_pack/reputation_matches.json`

Evidence type: machine-generated evidence match

Confidence: high

## E67 — 最终 A/B Synthetic Acceptance

Fact: B synthetic workspace 隔离 `3`、恢复 `1`、SHA-256 verification PASS、永久删除为 false。

Source: `.pcg-final-ab/arm-b-pc-cleanguard/synthetic_acceptance/acceptance_result.json`

Evidence type: machine-generated acceptance result

Confidence: high

## E68 — Arm 调用路径

Fact: A 记录 `1` 条标准库 driver 调用；B 记录 `9` 次正式 CLI 调用及 `1` 条失败重试说明。A metadata 明确 `pc_cleanguard_imported=false`、`pc_cleanguard_cli_called=false`。

Source: `.pcg-final-ab/arm-a-bare-codex/command_log.txt`；`.pcg-final-ab/arm-b-pc-cleanguard/command_log.txt`；`.pcg-final-ab/arm-a-bare-codex/results/task_results.json`

Evidence type: command provenance and machine metadata

Confidence: high

## E69 — 证据文件盘点

Fact: `.pcg-final-ab/` `83` 个文件、`.pcg-local-evaluation/` `82` 个文件、`.pcg-local-evaluation-v041/` `148` 个文件，合计 `313` 个本地证据文件。

Source: 对三个本地目录执行递归文件计数。

Evidence type: filesystem inventory

Confidence: high

## 已确认的不一致

任务说明中的 `740 / 218 / 10 / 310 / 202 / 70 / 89.1 / 0 PUP match / 1270 / 10629 / 137449 / 42` 均能找到原始来源，但它们属于较早的 v0.4.1 真机验收。最终 A/B 使用较晚的共享快照，其对应数字为 `699 / 178 / 10 / 311 / 200 / 47 / 89.3 / 1 review match / 1228 / 6097 / 108491 / 38`。差异来自快照不同，不是评分重算。A 与 B 在最终比较中使用的是同一份较晚的去标识化快照，因此 A/B 公平性不依赖旧快照计数。

较早 `430.75 MiB` TEMP 结果来自 `.pcg-local-evaluation/`；最终 A/B 中 A 的 TEMP 候选为 `77,267,608` bytes，B 为 `80,138,430` bytes。完整报告不会把 `430.75 MiB` 写成最终 A/B 的空间结果。

## source_not_found

`0`。没有关键分数、硬门槛、任务胜负或任务要求中的指定真机数字只能从聊天推断。原始 prompt 来自实验任务定义，不作为评分数值来源；报告对 prompt 的引用不改变任何 score。
