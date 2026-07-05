# Audit JSONL / JSONL 审计日志

## Purpose / 用途

JSONL 是追加式审计日志：每个事件是一行独立 JSON。PR3 只支持 dry-run audit events，记录计划、模拟、阻断、拒绝或跳过，不记录真实系统动作。

JSONL is an append-only audit format with one JSON object per line. PR3 supports dry-run audit events only: plans, simulations, policy blocks, refusals, and skipped actions—not real system operations.

**JSONL 管审计，SQLite 管历史。PR3 只记录 dry-run，不代表执行。**

**JSONL carries audit events; SQLite will carry history. A PR3 dry-run record is not proof of execution.**

## Safety boundary / 安全边界

- Audit log 不是执行证明，只是计划、模拟或阻断记录。
- `dry_run` 必须为 `true`；PR3 的 `result` 不允许表示成功执行。
- logger 只接受调用方显式传入的本地 `.jsonl` 路径，不自动发现位置，不默认写入 AppData。
- logger 只追加，不覆盖、清空、移动或删除日志。
- logger 拒绝系统目录、UNC/network 路径和不符合 PR3 白名单的事件。
- PR3 不执行系统命令，不调用外部工具，也不联网或上传。

An audit log is not execution proof. The logger writes only to an explicit local `.jsonl` path, appends without truncation, rejects system/network paths, and revalidates every event immediately before writing.

## Event flow / 事件流程

未来真实执行必须先经过 Policy Engine，再由受控执行层完成动作，最后写 audit event。任何真实成功事件必须来自未来受控执行层，不属于 PR3。

Future real execution must pass the Policy Engine, be performed by a governed execution layer, and only then produce an audit event. Any real success event belongs to that future layer, never PR3.

SQLite schema 与 history/audit store 从 PR4 开始实现。PR3 本身不创建数据库，也不维护历史查询。

The SQLite schema and history/audit store begin in PR4. PR3 itself creates no database and provides no historical query store.
