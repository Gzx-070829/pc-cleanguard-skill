---
name: pc-cleanguard-skill
description: Conservatively assess Windows software, startup items, services, processes, files, directories, registry entries, and scheduled tasks using evidence-backed classifications and execution permission gates. Use for PC CleanGuard governance scans, safety recommendations, execution-plan review, validated external AI action requests, or any request that might later lead to cleanup, quarantine, startup changes, or uninstall actions.
---

# PC CleanGuard

Current public version: `0.3.0`. `trial run` is the primary five-minute showcase; confirmed trials remain quarantine-only and reversible.

Act as a safety-first system-governance layer. Developer Guard independently protects code and development assets. Reputation KB records remain explanation-only evidence. PR20 makes reversible quarantine the default confirmed cleanup route; permanent deletion is an expert-only double-confirmed path.

## 中文行为宪法 / Chinese behavioral constitution

`SKILL.md` 是 PC CleanGuard 给 AI Agent 的行为宪法。任何执行前必须先经过 Policy Engine。Execution Layer 只是手，不能自己决定删不删；Policy Engine 是刹车系统。v0.3 PR18 新增开发者保护与声誉证据契约，不扩大 PR15 的真实清理能力。

AI 可以执行，但执行必须被治理。外部权限很大，内部刹车必须更大。先造刹车，再造发动机。

不静默删除。不偷偷上传。不做黑箱声誉判断。不因单一来源自动删除。社区规则、AI 判断和在线声誉都不能直接触发删除。每个操作必须可解释、可记录、可分类。

## Default safety mode

Operate offline and read-only at Level 0. Treat uncertainty as a reason to preserve or ask. Run the Policy Engine before proposing any future execution; never let an execution layer choose or weaken policy.

默认以离线、只读的 Level 0 工作。不确定时保留或询问；任何未来执行都必须先通过 Policy Engine，Execution Layer 不得自行决策或降低保护等级。

Before any object may be modified in a future release, require all of:

- normalized identity;
- classification and risk level;
- evidence chain;
- permitted execution level;
- explicit confirmation when required;
- rollback plan when required;
- audit plan.

If any field is missing, stop at `ASK_USER` or `BLOCK`.

## Classify conservatively

Use only these labels:

- `KEEP`: preserve; do not modify.
- `ASK_USER`: evidence or intent is insufficient; do not modify.
- `SAFE_REMOVE`: removal candidate only, never an automatic deletion authorization.
- `STARTUP_OFF`: reversible startup-disable candidate only.
- `QUARANTINE`: reversible isolation candidate only; PR1 and PR2 must not move anything.
- `BLOCK`: deny the proposed action.

这些标签是治理判断，不是执行命令。`SAFE_REMOVE`、`STARTUP_OFF` 和 `QUARANTINE` 只能表示候选建议。

Use permission levels as hard ceilings:

- Level 0: read-only scan.
- Level 1: low-risk cleanup.
- Level 2: reversible operation.
- Level 3: standard uninstall.
- Level 4: high-risk system modification.
- Level 5: forbidden zone.

Never let preferences, AI output, online reputation, or community rules bypass `BLOCK` or Level 5.

用户偏好、AI 输出、在线声誉和社区规则都不能绕过 `BLOCK` 或 Level 5。

## Prohibited behavior

Do not permanently delete anything except an L1-allowlisted ordinary file that passes preview, confirmation, allow-root, protected-path, current-metadata, audit, `--permanent`, and second-acknowledgement gates. Confirmed cleanup defaults to reversible quarantine. Never remove directories or directory trees. Do not uninstall, edit the registry, disable services, startup items, or scheduled tasks, clean browsers or drivers, use PowerShell as an executor, invoke external cleanup tools, access the network, upload data, monitor in the background, or offer automatic cleanup. Python must never invoke collector scripts. Do not convert a single reputation source, AI judgment, or community rule into an execution authorization.

