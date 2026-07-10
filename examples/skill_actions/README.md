# Skill action examples

本目录包含 PC CleanGuard 的六个 AI-callable action request 示例。所有示例都是离线、Level 0 治理请求，不包含清理执行授权。

This directory contains one JSON request for every public-preview action. Each request is offline, JSON-safe, and non-executing.

## 运行示例 / Run an example

在仓库根目录中运行：

```python
import json
from pathlib import Path

from pc_cleanguard.skill import invoke_skill_action

request = json.loads(
    Path("examples/skill_actions/scan_from_json.request.json").read_text(
        encoding="utf-8"
    )
)
response = invoke_skill_action(request)
print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))
```

`write_report` 和 `write_audit` 示例使用 `output/` 下的显式路径。文件如已存在，动作会拒绝覆盖；示例不启用 `explicit_overwrite`。

The write examples use explicit paths under `output/` and preserve existing files by default.

PR13 的 `recommend_external_tools_request.json` 展示 cleanup plan、显式 catalog、allowlist 与 installed-app metadata 的组合输入。对应 response 只包含 plan-only recommendations。

`v0.2_cleanup_agent_flow.json` 展示 cleanup preview、dry-run execute、Markdown report、离线 explain 与 Skill action 的推荐编排顺序。它是说明性 workflow，不是执行请求，也不授权删除。

## 响应约束 / Response contract

每个成功响应都包含 `requires_user_confirmation`、`execution_level`、`evidence`、`execution_authorized` 和 `result`。Public Preview 中 `execution_level` 始终为 `LEVEL_0_READ_ONLY`，`execution_authorized` 始终为 `false`。
