# PC CleanGuard Skill

开源、可审计、隐私优先的 AI 系统治理 Skill。

Open-source, auditable, privacy-first AI System Governance Skill.

**v0.1.0 Public Preview**

> **PC CleanGuard 不是传统清理软件。**
> **It is not a traditional cleaner.**
>
> 它面向 AI Agent 建立受治理的系统安全边界；v0.1.0 提供只读动作接口，不执行任何真实清理。
> It establishes governed safety boundaries for AI agents; v0.1.0 exposes read-only actions and performs no cleanup.

PC CleanGuard 面向 Codex、WorkBuddy、本地 AI Agent 和未来系统级 AI 助手。它的目标不是“一键清理电脑”，而是让 AI Agent 在严格策略、权限分级、证据链、用户确认、隐私保护和审计留痕约束下，安全地分析、分类和规划未来的系统治理操作。

PC CleanGuard is designed for Codex, WorkBuddy, local AI agents, and future system-level assistants. It replaces one-click cleanup with governed analysis, classification, and planning under policy, permission, evidence, consent, privacy, and audit controls.

核心原则 / Core principle:

**AI 可以执行，但执行必须被治理。**

**AI may execute, but execution must be governed.**

**外部权限很大，内部刹车必须更大。**

**External permission is large; internal brakes must be larger.**

## 快速开始 / Quick start

要求：Python 3.10+ 和 Git。v0.1.0 仅使用 Python 标准库；Public Preview 需在仓库根目录运行。

Requirements: Python 3.10+ and Git. The public preview uses the Python standard library only and runs from the repository root.

```powershell
git clone https://github.com/Gzx-070829/pc-cleanguard-skill.git
cd pc-cleanguard-skill
python -m unittest discover -s tests
```

### 1. 只读扫描 / Read-only scan

```powershell
python -m pc_cleanguard.cli scan --input examples/scan_samples/pr7_readonly_scan_input.json --report output/report.json --audit output/audit.jsonl
```

输出包含 normalized counts、targets、Policy Engine decisions、report 和强制 dry-run audit events。如果输出文件已存在，CLI 默认拒绝覆盖。

### 2. 离线解释报告 / Explain a report offline

```powershell
python -m pc_cleanguard.cli explain --report output/report.json --output output/explanation.md --provider mock
```

Mock provider 不联网。要只查看受限 prompt，将 `--provider mock` 替换为 `--dry-run-prompt`。

### 3. 从 AI/Agent 调用 Skill action

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

五个 action 的完整 request 见 [`examples/skill_actions/`](examples/skill_actions/README.md)。所有 action response 均固定为 Level 0，且 `execution_authorized=false`。

## 项目定位

PC CleanGuard 在 AI 建议与系统操作之间建立可审计的安全门。它先回答“能否做、为何做、需要谁确认”，而不是直接动手。

PC CleanGuard is an auditable safety gate between AI recommendations and system operations. It answers whether an action is permitted, why, and whose confirmation is required before execution is considered.

## 它是什么

- Windows 对象的保守治理策略模型。
- 以证据链、风险标签和权限等级约束 Agent 的 Skill。
- 为未来受控执行层提供独立、不可绕过的 Policy Engine。

## 它不是什么

它不是磁盘清理器、卸载器、杀毒软件、系统优化器或后台监控器。v0.1.0 没有删除、卸载、移动、注册表写入、服务/启动项修改、联网或上传能力。

## v0.1.0 Public Preview 范围

PR7 打通可用的只读治理链路：显式 JSON 输入 → normalizer → `GovernanceTarget` → Policy Engine → Report Builder → dry-run Audit。调用方还可显式指定安全本地路径，写出 report JSON 和 audit JSONL；默认不覆盖已有文件。

PR7 completes a useful read-only governance chain from explicit JSON input to normalized targets, policy decisions, reports, and dry-run audit events. Optional artifact writing requires explicit safe local paths and does not overwrite by default.

