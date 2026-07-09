# PR12 外部工具适配层基础 / External Tool Adapter Foundation

PR12 为 v0.2 建立外部卸载/清理工具的治理基础。它只描述工具、评估信任并生成符号化调用计划；不会下载、发现、启动或执行任何外部工具。

PR12 establishes the governance foundation for external uninstall and cleanup tools. It describes tools, evaluates trust, and produces symbolic invocation plans only. It does not download, discover, launch, or execute any tool.

## 三层模型 / Three-layer model

```text
Explicit ExternalToolCatalog
        → ToolTrustPolicy allowlist
        → ExternalToolInvocationPlan (plan_only, Level 0)
```

1. `ExternalToolRecord` 记录工具名称、类型、HTTPS 官网、许可证、支持动作、风险级别和确认要求。
2. `ExternalToolCatalog` 仅包含显式提供的 record；PR12 没有默认发现、扫描或下载。
3. `ToolTrustPolicy` 只信任精确匹配的 allowlisted `tool_id`，并可限制适配器类型。
4. `ExternalToolInvocationPlan` 是 `plan_only`、`LEVEL_0_READ_ONLY`、`execution_authorized=false` 的审查产物。

## 支持类型 / Supported types

- `official_uninstaller`
- `winget`
- `vendor_cleanup_tool`
- `trusted_third_party_uninstaller`

类型支持不等于允许调用。每个 record 都仍须出现在显式 allowlist 中，且每个计划都需用户确认。

Supporting a type does not authorize invocation. Every record must still be explicitly allowlisted, and every plan requires user confirmation.

## 构造计划 / Build a plan

```python
from pc_cleanguard.core.models import RiskLevel
from pc_cleanguard.external_tools import (
    ExternalToolCatalog,
    ExternalToolRecord,
    ExternalToolType,
    ToolTrustPolicy,
    build_external_tool_invocation_plan,
)

record = ExternalToolRecord(
    tool_id="example-official-tool",
    name="Example Tool Metadata",
    tool_type=ExternalToolType.OFFICIAL_UNINSTALLER,
    official_website="https://tools.example.invalid/example-tool",
    license="Example License",
    supported_actions=("standard_uninstall",),
    risk_level=RiskLevel.HIGH,
    required_user_confirmation=True,
)
catalog = ExternalToolCatalog((record,))
policy = ToolTrustPolicy((record.tool_id,))

plan = build_external_tool_invocation_plan(
    catalog,
    policy,
    tool_id=record.tool_id,
    requested_action="standard_uninstall",
    reason="A reviewed candidate needs a future human decision.",
    evidence=({"source": "policy_decision", "fact": "candidate requires review"},),
)
print(plan.to_dict())
```

返回的计划包含 `evidence`、`reason`、`required_user_confirmation`、`execution_level` 和 `blocked_if_untrusted`。它不包含命令、路径参数、执行函数或工具启动授权。

## 信任边界 / Trust boundary

- 不在 catalog 中的工具不能进入计划。
- cataloged 但未 allowlist 的工具只产生 `blocked=true` 的解释性计划。
- allowlisted 工具也仅产生需确认的 Level 0 plan，而不产生调用授权。
- `SAFE_REMOVE` 不等于外部工具调用许可。

## PR12 明确不做的事 / Explicit non-goals

- 不下载 exe、msi 或任何工具资产。
- 不启动外部工具、不运行 winget、不运行 uninstall string。
- 不调用子进程、不联网、不上传。
- 不删除文件、不卸载软件、不修改注册表或 Windows 系统状态。

Schemas: [`external_tool.schema.json`](../schemas/external_tool.schema.json) and [`external_tool_invocation_plan.schema.json`](../schemas/external_tool_invocation_plan.schema.json).