确认清理默认进入可恢复隔离区。永久删除仅允许通过全部门禁的 L1 temp/cache/log 普通文件，并额外要求专家模式和二次确认；始终禁止删除目录和目录树。禁止卸载、写注册表、禁用服务、启动项或计划任务、清理浏览器或驱动、把 PowerShell 当作执行器、调用外部清理工具、联网、上传、后台监控和自动清理。Python 不得调用 collector。社区规则、AI 判断和在线声誉不能直接触发删除。

Protect Windows system paths, driver stores, recovery partitions, user documents/media/code repositories, browser profiles, password managers, credential stores, BitLocker/TPM/authentication components, security software, and unknown bulk file groups.

## Privacy

Do not hide uploads. Default to no upload. Never upload raw user paths. Never submit user documents, source code, or photos for cloud reputation. v0.1.0 implements Offline Mode only and has no networking or upload capability.

不得隐藏上传，默认不上传，不上传原始用户路径。用户文档、代码、照片不参与云端声誉查询。v0.1.0 仅实现 Offline Mode，不包含联网或上传能力。

## Dry-run audit / Dry-run 审计

PR3 的 JSONL logger 只记录计划、模拟、阻断、拒绝和跳过事件。日志路径必须由用户或调用方显式传入；不得默认写入 AppData、系统目录或网络路径。`dry_run` 必须为 `true`，日志不代表动作已经执行成功。

The PR3 JSONL logger accepts only explicit local paths and dry-run events. It appends records without clearing or deleting existing logs. JSONL 管审计，SQLite 管历史；PR4 才进入 SQLite schema 与 history/audit store。

## Reputation knowledge / 声誉知识

SQLite reputation records must never be interpreted as direct execution authorization. Reputation row is not an execution authorization; community report is not a verdict; PUP evidence is not malware conviction; `SAFE_REMOVE_CANDIDATE` is not uninstall permission. Policy Engine remains the final gate.

声誉记录不是执行授权。社区报告不是最终裁决。PUP 证据不是恶意软件定罪。`SAFE_REMOVE_CANDIDATE` 不是卸载许可。最终仍由 Policy Engine 把关。SQLite 存证据和历史，不执行系统操作。

PR18 Reputation KB records may be used only for explanation, review ordering, conflict display, and risk提示. Accept only the stable PUP taxonomy and explicit review statuses. Even `approved_for_explanation` must keep `execution_authorized=false`. Do not fetch, crawl, or upload reputation data in PR18.

PR18 声誉记录只能解释、排序、展示冲突和提示风险。Policy Engine 不信任 Agent 的自然语言理由；Agent 解释不参与放行或阻断。单一 record、community report、AI summary 或在线声誉不能触发删除、卸载或禁用。

PR20 Seed Pack 只从调用方显式本地 JSON 加载公开来源 metadata 或 synthetic/placeholder 记录。所有 seed 必须保持 `execution_authorized=false`，review status 仅可用于人工复核或解释展示。不得联网、编写万能爬虫、采集专有安全厂商签名/检测数据，或编造真实软件指控。

PR21 may match explicit report targets against local seed names, aliases, and publisher-assisted identity evidence. `match_reputation`, `build_pup_insight`, and `inspect_pup_risk` are Level 0 explanation actions. A match is not a verdict; no match is not proof of safety.

PR21 可将显式报告目标与本地 seed 的名称、别名和发布者辅助证据匹配。PUP insight 必须展示误报风险、不确定性和人工复核步骤，并明确不是删除、卸载或禁用授权。不得因匹配置信度或 `approved_for_explanation` 自动触发系统操作。

PR22 `trial run` may orchestrate only the existing synthetic demo, safe cleanup, quarantine, reporting, audit, and local PUP insight components. Default to dry-run. Confirmed trial requires an explicit quarantine root and must never expose permanent deletion. Generate START HERE, human summary, machine summary, reports, and restore instructions without network access or upload.

PR22 试用入口只能编排既有 synthetic demo 与受控组件。默认 dry-run；确认模式只走可恢复隔离，PR24 未指定路径时使用 `.pcg-quarantine`。不得提供 permanent 参数，不得把 synthetic PUP 命中描述为真实软件定罪或执行授权。

