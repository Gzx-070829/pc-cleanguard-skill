"""Deterministic offline providers for PR9; no live model clients."""

from __future__ import annotations

from collections import Counter
from typing import Protocol

from .prompts import SAFETY_NOTICE, build_safe_report_digest


class AIProvider(Protocol):
    """Small provider contract with no transport or credential surface."""

    name: str

    def generate(self, prompt: str, report: dict) -> str:
        """Return Markdown derived from an already-built safe prompt."""


class DryRunPromptProvider:
    """Return the prompt verbatim for local inspection."""

    name = "dry-run-prompt"

    def generate(self, prompt: str, report: dict) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if not isinstance(report, dict):
            raise TypeError("report must be a dict")
        return prompt


class MockAIProvider:
    """Generate a deterministic Chinese explanation without any model call."""

    name = "mock"

    def generate(self, prompt: str, report: dict) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        digest = build_safe_report_digest(report)
        decisions = digest["decisions"]
        counts = Counter(item["classification"] for item in decisions)
        total = digest["normalized_counts"]["total_targets"] or len(decisions)
        needs_confirmation = counts["ASK_USER"] + counts["UNKNOWN"]
        high_risk = sum(
            item["risk_level"] in {"HIGH", "CRITICAL"} for item in decisions
        )
        protected_reminder = (
            "用户文档、代码、照片、浏览器资料和密码管理器默认保护。"
        )
        return f"""# PC CleanGuard AI 报告解释（Mock）

## safety_notice

{SAFETY_NOTICE}

## 扫描摘要

- 归一化目标：{total}
- 策略决策：{len(decisions)}
- 高风险或严重项：{high_risk}
- 本解释由离线 Mock provider 生成，未访问网络。

## 分类解释

- `KEEP`：{counts['KEEP']}，建议保留。
- `ASK_USER`：{counts['ASK_USER']}，需要用户确认。
- `SAFE_REMOVE`：{counts['SAFE_REMOVE']}，仅为候选建议，不是卸载授权。
- `STARTUP_OFF`：{counts['STARTUP_OFF']}，仅为可逆候选建议，不是禁用授权。
- `QUARANTINE`：{counts['QUARANTINE']}，仅为候选建议，不是隔离授权。
- `BLOCK`：{counts['BLOCK']}，不可绕过。

## 需要用户确认的项目

共 {needs_confirmation} 项明确属于不确定或需要确认的分类。证据不足时应继续保留，由用户核对软件用途与依赖关系。

## 仅供人工复核的建议

优先检查发布者、安装来源、用户用途和多来源证据。不能因单一来源、AI 判断、社区规则或在线声誉建议删除。本输出不提供任何可执行系统命令。

## 受保护对象提醒

{protected_reminder}
"""
