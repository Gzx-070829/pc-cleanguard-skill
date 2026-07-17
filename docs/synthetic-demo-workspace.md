# Synthetic Demo Workspace

仓库可能位于 Desktop，而 Desktop 必须保持保护。v0.4.1 不给 Desktop 加 allowlist；`demo acceptance` 在系统临时目录的固定命名空间创建随机 workspace：

```text
%TEMP%\PC-CleanGuard\acceptance\<random-id>\
```

workspace 使用 `.pcg-synthetic-workspace.json` 记录随机 nonce、创建者、时间、预期相对路径、SHA-256、允许操作和精确根路径。只有 manifest 登记的合成 temp/cache/log 文件可以进入 preview、quarantine 与 restore。

以下任一情况都会 fail-closed：

- 根不在专用 temp 命名空间；
- manifest、nonce、root 或 workspace ID 不一致；
- 文件缺失、hash 改变或出现未知 entry；
- 路径穿越、symbolic link 或 reparse point；
- 用普通目录伪造 manifest。

```powershell
python -m pc_cleanguard.cli demo acceptance --output .pcg-demo-acceptance --confirm-synthetic
```

该验收会隔离合成 L1 文件、恢复一个 item、核对 SHA-256 和 audit。它不永久删除，不触碰真实 Desktop 文件，也不提供通用 protected-root bypass。
