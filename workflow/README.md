# Thesis Workflow

本目录是论文工作流的统一入口，目标是把“项目材料抽取、章节写作、DOCX 生成、交付校验”收敛为一套可复用流程。

当前正式入口已经切换到：

- `/home/ub/thesis_materials/workflow_bundle`

根目录下的 `workflow/`、`tools/` 继续保留兼容入口，但新的 AI 对话、无参脚本和接手流程应优先以 `workflow_bundle/` 为准。
当前 root 侧 `tools/cli.py` 与 `workflow/scripts/*.sh` 已收敛为 bundle 转发层，不再承载独立运行逻辑。
当前 root 侧 `tools/core/` 也仅保留为兼容镜像；真实运行实现以 `workflow_bundle/tools/core/` 为准。修改工具链后应执行 `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh` 确认 mirror 未漂移。
如需把 bundle 侧核心实现回刷到 root 兼容镜像，可执行 `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`。
root `tools/*.py` 与 `workflow/scripts/*.sh` 兼容层也由该命令自动重建，不建议再手工编辑这些 wrapper。

## 先读什么

- [06-ai-prompt-guide.md](06-ai-prompt-guide.md)：给人类操作者的 AI 提示词模板与接手规则。
- [THESIS_WORKFLOW.md](THESIS_WORKFLOW.md)：标准阶段说明。
- [CHAPTER_EXECUTION.md](CHAPTER_EXECUTION.md)：逐章写作执行协议。
- [WORKSPACE_SPEC.md](WORKSPACE_SPEC.md)：标准工作区与配置接口。
- [references/command-map.md](references/command-map.md)：命令清单。
- [MIGRATION.md](MIGRATION.md)：旧入口到新入口的映射。

## 当前仓库如何对应到标准流程

- 工作流框架：本目录 `workflow/`
- 当前项目实例：`docs/`、`code/`、`polished_v3/`
- 生成脚本：`tools/`
- 生成产物：`word_output/`

## 推荐执行顺序

接入新项目：

1. `python3 workflow_bundle/tools/cli.py intake --project-root <path> --title <title> --out <workspace-dir>`
   - `intake` 现在会同时把 workspace 本地 `workflow/*.md` 与 `workflow/skills/*` 同步到当前 bundle 版本
2. `python3 workflow_bundle/tools/cli.py extract-code --config <workspace-dir>/workflow/configs/workspace.json`
3. `python3 workflow_bundle/tools/cli.py extract --config <workspace-dir>/workflow/configs/workspace.json`
4. `python3 workflow_bundle/tools/cli.py scaffold --config <workspace-dir>/workflow/configs/workspace.json`
5. `python3 workflow_bundle/tools/cli.py literature --config <workspace-dir>/workflow/configs/workspace.json`
6. `python3 workflow_bundle/tools/cli.py prepare-outline --config <workspace-dir>/workflow/configs/workspace.json`
7. `python3 workflow_bundle/tools/cli.py prepare-writing --config <workspace-dir>/workflow/configs/workspace.json`
8. `python3 workflow_bundle/tools/cli.py start-chapter --config <workspace-dir>/workflow/configs/workspace.json --chapter 04-系统设计.md`
9. 完成正文后执行 `python3 workflow_bundle/tools/cli.py prepare-figures --config <workspace-dir>/workflow/configs/workspace.json`

其中：

- `scaffold` 会生成 `docs/writing/project_profile.json` 与 `docs/writing/project_profile.md`
- `scaffold` 只会初始化 `polished_v3/` 中缺失或空白的章节骨架，不会覆盖已存在的正文文件
- 大章节框架固定，小节结构按项目画像动态生成
- `prepare-outline` 会在写作前生成 `docs/writing/thesis_outline.json` 与 `docs/writing/thesis_outline.md`，并展开到章节、小节、子小节层级，用于先锁定论文大纲和目录
- `extract-code` 会先把第 5 章可直接引用的源码片段摘录到 `docs/materials/code_snippets/`，并同步生成白底黑字代码截图到 `docs/materials/code_screenshots/`
- `extract` 会补充结构化论文资产，不只抽 summary；图、表、附录索引、代码入口、测试证据都会进入 `material_pack`
- `prepare-writing` 与 `prepare-chapter` 默认消费该 project profile，而不是旧的固定小节模板
- `chapter packet` 会内置 `outline_snapshot` 与 `outline_sync`，用于记录写作包生成时所依据的大纲快照
- `start-chapter` 会在 packet 基础上额外生成 `*.start.md` 开写 brief，便于直接进入单章执行
- 若 `outline_sync.status` 不是 `current`，表示章节写作包与当前论文目录不同步，应先重新执行 `prepare-chapter`
- `prepare-chapter` 会为每章生成资产合同，显式要求图题、表题、附录项或占位，不允许自然退化为纯文字章节
- `literature` 会继续生成 `literature_pack/reference_registry`，并额外生成 `docs/writing/research/` 侧车调研包
- `finalize-chapter` 之后会自动刷新 `docs/writing/citation_audit.md`，把全文引用按首次出现顺序重排，并对重复引用、单句多引用给出告警
- `prepare-figures` 会从项目原始文档和当前第 5 章结构中生成项目专属图资源，写入 `docs/images/generated/`，并同步更新 `workspace.json.figure_map`
- `prepare-figures` 会为每张生成图记录 `spec_hash`；当输入未变化时会直接复用已有 PNG，避免每次发布都重新请求 Mermaid 渲染