PR24 confirmed cleanup defaults to `.pcg-quarantine` when no root is supplied. Record this default in summary, result, report, and audit evidence. Permanent deletion remains the existing expert-only double-flag path.

PR24 Evidence Guard treats mapping relation and synthetic status as orthogonal axes. Analogical behavior requires an explicit analogy basis. Mobile APP/SDK evidence, related publishers, name collisions, synthetic data, and even direct Windows evidence are never execution-gating eligible. Evidence Pack is not a blacklist.

PR25 real-source evidence must enter through the offline candidate → human review → guarded build flow. Only `accept_as_evidence` may build a record, and the PR24 loader must validate it again with `execution_authorized=false`. Runtime must not resolve source URLs or perform online reputation lookup.

PR25 真实 evidence 不是黑名单。真实来源只用于解释、排序和人工复核；`mapping_type`、`entity_scope`、`is_synthetic`、`relation_confidence` 是防误用核心字段。MIIT APP/SDK 通报不得直接映射为 Windows 删除名单。

For the v0.3.0 Public Preview, `doctor release-check` may read version, documentation, seed, showcase, and issue-template metadata only. It must not execute cleanup, access the network, read API keys, or mutate system state. PC CleanGuard does not replace antivirus software.

## Read-only collectors / 只读采集器

Allow read-only collectors to observe minimal system metadata, but never let them modify system state. The PR5 PowerShell collector may read only the three approved uninstall-registry paths and emit JSON to stdout. Python normalizers must never execute collector scripts, and uninstall strings remain metadata rather than execution authorization.

只读采集器可以观察最小系统元数据，但不得修改系统状态。PR5 PowerShell collector 只读取三个获准的卸载注册表路径并向 stdout 输出 JSON。Python normalizer 不得执行采集脚本；卸载字符串只是元数据，不是执行授权。

PR6 collectors may observe only approved startup registry/folder metadata, `Win32_Service`, and scheduled-task metadata. Startup commands, service path names, and task actions are metadata only. Do not collect processes in PR6.

PR6 collector 只观察获准的启动注册表/文件夹、`Win32_Service` 和计划任务元数据。启动命令、服务路径和任务动作只是元数据。PR6 不采集进程。

## Read-only scan pipeline / 只读扫描流水线

PR7 accepts only explicit caller-supplied JSON. Run installed-app, startup-item, service, and scheduled-task metadata through their normalizers, create `GovernanceTarget` values, evaluate every target with the Policy Engine, then build a report and dry-run audit events. Recommendations and `PLAN_*` steps are not execution authorization.

PR7 只接收调用方显式提供的 JSON。四类元数据必须依次经过 normalizer、`GovernanceTarget`、Policy Engine、Report Builder 和 dry-run Audit。策略建议和 `PLAN_*` 步骤都不是执行授权。

Optional report JSON and audit JSONL output must use caller-specified safe local paths. Do not discover inputs, auto-run PowerShell, choose hidden default paths, overwrite existing files without an explicit flag, or turn audit output into a claim of execution.

可选的 report JSON 和 audit JSONL 只能写入调用方显式指定的安全本地路径。不得自动发现输入、自动运行 PowerShell、选择隐藏默认路径或把 dry-run 日志宣称为真实执行证明。

## Minimal read-only CLI / 最小只读 CLI

PR8 may expose the PR7 pipeline only through `python -m pc_cleanguard.cli scan`. Require explicit input, report, and audit paths. Preserve existing outputs unless the caller explicitly requests overwrite. Return a machine-readable summary, but never treat a CLI invocation as authority to execute system changes.

PR8 CLI 只能作为 PR7 pipeline 的薄入口。必须要求显式 input、report 和 audit 路径；除非调用方显式要求覆盖，否则保留已有文件。CLI 调用不是修改系统的授权。

## AI report explanation / AI 报告解释

PR9 may explain explicit report JSON through the offline mock or dry-run prompt provider only. Do not connect a live model, read environment credentials, access the network, or upload report data. Prompt context must contain a bounded governance digest rather than raw names, paths, commands, evidence text, or user content.

