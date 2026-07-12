# PC CleanGuard 试用摘要

- 清理候选数量：6
- 预计可释放空间：177 bytes
- 已隔离/可恢复：0
- 已跳过：3
- PUP 线索：1（synthetic demo）

## 安全边界

默认 dry-run；确认后默认隔离。不联网、不上传、不静默删除。PUP 线索不是删除、卸载或禁用授权。

## 如何恢复

确认隔离后使用 `quarantine list` 查看条目，再使用 `quarantine restore` 恢复。
