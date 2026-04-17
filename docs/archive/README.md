# Historical Notes

本目录用于说明 `workflow_bundle` 公共仓库如何处理历史材料。

## 归档原则

- 默认接手与执行应只依赖 `README.md`、`workflow/*.md`、`workflow/templates/*`、`tools/cli.py` 与正式回归入口。
- 历史审计、阶段性复盘和一次性迁移说明，不应进入默认阅读顺序，也不应替代正式 CLI 状态判断。
- 与具体 workspace、具体学校论文、具体本机路径强绑定的执行日记，应留在对应 workspace 或 companion 文档仓库，不应继续作为公共 bundle 的主文档。

## 当前仓库中的历史文件

- `docs/current_workflow_status_audit_2026-03-31.md`
  - 仅保留历史结论摘要，不再代表当前状态。
- `docs/workflow_optimization_log.md`
  - 作为 bundle 面向公共仓库的轻量变更记录保留；不再承载项目级长日志。

## 使用建议

- 想知道“现在这个 workspace 处于什么状态”，请直接执行 `resume`、`release-preflight` 或 `selftest`。
- 想知道“bundle 最近做了什么正式改动”，请查看 `docs/workflow_optimization_log.md`。
- 想知道“某篇论文当时具体怎么改过”，应回到那篇论文对应的 workspace 文档，而不是依赖公共 bundle 仓库。
