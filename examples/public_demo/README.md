# PC CleanGuard v0.2 Public Demo artifacts

本目录是一组使用虚构路径和合成 metadata 的公开展示资产。它们帮助读者在不接触真实电脑数据的情况下理解 PR16/PR17 清理闭环。

- `preview.json`：两个候选的只读预览。
- `dry_run_result.json`：默认无确认运行，一个 `would_clean`、一个 `skipped`。
- `confirmed_result.json`：展示同一合成 L1 文件在全部门禁通过后的结果；它不是可重放命令。
- `audit.jsonl`：dry-run 决定的逐行审计事件。
- `cleanup_report.md`：面向用户的 Markdown 摘要。

这些文件不包含真实用户路径、命令、token 或软件指控。`confirmed_result.json` 是历史结果形状示例，不提供执行授权，也不能触发删除。

要在本机生成新的安全 demo，请运行：

```powershell
python -m pc_cleanguard.cli demo quickstart --root .pcg-demo --output .pcg-demo-output
```

该 quickstart 永远以 dry-run 运行。
