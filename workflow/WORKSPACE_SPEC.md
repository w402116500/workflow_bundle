# Workspace Spec

## 1. 目标

标准工作区用于把“任意项目材料”转换成统一的论文写作输入。后续自动化抽取与论文生成都应以本规范为接口。

## 2. 核心接口

### 2.1 Workspace Config

`workspace config` 描述一个论文工作区的构建入口与正文输出设置，建议字段如下：

```json
{
  "workspace_name": "example",
  "workspace_root": "../..",
  "project_manifest": "workflow/configs/current_project_manifest.json",
  "materials": {
    "material_pack_json": "docs/materials/material_pack.json",
    "material_pack_md": "docs/materials/material_pack.md",
    "code_evidence_pack_json": "docs/materials/code_evidence_pack.json",
    "code_evidence_pack_md": "docs/materials/code_evidence_pack.md",
    "code_snippets_dir": "docs/materials/code_snippets",
    "code_screenshots_dir": "docs/materials/code_screenshots",
    "source_inventory_md": "docs/materials/source_inventory.md",
    "missing_items_md": "docs/materials/missing_items.md",
    "intake_report_md": "docs/materials/intake_report.md"
  },
  "tasks": {
    "literature_plan_md": "docs/tasks/literature_plan.md"
  },
  "workflow_state": {
    "handoff_json": "docs/workflow/handoff.json",
    "handoff_md": "docs/workflow/handoff.md",
    "execution_log_md": "docs/workflow/execution_log.md",
    "workspace_lock_json": "docs/workflow/workspace.lock.json"
  },
  "writing": {
    "project_profile_json": "docs/writing/project_profile.json",
    "project_profile_md": "docs/writing/project_profile.md",
    "thesis_outline_json": "docs/writing/thesis_outline.json",
    "thesis_outline_md": "docs/writing/thesis_outline.md",
    "literature_pack_json": "docs/writing/literature_pack.json",
    "literature_pack_md": "docs/writing/literature_pack.md",
    "reference_registry_json": "docs/writing/reference_registry.json",
    "citation_audit_md": "docs/writing/citation_audit.md",
    "research_dir": "docs/writing/research",
    "research_index_json": "docs/writing/research_index.json",
    "research_index_md": "docs/writing/research_index.md",
    "chapter_queue_json": "docs/writing/chapter_queue.json",
    "chapter_packets_dir": "docs/writing/chapter_packets",
    "chapter_briefs_dir": "docs/writing/chapter_briefs",
    "review_dir": "docs/writing/review",
    "local_skill_path": "workflow/skills/academic-paper-crafter/SKILL.md",
    "resume_skill_path": "workflow/skills/thesis-workflow-resume/SKILL.md",
    "orchestrator_skill_path": "workflow/skills/thesis-workflow-orchestrator/SKILL.md",
    "research_skill_path": "workflow/skills/paper-research-agent/SKILL.md",
    "paper_reader_skill_path": "workflow/skills/paper-reader/SKILL.md"
  },
  "scaffold": {
    "chapter_template_profile": "blockchain-fullstack"
  },
  "build": {
    "input_dir": "polished_v3",
    "diagram_dir": "docs/images",
    "output_dir": "word_output",
    "output_docx": "example.docx",
    "figure_log": "figure_insert_log.csv",
    "processed_image_dir": "processed_images",
    "reference_file": "REFERENCES.md",
    "abstract_cn_file": "00-摘要.md",
    "abstract_en_file": "00-Abstract.md",
    "chapter_order": []
  },
  "postprocess": {
    "final_dir": "final",
    "output_docx": "example_windows_final.docx",
    "figure_log": "figure_insert_log_final.csv"
  },
  "defaults": {
    "keywords_cn": "",
    "keywords_en": ""
  },
  "image_generation": {
    "enabled": false,
    "provider": "zetatechs-gemini",
    "base_url": "https://api.zetatechs.com",
    "api_key_env": "NEWAPI_API_KEY",
    "default_model": "gemini-3.1-flash-image-preview",
    "default_quality": "high",
    "default_size": "1536x1024",
    "response_format": "b64_json",
    "gemini_image_size": "1K",
    "gemini_response_modalities": ["IMAGE", "TEXT"],
    "timeout_sec": 300,
    "output_dir": "docs/images/generated_ai",
    "auto_generate_on_prepare_figures": false
  },
  "reference_extraction": {
    "enabled": false,
    "provider": "zetatechs-gemini",
    "base_url": "https://api.zetatechs.com",
    "api_key_env": "NEWAPI_API_KEY",
    "default_model": "gemini-3.1-flash-image-preview",
    "timeout_sec": 180,
    "output_dir": "docs/images/reference_guides"
  },
  "ai_figure_specs": {},
  "reference_guide_specs": {},
  "plantuml_figure_specs": {},
  "er_figure_specs": {},
  "figure_map": {},
  "metadata": {
    "project_root": "/abs/path/to/project",
    "title": "论文题目",
    "discipline": "计算机类",
    "chain_platform": "fisco"
  }
}
```

