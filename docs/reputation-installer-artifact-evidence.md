# Installer Artifact Evidence

installer_artifact 必须具备时间范围与受影响组件；它只描述特定安装器或推广链路，不是软件本体结论。

`installer_artifact` 表示来源指向特定安装器、下载器、捆绑器、推广链路、更新器或组件。它必须包含 `installer_or_bundle_artifact`、`version_or_time_scope` 和 `affected_component`。

它不等于软件本体永久定性，不等于厂商所有产品，也不代表其他版本或渠道。Matcher 只能输出 review hint；Review Pack 必须展示范围与 guard reason。它永远不能单独授权系统动作。
