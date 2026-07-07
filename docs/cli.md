# PR8 最小只读 CLI / Minimal Read-only CLI

PR8 为 PR7 的只读扫描流水线提供一个薄命令行入口。CLI 只读取用户显式指定的 JSON，调用现有 normalizer、Policy Engine、Report Builder 和 dry-run Audit，然后写出用户显式指定的 report JSON 和 audit JSONL。

PR8 adds a thin command-line wrapper around the PR7 pipeline. It accepts one explicit JSON input and two explicit output paths. It does not discover or execute collectors.

## 用法 / Usage

```powershell
python -m pc_cleanguard.cli scan `
  --input examples/scan_samples/windows_pr6_normalized_sample.json `
  --report output/pr8_cli_report.json `
  --audit output/pr8_cli_audit.jsonl
```

`--input`、`--report` 和 `--audit` 都是必填参数。可以用 `--scan-id` 显式设置扫描标识。输出文件默认不覆盖；只有用户主动传入 `--overwrite` 时才会替换已有文件。

All three paths are required. Use `--scan-id` for an explicit identifier. Existing outputs are preserved by default and replaced only with an explicit `--overwrite` flag.

成功时，CLI 在 stdout 输出单行 JSON 摘要，并返回退出码 `0`。输入、路径或写入错误会输出到 stderr，并返回 `2`。

## 安全边界 / Safety boundary

- CLI 不运行 PowerShell，不自动执行 collector。
- CLI 不清理、删除、卸载、隔离或禁用任何对象。
- CLI 不联网、不上传、不后台监控。
- report 是治理建议，不是执行授权。
- audit JSONL 的所有事件仍强制 `dry_run=true` 和 `command_summary=null`。
- PR7 的 UNC、device path、系统目录、文件大小和扩展名校验继续生效。

The CLI performs no system action and grants no execution authorization. Its only writes are the two explicit, validated output artifacts.
