# PC CleanGuard Skill

> **PC CleanGuard Skill 不是传统清理软件。**
> 它是面向 AI Agent 的开源系统治理 Skill。
> 它未来可以具备受控执行能力，但当前 PR1 不执行任何真实清理。
> 它不会静默删除，也不会偷偷上传，更不会根据单一声誉来源自动删除。
> 它要求证据链、风险分类、权限等级、用户确认和审计准备。

## 项目定位

PC CleanGuard 在 AI 建议与系统操作之间建立可审计的安全门。它先回答“能否做、为何做、需要谁确认”，而不是直接动手。

## 它是什么

- Windows 对象的保守治理策略模型。
- 以证据链、风险标签和权限等级约束 Agent 的 Skill。
- 为未来受控执行层提供独立、不可绕过的 Policy Engine。

## 它不是什么

它不是磁盘清理器、卸载器、杀毒软件、系统优化器或后台监控器。PR1 没有删除、卸载、移动、注册表写入、服务/启动项修改、联网或上传能力。

## v0.1 PR1 当前范围

本 PR 仅包含仓库骨架、安全契约、规则占位、Draft 2020-12 JSON Schema、Python 标准库数据模型、纯判断型 Policy Engine 和危险场景单元测试。

## 安全原则

1. 硬规则先于普通分类，敏感目标直接 `BLOCK`。
2. 不确定时 `KEEP` 或 `ASK_USER`。
3. AI、声誉、社区规则和用户偏好都不能单独授权删除。
4. 所有非 `KEEP` 决策必须有证据链并准备审计。
5. 用户偏好不能绕过 `BLOCK` 或 Level 5。

## 系统架构

```text
Normalized Target + Evidence
             |
        Policy Engine
             |
 Classification + Risk + Permission + Confirmation + Audit
             |
      Non-executable PR1 report
```

未来 Execution Layer 必须消费 Policy Engine 的结果，不能自行制定或弱化策略。

## 风险分类标签

`KEEP`、`ASK_USER`、`SAFE_REMOVE`、`STARTUP_OFF`、`QUARANTINE`、`BLOCK`。候选标签不是执行授权。

## 执行权限等级

Level 0 只读扫描；Level 1 低风险清理；Level 2 可逆操作；Level 3 标准卸载；Level 4 高风险系统修改；Level 5 禁止区。PR1 只运行 Level 0。

## 隐私承诺

PR1 仅实现 Offline Mode：不联网、不上传，不收集原始用户路径，不对用户文档、代码或照片做云端声誉检查。

## 开发状态

当前里程碑：**v0.1 PR1 — 安全地基**。任何 `SAFE_REMOVE`、`STARTUP_OFF` 或 `QUARANTINE` 都只是带确认要求的建议，不会执行。
