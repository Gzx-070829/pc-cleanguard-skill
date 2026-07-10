# Cleanup Report Showcase / 清理报告展示

PR16 将 PR14 cleanup preview 与 PR15 execution result 合并为一份便于用户审阅的摘要，并可导出 Markdown。报告层只读取两个显式 JSON 文件，不扫描目录、不执行清理，也不扩大原执行结果的权限。

## CLI

```powershell
python -m pc_cleanguard.cli clean report `
  --preview output\cleanup-preview.json `
  --result output\cleanup-result.json `
  --output output\cleanup-report.md
```

输出已存在时默认拒绝覆盖；只有调用方显式传入 `--overwrite` 才能替换 Markdown 文件。

## Summary fields

- `total_candidates` / `total_reclaimable_bytes`：preview 中的候选数与估算大小。
- `cleaned_count` / `cleaned_bytes`：执行结果中真正成功的 L1 文件及实际释放字节。
- `would_clean_count`：未传确认参数时会处理、但尚未修改的项目。
- `skipped_count` / `blocked_count`：超出 L1 范围或未通过路径门禁的项目。
- `by_category` / `by_status`：类别与结果状态分组。
- `top_items`：合并 preview 大小和 execution 状态后的重点项目。
- `safety_notes`：报告自身不构成清理授权的固定说明。

示例见 [`examples/cleanup/pr16_cleanup_report.md`](../examples/cleanup/pr16_cleanup_report.md) 和 [`examples/cleanup/pr16_cleanup_summary.json`](../examples/cleanup/pr16_cleanup_summary.json)。

## Safety boundary / 安全边界

`clean report` 不删除、不移动、不联网、不上传。它不会把 `would_clean`、候选大小或 Markdown 文本解释为执行授权。真实 L1 清理仍只能由 PR15 executor 在显式 `--confirm`、allow-root、运行时重新分类、protected-path 检查和审计门全部通过后完成。
