# PUP 风险洞察 / PUP Risk Insight

## safety_notice

此洞察不是删除授权、不是卸载授权、不是禁用授权；真实来源 evidence 仅用于解释、排序和人工复核，不是删除、卸载、禁用授权；所有不确定项需要用户确认。

- 命中目标：2
- 真实来源命中：2
- Synthetic 命中：0
- 执行门控合格：0

## Evidence Guard details

- `PUA:Win32/InstallCore`：mapping_type=`direct_entity`，entity_scope=`windows_desktop_software`，relation_confidence=`high`，source_title=`PUA:Win32/InstallCore threat description - Microsoft Security Intelligence`，source_date=`2015-03-11`，source_url=`https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FInstallCore`，guard_reason=`execution gating is always blocked`。
- `PUA:Win32/MediaArena`：mapping_type=`direct_entity`，entity_scope=`windows_desktop_software`，relation_confidence=`high`，source_title=`PUA:Win32/MediaArena threat description - Microsoft Security Intelligence`，source_date=`2023-03-20`，source_url=`https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FMediaArena&threatId=359463`，guard_reason=`execution gating is always blocked`。

即使来源真实、名称直接匹配、关系置信度较高，`execution_gating_eligible_count` 仍为 0。必须结合本地发布者、安装来源、用户意图和 Policy Engine 重新判断。
