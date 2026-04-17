# Workflow Bundle Manifest

## Included

- `VERSION`
- `CHANGELOG.md`
- `workflow/README.md`
- `workflow/THESIS_WORKFLOW.md`
- `workflow/CHAPTER_EXECUTION.md`
- `workflow/WORKSPACE_SPEC.md`
- `workflow/05-draft-polished-alignment.md`
- `workflow/07-current-project-execution-checklist.md`
- `workflow/08-dual-platform-release.md`
- `workflow/09-testing-and-regression.md`
- `workflow/11-versioning-and-release.md`
- `workflow/MIGRATION.md`
- `workflow/configs/`
- `workflow/references/`
- `workflow/scripts/`
- `workflow/templates/`
- `workflow/skills/academic-paper-crafter/`
- `workflow/skills/thesis-workflow-resume/`
- `workflow/skills/thesis-workflow-orchestrator/`
- `workflow/skills/paper-research-agent/`
- `workflow/skills/paper-reader/`
- `workflow/fixtures/fabric_trace_demo/`
- `tools/cli.py`
- `tools/core/`
- `tools/windows/`
- `tools/README.md`
- `tools/build_final_thesis_docx.py`
- `tools/verify_citation_links.py`
- `tools/postprocess_word_format.py`
- `tools/core/bundle_version.py`
- `paper-research-agent/`
- `paper-reader/`
- `docs/current_workflow_status_audit_2026-03-31.md`
- `docs/archive/README.md`
- `docs/releases/`
- `docs/workflow_optimization_log.md`

## Excluded

- `tools/node_modules/`
- `tools/unpacked_*`
- `tools/examples/health_record/`
- `word_output/`
- `final/`
- `docs/materials/`
- `docs/writing/`
- `polished_v3/`
- `workspaces/`

## Rationale

- `workflow/` 与 `tools/` 是正式流程入口。
- `VERSION` 与 `CHANGELOG.md` 用于提供正式版本号与变更追踪入口。
- `docs/releases/` 用于归档对外发布说明，补充 `CHANGELOG.md` 的结构化变更摘要。
- `workflow/skills/` 是 workspace 配置和写章流程的直接依赖。
- `workflow/fixtures/fabric_trace_demo/` 被保留，是为了提供 bundle 内自包含的 smoke intake 验证入口。
- 根目录 `paper-research-agent/` 与 `paper-reader/` 被保留，是为了兼容当前 `intake` 工具的技能复制源路径。
- 工作区正文、材料包和生成产物不复制进 bundle，避免把“流程入口”和“具体项目实例”再次混在一起。
