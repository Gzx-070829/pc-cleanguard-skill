# PC CleanGuard Cleanup Report / 清理报告

> This report summarizes an explicit cleanup preview and optional L1 execution result.
> 本报告仅汇总显式预览与可选的 L1 执行结果，不扩大执行权限。

## Summary / 摘要

- Candidates / 候选：6
- Reclaimable / 可释放：178 B
- Cleaned / 已清理：0 (0 B)
- Would clean / 待确认：3
- Skipped / 已跳过：3
- Blocked / 已阻断：0

## By category / 按类别

| Category | Count | Bytes |
| --- | ---: | ---: |
| temp_file | 1 | 34 B |
| cache_file | 1 | 30 B |
| log_file | 1 | 29 B |
| crash_dump | 1 | 42 B |
| installer_leftover | 1 | 43 B |
| empty_directory_candidate | 1 | 0 B |

## Top items / 重点项目

| Path | Category | Status | Reclaimed |
| --- | --- | --- | ---: |
| C:\SyntheticDemo\installers\example.old | installer_leftover | skipped | 0 B |
| C:\SyntheticDemo\dumps\example.dmp | crash_dump | skipped | 0 B |
| C:\SyntheticDemo\temp\example.tmp | temp_file | would_clean | 0 B |

## Safety notes / 安全说明

- 报告用于展示预览与执行结果，不构成新的清理授权。
- 只有显式确认且通过 allow-root 与 L1 安全门的文件才能由现有执行器处理。
- crash dump、installer leftover 与目录候选不会被 L1 执行器删除。
