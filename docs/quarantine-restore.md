# Quarantine and Restore / 隔离区与恢复

PR19 提供 manifest-backed 可逆文件隔离。只处理显式普通文件，不处理目录树，不提供 purge，也不会永久删除隔离区内容。

```powershell
python -m pc_cleanguard.cli quarantine add --root C:\Safe\Quarantine --path C:\Scratch\sample.tmp --reason "explicit review"
python -m pc_cleanguard.cli quarantine list --root C:\Safe\Quarantine
python -m pc_cleanguard.cli quarantine restore --root C:\Safe\Quarantine --item-id <id>
```

manifest 记录 original/quarantine path、SHA-256、大小、mtime、reason、evidence、时间与状态。restore 在移动前验证 hash/size；原路径已存在时拒绝覆盖。

## Cleanup integration

```powershell
python -m pc_cleanguard.cli clean execute --preview preview.json --allow-root C:\Scratch --result result.json --audit audit.jsonl --confirm --quarantine-root C:\Safe\Quarantine
```

该模式复用 preview、显式确认、allow-root、L1 allowlist、protected path、Developer Guard 与 runtime revalidation。temp/cache/log 普通文件进入 quarantine；crash dump、installer leftover 与目录继续 skipped。无 `--quarantine-root` 时保留 PR15 原有受控删除行为。

Quarantine root 不能位于系统目录、Program Files、用户文档/桌面/图片/视频或开发者保护路径。PR19 不联网、不上传、不修改注册表、不卸载软件、不调用 PowerShell 或 subprocess。
