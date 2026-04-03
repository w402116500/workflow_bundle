# Command Map

## 标准入口

- 冷启动推荐顺序
  - `python3 workflow_bundle/tools/cli.py resume --config <workspace.json>`
  - 若输出 `workflow_signature_status: drifted`：`python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`
  - 如需刷新 handoff：`python3 workflow_bundle/tools/cli.py refresh-handoff --config <workspace.json>`
  - 如需先准备 AI 插图：`python3 workflow_bundle/tools/cli.py prepare-ai-figures --config <workspace.json>`
  - 进入发布链路：`python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>` -> `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>` -> `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>`
  - 回归当前 bundle：`python3 workflow_bundle/tools/cli.py selftest`
  - 回归 bundle + 真实 workspace：`python3 workflow_bundle/tools/cli.py selftest --workspace-config <workspace.json>`
- 设置当前活动工作区
  - `python3 workflow_bundle/tools/cli.py set-active-workspace --config <workspace.json>`
- 解析当前活动工作区
  - `python3 workflow_bundle/tools/cli.py resolve-active-workspace`
- 冷启动接手
  - `python3 workflow_bundle/tools/cli.py resume --config <workspace.json>`
- 同步工作流资产
  - `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`
- 刷新 handoff
  - `python3 workflow_bundle/tools/cli.py refresh-handoff --config <workspace.json>`
- 查看工作区锁
  - `python3 workflow_bundle/tools/cli.py lock-status --config <workspace.json>`
- 清理过期锁
  - `python3 workflow_bundle/tools/cli.py clear-lock --config <workspace.json> --force`
- 检查 root/bundle 兼容镜像是否漂移
  - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
- 回刷 root `tools/core/` 兼容镜像
  - `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`
- 检查工作区
  - `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>`
  - `bash workflow_bundle/workflow/scripts/release_preflight.sh`
  - `bash workflow_bundle/workflow/scripts/check_workspace.sh`
  - `python3 workflow_bundle/tools/cli.py check-workspace --config <workspace.json>`
- 对比草稿与正文
  - `bash workflow_bundle/workflow/scripts/compare_versions.sh`
- 工作流回归
  - `python3 workflow_bundle/tools/cli.py selftest`
  - `bash workflow_bundle/workflow/scripts/selftest.sh`
- 构建发布稿
  - `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>`
  - `bash workflow_bundle/workflow/scripts/build_release.sh`
- 平台后处理
  - `bash workflow_bundle/workflow/scripts/postprocess_release.sh`
  - `bash workflow_bundle/workflow/scripts/postprocess_release_linux.sh`
- 校验引用锚点
  - `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>`
  - `bash workflow_bundle/workflow/scripts/verify_release.sh`

## 官方工具 CLI

- `python3 workflow_bundle/tools/cli.py set-active-workspace --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py resolve-active-workspace`
- `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py refresh-handoff --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py resume --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py lock-status --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py clear-lock --config <workspace.json> --force`
- `python3 workflow_bundle/tools/cli.py intake --project-root <path> --title <title> --out <workspace-dir>`
- `python3 workflow_bundle/tools/cli.py smoke-intake --project-root <fixture-path> --title <title> --out <workspace-dir>`
- `python3 workflow_bundle/tools/cli.py extract-code --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py extract --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py scaffold --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py literature --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py prepare-outline --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py prepare-writing --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py prepare-chapter --config <workspace.json> --chapter <chapter-file>`
- `python3 workflow_bundle/tools/cli.py start-chapter --config <workspace.json> --chapter <chapter-file>`
- `python3 workflow_bundle/tools/cli.py finalize-chapter --config <workspace.json> --chapter <chapter-file>`
- `python3 workflow_bundle/tools/cli.py normalize-citations --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py prepare-ai-figures --config <workspace.json> [--fig <图号>] [--force] [--dry-run]`
- `python3 workflow_bundle/tools/cli.py check-workspace --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py selftest`
- `python3 workflow_bundle/tools/cli.py prepare-figures --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py postprocess --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py write-build-summary --config <workspace.json> --docx <docx-path>`
- `python3 workflow_bundle/tools/cli.py write-release-summary --config <workspace.json> --docx <docx-path>`
- `python3 workflow_bundle/tools/cli.py write-finalization-summary --config <workspace.json> --base-docx <docx-path> --final-docx <docx-path>`
- `python3 workflow_bundle/tools/cli.py build --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py verify <workspace.json|docx-path>`
- `python3 tools/cli.py example generate-diagrams --example health_record`
- `python3 tools/cli.py example generate-skeleton --example health_record`

## 章节执行说明

- `workflow/CHAPTER_EXECUTION.md`

## 兼容旧入口

- `python3 tools/build_final_thesis_docx.py`
- `python3 tools/verify_citation_links.py word_output/<file>.docx`
- `python3 tools/generate_thesis_diagrams.py`

## 默认配置

- 当前活动工作区指针：`workflow_bundle/workflow/configs/active_workspace.json`
- 示例工作区配置：`workflow/configs/current_workspace.json`（仅示例，不再作为当前项目默认值）
- 项目清单：`workflow/configs/current_project_manifest.json`

## 说明

- `workflow_signature_status` 以 workspace 本地 `docs/workflow/workflow_assets_state.json` 为准，不再以 handoff 更新时间代替同步状态。
- `refresh-handoff` 只刷新 handoff 快照，不会把 `workflow_signature_status: drifted` 自动改回 `current`。
- `build_release.sh`、`verify_release.sh`、`check_workspace.sh`、`selftest.sh` 仍可继续使用，但它们现在都是 CLI 官方入口的兼容包装层。
