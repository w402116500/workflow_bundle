# Standard Thesis Workflow

## 1. 流程目标

标准流程面向“给定一个计算机项目及其文档材料，产出完整论文正文与 DOCX 交付件”的场景，按阶段组织如下：

1. 项目接入
2. 材料抽取
3. 标准工作区生成
4. 章节写作
5. 发布构建
6. 交付校验

当前仓库已完成第 3 到第 6 阶段的示例实例化，并为第 1 到第 2 阶段预留了标准配置与目录接口。
当前版本已补齐第 1 到第 3 阶段的基础命令接口，但正文自动写作仍在后续阶段。

如果是由人工发起一个新的 AI 对话来执行本流程，建议先直接使用：

- `workflow/06-ai-prompt-guide.md`

其中已经提供了可复制的接手、写章、发布、排障提示模板。

## 2. 阶段说明

### 2.1 项目接入

输入至少包含以下几类材料中的大部分：

- 前端源码
- 后端源码
- 数据库设计或 SQL
- 智能合约代码或合约设计文档
- 规划文档、需求文档、设计文档

推荐做法：

- 用一个 `project manifest` 明确这些路径。
- 缺失材料允许先推断，再在待补项中列出。

CLI：

- `python3 workflow_bundle/tools/cli.py intake --project-root <path> --title <title> --out <workspace-dir>`
- `intake` 完成后会同步 workspace 本地 `workflow/*.md` 与 `workflow/skills/*`，避免新对话继续读取旧接手资产

### 2.2 材料抽取

目标是把原项目里的信息沉淀为“证据材料包”，后续写作不直接反复扫整个源仓库。

输出建议包含：

- 项目目标与应用场景
- 架构与模块边界
- 角色与权限模型
- 核心业务流程
- API 与接口列表
- 数据库表与关键字段
- 合约/链上职责
- 部署与测试要点
- 图、表、测试截图、附录索引等论文资产
- 代码证据包，包括真实代码片段与白底黑字代码截图
- 缺失项与推断项

CLI：

- `python3 workflow_bundle/tools/cli.py extract-code --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py extract --config <workspace.json>`

### 2.3 标准工作区生成

把抽取后的材料映射到统一工作区：

- `docs/`：规划、需求、参考材料
- `polished_v3/`：论文正文真源
- `images/` / `docs/images/`：图表与插图
- `tools/`：构建脚本
- `word_output/`：生成产物

对于新项目，可以沿用本仓库的结构，也可以保持原项目目录不动，再通过 `workspace config` 指向真实路径。

CLI：

- `python3 workflow_bundle/tools/cli.py scaffold --config <workspace.json>`

### 2.4 章节写作

推荐按以下逻辑推进：

1. 摘要与题目
2. 绪论与研究现状
3. 技术与工具介绍
4. 需求分析
5. 系统设计
6. 系统实现
7. 系统测试
8. 结论、致谢与参考文献

当前示例实例的章节正文真源是：

- [polished_v3](../polished_v3)

章节准备命令建议：

- `python3 workflow_bundle/tools/cli.py prepare-writing --config <workspace.json>` 可在材料抽取或 profile 更新后重复执行；当前版本会保留 `chapter_queue.json` 中已有的写作进度。
- `python3 workflow_bundle/tools/cli.py prepare-chapter --config <workspace.json> --chapter <chapter-file>` 用于按单章刷新 packet，不会回退章节状态。
- `python3 workflow_bundle/tools/cli.py start-chapter --config <workspace.json> --chapter <chapter-file>` 会在 `prepare-chapter` 基础上额外生成一个 `*.start.md` 开写 brief，便于直接进入写章。
- 对第 5 章，推荐先执行 `extract-code` 或直接执行 `extract`，确保代码片段和代码截图已经入库到工作区，再执行 `prepare-chapter`。

### 2.5 发布构建

推荐入口：

- `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>`
- `bash workflow_bundle/workflow/scripts/build_release.sh`

其中 shell wrapper 只保留兼容作用；标准发布构建链以 `release-build` 为准。

### 2.6 交付校验

推荐至少执行：

- 文档是否成功生成
- 引用锚点是否完整
- 图题、表题、标题层级是否正常
- 章节是否包含 packet 要求的图表/结构化条目，避免退化成纯叙述稿
- 第 5 章是否同时包含后端实现、前端实现和真实代码截图
- 交付件是否属于 Linux 交付版还是 Windows 终稿

推荐入口：

- `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>`
- `bash workflow_bundle/workflow/scripts/verify_release.sh`
- `bash workflow_bundle/workflow/scripts/postprocess_release.sh`

如果冷启动 `resume` 输出 `workflow_signature_status: drifted`，先执行：

- `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`

然后再继续读取 workspace 本地 skill 和执行文档。

### 2.7 工作流回归

如果本轮修改的是 `workflow_bundle/` 下的工具、技能、脚本或工作流文档，不应只靠手工 spot check。推荐直接执行：

- `python3 workflow_bundle/tools/cli.py selftest`
- `python3 workflow_bundle/tools/cli.py selftest --workspace-config <workspace.json>`

其中：

- 默认 `selftest` 只覆盖 bundle 自带 fixture 的冷启动链
- 传入 `--workspace-config` 后会追加真实 workspace 的 Linux 发布回归
- `selftest` 不会自动修复 `workflow_signature_status: drifted` 或活动锁；这两种状态会被直接报错出来

## 3. 当前示例实例的源与产物边界

- 正文真源：`polished_v3/`
- 证据材料：`docs/`、`code/`
- 工作流文档：`workflow/`
- 生成产物：`word_output/`
- 调试解包：`tools/unpacked_*`

不要把 `word_output/` 或 `tools/unpacked_*` 当成正文真源。
