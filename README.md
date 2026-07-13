# PC CleanGuard Skill

PC CleanGuard Skill 让 AI 更安全地分析、解释、预览、隔离和审计 Windows 清理任务。

PC CleanGuard Skill helps AI agents safely inspect, explain, preview, quarantine, and audit Windows cleanup tasks.

**v0.3.0 Public Preview · 默认隔离，可恢复 · Offline by default**

PUP Review Pack 可以离线生成带来源追溯的 PUP 线索复核包，但不会删除、卸载、禁用、上传或修改注册表。
PUP Review Pack can generate a local, offline, source-traceable review folder for suspicious PUP signals without deleting, uninstalling, disabling, uploading, or modifying the registry.

快速试用：

```powershell
python -m pc_cleanguard.cli trial run --root .pcg-demo --output .pcg-trial
```

确认隔离试用：

```powershell
python -m pc_cleanguard.cli trial run --root .pcg-demo --output .pcg-trial-confirm --confirm --quarantine-root .pcg-quarantine
```

PUP 线索检查：

```powershell
python -m pc_cleanguard.cli pup inspect --input <report.json> --seed examples/reputation/seed_records.zh-CN.json --output pup_insight.md
```

生成完整离线复核包：

```powershell
python -m pc_cleanguard.cli pup review-pack --input examples/reputation/pr26_realistic_windows_inventory.json --evidence-pack data/reputation/evidence_pack.real.zh-CN.json --output .pcg-pup-review
```

恢复隔离文件：

```powershell
python -m pc_cleanguard.cli quarantine restore --root .pcg-quarantine --item-id <id>
```

5 分钟即可看到清理预览、空间估算、审计报告和 synthetic PUP 线索。默认 dry-run；确认后默认隔离、可恢复。PUP 线索只是提示，不是删除授权。不联网、不上传、不静默删除，也不替代杀毒软件。

确认清理时可省略 `--quarantine-root`，系统会使用当前目录下的 `.pcg-quarantine`；用户不必自己设计隔离路径。永久删除仍是显式双旗专家模式。

> PC CleanGuard 不追求“点一下就删干净”。它把 AI 建议与系统修改隔开，让每个候选、权限、确认和结果都可解释。
>
> PC CleanGuard is not a one-click disk cleaner. It places auditable policy and consent gates between AI advice and system changes.

## 这是什么 / What it is

PC CleanGuard 当前可以在用户显式提供的本地路径中读取文件 metadata，识别临时文件、缓存、日志、崩溃转储、安装残留和空目录候选，估算可释放空间，并生成 JSON preview。默认执行是 dry-run；确认后默认把通过全部 L1 门禁的普通 temp/cache/log 文件移入可恢复隔离区。

完整链路：

```text
Explicit path
  → metadata-only junk scan
  → cleanup preview + reclaimable bytes
  → dry-run or explicitly confirmed L1 execution
  → JSONL audit
  → JSON summary + Markdown report
```

同一项目还提供只读 Windows governance pipeline、Policy Engine、离线 Mock AI 报告解释器和外部 AI 可调用的 Skill action 接口。

v0.3 PR18 正在增加 Developer Guard 与 Reputation KB 数据契约：开发路径在 scanner/executor 两层默认阻断，PUP 声誉记录只能解释和排序，不能授权删除或卸载。

PR19 增加可恢复 quarantine → manifest → restore 链路，并把隔离模式接入受控 L1 cleanup、CLI 与 Skill actions；不提供 purge。

PR20 增加普通用户 `clean safe` 入口和离线 Reputation Seed Pack。永久删除降为专家模式，必须双重显式确认；种子证据始终 `execution_authorized=false`。

PR21 让本地 Reputation KB 变得用户可见：可对 report 中的软件、启动项、服务和计划任务进行名称/别名匹配，生成中文 PUP 风险洞察；匹配与洞察只用于解释、排序和人工复核。

PR22 把上述能力编排为 `trial run` 产品体验：自动生成 START HERE、用户摘要、机器摘要、清理报告、PUP 洞察、审计和恢复说明。

