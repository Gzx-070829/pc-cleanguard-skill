# SQLite State and Reputation Knowledge Store / SQLite 状态与声誉知识库

## Roles / 角色

SQLite 是 PC CleanGuard 的可查询记忆系统；JSONL 是追加式审计黑盒。State Store 记录本机历史、扫描、决策、审计索引和用户偏好。Reputation Knowledge Store 记录软件声誉证据，不是黑名单。

SQLite is PC CleanGuard's queryable memory; JSONL is its append-only audit black box. The State Store holds local scans, targets, decisions, audit indexes, and preferences. The Reputation Knowledge Store holds evidence and metadata—not a blacklist.

## Non-negotiable principles / 不可协商原则

- Reputation row is not an execution authorization. / 声誉记录不是执行授权。
- Community report is not a verdict. / 社区报告不是最终裁决。
- PUP evidence is not malware conviction. / PUP 证据不是恶意软件定罪。
- `SAFE_REMOVE_CANDIDATE` is not uninstall permission. / `SAFE_REMOVE_CANDIDATE` 不是卸载许可。
- Policy Engine remains the final gate. / 最终仍由 Policy Engine 把关。
- SQLite stores evidence and history; it does not execute. / SQLite 存证据和历史，不执行系统操作。

数据库绝不能成为流氓软件黑名单、垃圾软件黑名单、自动删除列表或自动卸载列表。查询结果只包含 evidence 与 metadata，不包含执行授权或命令字段。

The database must never become a junkware blacklist, automatic removal list, or automatic uninstall list. Query results contain evidence and metadata only; they expose no execution-authorization or command field.

## Path and SQL safety / 路径与 SQL 安全

所有 Store 都要求调用方显式传入本地 `.sqlite` 或 `.db` 路径。PR4 不自动发现路径、不默认写入 AppData，并拒绝 UNC、设备路径和明显系统目录。只允许为该显式路径创建父目录。

Every store requires an explicit local `.sqlite` or `.db` path. PR4 performs no path discovery, has no AppData default, and rejects UNC/device paths and obvious system directories. It may create only the explicit path's parent directory.

Schema SQL 是内部常量；所有业务写入和查询都使用参数绑定。PR4 不接受任意 SQL，不提供 raw query、database clear、database delete 或 export API。

Schema SQL is internal and constant. Every data write and query uses bound parameters. PR4 accepts no arbitrary SQL and exposes no raw-query, database-clear, database-delete, or hidden-export API.

## Scope / 范围

PR4 不联网、不扫描、不清理、不卸载、不上传。后续版本才会把 reputation evidence 作为受限证据融合进 Decision Fusion / Policy Engine；即使融合，Policy Engine 仍是最终安全门。

PR4 performs no networking, scanning, cleanup, uninstall, or upload. A future version may feed reputation evidence into governed decision fusion, but the Policy Engine remains the final safety gate.