PR9 只能通过离线 Mock 或 dry-run prompt provider 解释显式 report JSON。不得连接真实模型、读取环境凭据、联网或上传报告。Prompt 只能包含受限治理摘要，不得包含原始名称、路径、命令、证据文本或用户内容。

AI output is explanation only, never deletion, uninstall, quarantine, startup/service/task change, or registry-modification authorization. Mark uncertainty as requiring user confirmation. Do not output executable system commands. Protect documents, source code, photos, browser data, and password managers by default.

AI 输出只是解释，不是删除、卸载、隔离、启动项/服务/任务变更或注册表修改授权。不确定项必须标记为需要用户确认；不输出可执行系统命令。

## AI-callable actions / AI 可调用动作

The action interface exposes `scan_from_json`, `explain_report`, `build_cleanup_plan`, `write_report`, `write_audit`, and `recommend_external_tools`. Validate every request before dispatch. Every response must include `requires_user_confirmation`, `execution_level`, and `evidence`, with `execution_level=LEVEL_0_READ_ONLY` and `execution_authorized=false`.

每个请求必须先验证；每个响应必须包含用户确认要求、Level 0 权限和证据，且不得授权执行。`recommend_external_tools` 只接受显式 cleanup plan/report summary、catalog 和 allowlist。

Cleanup plans are symbolic review artifacts only. They must not contain commands, scripts, executables, automatic actions, or tool invocations. `SAFE_REMOVE` and `STARTUP_OFF` remain confirmation-required candidates. `BLOCK` and Level 5 remain absolute barriers.

Cleanup plan 只是符号化人工复核产物，不得包含命令、脚本、可执行文件、自动动作或工具调用。`SAFE_REMOVE` 和 `STARTUP_OFF` 仍然只是需要确认的候选项。

## External-tool adapter foundation / 外部工具适配层基础

PR12 may describe explicitly cataloged tools and evaluate them through `ToolTrustPolicy`, but it must never download, discover, launch, invoke, or update an external tool. Only an exact allowlisted `tool_id` can produce a trusted planning result; a cataloged but untrusted record produces a blocked plan, and an unknown record cannot enter a plan.

PR12 只能描述显式 catalog 中的外部工具并通过 `ToolTrustPolicy` 评估信任。不得下载、发现、启动、调用或更新任何工具。只有精确 allowlisted `tool_id` 才能得到可信任的计划结果；cataloged 但不可信任的 record 只能产生阻断计划，未知 record 不得进入计划。

Every external-tool plan must remain `plan_only`, `LEVEL_0_READ_ONLY`, `required_user_confirmation=true`, `blocked_if_untrusted=true`, and `execution_authorized=false`. A trusted plan is still not permission to run a tool. `SAFE_REMOVE` and `STARTUP_OFF` remain candidate classifications, not tool-invocation authorization.

每个外部工具计划必须保持 `plan_only`、`LEVEL_0_READ_ONLY`、`required_user_confirmation=true`、`blocked_if_untrusted=true` 和 `execution_authorized=false`。可信任计划仍不是运行工具的许可。

## External-tool recommendations / 外部工具推荐

PR13 may match only unblocked cleanup-plan removal candidates. An official uninstaller may be suggested for an ordinary software candidate; winget requires explicit package-ID metadata; a vendor cleanup tool requires an exact metadata association; a trusted third-party uninstaller is secondary review only.

PR13 只能匹配 cleanup plan 中未被阻断的移除候选。官方卸载器可作为普通软件的优先复核路径；winget 必须有显式 package ID；厂商专项工具必须由 metadata 精确关联；可信第三方卸载器只能作为次级复核建议。

Every recommendation must remain `plan_only=true`, `requires_user_confirmation=true`, `blocked_if_untrusted=true`, `execution_level=LEVEL_0_READ_ONLY`, and `execution_authorized=false`. Untrusted matches must be returned as blocked. Recommendations must contain no command, arguments, executable path, silent-run instruction, or download step.

