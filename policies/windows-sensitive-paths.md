# Windows Sensitive Paths

下列路径模式默认 `BLOCK` 或强 `KEEP`（不区分大小写，包含其子路径）：

The following path patterns and their descendants default to `BLOCK` or strong `KEEP`, case-insensitively:

```text
C:\Windows
C:\Windows\System32
C:\Windows\SysWOW64
C:\Windows\WinSxS
C:\Windows\System32\DriverStore
C:\ProgramData\Microsoft\Crypto
C:\ProgramData\Microsoft\Protect
%USERPROFILE%\Documents
%USERPROFILE%\Desktop
%USERPROFILE%\Pictures
%USERPROFILE%\Videos
%APPDATA%\Microsoft\Credentials
%LOCALAPPDATA%\Microsoft\Credentials
browser profile directories
password-manager vaults
source-code repositories
recovery partitions
```

这些路径默认 `BLOCK` 或强 `KEEP`。除非未来专家策略明确允许，否则不得修改。路径别名、短路径、符号链接、大小写和环境变量展开都必须在判断前规范化；PR1 仅做保守字符串识别，不进行文件系统解析。

These paths must not be modified unless a future expert policy explicitly permits it. Normalize aliases, short paths, symbolic links, case, and environment variables before evaluation. PR1 performs conservative string recognition only and does not resolve the filesystem.
