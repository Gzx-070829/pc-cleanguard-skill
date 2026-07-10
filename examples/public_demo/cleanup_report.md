# PC CleanGuard Public Demo Cleanup Report

> Synthetic example only. This report is not cleanup authorization.
> 仅为合成示例，本报告不是清理授权。

## Summary / 摘要

- Candidates / 候选：2
- Reclaimable / 可释放：76 B
- Cleaned / 已清理：0 (0 B)
- Would clean / 待确认：1
- Skipped / 已跳过：1
- Blocked / 已阻断：0

## Outcomes / 结果

| Path | Category | Dry-run status | Reason |
| --- | --- | --- | --- |
| `C:\SyntheticDemo\temp\example.tmp` | temp_file | would_clean | Missing explicit confirmation |
| `C:\SyntheticDemo\dumps\example.dmp` | crash_dump | skipped | Outside the L1 allowlist |

## Safety notes / 安全说明

- Dry-run made no filesystem change.
- A confirmed run may clean only a regular temp/cache/log file after every PR15 gate passes.
- Crash dumps, installer leftovers, and directories remain skipped.
