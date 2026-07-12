# v0.3.0 Public Preview Release Checklist

- [ ] `pc_cleanguard.__version__` 与 CLI `--version` 均为 `0.3.0`。
- [ ] 运行 `python -m pc_cleanguard.cli doctor release-check`，所有本地检查通过。
- [ ] 运行五分钟 dry-run 试用并阅读 START HERE、用户摘要、清理报告、PUP insight 和 audit。
- [ ] 确认试用只进入 quarantine，并验证 `quarantine list/restore`。
- [ ] Reputation 命中明确不是删除、卸载或禁用授权。
- [ ] 文档明确不替代杀毒软件，不联网、不上传、不静默删除。
- [ ] showcase 去标识化，不含真实用户路径、机器名、账号、token 或凭据。
- [ ] compileall、全部 unittest、diff check、危险 API 搜索通过。
- [ ] main 工作树干净，已有 `v0.1.0`、`v0.2.0`，尚无 `v0.3.0`。
