# Migration Notes

## 路径迁移

旧习惯：

- 直接查看 `README.md`
- 直接运行 `python3 tools/build_final_thesis_docx.py`
- 文档中引用不存在的 `workflow/` 路径

现在建议：

- 从 `workflow_bundle/README.md` 开始了解工作流
- 优先运行 `workflow_bundle/workflow/scripts/*.sh`
- 直接调用工具时优先使用 `python3 workflow_bundle/tools/cli.py ...`
- 版本号与发版状态优先使用 `python3 workflow_bundle/tools/cli.py version` 与 `VERSION`
- 无参命令默认从 `workflow_bundle/workflow/configs/active_workspace.json` 解析当前活动工作区
- `workflow/configs/current_workspace.json` 只保留为示例配置，不再作为当前项目默认值
- 新项目接入使用 `intake -> extract-code -> extract -> scaffold`
- 若 bundle 侧核心工具有更新，使用 `bash workflow_bundle/workflow/scripts/sync_root_compat.sh` 回刷 root `tools/core/` 兼容镜像
- root `tools/*.py` launcher 与 `workflow/scripts/*.sh` wrapper 也由同一命令自动重建，不再建议手工维护

## 兼容性

- 旧构建命令仍然保留
- 旧正文目录 `polished_v3/` 仍然保留
- 旧生成目录 `word_output/` 仍然保留

## 新增入口

- `workflow_bundle/workflow/scripts/check_workspace.sh`
- `workflow_bundle/workflow/scripts/compare_versions.sh`
- `workflow_bundle/workflow/scripts/release_preflight.sh`
- `workflow_bundle/workflow/scripts/build_release.sh`
- `workflow_bundle/workflow/scripts/postprocess_release.sh`
- `workflow_bundle/workflow/scripts/postprocess_release_linux.sh`
- `workflow_bundle/workflow/scripts/verify_release.sh`
- `workflow_bundle/workflow/scripts/check_bundle_sync.sh`
- `workflow_bundle/workflow/scripts/sync_root_compat.sh`
- `python3 workflow_bundle/tools/cli.py lock-status --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py clear-lock --config <workspace.json> --force`
- `python3 workflow_bundle/tools/cli.py version`
- `python3 workflow_bundle/tools/cli.py resume --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py intake --project-root <path> --title <title> --out <workspace-dir>`
- `python3 workflow_bundle/tools/cli.py smoke-intake --project-root <fixture-path> --title <title> --out <workspace-dir>`
- `python3 workflow_bundle/tools/cli.py extract-code --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py extract --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py scaffold --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py start-chapter --config <workspace.json> --chapter <chapter-file>`
