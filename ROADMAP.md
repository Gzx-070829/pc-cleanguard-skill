# Roadmap

PC CleanGuard 以用户可见闭环为 Sprint PR 单位快速推进，同时保持“不静默删除、不绕过确认、不联网泄露、不把 AI 建议当授权”的安全底线。

## v0.1.0 — Read-only governance loop / 只读治理闭环

已发布。包括 Policy Engine、报告与声明式 plan、dry-run JSONL 审计、SQLite state/reputation evidence、Windows 只读 collector/normalizer、只读 scan pipeline、最小 CLI、离线 AI explainer 和 AI-callable Skill action。

## v0.2.0 — Controlled L1 cleanup + public demo / L1 受控清理与可试用 Demo

当前发布候选。包括：

- 外部工具 catalog、trust policy 与 plan-only recommender；
- 显式路径 junk candidate scan 与 cleanup preview；
- 默认 dry-run、显式确认、allow-root、protected-path、runtime revalidation 与强制审计约束下的 L1 temp/cache/log 文件清理；
- cleanup summary、Markdown report、合成 demo root 和一条命令 dry-run quickstart；
- Public Demo 示例包、AI Agent flow、issue templates 与 v0.2.0 release checklist。

v0.2.0 不卸载软件、不删除目录、不扩大到 crash dump/installer leftover，不自动执行 PowerShell 或外部工具，不联网或上传。

## v0.3 — Stronger external-tool and uninstaller adapters / 更强外部工具与卸载器适配

在独立 trust policy、显式用户确认、可审计 invocation contract 和失败隔离前提下，推进官方卸载器、winget 与厂商 cleanup tool 的受控适配。不会把 catalog/reputation/AI recommendation 直接转成执行授权。

## v0.4 — Recovery, quarantine, and GUI / 回滚、隔离区与 GUI

建设更完整的 rollback/restore contract、可逆 quarantine、操作历史与面向普通用户的可视化 review/confirmation 界面。Level 4/5 与系统关键路径仍保持硬阻断。

## Long-term / 长期方向

迈向 Governed Managed Mode：AI 可以执行，但执行必须经过 Policy Engine、最小权限、证据链、明确确认、可逆优先和完整审计。

PR 不创建 tag；只有 `v0.1.0`、`v0.2.0` 等正式版本创建 tag。Commit message 使用中文。研发原则见 [docs/development-principles.md](docs/development-principles.md)。