说明：

- 大章节框架固定，当前默认为摘要、绪论、技术介绍、需求分析、系统设计、系统实现、系统测试、结论与展望、致谢、参考文献。
- 小节结构不再写死在工具代码中，而是由 `docs/writing/project_profile.json` 按项目画像动态生成。
- `docs/materials/material_pack.json` 不只承载 `summary/evidence`，还承载结构化 `assets`，用于图表、结构化索引和测试证据抽取。
- `docs/materials/code_evidence_pack.json` / `code_evidence_pack.md` 是第 5 章的代码证据索引，配套真实代码片段与白底黑字代码截图目录。
- `image_generation` 用于声明 AI 生图提供方和默认模型参数；当前工作流默认走 `zetatechs-gemini` provider，通过 Gemini Generate Content 生图；仍兼容 `zetatechs` / `zetatechs-openai-image` 的 OpenAI Image 路径。API key 建议只通过环境变量传入，不写进 workspace config。
- `reference_extraction` 用于声明“参考图规范抽取”阶段的 provider、模型与产物输出目录。该阶段负责先把教程 Markdown / 样图抽成 guide JSON/Markdown，再供 `prepare-ai-figures` 消费。当前 v1 仅支持 `zetatechs-gemini`。
- `reference_guide_specs` 用于按 guide 名声明哪些教程材料要先抽取成通用图法规范。
  常用字段包括：
  - `guide_type`
  - `description`
  - `enabled`
  - `model`
  - `sources`
  - `extract_focus`
  `sources` 的元素支持：
  - `kind = markdown | image`
  - `path`
  - `role`
  - `note`
  guide 产物默认落到 `docs/images/reference_guides/`，每个 guide 会输出一份 `.json` 和一份 `.md`。
  如需让 guide 具备可重复生成性，建议先把参考图片和说明文档冻结到 workspace 内，例如 `docs/images/reference_guides_src/<diagram-family>/`，再从该目录抽取 guide；不要直接引用 `tmp_*` 临时目录或运行期 `docs/images/generated_ai/` 产物。
