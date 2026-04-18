# Tools Layout

`tools/` 现在按职责拆分为四层：

- `cli.py`
  - 官方统一命令入口
- `core/`
  - 跨平台核心逻辑，如 DOCX 构建、引用锚点校验
  - `workflow_bundle/tools/core/` 是权威运行实现；root `tools/core/` 保留为字节级兼容镜像，供旧导入路径继续可用
- `windows/`
  - 仅在 Windows + Microsoft Word 环境下可用的后处理逻辑
- `examples/health_record/`
  - 当前内置健康档案示例项目专用的配图与骨架脚本

根目录下保留的 `build_final_thesis_docx.py`、`verify_citation_links.py`、`postprocess_word_format.py`、`generate_thesis_diagrams.py`、`generate_thesis_skeleton.js` 都是兼容包装，不再是主要实现所在位置。
root 侧兼容 launcher 与 `workflow/scripts/*.sh` wrapper 统一视为生成产物，不应手工维护。

如需维护 root/bundle 的兼容层是否仍然收敛，可以执行：

- `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
- `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`

当前项目接入能力的边界：

- 只支持本地项目路径
- 只支持 `FISCO BCOS` 和 `Hyperledger Fabric`

推荐入口：

- `python3 workflow_bundle/tools/cli.py version`
- `python3 workflow_bundle/tools/cli.py set-active-workspace --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py resolve-active-workspace`
- `python3 workflow_bundle/tools/cli.py refresh-handoff --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py resume --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py lock-status --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py clear-lock --config <workspace.json> --force`
- `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
- `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`
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
- `python3 workflow_bundle/tools/cli.py prepare-reference-guides --config <workspace.json> [--guide <guide-name>]`
- `python3 workflow_bundle/tools/cli.py normalize-citations --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py prepare-ai-figures --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py selftest`
- `python3 workflow_bundle/tools/cli.py selftest --workspace-config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py prepare-figures --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py postprocess --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py write-build-summary --config <workspace.json> --docx <docx-path>`
- `python3 workflow_bundle/tools/cli.py write-release-summary --config <workspace.json> --docx <docx-path>`
- `python3 workflow_bundle/tools/cli.py write-finalization-summary --config <workspace.json> --base-docx <docx-path> --final-docx <docx-path>`
- `python3 workflow_bundle/tools/cli.py build --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py verify <workspace.json|docx-path>`
- `python3 tools/cli.py example generate-diagrams --example health_record`

结构约束：

