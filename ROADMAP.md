# Roadmap

本路线图以中文说明项目阶段，并保留英文组件名称，方便中英文社区共同审计。

This roadmap keeps stage descriptions in Chinese while retaining English component names for international collaboration.

从 v0.2 起采用 Sprint PR 加速研发：每个 PR 交付用户可见价值，可包含多个强相关模块，并允许先发布 80% 可用版本再根据 issue 与反馈迭代；安全底线保持不变。详见 [研发原则](docs/development-principles.md)。

- **v0.1**：安全扫描 + 报告 + 规则分类基础。
  - **v0.1 PR1**：仓库骨架、安全契约、schemas、最小 Policy Engine、测试。
  - **v0.1 PR2**：非破坏性 Report Builder、Execution Plan Builder、示例报告和测试。
  - **v0.1 PR3**：AuditEvent、append-only JSONL dry-run logger、示例审计日志和测试。
  - **v0.1 PR4**：SQLite State Store + Reputation Knowledge Store。
  - **v0.1 PR5**：Windows installed apps read-only collector + normalizer。
  - **v0.1 PR6**：Windows startup、services、scheduled tasks read-only collectors + normalizers。
  - **v0.1 PR7**：显式 JSON 输入、四类 metadata normalizer、Policy Engine、Report Builder、dry-run Audit 和可选本地结果写出的只读扫描流水线。
  - **v0.1 PR8**：包装 PR7 pipeline 的最小只读 CLI，只处理显式 JSON 输入并写出显式 report/audit 路径。
  - **v0.1 PR9**：离线 AI Report Explainer、安全 prompt、Mock provider、dry-run prompt 和 Markdown 输出。
  - **v0.1 PR10**：AI 可调用的 Level 0 Skill 动作契约与非执行 cleanup review plan。
  - **v0.1 PR11**：v0.1.0 Public Preview 快速开始、action 示例、公开说明与 release checklist。
- **v0.2**：受控 cleanup planning + external tool adapter foundations。
  - **v0.2 PR12**：显式 external tool catalog、allowlist trust policy、无命令 invocation plan。
  - **v0.2 PR13**：证据驱动 external tool recommender、cleanup plan 集成、Skill action 和只读 CLI。
  - **当前 PR — v0.2 PR14**：显式路径 junk candidate scanner、保护目录阻断、cleanup preview 和 dry-run CLI。
  - 后续优先快速推进只读、计划、预览和推荐闭环，并从 Level 1 低风险能力开始建设受控执行，不无限推迟真实价值验证。
- **v0.3**：只开放低风险清理的受控执行。
- **v0.4**：Reputation Engine + 更新管理器。
- **v0.5**：Quarantine + Restore Manager。
- **v1.0**：Governed Managed Mode。

后续版本仍须遵守 Policy Engine 前置、最小权限、明确确认、可逆优先和审计完整性原则。

Every future milestone remains subject to Policy Engine gating, least privilege, explicit confirmation, reversibility, and audit integrity.

PR 不创建 tag；只有 `v0.1.0`、`v0.2.0` 等正式版本创建 tag。Commit message 使用中文。

JSONL 管审计，SQLite 管历史。PR3 只记录 dry-run，不代表执行；PR4 才进入 SQLite schema 与 history/audit store。