- `ai_figure_specs` 用于按图号声明哪些插图走 AI 生成，以及这些图的意图、章节归属和是否覆盖内置生成图。
  常用字段包括：
  - `caption`
  - `chapter`
  - `intent`
  - `diagram_type`
  - `style_notes`
  - `enabled`
  - `override_builtin`
  - `reference_guides`
  其中 `diagram_type` 推荐使用：
  - `use_case`
  - `function_structure`
  - `flowchart`
  - `sequence`
  - `er`
  - `architecture`
  `style_notes` 用于补充对参考图风格、布局方式、线框样式、图标使用边界等具体要求。
  `reference_guides` 用于声明当前图号要消费哪些已抽取好的 guide；如果声明了 guide 但 guide JSON 不存在或相对当前 guide spec 已过期，`prepare-ai-figures` 会直接失败。
  当前推荐优先对 `use_case`、`architecture`、`flowchart`、`function_structure` 这类 AI 技术图启用 `reference_guides`；`er` 图通常继续走 `er_figure_specs + dbdia-er` 的确定性链路。
  AI 图默认应只生成图主体本身，不在 PNG 内嵌图号、图题、章节名、页眉页脚或 `Fig.` / `Figure`。论文题注由正文和导出流程统一插入。
  `enabled=false` 可用于按图号关闭 AI 覆盖并回退到 `prepare-figures` 的确定性生成结果，适合额度不足、质量不稳或该图不适合 AI 生成的场景。
- `plantuml_figure_specs` 用于按图号显式声明哪些流程图、用例图或 UML 图走本地 `PlantUML`。该字段是**输入配置**，适合需要传统正式图法、且希望保留可重复生成源码的项目。
  常用字段包括：
  - `caption`
  - `source_path`
  - `enabled`
  - `override_builtin`（可选，默认 `true`，用于覆盖同图号内置图）
  - `output_name`（可选，默认 `generated/fig<图号>-plantuml.png`）
  `source_path` 指向 workspace 根目录相对路径下的 `.puml` 源文件；启用后 `prepare-figures` 会在 `docs/images/generated_src/` 额外写出 `.puml/.svg` 侧车文件。当前 renderer 会自动查找 Java 11+ 运行时，建议在 `.puml` 中显式声明 `!pragma layout smetana` 以获得更稳定的本地布局。
- `er_figure_specs` 用于按图号显式声明哪些 E-R 图走本地 `dbdia-er`。该字段是**输入配置**，适合需要传统 Chen 风格 E-R 图、且不想依赖 Mermaid `erDiagram` 自动提取的项目。
  常用字段包括：
  - `caption`
  - `source_path`
  - `enabled`
  - `output_name`（可选，默认 `generated/fig<图号>-er-diagram.png`）
  `source_path` 指向 workspace 根目录相对路径下的 `.dbdia` 源文件；启用后 `prepare-figures` 会在 `docs/images/generated_src/` 额外写出 `.dbdia/.dot/.svg` 侧车文件。
- `postprocess` 段用于声明 Windows Word 终排输出位置，默认会写到 `final/`，不与 `word_output/` 中的基础排版稿混放。
- `postprocess.windows_bridge` 用于声明 WSL -> Windows 终排桥接参数。默认通过 `powershell.exe + py` 调宿主 Windows PowerShell / Word；如宿主环境不同，可覆写 PowerShell 或 Python 启动器。
- `document_format` 段用于声明当前 workspace 的文档版式 profile。默认 `legacy` 保持原有输出风格；如需贴近学校模板，可切换到如 `cuit-undergrad-zh` 这类 profile，并允许按字段覆写页边距、标题、题注、页眉页脚、图表编号风格与代码块导出方式。
- `document_format.code_blocks` 用于控制 Markdown fenced code block 的 DOCX 导出策略。当前支持：
  - `render_mode = image | text`
  - `text_style = plain-paper | mono-block`
  `image` 保持旧行为，把代码块转成 PNG 再插入 DOCX；`text` 直接以文字代码块写入 DOCX，适合需要可复制源码的论文版本。
