# PR7 只读扫描流水线 / Read-only Scan Pipeline

PR7 将已有的只读组件连成一条实际可用的离线治理链路：

```text
显式 JSON 输入
  → normalizers
  → GovernanceTarget
  → Policy Engine
  → Report Builder
  → dry-run AuditEvent
  → 可选 report JSON / audit JSONL
```

The pipeline connects existing read-only components into a useful offline governance chain. It processes metadata; it does not invoke collectors or modify Windows.

## 输入 / Input

`load_scan_json_file(path)` 只读取调用方显式传入的 `.json` 文件，上限 10 MiB。它不遍历目录、不自动发现 collector 输出，并拒绝 UNC、Windows device 和系统目录路径。JSON 顶层必须是对象。

Supported arrays are `installed_apps` (or `software_entries`), `startup_items`, `services`, and `scheduled_tasks`. Missing arrays are treated as empty. `privacy_mode` is offline-only.

```python
from pc_cleanguard.pipeline import (
    load_scan_json_file,
    run_readonly_scan_pipeline,
    write_pipeline_audit_jsonl,
    write_pipeline_report,
)

data = load_scan_json_file("my-explicit-input.json")
result = run_readonly_scan_pipeline(data, scan_id="scan:local-example")

print(result.normalized_counts)
print(len(result.targets), len(result.decisions), len(result.audit_events))

write_pipeline_report("output/my-report.json", result)
write_pipeline_audit_jsonl("output/my-audit.jsonl", list(result.audit_events))
```

## 输出 / Output

`ScanPipelineResult` 包含 input summary、normalized counts、targets、policy decisions、report、dry-run audit events、可选 SQLite scan records 以及 warnings。`result.to_dict()` 可直接 JSON 序列化。

Writers accept only explicit safe local `.json` or `.jsonl` paths. They create the explicitly named parent directory when needed and use exclusive creation by default. Existing output is replaced only when the caller deliberately passes `explicit_overwrite=True`.

## 安全边界 / Safety boundary

- Python 不执行 PowerShell collector，不启动子进程。
- 不清理、删除、卸载、隔离，不修改启动项、服务、计划任务或注册表。
- 不联网、不上传、不后台监控。
- `SAFE_REMOVE`、`STARTUP_OFF` 和 `QUARANTINE` 只是候选建议，不是执行授权。
- 所有 audit event 强制 `dry_run=true`，`command_summary=null`，不代表真实动作成功。

No pipeline output is an execution authorization or proof of system modification.
