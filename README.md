# Workflow Bundle

本目录用于把当前论文工作流中真正会被读取、执行和复用的入口收拢到一个统一位置，方便新的 AI 对话在不依赖历史聊天上下文的前提下，快速接手同一套流程。

## 目录定位

- `workflow/`
  - 工作流文档、命令地图、脚本、默认配置模板、技能入口
- `tools/`
  - 统一 CLI、核心 Python 工具、Windows 后处理兼容入口
  - 其中 `workflow_bundle/tools/core/` 是权威运行实现，root `tools/core/` 仅作为兼容镜像保留
  - root `tools/*.py` launcher 与 `workflow/scripts/*.sh` wrapper 由 `sync_root_compat.sh` 自动重建
- `paper-research-agent/`
  - 文献调研技能根目录镜像，供 `tools/core/intake.py` 在 bundle 内直接复制
- `paper-reader/`
  - 论文 PDF 阅读技能根目录镜像，供 `tools/core/intake.py` 在 bundle 内直接复制
- `docs/`
  - 当前工作流状态审计与优化日志快照

## 先看什么

新的 AI 对话接手时，推荐按以下顺序阅读：

1. `python3 workflow_bundle/tools/cli.py resume`
   - 若输出 `workflow_signature_status: drifted`，立即执行 `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`
2. `workflow/06-ai-prompt-guide.md`
3. `workflow/README.md`
4. `workflow/THESIS_WORKFLOW.md`
5. `workflow/CHAPTER_EXECUTION.md`
6. `workflow/references/command-map.md`
7. `workflow/09-testing-and-regression.md`
8. `docs/current_workflow_status_audit_2026-03-31.md`
9. `docs/workflow_optimization_log.md`

## 正式入口

推荐优先使用 bundle 内的脚本和 CLI，而不是重新去根目录手工拼命令：

- `python3 workflow_bundle/tools/cli.py set-active-workspace --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py resolve-active-workspace`
- `python3 workflow_bundle/tools/cli.py refresh-handoff --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py resume --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py lock-status --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py clear-lock --config <workspace.json> --force`
- `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py selftest`
- `python3 workflow_bundle/tools/cli.py selftest --workspace-config <workspace.json>`
- `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
- `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`
- `bash workflow_bundle/workflow/scripts/release_preflight.sh <workspace.json>`
- `bash workflow_bundle/workflow/scripts/check_workspace.sh <workspace.json>`
- `bash workflow_bundle/workflow/scripts/compare_versions.sh <workspace.json>`
- `python3 workflow_bundle/tools/cli.py smoke-intake --project-root <fixture-path> --title <title> --out <workspace-dir>`
- `python3 workflow_bundle/tools/cli.py extract-code --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py extract --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py scaffold --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py literature --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py prepare-outline --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py prepare-writing --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py start-chapter --config <workspace.json> --chapter <chapter-file>`
- `python3 workflow_bundle/tools/cli.py finalize-chapter --config <workspace.json> --chapter <chapter-file> --status <drafted|polished|reviewed>`
- `bash workflow_bundle/workflow/scripts/build_release.sh <workspace.json>`
- `bash workflow_bundle/workflow/scripts/verify_release.sh <workspace.json>`

其中：

- `python3 workflow_bundle/tools/cli.py release-preflight` 是官方发布前检查入口；`workflow/scripts/release_preflight.sh` 只是对应的 shell 转发层
- `python3 workflow_bundle/tools/cli.py release-build` 是官方 Linux 发布构建入口，会顺序执行 `release-preflight -> prepare-figures -> build -> write-build-summary`
- `python3 workflow_bundle/tools/cli.py release-verify` 是官方 Linux 发布校验入口，会顺序执行 `release-preflight -> prepare-figures -> build -> verify -> write-release-summary`
- `python3 workflow_bundle/tools/cli.py selftest` 是官方本地回归入口；默认执行 bundle 自带 fixture 冷启动回归，传入 `--workspace-config` 后会追加真实 workspace 的 Linux 发布回归
- `python3 workflow_bundle/tools/cli.py sync-workflow-assets` 用于把 workspace 本地 `workflow/*.md` 与 `workflow/skills/*` 同步到当前 bundle 版本；当 `workflow_signature_status=drifted` 时应先执行它
- `check_workspace.sh` 现在保留为兼容别名，内部直接转发到 `release_preflight.sh`
- `build_release.sh` 与 `verify_release.sh` 现在也只是对应 `release-build` 与 `release-verify` 的 shell 转发层
- `build_release_docx.sh` 仅保留为内部兼容 helper，用于输出构建后的 DOCX 路径，不再作为新对话的公开入口

## 当前活动工作区

当前实际正在写作和验证的项目工作区仍在仓库外层目录，不在本 bundle 内复制正文：

- `workspaces/teatrace_thesis/workflow/configs/workspace.json`

需要注意：

- 本 bundle 是流程运行时入口，不是正文真源。
- 论文正文真源仍然是各 workspace 下的 `polished_v3/`。
- `word_output/`、`final/`、`tools/unpacked_*` 都不是正文来源。

## 技能布局

当前 bundle 内保留了四类实际会被消费的技能：

- `workflow/skills/academic-paper-crafter/`
- `workflow/skills/thesis-workflow-resume/`
- `workflow/skills/thesis-workflow-orchestrator/`
- `workflow/skills/paper-research-agent/`
- `workflow/skills/paper-reader/`

同时保留根目录级 `paper-research-agent/` 与 `paper-reader/` 镜像，是为了兼容当前 `tools/core/intake.py` 的复制逻辑，避免在 bundle 内运行 `intake` 时找不到技能源目录。

## 不包含什么

为了保持目录可维护，本 bundle 没有收进以下内容：

- `tools/node_modules/`
- `tools/unpacked_*`
- `tools/examples/health_record/`
- 任意 workspace 下的正文、材料包、DOCX 产物

当前唯一保留在 bundle 内的 fixture 是最小 smoke fixture：

- `workflow/fixtures/fabric_trace_demo/`

它用于验证新 workspace 的 intake -> prepare-writing 冷启动链，而不是作为正文实例。

## 回归测试

推荐的本地回归入口：

- `python3 workflow_bundle/tools/cli.py selftest`
- `python3 workflow_bundle/tools/cli.py selftest --workspace-config <workspace.json>`
- `bash workflow_bundle/workflow/scripts/selftest.sh`

说明：

- 默认 `selftest` 只运行 bundle 内 fixture，并把测试输出写到系统临时目录
- 传入 `--workspace-config` 后，会追加真实 workspace 的 `release-preflight -> release-build -> release-verify` 回归
- 对真实 workspace 的回归不会自动修复 `drifted` 或活动锁；这两类状态会直接失败并给出修复命令
