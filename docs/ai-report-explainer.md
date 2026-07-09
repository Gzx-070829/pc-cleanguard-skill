# PR9 AI 报告解释器 / AI Report Explainer

PR9 在只读 report JSON 之上增加用户可读的中文解释层。它只做 prompt 构造、离线 mock 解释和 dry-run prompt 导出，不连接真实模型 API。

PR9 adds a user-readable Chinese explanation layer over read-only report JSON. It provides prompt construction, deterministic mock output, and dry-run prompt export only. No live model service is connected.

## CLI 用法 / Usage

使用离线 Mock provider：

```powershell
python -m pc_cleanguard.cli explain `
  --report examples/reports/pr7_readonly_scan_pipeline_report.json `
  --output output/pr9_explainer_output.md `
  --provider mock
```

只导出受限 prompt，不运行任何模型：

```powershell
python -m pc_cleanguard.cli explain `
  --report examples/reports/pr7_readonly_scan_pipeline_report.json `
  --output output/pr9_prompt.md `
  --dry-run-prompt
```

`--report` 和 `--output` 必须由用户显式提供。Markdown 默认不覆盖；只有显式传入 `--overwrite` 时才会替换已有文件。

Both paths are explicit and required. Existing Markdown is preserved unless the caller deliberately supplies `--overwrite`.

## Provider

- `MockAIProvider`：根据白名单计数和分类生成确定性中文 Markdown，不联网。
- `DryRunPromptProvider`：原样返回已构造的安全 prompt，用于本地审查。

Neither provider reads environment credentials, opens a network connection, starts a process, or executes a collector. A future live provider is outside PR9.

## Prompt 隐私与安全 / Prompt privacy and safety

Prompt 不嵌入原始名称、路径、命令、证据自由文本或用户文件内容。它只携带白名单字段：数量、分类、风险级别、权限级别、确认要求与硬规则阻断状态。报告摘要被明确标记为不可信数据，不是 prompt 指令。

The prompt uses a bounded digest rather than raw report text. This reduces path disclosure, command echoing, and prompt-injection risk.

## 不可越过的边界 / Non-negotiable boundary

- AI 只能解释和建议，不能执行。
- AI 输出不是删除、卸载、隔离或禁用授权。
- 不确定项必须标记为需要用户确认。
- 不输出 PowerShell、cmd、reg、sc、schtasks 或其他可执行系统命令。
- 不能因单一来源、AI 判断、社区规则或在线声誉建议删除。
- 用户文档、代码、照片、浏览器资料和密码管理器默认保护。

PR9 does not clean, delete, uninstall, disable, modify the registry, execute PowerShell, access the network, or upload data.
