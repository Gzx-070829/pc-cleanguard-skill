# 5 分钟试用清理 Demo / Five-minute cleanup demo

PR16 demo 只在用户显式指定的安全目录中创建合成测试文件，让开发者无需准备真实垃圾即可体验 preview → execute → audit → report 闭环。

## 1. 初始化安全测试目录

在仓库根目录运行：

```powershell
python -m pc_cleanguard.cli demo init-cleanup --root .pcg-demo
```

该命令只在 `.pcg-demo` 下创建 temp、cache、log、crash dump、installer leftover 和空目录示例，并写入专用 marker 与 README。已有目录默认不会被覆盖。`--force` 也只接受先前由本命令创建且 marker 匹配的 demo root。

## 2. 一条命令运行默认 dry-run

```powershell
python -m pc_cleanguard.cli demo run-cleanup --root .pcg-demo --output .pcg-demo-output
```

输出目录包含：

- `preview.json`
- `dry_run_result.json`
- `audit.jsonl`
- `cleanup_report.md`

默认不会删除任何文件。打开 `cleanup_report.md` 即可查看候选大小、would-clean、skipped 和 blocked 汇总。

## 3. 可选：确认 demo L1 文件

先选择一个新的输出目录，然后显式确认：

```powershell
python -m pc_cleanguard.cli demo run-cleanup --root .pcg-demo --output .pcg-demo-confirmed --confirm
```

即使传入 `--confirm`，执行范围也固定为 marker 对应的 demo root，并复用 PR15 的 allow-root、protected-path、当前 metadata 和 L1 allowlist 门禁。只有 demo manifest 中路径和内容均未改变的 `temp_file`、`cache_file`、`log_file` 合成文件可被处理；后来加入或改写的文件会被阻断。crash dump、installer leftover 和空目录仍然跳过，目录永不删除。

## Refusal behavior / 拒绝行为

demo 会拒绝系统目录、Program Files、用户文档/桌面/图片/视频、UNC 路径、符号链接 root、未标记目录、demo root 内部的输出目录和已有输出目录。它不扫描全盘、不调用 PowerShell 或 subprocess、不联网、不上传。