PR24 增加默认 `.pcg-quarantine` 与 Evidence Guard。Evidence Pack 不是黑名单；mapping relation 与 synthetic 状态是正交轴，所有 evidence 均被阻断在执行门之外。

PR25 增加离线 Evidence Intake/Review/Build 和首批 5 条人工核验公开来源记录。真实来源只让 PUP insight 更有信息量，`execution_gating_eligible_count` 始终为 0。

PR26 增加保守 Evidence Indicator matching、PUP Intelligence Engine 和一条命令生成的本地 Review Pack。detection family 不等于 installed app display name；所有 match 仍需人工复核。

## 5 分钟试用 / Try it in five minutes

要求 Python 3.10+。克隆仓库并在根目录运行：

```powershell
git clone https://github.com/Gzx-070829/pc-cleanguard-skill.git
cd pc-cleanguard-skill
python -m pc_cleanguard.cli demo quickstart --root .pcg-demo --output .pcg-demo-output
```

这条命令只创建合成 demo 文件并运行 dry-run，不会删除文件。随后打开：

- `.pcg-demo-output/preview.json`
- `.pcg-demo-output/dry_run_result.json`
- `.pcg-demo-output/audit.jsonl`
- `.pcg-demo-output/cleanup_report.md`

完整教程：[docs/v0.2-quick-try.md](docs/v0.2-quick-try.md) · 静态展示包：[examples/public_demo/README.md](examples/public_demo/README.md)

## 能清理什么 / What can be cleaned

| Category | Preview | Confirmed L1 cleanup | Notes |
| --- | --- | --- | --- |
| `temp_file` | Yes | Yes, gated | 普通文件、allow-root 内、重新验证 |
| `cache_file` | Yes | Yes, gated | 不处理浏览器 profile |
| `log_file` | Yes | Yes, gated | 必须显式 `--confirm` |
| `crash_dump` | Yes | No | `skipped` |
| `installer_leftover` | Yes | No | `skipped` |
| `empty_directory_candidate` | Yes | No | 永不删除目录 |

“可清理”不等于自动授权。真实 L1 文件操作必须同时满足：preview 来源有效、用户显式 `--confirm`、路径仍存在、普通文件、类别在 L1 allowlist、位于显式 allow-root、未命中 protected path/code/browser profile、当前 metadata 仍匹配，并且 audit JSONL 已准备好。

## 为什么适合 AI Agent / Why it fits AI agents

普通 disk cleaner 通常把扫描、判断和执行打包在一个 UI 流程里。PC CleanGuard 更适合 Agent 编排，因为它提供机器可读、可分阶段验证的治理接口：

- Policy decision、risk level、evidence、confirmation 与 execution level 分离。
- Preview candidate 不是删除授权；AI 建议和外部工具推荐也不是授权。
- 默认 dry-run，输出 JSON/JSONL/Markdown，便于 Agent 展示给用户后再决定下一步。
- 明确保护系统目录、用户文档/媒体/代码、浏览器资料和未知批量文件。
- Developer Guard 独立保护依赖树、虚拟环境、IDE metadata、开发缓存和显式 user code roots。
- Offline by default：不联网、不上传、不读取 API key。

## 常用命令 / Core commands

### 预览显式目录

```powershell
python -m pc_cleanguard.cli clean preview --path C:\Explicit\Temp --output output\preview.json
```

### 默认 dry-run 执行计划

```powershell
python -m pc_cleanguard.cli clean execute --preview output\preview.json --allow-root C:\Explicit\Temp --result output\result.json --audit output\audit.jsonl
```

没有 `--confirm` 时只产生 `would_clean`。普通用户推荐使用一条安全入口：

```powershell
python -m pc_cleanguard.cli clean safe --path C:\Explicit\Temp --output output\safe
```

确认后默认隔离：

```powershell
python -m pc_cleanguard.cli clean safe --path C:\Explicit\Temp --output output\safe --confirm --quarantine-root output\quarantine
```

