# PC CleanGuard v0.2.0 Release Checklist

本清单用于 v0.2.0 Public Demo 候选版本的最终发布门禁。PR17 只整理发布材料，不创建 tag；tag 与 GitHub Release 必须由后续明确授权单独执行。

## 1. 用户可见能力 / User-visible capabilities

- [ ] `demo quickstart` 可在合成目录生成完整 dry-run 产物。
- [ ] `clean preview` 展示候选数量、类别和预计可释放空间。
- [ ] `clean execute` 默认 dry-run，并在缺少 `--confirm` 时不删除文件。
- [ ] 显式确认仅开放 allow-root 内的 L1 temp/cache/log 普通文件。
- [ ] 每个执行决定写入 audit JSONL，并可导出 Markdown 报告。
- [ ] 离线 AI explainer 与 Skill action 示例可读取和解释治理产物。

## 2. 安全与隐私 / Safety and privacy

- [ ] 不存在新的删除机制；生产代码只有 PR15 executor 的受控 `Path.unlink()`。
- [ ] 不删除目录树，不清空目录，不扩大 L1 allowlist。
- [ ] 不卸载软件，不修改注册表、启动项、服务或计划任务。
- [ ] Python 不调用 PowerShell、subprocess 或外部清理工具。
- [ ] 不联网、不上传、不读取 API key。
- [ ] Public Demo 只包含虚构路径与合成数据。

## 3. 文档与公开资产 / Documentation and public assets

- [ ] README 首页包含产品定位、五分钟试用、能力、限制和安全边界。
- [ ] `docs/v0.2-quick-try.md` 命令已人工运行复核。
- [ ] `examples/public_demo/` 的 JSON、JSONL 和 Markdown 可读取。
- [ ] AI Agent flow 示例明确默认 dry-run 与用户确认边界。
- [ ] bug、规则反馈和误报 issue templates 可用且包含隐私提醒。

## 4. 最终验证 / Final validation

- [ ] 运行 `python -m compileall pc_cleanguard`。
- [ ] 运行 `python -m unittest discover -s tests`。
- [ ] 运行 `git diff --check`。
- [ ] 确认 `git status --short` 为空。
- [ ] 运行危险 API、网络/进程 import 和删除机制搜索。
- [ ] 在干净临时目录手工运行 quickstart dry-run。
- [ ] 在临时 demo root 中人工复核一次受控 `--confirm`。

## 5. 发布批准 / Release approval

- [ ] PR17 已审查并合并到 `main`。
- [ ] `main` 与 `origin/main` 一致。
- [ ] 版本元数据、release notes 和候选 commit 已人工确认。
- [ ] 已获得创建 `v0.2.0` tag 的明确授权。
- [ ] tag 推送后创建 GitHub Release，并再次检查工作树和远程 tag。

Do not infer tag authorization from this checklist. / 不得从本清单推断创建 tag 的权限。