- `workflow_state` 段用于声明工作流状态文件位置，包括冷启动 handoff 和 workspace 执行日志。
- `workflow_state.workspace_lock_json` 用于串行化同一 workspace 的变更型命令，避免多会话并发改写。
- `project_profile.md` 是给执行者阅读的可视化版本，`project_profile.json` 是 `prepare-writing` 与 `prepare-chapter` 的结构输入。
- `project_profile.json` 会声明每章的 `required_assets / required_table_types / required_appendix_items / placeholder_policy`。
- `literature` 阶段除轻量 `literature_pack/reference_registry` 外，还会生成 `docs/writing/research/` 侧车调研包。
- `chapter_packets_dir` 是调试层写作包，保留完整规则命中、路径和诊断信息。
- `chapter_briefs_dir` 是写作层 brief，默认供写作者与润色技能直接消费，不暴露原始源码路径与调试字段。
- `docs/workflow/handoff.json` / `handoff.md` 是新的单一接手入口，用于新的 AI 对话快速恢复当前阶段、阻塞项和下一步。
- `docs/workflow/execution_log.md` 是 workspace 级执行日志，不与根目录流程优化日志混写。
- `writing.orchestrator_skill_path` 是新的总控技能入口，用于让新 AI 对话按固定顺序读取 `resume -> handoff -> chapter_briefs`，而不是依赖历史聊天记忆。

### 2.2 Project Manifest

`project manifest` 描述一个具体项目的输入材料位置，建议字段如下：

```json
{
  "project_id": "example",
  "title": "论文题目",
  "discipline": "计算机类",
  "project_type": "blockchain-fullstack",
  "project_root": "/abs/path/to/project",
  "chain_platform": "fisco",
  "detection_confidence": "high",
  "source_paths": {
    "frontend": "",
    "backend": "",
    "contracts": "",
    "chaincode": "",
    "database": ""
  },
  "document_paths": {
    "requirements": [],
    "design": [],
    "references": []
  },
  "detected_stack": {
    "frontend_framework": "vue",
    "backend_framework": "spring-boot",
    "database_kind": "mysql",
    "chain_sdk": "fisco-java-sdk"
  },
  "missing_inputs": []
}
```

## 3. 目录角色

推荐目录职责如下：

- `workflow/`：工作流文档、配置、兼容脚本
- `docs/`：规划与证据材料
- `polished_v3/`：正文真源
- `images/` / `docs/images/`：图表资产
- `tools/`：构建脚本
- `word_output/`：生成产物
- `docs/writing/project_profile.json`：当前项目的动态章节画像
- `docs/writing/research/`：PDF、analysis task、调研索引等文献侧车产物
- `docs/writing/chapter_packets/`：完整调试型章节 packet
- `docs/writing/chapter_briefs/`：面向写作者的精简章节 brief

## 4. 当前仓库的实例化

当前仓库不是纯框架仓库，而是“框架 + 示例实例”合并形态：

- 框架接口已在 `workflow/` 固化
- 当前健康档案项目作为内置示例实例保留在 `docs/`、`code/`、`polished_v3/`
- 当前官方流程入口已切换到 `workflow_bundle/`，根目录 `workflow/` 与 `tools/` 只保留兼容入口

后续接入新项目时，优先新增新的 `workspace config` 与 `project manifest`，不要直接把构建脚本再次写死到某一个项目路径。

## 5. 新阶段命令

项目接入与材料抽取的正式入口：

- `python3 workflow_bundle/tools/cli.py intake --project-root <path> --title <title> --out <workspace-dir>`
- `python3 workflow_bundle/tools/cli.py smoke-intake --project-root <fixture-path> --title <title> --out <workspace-dir>`
- `python3 workflow_bundle/tools/cli.py extract-code --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py extract --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py scaffold --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py literature --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py prepare-writing --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py prepare-chapter --config <workspace.json> --chapter <chapter-file>`
- `python3 workflow_bundle/tools/cli.py start-chapter --config <workspace.json> --chapter <chapter-file>`
- `python3 workflow_bundle/tools/cli.py finalize-chapter --config <workspace.json> --chapter <chapter-file>`
- `python3 workflow_bundle/tools/cli.py prepare-reference-guides --config <workspace.json> [--guide <guide-name>]`
- `python3 workflow_bundle/tools/cli.py prepare-ai-figures --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py lock-status --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py clear-lock --config <workspace.json> --force`