PR8 在这条链路上增加最小命令行入口：`python -m pc_cleanguard.cli scan`。它只接收显式 input/report/audit 路径，不运行 collector。

PR9 增加离线 AI Report Explainer、安全 prompt、Mock provider、dry-run prompt 和 `explain` CLI。AI 只能解释与建议，输出不是删除、卸载或禁用授权。

PR10 新增 AI 可调用的五个动作：`scan_from_json`、`explain_report`、`build_cleanup_plan`、`write_report` 和 `write_audit`。所有响应都包含确认要求、Level 0 执行级别和证据，且不授权执行。

PR11 整理公开快速开始、AI action usage、可运行示例、Public Preview 说明和 v0.1.0 release checklist，不新增执行能力。

## 安全原则

1. 不静默删除。
2. 不偷偷上传。
3. 不做黑箱声誉判断。
4. 不因单一来源自动删除。
5. 社区规则不能直接触发删除。
6. AI 判断不能直接触发删除。
7. 在线声誉不能直接触发删除。
8. 用户文档、代码、照片不参与云端声誉查询。
9. 每个操作必须可解释、可记录、可分类。
10. 硬规则先于普通分类，敏感目标直接 `BLOCK`。
11. 不确定时 `KEEP` 或 `ASK_USER`。
12. 用户偏好不能绕过 `BLOCK` 或 Level 5。

In short: no silent deletion, hidden upload, black-box reputation verdict, or automatic removal from a single source. Every proposed action must be explainable, classifiable, consent-aware, and auditable.

**先造刹车，再造发动机。 / Build the brakes before the engine.**

## 系统架构

```text
Normalized Target + Evidence
             |
        Policy Engine
             |
 Classification + Risk + Permission + Confirmation + Audit
             |
      Non-executable PR2 report
```

未来 Execution Layer 必须消费 Policy Engine 的结果，不能自行制定或弱化策略。

The future Execution Layer may consume policy decisions, but it may never create or weaken them.

## 风险分类标签

`KEEP`、`ASK_USER`、`SAFE_REMOVE`、`STARTUP_OFF`、`QUARANTINE`、`BLOCK`。候选标签不是执行授权。

## 执行权限等级

Level 0 只读扫描；Level 1 低风险清理；Level 2 可逆操作；Level 3 标准卸载；Level 4 高风险系统修改；Level 5 禁止区。v0.1.0 只开放 Level 0。

## 隐私承诺

v0.1.0 仅实现 Offline Mode：不连接真实模型 API、不联网、不上传，不读取环境凭据。

v0.1.0 is offline-only: no live model API, networking, uploads, or environment credentials.

## 开发状态

当前里程碑：**v0.1.0 Public Preview**。PR11 专注公开展示、开发者快速开始和 AI action 调用说明。

Current milestone: **v0.1.0 Public Preview**. PR11 focuses on public documentation, runnable examples, and release readiness.

详细用法见 [只读扫描流水线](docs/readonly-scan-pipeline.md)。

CLI 用法见 [最小只读 CLI](docs/cli.md)。

AI 解释器见 [AI 报告解释器](docs/ai-report-explainer.md)。

Skill 动作接口见 [AI 可调用 Skill 动作接口](docs/skill-action-interface.md)。

Public Preview 说明见 [v0.1.0 Public Preview](docs/public-preview.md)；发布门禁见 [v0.1.0 release checklist](docs/v0.1.0-release-checklist.md)。

**JSONL 管审计，SQLite 管历史。PR3 只记录 dry-run，不代表执行。**

**声誉记录不是执行授权；最终仍由 Policy Engine 把关。**

**卸载字符串只是元数据，不是执行授权。PR5 不清理、不删除、不卸载、不联网、不上传。**

**启动命令、服务路径和任务动作只是元数据。PR6 不采集进程，也不修改系统。**