`clean execute --confirm` 也必须提供 `--quarantine-root`。永久删除是专家模式，必须同时提供 `--permanent --i-understand-permanent-delete`，且不会扩大 L1 范围。详见 [Safe Clean Flow](docs/safe-clean-user-flow.md)。

### 导出 Markdown 报告

```powershell
python -m pc_cleanguard.cli clean report --preview output\preview.json --result output\result.json --output output\cleanup-report.md
```

### 只读 Windows governance scan

```powershell
python -m pc_cleanguard.cli scan --input examples/scan_samples/pr7_readonly_scan_input.json --report output/governance-report.json --audit output/governance-audit.jsonl
```

Python 不自动执行 PowerShell collectors；`scan` 只读取调用方显式提供的 JSON。

### 离线解释治理报告

```powershell
python -m pc_cleanguard.cli explain --report output/governance-report.json --output output/explanation.md --provider mock
```

`pc_cleanguard.cli explain` 使用离线 Mock 或 dry-run prompt provider，不连接真实模型。

### 检查 PUP / 流氓软件线索

```powershell
python -m pc_cleanguard.cli pup inspect --input report.json --seed examples/reputation/seed_records.zh-CN.json --output pup_inspection.md
```

输出不是删除、卸载或禁用授权；高误报风险和未审核记录会明确要求用户复核。

人工核验证据可通过离线 intake/review/build 流程重建，再用于 PUP 洞察：

```powershell
python -m pc_cleanguard.cli reputation evidence intake validate --input data/reputation/evidence_candidates.zh-CN.json
python -m pc_cleanguard.cli reputation evidence review validate --input data/reputation/evidence_review_queue.zh-CN.json
python -m pc_cleanguard.cli reputation evidence stats --input data/reputation/evidence_pack.real.zh-CN.json
python -m pc_cleanguard.cli pup inspect --input report.json --evidence-pack data/reputation/evidence_pack.real.zh-CN.json --output pup_insight.md
```

## AI / Skill 调用

外部 Agent 可以通过 `invoke_skill_action` 调用 `scan_from_json`、`explain_report`、`build_cleanup_plan`、`write_report`、`write_audit` 和 `recommend_external_tools`：

```python
import json
from pathlib import Path

from pc_cleanguard.skill import invoke_skill_action

request = json.loads(
    Path("examples/skill_actions/scan_from_json.request.json").read_text(
        encoding="utf-8"
    )
)
response = invoke_skill_action(request)
print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))
```

v0.2 编排示例：[examples/skill_actions/v0.2_cleanup_agent_flow.json](examples/skill_actions/v0.2_cleanup_agent_flow.json)。Skill action 仍是 Level 0 分析/计划接口，不直接触发 PR15 清理执行器。

## 当前限制 / Current limitations

- 只开放 L1 temp/cache/log 普通文件的受控清理，不删除目录树。
- 不卸载软件；外部工具 catalog/recommender 只生成 plan-only 建议。
- 不修改注册表、启动项、服务或计划任务。
- 不自动运行 Windows PowerShell collectors，也不扫描全盘。
- 没有真实在线 AI provider、GUI、后台监控、遥测或云同步。
- 垃圾规则以明确 metadata 为主，仍需要社区反馈持续降低误报。
- PR20 Seed Pack 提供 20 条 synthetic/placeholder 中文记录；PR25 另提供 5 条人工核验公开来源 detection-family 记录。两者都在本地离线加载，不联网抓取声誉数据，也不包含专有检测库。

## 安全边界 / Safety boundaries

- 不静默删除，不绕过用户确认。
- 不偷偷上传，不联网上传用户数据。
- 不做黑箱声誉判断，不因单一来源自动删除。
- 社区规则、AI 判断、在线声誉和外部工具推荐都不是执行授权。
- 用户文档、代码、照片、视频、浏览器资料和密码管理器默认保护。
- `BLOCK` 与 Level 5 不得被用户偏好或 Agent 输出绕过。
- 每个操作必须可解释、可记录、可分类。
- Reputation KB 只能解释、排序和提示风险；不能单独触发删除、卸载或禁用。

