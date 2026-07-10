# Junk Cleanup Preview / 垃圾候选清理预览

PR14 提供第一条用户可见的清理价值链：从用户显式指定的本地目录读取文件系统元数据，识别常见垃圾候选，并生成 dry-run JSON 预览。它不删除、移动、改名或清空任何对象。

PR14 reads metadata only from explicit caller-supplied local directories, identifies common junk candidates, and writes a dry-run JSON preview. It performs no cleanup action.

## 支持的候选类别

- `temp_file`：`.tmp`、`.temp`
- `cache_file`：`.cache` 或明确的 cache 目录
- `log_file`：`.log`、`.trace`
- `crash_dump`：`.dmp`、`.dump`、`.mdmp`
- `installer_leftover`：`.msi`、`.msp`，仅作为中风险候选
- `empty_directory_candidate`：空目录候选，大小为 0，绝不自动移除

候选只依据路径、文件大小、修改时间和扩展名产生。scanner 不读取文件内容。每个 `JunkCandidate` 都固定为 `LEVEL_0_READ_ONLY`、`requires_user_confirmation=true`、`dry_run_only=true` 和 `execution_authorized=false`。

## 路径与资源边界

- 必须显式提供至少一个现有本地目录；不自动发现目录，不扫描全盘根路径。
- 拒绝 UNC、网络路径和符号链接遍历。
- 阻断 Documents、Desktop、Pictures、Videos、用户主目录、系统目录和代码仓库。
- 代码目录通过受保护名称或 `.git`、`pyproject.toml`、`package.json` 等元数据标记识别。
- 默认最多读取 10,000 个文件的元数据，累计文件大小上限为 10 GiB；达到上限立即停止并写入 warning。
- 多个显式路径重叠时只扫描外层路径一次。

本 PR 不提供保护目录 override。被阻断路径进入 `blocked_candidates`，不会进入垃圾候选。

## CleanupPreview

预览包含：

- `total_candidates`
- `total_reclaimable_bytes`
- `by_category`
- `blocked_candidates`
- `requires_confirmation`
- `top_candidates`
- `warnings`

`total_reclaimable_bytes` 只是候选文件大小合计，不表示空间已经释放。`top_candidates` 按大小排序，仍然只是待用户复核的 dry-run 候选。

## CLI

```powershell
python -m pc_cleanguard.cli clean preview --path C:\Explicit\Temp --path C:\Explicit\Cache --output output\cleanup-preview.json
```

`--path` 可以重复。CLI 默认拒绝覆盖已有输出；只有显式添加 `--overwrite` 才会替换预览 JSON。该命令只写报告，不调用系统清理工具或脚本。

Schema 位于 `schemas/junk_candidate.schema.json` 和 `schemas/cleanup_preview.schema.json`；合成示例见 `examples/cleanup/pr14_cleanup_preview.json`。