对已有工作区发布：

1. `python3 workflow_bundle/tools/cli.py resume --config <workspace-dir>/workflow/configs/workspace.json`
   - 若输出 `workflow_signature_status: drifted`，先执行 `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace-dir>/workflow/configs/workspace.json`
2. `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace-dir>/workflow/configs/workspace.json`
3. `bash workflow_bundle/workflow/scripts/check_workspace.sh <workspace-dir>/workflow/configs/workspace.json`
4. `bash workflow_bundle/workflow/scripts/compare_versions.sh`
5. `python3 workflow_bundle/tools/cli.py release-build --config <workspace-dir>/workflow/configs/workspace.json`
6. `bash workflow_bundle/workflow/scripts/postprocess_release.sh <workspace-dir>/workflow/configs/workspace.json`
7. `python3 workflow_bundle/tools/cli.py release-verify --config <workspace-dir>/workflow/configs/workspace.json`

写作阶段如需单独整理引用编号，也可以显式执行：

- `python3 workflow_bundle/tools/cli.py normalize-citations --config <workspace-dir>/workflow/configs/workspace.json`

图资源阶段也可以显式执行：

- `python3 workflow_bundle/tools/cli.py prepare-figures --config <workspace-dir>/workflow/configs/workspace.json`

Linux 下也可以显式使用：

- `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>`
- `bash workflow_bundle/workflow/scripts/release_preflight.sh`
- `bash workflow_bundle/workflow/scripts/postprocess_release_linux.sh`
- `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>` 是统一发布前检查入口；`check_workspace.sh` 现在只是它的兼容别名
- `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>` 是本地 workflow 文档和技能副本的同步入口；`refresh-handoff` 不会替代它把 drifted 状态改回 current
- `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>` 会自动执行 `release-preflight`、刷新 `figure_map`、构建 DOCX 并写出 build summary
- `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>` 会自动执行 `release-preflight`、刷新配图、重建 DOCX、校验引用锚点并写出 release summary
- `bash workflow_bundle/workflow/scripts/check_workspace.sh <workspace.json>` 现在会同时检查 `chapter_queue.json` 中的 `packet_outline_status`，并列出 `stale / legacy / missing` 的阻塞项
- `bash workflow_bundle/workflow/scripts/check_workspace.sh <workspace.json>` 现在还会显示 `workflow_signature_status`、`lock_status` 和 orchestration skills
- `bash workflow_bundle/workflow/scripts/build_release.sh <workspace.json>` 与 `bash workflow_bundle/workflow/scripts/verify_release.sh <workspace.json>` 现在只是上述 CLI 发布命令的薄封装
- `bash workflow_bundle/workflow/scripts/postprocess_release.sh <workspace.json>` 在 Windows 下会自动解析基础排版稿与终稿输出路径，并在终排成功后写出终稿审计摘要
- `workflow_bundle/workflow/scripts/build_release_docx.sh` 仅保留为内部兼容 helper，用于返回 DOCX 路径，不建议作为正常发布入口
- `bash workflow_bundle/workflow/scripts/build_release.sh <workspace.json>` 完成后会在 `word_output/` 下写出：
  - `build_summary.json`
  - `build_runs/build_summary_<timestamp>.json`
- `bash workflow_bundle/workflow/scripts/verify_release.sh <workspace.json>` 完成后会在 `word_output/` 下写出：
  - `figure_prepare_summary.json`
  - `release_summary.json`
  - `release_runs/release_summary_<timestamp>.json`
- Windows `postprocess_release.sh <workspace.json>` 完成后会在 `final/` 下写出：
  - `final_summary.json`
  - `final_runs/final_summary_<timestamp>.json`

## 当前默认配置

默认工作区配置：

- [configs/current_workspace.json](configs/current_workspace.json)
- 它只保留为示例实例配置；无参命令现在优先读取 `workflow_bundle/workflow/configs/active_workspace.json`

当前活动工作区可通过以下命令查看：

- `python3 workflow_bundle/tools/cli.py resolve-active-workspace`
- `python3 workflow_bundle/tools/cli.py lock-status`

当前工作流接手入口：

- `python3 workflow_bundle/tools/cli.py resume`
- `python3 workflow_bundle/tools/cli.py sync-workflow-assets`
- `python3 workflow_bundle/tools/cli.py refresh-handoff`
- `workflow/skills/thesis-workflow-orchestrator/SKILL.md`
- `workflow/06-ai-prompt-guide.md`

当前示例项目清单：

- [configs/current_project_manifest.json](configs/current_project_manifest.json)

本地章节润色 skill：

- [skills/academic-paper-crafter/SKILL.md](skills/academic-paper-crafter/SKILL.md)
- [skills/thesis-workflow-orchestrator/SKILL.md](skills/thesis-workflow-orchestrator/SKILL.md)

本地文献调研与论文阅读 skill 来源：

- `paper-research-agent/`
- `paper-reader/`

新项目模板：

- [templates/workspace-config.template.json](templates/workspace-config.template.json)
- [templates/project-manifest.template.json](templates/project-manifest.template.json)

本仓库还提供一个最小 Fabric 样本，用于验证 Hyperledger Fabric 分支：

- [fixtures/fabric_trace_demo](fixtures/fabric_trace_demo)
