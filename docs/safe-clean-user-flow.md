# 安全清理入口 / Safe Clean Flow

普通用户建议先运行：

```console
python -m pc_cleanguard.cli clean safe --path <dir> --output <dir>
```

该命令生成 preview、dry-run result、audit、Markdown report 和 summary，不修改候选文件。

确认隔离模式：

```console
python -m pc_cleanguard.cli clean safe --path <dir> --output <dir> --confirm --quarantine-root <dir>
```

`clean safe` 不支持永久删除。专家永久删除只能通过 `clean execute`，且同时需要 `--confirm --permanent --i-understand-permanent-delete`。所有模式仍受 preview、L1 allowlist、allow-root、protected path、Developer Guard 和运行时复核约束。
