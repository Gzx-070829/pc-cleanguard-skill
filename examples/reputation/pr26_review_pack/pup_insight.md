# PUP 风险洞察 / PUP Risk Insight

## safety_notice

真实来源 evidence 和 indicator match 仅用于解释、排序和人工复核，不是删除、卸载、禁用或注册表修改授权。Review Pack 在本地离线生成，不联网、不上传，也不替代 Microsoft Defender 或其他安全工具。

命中目标：5
真实来源命中：5
Synthetic 命中：0
执行门控合格：0
Indicator 命中：5
高不确定性命中：1

## 可疑行为类别

- `ad_popup`
- `browser_hijacking`
- `forced_installation`
- `malicious_bundling`
- `malicious_collection`
- `other_user_rights_violation`

## 不确定性

- app:installcore: mapping_type=direct_entity, false_positive_risk=medium
- app:slimware: mapping_type=direct_entity, false_positive_risk=medium
- app:mediaarena: mapping_type=direct_entity, false_positive_risk=medium
- app:fusioncore: mapping_type=direct_entity, false_positive_risk=medium
- app:piriform: mapping_type=direct_entity, false_positive_risk=high

## 建议人工复核

- 先查看 source_url、match_basis、false_positive_risk 与人工复核清单。
- 核对本地软件身份与用户安装意图；证据不足时保留并收集更多证据。
- 若名称或实体不一致，提交本地 false-positive feedback 模板供人工修订。

## Evidence Guard details

- record=`ev-real-ms-installcore` / mapping_type=`direct_entity` / entity_scope=`windows_desktop_software` / match_basis=`evidence_indicator` / indicator_type=`installer_family` / indicator_value=`InstallCore` / target_observed=`Example InstallCore Bundle Helper` / match_strength=`medium` / source_title=PUA:Win32/InstallCore threat description - Microsoft Security Intelligence / source_date=2015-03-11 / source_url=https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FInstallCore / guard_reason=evidence is explanation/review/sorting/risk-hint only; execution gating is always blocked; Family-name overlap is a high-false-positive review hint and requires local identity checks.; indicator matching cannot authorize execution / why_not_execution_authorization=Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。 / human_review_checklist=核对软件是否由用户主动安装以及安装来源。; 核对本地发布者、版本、签名与来源页面描述是否属于同一实体。; 检查是否存在捆绑、浏览器修改、异常启动项或安全工具独立提示。
- record=`ev-real-ms-slimware` / mapping_type=`direct_entity` / entity_scope=`windows_desktop_software` / match_basis=`evidence_indicator` / indicator_type=`installer_family` / indicator_value=`Slimware` / target_observed=`Example Slimware Driver Utility` / match_strength=`medium` / source_title=PUA:Win32/Slimware threat description - Microsoft Security Intelligence / source_date=2017-02-08 / source_url=https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FSlimware / guard_reason=evidence is explanation/review/sorting/risk-hint only; execution gating is always blocked; Family-name overlap is a high-false-positive review hint and requires local identity checks.; indicator matching cannot authorize execution / why_not_execution_authorization=Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。 / human_review_checklist=核对软件是否由用户主动安装以及安装来源。; 核对本地发布者、版本、签名与来源页面描述是否属于同一实体。; 检查是否存在捆绑、浏览器修改、异常启动项或安全工具独立提示。
- record=`ev-real-ms-mediaarena` / mapping_type=`direct_entity` / entity_scope=`windows_desktop_software` / match_basis=`evidence_indicator` / indicator_type=`installer_family` / indicator_value=`MediaArena` / target_observed=`Example MediaArena Search Tool` / match_strength=`medium` / source_title=PUA:Win32/MediaArena threat description - Microsoft Security Intelligence / source_date=2023-03-20 / source_url=https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FMediaArena&threatId=359463 / guard_reason=evidence is explanation/review/sorting/risk-hint only; execution gating is always blocked; Family-name overlap is a high-false-positive review hint and requires local identity checks.; indicator matching cannot authorize execution / why_not_execution_authorization=Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。 / human_review_checklist=核对软件是否由用户主动安装以及安装来源。; 核对本地发布者、版本、签名与来源页面描述是否属于同一实体。; 检查是否存在捆绑、浏览器修改、异常启动项或安全工具独立提示。
- record=`ev-real-ms-fusioncore` / mapping_type=`direct_entity` / entity_scope=`windows_desktop_software` / match_basis=`evidence_indicator` / indicator_type=`installer_family` / indicator_value=`FusionCore` / target_observed=`Example FusionCore Offer Manager` / match_strength=`medium` / source_title=PUA:Win32/FusionCore threat description - Microsoft Security Intelligence / source_date=2016-06-28 / source_url=https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FFusionCore / guard_reason=evidence is explanation/review/sorting/risk-hint only; execution gating is always blocked; Family-name overlap is a high-false-positive review hint and requires local identity checks.; indicator matching cannot authorize execution / why_not_execution_authorization=Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。 / human_review_checklist=核对软件是否由用户主动安装以及安装来源。; 核对本地发布者、版本、签名与来源页面描述是否属于同一实体。; 检查是否存在捆绑、浏览器修改、异常启动项或安全工具独立提示。
- record=`ev-real-ms-piriformbundler` / mapping_type=`direct_entity` / entity_scope=`windows_desktop_software` / match_basis=`evidence_indicator` / indicator_type=`installer_family` / indicator_value=`PiriformBundler` / target_observed=`Example PiriformBundler Installer Artifact` / match_strength=`medium` / source_title=PUA:Win32/PiriformBundler threat description - Microsoft Security Intelligence / source_date=2020-07-27 / source_url=https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FPiriformBundler / guard_reason=evidence is explanation/review/sorting/risk-hint only; execution gating is always blocked; relation confidence is not high; Family-name overlap is a high-false-positive review hint and requires local identity checks.; indicator matching cannot authorize execution / why_not_execution_authorization=Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。 / human_review_checklist=核对软件是否由用户主动安装以及安装来源。; 核对本地发布者、版本、签名与来源页面描述是否属于同一实体。; 检查是否存在捆绑、浏览器修改、异常启动项或安全工具独立提示。

真实来源 evidence 仅用于解释、排序和人工复核，不是删除、卸载、禁用授权。