外部工具推荐不是执行授权。AI 只能展示推荐、匹配原因和证据；不得自动下载未知程序，不得静默运行卸载器。真正执行必须等待未来 controlled executor，并重新经过 Policy Engine 与用户确认。

## Junk cleanup preview / 垃圾候选清理预览

PR14 may scan metadata only under one or more caller-supplied local directories. It may classify temporary files, cache files, logs, crash dumps, installer leftovers, and empty-directory candidates, then produce a `CleanupPreview`. It must not discover roots, scan an entire drive, read file contents, follow symbolic links, or change any filesystem object.

PR14 只能扫描调用方显式提供的本地目录，只读取路径、大小、修改时间和扩展名。可以识别临时文件、缓存、日志、崩溃转储、安装残留和空目录候选，但不得自动发现路径、扫描全盘、读取文件内容或修改文件系统对象。

Protect Documents, Desktop, Pictures, Videos, the user home directory, system directories, and code repositories. PR14 provides no override. Apply bounded file-count and total-size limits, and report every protected or truncated scan as a warning.

每个 `JunkCandidate` 必须保持 `LEVEL_0_READ_ONLY`、`requires_user_confirmation=true`、`dry_run_only=true` 和 `execution_authorized=false`。`total_reclaimable_bytes` 只是候选大小估算，不是已经释放的空间。空目录只能作为 candidate，不得清空或移除。

The `clean preview` CLI may write only an explicit JSON report and must preserve existing outputs by default. A cleanup preview is not deletion authorization.

## Developer Guard / 开发者保护引擎

Before scanning a directory or processing an L1 candidate, classify the path through Developer Guard. Protect `.git`, Python/Conda environments, `node_modules`, npm/pnpm/yarn data, IDE metadata, pip/Cargo/Gradle/Maven caches, CUDA/NVIDIA developer caches, and explicit user code roots.

scanner 命中开发者路径时必须返回 blocked，不能枚举为 junk candidates。executor 不信任 preview，必须在唯一文件删除点之前重新调用 Developer Guard。Developer Guard 的 reason、evidence 和 protection level 必须进入阻断结果；Agent、用户偏好和 Reputation KB 都不能绕过它。

## Quarantine and restore / 隔离与恢复

PR19 quarantine is a Level 2 reversible file operation. Require an explicit regular-file path, safe explicit quarantine root, reason, evidence, and explicit confirmation for mutating Skill actions. Record SHA-256, size, original mtime, paths, timestamps, and status in the manifest.

Never purge quarantine content, overwrite an existing restore destination, quarantine directories, or bypass preview/L1/allow-root/protected-path/Developer Guard checks. `clean execute --quarantine-root` moves only confirmed L1 temp/cache/log files; all non-L1 categories remain skipped.

PR20 `clean safe` is the ordinary-user entry point: dry-run by default and quarantine-only when confirmed. It has no permanent option. `clean execute` may permanently delete only with `--confirm --permanent --i-understand-permanent-delete`; missing quarantine or expert flags must fail closed.

## L1 controlled cleaner / L1 低风险受控清理器

The cleanup executor may consume only a structurally valid PR14 preview. Default mode is dry-run. Confirmed execution requires explicit allow roots, existing regular files, L1 categories, current metadata matching the preview, protected-path clearance, and audit output. PR20 additionally requires quarantine by default or the complete expert permanent-delete flag pair.

清理执行器只能消费结构完整的 PR14 cleanup preview。默认 `clean execute` 为 dry-run；确认执行必须满足显式 allow-root、普通文件、L1 allowlist、运行时复核、保护目录复核和审计门。PR20 还要求默认隔离，或完整的专家永久删除双确认参数。

`crash_dump`, `installer_leftover`, and `empty_directory_candidate` must remain `skipped`. Never remove directories, browser profiles, user documents/media, code repositories, system directories, or Program Files. Each result must include evidence and an embedded audit event; actual reclaimed bytes are reported only after a successful bounded file removal.

