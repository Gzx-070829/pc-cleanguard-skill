# 5 分钟用户试用 / Five-minute User Trial

PC CleanGuard 用一条命令展示安全清理预览、审计报告和 PUP 线索：

```console
python -m pc_cleanguard.cli trial run --root .pcg-demo --output .pcg-trial
```

默认模式只创建 synthetic demo 文件并 dry-run，不移动或删除候选。请依次阅读 `START_HERE.md`、`user_summary.md`、`cleanup_report.md`、`pup_insight.md` 和 `audit.jsonl`。

确认隔离试用：

```console
python -m pc_cleanguard.cli trial run --root .pcg-demo --output .pcg-trial-confirm --confirm --quarantine-root .pcg-quarantine
```

确认模式只把 demo root 内通过 L1 安全门的 temp/cache/log 文件移入可恢复隔离区。`--quarantine-root` 可省略；省略时自动使用 `.pcg-quarantine`。查看和恢复：

```console
python -m pc_cleanguard.cli quarantine list --root .pcg-quarantine
python -m pc_cleanguard.cli quarantine restore --root .pcg-quarantine --item-id <id>
```

`trial run` 不支持 permanent，不联网、不上传、不调用 PowerShell 或外部进程。PUP 线索使用 synthetic 本地 seed，只是提示，不是删除、卸载或禁用授权。
