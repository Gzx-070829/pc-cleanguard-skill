# L1 Controlled Cleaner / L1 低风险受控清理器

PR15 是 PC CleanGuard 的第一条真实清理路径。它只处理 PR14 cleanup preview 中的 `temp_file`、`cache_file` 和 `log_file` 普通文件；默认仍为 dry-run，只有显式 `--confirm` 且全部门禁通过时才删除文件。

PR15 is the first real cleanup path. It is limited to ordinary temp, cache, and log files from a structurally valid PR14 cleanup preview. Dry-run remains the default.

当前实现只处理 preview JSON 中实际序列化的 `top_candidates`；未出现在该列表中的扫描候选不会被执行。

## 执行门禁

每个候选在执行瞬间必须同时满足：

1. 输入是结构完整、`dry_run_only=true`、`execution_authorized=false` 的 PR14 preview JSON。
2. 候选自身保持 `dry_run_only=true`、`requires_user_confirmation=true` 和 Level 0 preview 属性。
3. category 属于 L1 allowlist：`temp_file`、`cache_file`、`log_file`。
4. 路径当前仍存在、是普通文件且不经过符号链接。
5. 路径位于用户显式提供的 `--allow-root` 内。
6. 路径不属于 Documents、Desktop、Pictures、Videos、系统目录、Program Files、代码仓库或浏览器 profile。
7. 当前路径元数据重新匹配 preview category。
8. CLI 显式传入 `--confirm`。

任一门禁失败都不会删除文件。`crash_dump`、`installer_leftover` 和 `empty_directory_candidate` 固定为 `skipped`。目录树和空目录不属于 PR15 的执行范围。

## CLI

默认 dry-run：

```powershell
python -m pc_cleanguard.cli clean execute --preview preview.json --allow-root C:\Explicit\Temp --result result.json --audit audit.jsonl
```

显式确认 L1 文件清理：

```powershell
python -m pc_cleanguard.cli clean execute --preview preview.json --allow-root C:\Explicit\Temp --result result.json --audit audit.jsonl --confirm
```

`--allow-root` 可以重复。result 或 audit 已存在时默认拒绝执行，确保不会先删除再因输出冲突失败；只有显式 `--overwrite` 才替换输出产物。

## 结果与审计

每个结果包含 `path`、`action`、`status`、`reason`、`bytes_reclaimed`、`evidence` 和完整 `audit_event`。状态包括：

- `would_clean`：未确认的 dry-run 结果，文件保持不变。
- `cleaned`：所有门禁通过后的 L1 文件删除结果。
- `blocked`：路径、preview 或运行时复核未通过。
- `skipped`：category 不在 L1 allowlist，或为目录候选。
- `failed`：已确认执行过程中出现文件系统错误。

审计 JSONL 在候选处理前打开，并在每个结果后立即写入和 flush。`bytes_reclaimed` 只统计成功清理时重新读取的当前文件大小；dry-run、blocked、skipped 和 failed 均为 0。

## 明确不做

PR15 不删除目录树、不清空目录、不卸载软件、不修改启动项/服务/计划任务/注册表，不调用 PowerShell 或外部进程，不联网、不上传。它不是一键清理器，也不向 AI Skill action 暴露自动执行入口。

Schema：`schemas/cleanup_execution_result.schema.json`。合成示例：`examples/cleanup/pr15_execution_result.json`。
