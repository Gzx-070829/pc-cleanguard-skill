# 中文 Evidence 复核示例

## 可接受：官方移动 APP/SDK 批次通报

记录官方页面 URL、标题、日期和批次级行为摘要；映射为 `analogical_behavior + mobile_app/mobile_sdk`。允许用途仅为 explanation，误伤风险为 high。

## 需要更多证据：下载站或推广器争议

下载站页面、推广器行为或同名俗称不能映射到用户本机软件。缺少明确安装器哈希、发布者、版本与官方来源时，只进入 candidate/review queue。

## 拒绝：网传黑名单

无可核验 URL、论坛截图、单条投诉以及安全厂商专有签名、规则、检测逻辑或样本库均拒绝。任何 accepted record 仍固定 `execution_authorized=false`。
