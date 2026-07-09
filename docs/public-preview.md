# PC CleanGuard Skill v0.1.0 Public Preview

PC CleanGuard v0.1.0 Public Preview 是一个离线、可审计、安全优先的 Windows 系统治理 Skill。它让开发者和外部 AI 把显式 JSON 元数据转换为策略决策、报告、dry-run 审计、中文解释和非执行 cleanup review plan。

PC CleanGuard v0.1.0 Public Preview is an offline, auditable, safety-first Windows governance skill. It turns explicit JSON metadata into policy decisions, reports, dry-run audit events, Chinese explanations, and non-executable review plans.

## 适合谁 / Audience

- 需要在 AI 建议和 Windows 系统操作之间加入 Policy Engine 的 Agent 开发者。
- 需要审计分类、权限、证据和用户确认逻辑的安全研究者。
- 希望从命令行运行只读扫描与报告解释的开发者。

It is intended for agent developers, safety reviewers, and contributors who need a governed read-only workflow before any future system action is considered.

## v0.1.0 包含什么 / Included

1. 保守的 Policy Engine 和硬规则阻断。
2. Report Builder 和非执行 plan artifacts。
3. 强制 dry-run 的 JSONL audit contract。
4. 显式安全路径的 SQLite state/reputation stores。
5. Windows installed apps、startup items、services 和 scheduled tasks 的只读 collector/normalizer。
6. 纯 Python 只读 scan pipeline。
7. `scan` 和 `explain` CLI。
8. 离线 Mock AI Report Explainer 和 dry-run prompt。
9. 五个可验证的 AI-callable Skill actions。
10. 双语安全文档、JSON Schemas、示例和单元测试。

## 三条入口 / Three entry points

### CLI scan

```powershell
python -m pc_cleanguard.cli scan --input examples/scan_samples/pr7_readonly_scan_input.json --report output/report.json --audit output/audit.jsonl
```

### CLI explain

```powershell
python -m pc_cleanguard.cli explain --report output/report.json --output output/explanation.md --provider mock
```

### AI-callable actions

```python
from pc_cleanguard.skill import invoke_skill_action

response = invoke_skill_action(
    {
        "action": "build_cleanup_plan",
        "payload": {"report": {"decisions": []}},
    }
)
print(response.to_dict())
```

完整 request 示例见 [`examples/skill_actions/`](../examples/skill_actions/README.md)。

## Public Preview 边界 / Limitations

- 不接真实大模型 API，不读取环境凭据。
- Python 不自动运行 PowerShell collectors；collector 仅作为显式、人工运行的只读元数据输出器。
- 不删除、不卸载、不隔离、不禁用启动项/服务/计划任务，不写注册表。
- 不联网、不上传、不后台监控。
- `SAFE_REMOVE`、`STARTUP_OFF` 和 `QUARANTINE` 是需要用户确认的候选分类，不是执行授权。
- Cleanup plan 只包含符号化人工复核步骤，不包含命令。
- Public Preview 需从仓库根目录运行；尚未发布到 Python package index。

No output from v0.1.0 is proof of execution or authorization to modify a system.

## 验证与反馈 / Validation and feedback

提交反馈前，请运行：

```powershell
python -m compileall pc_cleanguard
python -m unittest discover -s tests
git diff --check
```

安全报告请遵循 [`SECURITY.md`](../SECURITY.md)；代码与规则贡献请遵循 [`CONTRIBUTING.md`](../CONTRIBUTING.md)。发布门禁见 [v0.1.0 release checklist](v0.1.0-release-checklist.md)。
