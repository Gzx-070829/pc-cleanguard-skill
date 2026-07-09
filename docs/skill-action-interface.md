# PR10 AI 可调用 Skill 动作接口 / AI-callable Skill Action Interface

PR10 为外部 AI 提供统一的 JSON 动作门面。它只编排已有的 PR7 只读 pipeline、PR9 离线报告解释器和显式本地产物写出。该接口不是执行层。

PR10 gives external AI callers one JSON action envelope. It orchestrates existing read-only analysis, offline explanation, non-executable planning, and explicit artifact writing. It is not a system execution layer.

## 动作 / Actions

- `scan_from_json`：将显式 JSON object 传入 PR7 pipeline，返回 targets、policy decisions、report 和 dry-run audit events。
- `explain_report`：调用 PR9 Mock 或 dry-run prompt provider，返回中文 Markdown 解释。
- `build_cleanup_plan`：把 policy decision 转换为符号化人工复核步骤。它不生成命令，不执行计划。
- `write_report`：将调用方提供的 report object 写入显式安全 `.json` 路径。
- `write_audit`：将已验证的 dry-run events 写入显式安全 `.jsonl` 路径。

## 请求 / Request

```python
from pc_cleanguard.skill import invoke_skill_action

response = invoke_skill_action(
    {
        "schema_version": "0.1",
        "request_id": "request:example",
        "action": "scan_from_json",
        "payload": {
            "input_data": {
                "privacy_mode": "offline",
                "installed_apps": [],
                "startup_items": [],
                "services": [],
                "scheduled_tasks": [],
            }
        },
    }
)

print(response.to_dict())
```

请求 schema 会按 action 约束 payload 的必填字段和可选字段。运行时 `SkillActionRequest` 还会拒绝未知 action、未知顶层字段和多余 payload 字段。

## 响应 / Response

每个动作响应都必须包含：

- `requires_user_confirmation`
- `execution_level`，PR10 固定为 `LEVEL_0_READ_ONLY`
- `evidence`
- `execution_authorized`，PR10 固定为 `false`
- JSON-safe `result`

Every action returns a JSON-safe response with explicit confirmation, execution-level, and evidence fields. The interface itself cannot elevate permission or authorize execution.

## Cleanup plan

Cleanup plan 是 `plan_only` 治理产物。每个 step 只包含 target identity、classification、symbolic review action、proposed permission level、confirmation requirement、blocked status 和 evidence。它不包含命令或可执行字段。

`SAFE_REMOVE` 只会生成 `REVIEW_REMOVAL_CANDIDATE`；`STARTUP_OFF` 只会生成 `REVIEW_STARTUP_CANDIDATE`。两者均必须要求用户确认，且 `execution_authorized=false`。`BLOCK` 或 Level 5 只能生成 `BLOCKED_BY_POLICY`。

## 边界 / Boundary

- 不删除文件、不卸载软件、不禁用启动项。
- 不停止或禁用服务，不修改计划任务或注册表。
- 不自动运行 PowerShell 或 collector。
- 不读取环境凭据、不联网、不上传。
- 报告和审计写入只允许调用方显式提供的安全本地路径，默认不覆盖。

The three PR10 schemas are `skill_action_request.schema.json`, `skill_action_response.schema.json`, and `cleanup_plan.schema.json`.
