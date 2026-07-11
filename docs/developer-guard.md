# Developer Guard / 开发者保护引擎

Developer Guard 是纯路径分类器，目的是避免垃圾规则误伤源代码、依赖树、虚拟环境、IDE metadata 和开发工具缓存。它不扫描文件内容，也不授予清理权限。

## Protected paths

- Git metadata：`.git`
- Python environments：`.venv`、`venv`、`env`、Conda `envs`
- JavaScript dependencies/caches：`node_modules`、`.npm`、`.pnpm-store`、`.yarn`
- IDE metadata：`.idea`、`.vscode`
- Python package cache：pip cache
- Rust：Cargo registry/cache
- JVM：Gradle cache、Maven repository
- Compute development cache：CUDA/NVIDIA cache
- 调用方显式声明的 user code roots

## API

```python
from pc_cleanguard.protection import (
    classify_developer_path,
    is_protected_developer_path,
)

decision = classify_developer_path(
    r"C:\SyntheticWorkspace\app\node_modules\package\cache.tmp"
)
assert decision.protected
assert decision.to_dict()["execution_authorized"] is False
```

`DeveloperGuardDecision.to_dict()` 输出 path、protected、reason、evidence、protection_level、matched_rule 与固定的 `execution_authorized=false`。Schema 位于 [`schemas/developer_guard_decision.schema.json`](../schemas/developer_guard_decision.schema.json)。

## Defense in depth

1. `JunkScanner` 在进入目录前调用 Developer Guard；命中后整个目录作为 `BlockedCandidate` 返回，不枚举其内部候选。
2. `CleanupExecutor` 不信任 preview。即使 preview 被篡改为指向开发路径，也会在现有 PR15 confirmation 与唯一 `Path.unlink()` 前再次调用 Developer Guard并返回 `blocked`。
3. 调用方可向 scanner/executor 提供显式 `user_code_roots`，保护没有 `.git` 等 marker 的代码目录。

Developer Guard 不扩大真实删除范围。普通 temp 文件仍需经过 preview、L1 allowlist、allow-root、protected path、runtime revalidation、显式确认与 audit gate。

## Limitations

PR18 使用保守的路径组件匹配，不解析项目文件、不读取依赖内容、不自动发现所有开发环境。无法确认的开发目录应由调用方作为 `user_code_roots` 显式声明；误报反馈应提供脱敏 synthetic path。