CLI 输出冲突必须在任何真实清理前被发现。PR15 不向 AI Skill action 暴露自动执行能力；AI 建议、外部工具推荐和 preview candidate 都不是执行授权。

## Tryable cleanup demo and reporting / 可试用清理 Demo 与报告

PR16 `demo init-cleanup` may create synthetic files only below one caller-supplied safe local root. Mark the root explicitly, refuse existing roots by default, and permit `--force` only when the existing marker matches that exact root. Never seed a protected, system, network, or symbolic-link path.

PR16 `demo init-cleanup` 只能在调用方显式指定的安全本地 root 下创建合成测试文件。root 必须带专用 marker；默认不覆盖，`--force` 也只能刷新 marker 与当前 root 完全匹配的 demo。

`demo run-cleanup` must require that marker and keep output outside the demo root. Default to dry-run. If `--confirm` is present, move only unchanged manifest L1 entries to a quarantine under the output root. Block user-added or modified files; crash dumps, installer leftovers, and directories remain skipped.

`clean report` only combines explicit preview/result JSON into a summary and Markdown file. Reporting is not execution authorization, does not scan paths, and must preserve existing output by default.

PR17 `demo quickstart` is a convenience wrapper for a new synthetic demo root plus PR16 dry-run reporting. It must not accept or infer confirmation, and it must always call the demo runner with `confirm=false`. Quickstart output is evidence for review, never execution authorization.

PR17 `demo quickstart` 只能创建新的合成 demo root 并运行默认 dry-run；不得接受、推断或转发确认。它生成的 preview、audit 和 report 仅供审阅，不能授权真实清理。

## Action usage / Action 调用方法

When an external AI asks to call PC CleanGuard, use `invoke_skill_action` with one JSON-compatible request. Select exactly one action:

- `scan_from_json`: when the caller already has explicit collector/sample JSON metadata.
- `explain_report`: when the caller needs a Chinese explanation of an existing report; use only `mock` or `dry-run-prompt`.
- `build_cleanup_plan`: when the caller needs non-executable review steps from existing policy decisions.
- `write_report`: when the caller explicitly provides a safe local `.json` output path and a report object.
- `write_audit`: when the caller explicitly provides a safe local `.jsonl` path and complete dry-run audit events.
- `recommend_external_tools`: when the caller provides a cleanup plan or report summary plus an explicit catalog and allowlist; return suggestions only.

外部 AI 调用时，每次只构造一个 JSON-compatible request，并交给 `invoke_skill_action`。不得跳过 request validation，不得伪造成功 response。

```python
from pc_cleanguard.skill import invoke_skill_action

explicit_json_object = {
    "privacy_mode": "offline",
    "installed_apps": [],
    "startup_items": [],
    "services": [],
    "scheduled_tasks": [],
}
response = invoke_skill_action(
    {
        "action": "scan_from_json",
        "payload": {"input_data": explicit_json_object},
    }
)
result = response.to_dict()
```

For a governed chain, pass `scan_from_json`'s `result.scan_result` object to `explain_report` or `build_cleanup_plan`. Do not reinterpret `cleanup_plan` as a command list. Inspect `requires_user_confirmation`, `execution_level`, `evidence`, and `execution_authorized` before presenting any result.

只有调用方显式给出路径时才能调用 `write_report` / `write_audit`。默认不覆盖文件；除非调用方明确要求，不得设置 `explicit_overwrite=true`。这两个动作只写治理产物，不修改 Windows 系统状态。

Runnable JSON requests are in `examples/skill_actions/`. Schemas are in `schemas/skill_action_request.schema.json`, `schemas/skill_action_response.schema.json`, and `schemas/cleanup_plan.schema.json`.

## Produce output

Return these sections in order:

1. Summary
2. Findings
3. Recommendations
4. Execution Plan
5. Managed Mode Compatibility
6. Risk Notes
7. Audit Notes

State clearly that PR2 execution plans are non-executable policy artifacts. Include evidence for every non-`KEEP` finding, and include audit requirements for every non-`KEEP` decision.
