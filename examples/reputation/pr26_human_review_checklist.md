# PUP Human Review Checklist / 人工复核清单

本清单只支持保留、询问、核验和收集更多证据，不授权系统修改。

## app:installcore

- matched_record_id: `ev-real-ms-installcore`
- evidence: `PUA:Win32/InstallCore`
- match_basis: `evidence_indicator`
- indicator_type: `installer_family`
- source_url: https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FInstallCore
- source_title: PUA:Win32/InstallCore threat description - Microsoft Security Intelligence
- source_date: 2015-03-11
- false_positive_risk: `medium`
- why_not_execution_authorization: Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。

用户应检查：

- [ ] 核对软件是否由用户主动安装以及安装来源。
- [ ] 核对本地发布者、版本、签名与来源页面描述是否属于同一实体。
- [ ] 检查是否存在捆绑、浏览器修改、异常启动项或安全工具独立提示。

允许的后续建议：

- `review`
- `keep`
- `ask_user`
- `check_vendor_uninstaller`
- `check_defender_or_security_tool`
- `collect_more_evidence`
- `report_false_positive`

## app:slimware

- matched_record_id: `ev-real-ms-slimware`
- evidence: `PUA:Win32/Slimware`
- match_basis: `evidence_indicator`
- indicator_type: `installer_family`
- source_url: https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FSlimware
- source_title: PUA:Win32/Slimware threat description - Microsoft Security Intelligence
- source_date: 2017-02-08
- false_positive_risk: `medium`
- why_not_execution_authorization: Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。

用户应检查：

- [ ] 核对软件是否由用户主动安装以及安装来源。
- [ ] 核对本地发布者、版本、签名与来源页面描述是否属于同一实体。
- [ ] 检查是否存在捆绑、浏览器修改、异常启动项或安全工具独立提示。

允许的后续建议：

- `review`
- `keep`
- `ask_user`
- `check_vendor_uninstaller`
- `check_defender_or_security_tool`
- `collect_more_evidence`
- `report_false_positive`

## app:mediaarena

- matched_record_id: `ev-real-ms-mediaarena`
- evidence: `PUA:Win32/MediaArena`
- match_basis: `evidence_indicator`
- indicator_type: `installer_family`
- source_url: https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FMediaArena&threatId=359463
- source_title: PUA:Win32/MediaArena threat description - Microsoft Security Intelligence
- source_date: 2023-03-20
- false_positive_risk: `medium`
- why_not_execution_authorization: Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。

用户应检查：

- [ ] 核对软件是否由用户主动安装以及安装来源。
- [ ] 核对本地发布者、版本、签名与来源页面描述是否属于同一实体。
- [ ] 检查是否存在捆绑、浏览器修改、异常启动项或安全工具独立提示。

允许的后续建议：

- `review`
- `keep`
- `ask_user`
- `check_vendor_uninstaller`
- `check_defender_or_security_tool`
- `collect_more_evidence`
- `report_false_positive`

## app:fusioncore

- matched_record_id: `ev-real-ms-fusioncore`
- evidence: `PUA:Win32/FusionCore`
- match_basis: `evidence_indicator`
- indicator_type: `installer_family`
- source_url: https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FFusionCore
- source_title: PUA:Win32/FusionCore threat description - Microsoft Security Intelligence
- source_date: 2016-06-28
- false_positive_risk: `medium`
- why_not_execution_authorization: Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。

用户应检查：

- [ ] 核对软件是否由用户主动安装以及安装来源。
- [ ] 核对本地发布者、版本、签名与来源页面描述是否属于同一实体。
- [ ] 检查是否存在捆绑、浏览器修改、异常启动项或安全工具独立提示。

允许的后续建议：

- `review`
- `keep`
- `ask_user`
- `check_vendor_uninstaller`
- `check_defender_or_security_tool`
- `collect_more_evidence`
- `report_false_positive`

## app:piriform

- matched_record_id: `ev-real-ms-piriformbundler`
- evidence: `PUA:Win32/PiriformBundler`
- match_basis: `evidence_indicator`
- indicator_type: `installer_family`
- source_url: https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FPiriformBundler
- source_title: PUA:Win32/PiriformBundler threat description - Microsoft Security Intelligence
- source_date: 2020-07-27
- false_positive_risk: `high`
- why_not_execution_authorization: Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。

用户应检查：

- [ ] 核对软件是否由用户主动安装以及安装来源。
- [ ] 核对本地发布者、版本、签名与来源页面描述是否属于同一实体。
- [ ] 检查是否存在捆绑、浏览器修改、异常启动项或安全工具独立提示。

允许的后续建议：

- `review`
- `keep`
- `ask_user`
- `check_vendor_uninstaller`
- `check_defender_or_security_tool`
- `collect_more_evidence`
- `report_false_positive`