- 固定的是大章节框架，不是每章的小节模板
- `scaffold` 会生成 `docs/writing/project_profile.json`
- `extract-code` 会先把第 5 章可用的真实源码片段摘录到 `docs/materials/code_snippets/`，并生成白底黑字代码截图到 `docs/materials/code_screenshots/`
- `extract` 现在会先刷新 `code_evidence_pack.json`，再在 `material_pack.json` 中输出 `summary/evidence/assets`，其中 `assets` 包含图、表、附录索引、代码片段、代码截图和测试证据
- `literature` 会生成 `docs/writing/research/` 与 `research_index.json`
- `prepare-writing` / `prepare-chapter` 以后续 project profile 为准，动态区分健康档案、溯源类和通用区块链项目
- `start-chapter` 会在 `prepare-chapter` 基础上额外生成一个 `*.start.md` 的开写 brief，便于直接进入写章
- `prepare-writing` 会增量刷新 `chapter_queue.json`，保留已有章节状态、时间戳和统计信息，不再覆盖已存在的 packet/review 文件
- `prepare-outline` 会先锁定论文目录和大纲，`normalize-citations` 会在写章后把全文引用按首次出现顺序重排
- `project_profile.json` 与 chapter packet 会声明每章必需图表/附录资产与占位策略，避免章节退化成纯叙述稿
- 第 5 章 `prepare-chapter` 会强制消费工作区中的 `code_evidence_pack`，要求按模块输出后端实现、前端实现和真实代码截图
- `prepare-figures` 会生成项目专属配图并同步更新 `workspace.json.figure_map`，发布脚本会在构建前自动调用该步骤
- `prepare-figures` 会在 `word_output/figure_prepare_summary.json` 中记录本次图生成/缓存命中状态
- `prepare-figures` 支持通过 `er_figure_specs` 按图号显式启用 `dbdia-er`，用于把指定 E-R 图从本地 `.dbdia` 源稳定生成到 PNG；该配置是输入，`figure_map` 只是输出登记
- 启用 `dbdia-er` 后，工作流会在 `docs/images/generated_src/` 写出 `.dbdia/.dot/.svg` 侧车文件；运行时依赖 bundle 内 vendored `dbdia + Graphviz WASM`，首次恢复需要 `java/javac` 与 `node/npm`
- `prepare-ai-figures` 会把 `ai_figure_specs` 中声明的 AI 插图生成到本地 PNG，写入 `docs/images/generated_ai/`，并同步更新 `workspace.json.figure_map`
- `prepare-reference-guides` 会把 `reference_guide_specs` 中声明的教程图/参考图/说明文档先抽成 `docs/images/reference_guides/*.json|*.md`
- 对 `use_case`、`architecture`、`flowchart`、`function_structure` 这类 AI 技术图，推荐先把说明文档和已验收样图冻结到 `docs/images/reference_guides_src/`，再执行 `prepare-reference-guides`
- `prepare-ai-figures` 当前默认走 `zetatechs-gemini` provider，并以 `gemini-3.1-flash-image-preview` 作为默认模型；如需继续走 OpenAI Image 兼容链，可把 `image_generation.provider` 改为 `zetatechs` 或 `zetatechs-openai-image`
- `ai_figure_specs` 建议为每张图补齐 `diagram_type`、`style_notes` 与 `reference_guides`，把“图法规范”和“项目特化约束”拆开
- `er` 图通常不纳入这轮 guide 驱动优化，继续优先走 `er_figure_specs + dbdia-er` 的确定性链路
- `prepare-ai-figures` 生成的 PNG 不应内嵌图题、图号、章节标题、页眉页脚或 `Fig.` / `Figure`；这些题注应由论文正文与 DOCX 排版层统一插入
- `prepare-ai-figures` 默认不在 `release-build` / `release-verify` 中自动联网执行；若某个内置图号被 AI 覆盖，则发布前检查会要求先显式准备对应 PNG
- 若图号声明了 `reference_guides`，但 guide JSON 不存在或已过期，应先重新执行 `prepare-reference-guides`
- `release-verify` / `verify` 当前除引用锚点外，还会校验 DOCX 是否保留真实目录域、页脚页码域、`w:updateFields`、代码截图单倍行距媒体段落，以及正文中声明的图题是否实际进入最终 DOCX
- 若单张 AI 图因额度不足或结果质量问题不再适合走联网生图，可把该图号的 `ai_figure_specs.<fig>.enabled` 设为 `false`，再执行 `prepare-figures` 恢复该图号的确定性生成资源
- `postprocess --config <workspace.json>` 会自动解析基础排版稿输入、Windows 终稿输出和终稿图页码日志输出
- `postprocess --config <workspace.json>` 现在会读取 `document_format`，并在 WSL 环境下自动桥接宿主 Windows PowerShell / Word 做终排；若正文引用上标审计失败，命令会直接返回非零退出码
- `document_format.profile` 用于控制基础排版稿的页边距、行距、标题、题注、页眉页脚与图表编号风格；当前内置 `legacy` 与 `cuit-undergrad-zh`
- `document_format.code_blocks` 用于控制 fenced code block 的 DOCX 导出方式，当前支持 `render_mode=image|text` 与 `text_style=plain-paper|mono-block`
- `write-build-summary` 会把 preflight、figure cache 和基础排版稿 DOCX 信息落到 `word_output/build_summary.json`
- `write-release-summary` 会把 preflight、figure cache、DOCX 时间戳和引用校验结果落到 `word_output/release_summary.json`
- `write-finalization-summary` 会把 Word 终排后的 base/final DOCX、终稿图页码日志，以及基础稿/终稿正文引用上标比对结果落到 `final/final_summary.json`
- `version` 会输出当前 bundle 的 semver 版本、建议使用的 semver tag、该 tag 是否已存在、当前 commit、dirty 状态和最近 semver tag，便于做正式发版
- `selftest` 会先跑 bundle 内 fixture 冷启动回归，并在可选的真实 workspace 上执行 Linux 发布回归；结果汇总到 `selftest_summary.json`
- `refresh-handoff` 会把当前 workspace 的章节状态、发布状态、阻塞项和下一步命令收敛到 `docs/workflow/handoff.json` / `handoff.md`
- `resume` 会基于 active workspace 指针和 handoff 输出新的 AI 对话应当读取的最小文件集，而不是假定之前的聊天上下文仍然有效
- `sync-workflow-assets` 会把 workspace 本地 `workflow/*.md`、`workflow/references/command-map.md` 和 `workflow/skills/*` 同步到当前 bundle 版本，并把 bundle 签名落到 `docs/workflow/workflow_assets_state.json`
- `refresh-handoff` 不会替代 `sync-workflow-assets` 把 drifted 状态改回 current；只有完成本地资产同步后，`workflow_signature_status` 才会恢复为 `current`
- `lock-status` / `clear-lock` 用于管理 `docs/workflow/workspace.lock.json`，防止多个 AI 会话并发改写同一工作区
- `thesis-workflow-orchestrator` 是新的总控技能入口，用于固定 `resume -> handoff -> chapter_briefs -> polish/research` 的执行顺序
- 若 bundle 侧核心工具有变更，先修改 `workflow_bundle/tools/core/`，再执行 `bash workflow_bundle/workflow/scripts/sync_root_compat.sh` 回刷 root `tools/core/` 兼容镜像
- root `tools/*.py` 兼容 launcher 与 `workflow/scripts/*.sh` wrapper 也由同一个同步命令自动重建