**AI 可以执行，但执行必须被治理。**
**AI may execute, but execution must be governed.**

## 公开资产与反馈 / Public assets and feedback

- v0.2 Quick Try：[docs/v0.2-quick-try.md](docs/v0.2-quick-try.md)
- Public Demo artifacts：[examples/public_demo/README.md](examples/public_demo/README.md)
- AI Agent flow：[examples/skill_actions/v0.2_cleanup_agent_flow.json](examples/skill_actions/v0.2_cleanup_agent_flow.json)
- v0.2.0 release checklist：[docs/release-v0.2.0-checklist.md](docs/release-v0.2.0-checklist.md)
- 安全策略：[SECURITY.md](SECURITY.md)
- 贡献规则：[CONTRIBUTING.md](CONTRIBUTING.md)
- 路线图：[ROADMAP.md](ROADMAP.md)
- v0.3 Vision：[docs/VISION.md](docs/VISION.md)
- Reputation KB contract：[docs/reputation-kb.md](docs/reputation-kb.md)
- Developer Guard：[docs/developer-guard.md](docs/developer-guard.md)
- Quarantine and Restore：[docs/quarantine-restore.md](docs/quarantine-restore.md)
- Safe Clean Flow：[docs/safe-clean-user-flow.md](docs/safe-clean-user-flow.md)
- Reputation Seed：[docs/reputation-seed.md](docs/reputation-seed.md)
- Reputation Source Policy：[docs/reputation-source-policy.md](docs/reputation-source-policy.md)
- Reputation Evidence Pack：[docs/reputation-evidence-pack.md](docs/reputation-evidence-pack.md)
- Reputation Source Review Policy：[docs/reputation-source-review-policy.md](docs/reputation-source-review-policy.md)
- Evidence Intake：[docs/reputation-evidence-intake.md](docs/reputation-evidence-intake.md)
- Real-source Evidence Review：[docs/reputation-real-source-review.md](docs/reputation-real-source-review.md)
- Reputation Matching：[docs/reputation-matching.md](docs/reputation-matching.md)
- PUP Insight Flow：[docs/pup-insight-user-flow.md](docs/pup-insight-user-flow.md)
- Evidence Indicators：[docs/reputation-evidence-indicators.md](docs/reputation-evidence-indicators.md)
- PUP Intelligence Review Pack：[docs/pup-intelligence-review-pack.md](docs/pup-intelligence-review-pack.md)
- PUP Human Review Checklist：[docs/pup-human-review-checklist.md](docs/pup-human-review-checklist.md)
- PUP False-positive Feedback：[docs/pup-false-positive-feedback.md](docs/pup-false-positive-feedback.md)
- User Trial：[docs/user-trial.md](docs/user-trial.md)
- Product Positioning：[docs/product-positioning.md](docs/product-positioning.md)
- v0.3 Public Preview：[docs/v0.3-public-preview.md](docs/v0.3-public-preview.md)
- v0.3 User Trial Script：[docs/v0.3-user-trial-script.md](docs/v0.3-user-trial-script.md)
- v0.3.0 Release Checklist：[docs/release-v0.3.0-checklist.md](docs/release-v0.3.0-checklist.md)
- v0.3 Showcase：[examples/showcase/v0.3/README.md](examples/showcase/v0.3/README.md)

仓库提供 bug、软件规则反馈和 cleanup false-positive issue templates。提交示例时请使用虚构路径，勿上传文件内容、凭据、token 或真实用户数据。

## 版本状态 / Version status

`v0.1.0 Public Preview` 与 `v0.2.0 Public Demo Preview` 已发布；当前版本为 `v0.3.0 Public Preview`，包含五分钟试用、Developer Guard、Reputation KB/Matcher/PUP Insight、可恢复 quarantine/restore 和默认隔离安全入口。

PR 不创建 tag；只有获得明确发布授权后才创建正式版本 tag。
