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
- `postprocess` 段用于声明 Windows Word 终排输出位置，默认会写到 `final/`，不与 `word_output/` 中的基础排版稿混放。
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
- `python3 workflow_bundle/tools/cli.py lock-status --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py clear-lock --config <workspace.json> --force`
