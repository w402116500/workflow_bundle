# Workflow Optimization Log

本文件只记录面向公共 `workflow_bundle` 仓库的通用工作流变更。
与某个具体 workspace、某台机器或某篇论文强绑定的执行日记，不再保存在这里，而应保留在对应 workspace 的文档目录或独立 companion 仓库中。

## 记录规则

- 只写 bundle 层的正式入口、配置接口、文档约束和回归链变化。
- 不写绝对机器路径、私人目录名或具体论文项目名。
- 每次修改尽量记录：目的、影响面、验证结果。

## 2026-04-17

- Purpose: 清理远端仓库中的项目残留，使公开仓库保持“通用论文工作流 bundle”定位，而不是某个具体项目的运行快照。
- Changes:
  - 清理 `README.md`、`workflow/README.md`、`workflow/07-current-project-execution-checklist.md`、`workflow/08-dual-platform-release.md`、`workflow/09-testing-and-regression.md` 中的项目化路径与措辞。
  - 将 `workflow/configs/current_project_manifest.json` 与 `workflow/configs/current_workspace.json` 收口为官方示例实例，不再使用真实项目快照。
  - 把 `docs/current_workflow_status_audit_2026-03-31.md` 改为历史说明文件，并新增 `docs/archive/README.md` 作为归档策略入口。
  - 修复 `tools/core/extract.py` 中的项目硬编码输出文案，改为按当前技术栈生成中性环境描述。
- Validation:
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`
  - `rg` 复查公开文档与代码中的项目残留关键词

## 2026-04-17 (versioning)

- Purpose: 为 bundle 建立正式版本号治理，避免只有零散 tag 和提交记录、却无法明确回答“当前是什么版本”。
- Changes:
  - 新增 `VERSION` 与 `CHANGELOG.md`。
  - 新增 `tools/core/bundle_version.py`，把版本号、tag、commit、dirty 状态收口成统一读取入口。
  - 为 CLI 增加 `version` 子命令与 `--version`。
  - 将 bundle version 写入 handoff、build/release/final/selftest summary。
  - 新增 `workflow/11-versioning-and-release.md`，明确 semver、tag 和发版流程。
- Validation:
  - `python3 tools/cli.py version`
  - `python3 tools/cli.py version --json`
  - `python3 tools/cli.py --version`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`

## 2026-04-18 (pre-release audit)

- Purpose: 在 `v0.5.0-rc1` 推送前做最后一轮公开仓库一致性复核，修正文档中的旧版本口径，并把未发布提交的作者身份收口到仓库正式身份。
- Changes:
  - 修正 `workflow/11-versioning-and-release.md` 中仍残留的 `0.5.0-dev` 表述，统一为当前预发布版本 `0.5.0-rc1`。
  - 复核公开文档中的版本、tag 与项目化残留口径，确认当前 bundle 对外说明以 `VERSION` 和 semver 为准。
  - 将当前仓库本地 Git 身份与未发布提交作者统一为 `Geek_L <402116500@qq.com>`。
- Validation:
  - `rg` 定向扫描 `0.5.0-dev`、`0.5.0-rc1`、semver 与项目残留关键词
  - `python3 tools/cli.py version`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`

## 2026-04-18 (release notes)

- Purpose: 为 `v0.5.0-rc1` 补齐可对外引用的发布说明，并给后续 semver 版本建立固定的 release note 归档位置。
- Changes:
  - 新增 `docs/releases/README.md`，明确 release note 的目录用途、命名规则和使用边界。
  - 新增 `docs/releases/v0.5.0-rc1.md`，归档首个 semver 预发布版本的中文 release note。
  - 更新 `BUNDLE_MANIFEST.md`，把 `docs/releases/` 纳入公共 bundle 文档清单。
- Validation:
  - `git diff --check`
  - `python3 tools/cli.py selftest`

## 2026-04-18 (v0.5.0 release)

- Purpose: 将 `v0.5.0-rc1` 收口为 `workflow_bundle` 首个正式 semver 版本，并统一仓库中的正式版版本口径。
- Changes:
  - 将根目录 `VERSION`、`CHANGELOG.md` 与 `workflow/11-versioning-and-release.md` 的当前版本说明统一更新为 `0.5.0`。
  - 新增 `docs/releases/v0.5.0.md`，归档正式版 release note，并在 `docs/releases/README.md` 中登记。
  - 保留 `v0.5.0-rc1` 作为预发布历史说明与 tag，不覆盖、不移动。
- Validation:
  - `python3 tools/cli.py version`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`
  - `git diff --check`

## 2026-04-18 (v0.5.1 release)

- Purpose: 以补丁版本修复 `latest_semver_tag` 在混合 tag 仓库中的误判问题，避免回改已发布的 `v0.5.0` 正式 tag。
- Changes:
  - 修复 `tools/core/bundle_version.py`，改为先过滤 semver tag 再按语义化版本规则选择最新 tag。
  - 将当前正式版本提升为 `0.5.1`，并新增 `docs/releases/v0.5.1.md` 记录补丁版 release note。
  - 保留 `v0.5.0` 与 `v0.5.0-rc1` 作为已发布历史版本，不重写既有 tag。
- Validation:
  - `python3 tools/cli.py version`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`
  - `git diff --check`

## 2026-04-18 (v0.5.1 github release copy)

- Purpose: 为 `v0.5.1` 补充可直接粘贴到 GitHub Release 页面的简版发布文案，避免每次手工从仓库 release note 再二次整理。
- Changes:
  - 在 `docs/releases/v0.5.1.md` 中新增 “GitHub Release 页面文案” 区块，提供可直接复制的 Markdown 内容。
  - 保留原有仓库内 release note 结构，不替代详细版发布说明。
- Validation:
  - `git diff --check`

## 2026-04-18 (generic er fallback hardening)

- Purpose: 修复通用 `dbdia-er` E-R fallback 在多外键场景下生成重复关系名而导致干净 `release-build` 失败的问题，并补齐对应回归覆盖。
- Changes:
  - 更新 `tools/core/figure_assets.py`，将通用 E-R fallback 的关系命名从固定 `关联` 改为基于 `target/current table` 的稳定唯一标识，避免 `dbdia` 在多关系模型中报 `can not be defined again`。
  - 更新 `tools/core/selftest.py`，新增“多关系通用 E-R DSL 唯一性”断言，防止后续修改再次产出重复关系名。
  - 运行 `bash workflow/scripts/sync_root_compat.sh`，同步根目录兼容镜像，确保 bundle 自测与 release-preflight 不会因为镜像漂移误报失败。
- Validation:
  - `python3 -m py_compile tools/core/figure_assets.py tools/core/selftest.py`
  - `bash workflow/scripts/sync_root_compat.sh`
  - `python3 tools/cli.py selftest`
  - `python3 tools/cli.py release-build --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --output-name selftest_release.docx`
  - `python3 tools/cli.py release-verify --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --output-name selftest_release.docx`

## 2026-04-18 (v0.5.2 release)

- Purpose: 以补丁版本正式发布通用 `dbdia-er` E-R fallback 稳定性修复，确保远端 `main`、`VERSION`、release note 和 semver tag 口径一致。
- Changes:
  - 将当前正式版本提升为 `0.5.2`，并更新 `CHANGELOG.md` 与 `workflow/11-versioning-and-release.md` 中的当前版本说明。
  - 新增 `docs/releases/v0.5.2.md`，记录本次补丁版发布说明与 GitHub Release 页面文案。
  - 更新 `docs/releases/README.md`，将 `v0.5.2` 纳入正式 release 归档清单。
- Validation:
  - `python3 tools/cli.py version`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`
  - `git diff --check`

## 2026-04-18 (chapter-3 plantuml workflow integration)

- Purpose: 将 PlantUML 纳入正式可重复生成链路，并修复当前环境默认 Java 8 无法直接运行 vendored PlantUML 的问题。
- Changes:
  - 扩展 `tools/core/figure_assets.py`，新增 `plantuml_figure_specs` 输入面、`plantuml` renderer、`.puml/.svg` 侧车产物写出，以及 Java 11+ 运行时自动选择逻辑。
  - 为 `dbdia-er` / `plantuml` 补充侧车存在性判定，避免输出 PNG 命中缓存时遗漏 `generated_src/` 中的源码与 SVG 侧车。
  - 扩展 `tools/core/selftest.py`，新增 PlantUML fixture 回归，验证 `prepare-figures` 能正确渲染 PNG、登记 `figure_map.renderer=plantuml` 并写出 `.puml/.svg`。
  - 更新 `workflow/README.md`、`workflow/WORKSPACE_SPEC.md`、`workflow/templates/workspace-config.template.json`、`workflow/configs/current_workspace.json` 与 `vendor/README.md`，把 PlantUML 明确纳入正式 figure workflow contract。
- Validation:
  - `python3 -m py_compile tools/core/figure_assets.py tools/core/selftest.py`
  - `bash workflow/scripts/sync_root_compat.sh`
  - `python3 tools/cli.py selftest`

## 2026-04-18 (traditional UML use-case AI workflow template)

- Purpose: 将传统 UML 用例图从不符合论文规范的临时位图/演示路径迁移为“参考图 + 提示词约束”的 AI 可重复生成链路，并把该做法沉淀为通用 workflow 模板。
- Changes:
  - 复核一组本地 UML 教程材料并抽取共性规范，明确传统 UML 用例图必须满足：
    - 参与者使用小人 `Actor`
    - 用例使用椭圆
    - 系统边界使用带系统名的矩形框
    - 参与者位于边界外，用例位于边界内
    - 默认只保留普通关联线，不使用 `include` / `extend` / 泛化
  - 更新 `workflow/06-ai-prompt-guide.md`，新增 `4.8.1 传统 UML 用例图 AI 模板`，明确：
    - `diagram_type` 使用 `use_case`
    - 使用本地教程参考图作为 `reference_images`
    - 用 `prompt_override` 明确禁止角色矩形框、流程图箭头、彩色教程风格与额外说明框
    - 如果正文 Markdown 已显式写死图片路径，需要同步改到 AI 输出路径
  - 在工作区示例中验证 `ai_figure_specs` 能输出黑白论文风格的传统 UML 用例图。
  - 验证当某图号转由 AI 接管时，可通过关闭对应 `plantuml_figure_specs` 项避免 `prepare-figures` 再次覆盖。
- Validation:
  - `python3 tools/cli.py sync-workflow-assets --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-ai-figures --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --fig 3.2 --dry-run`
  - `python3 tools/cli.py prepare-ai-figures --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --fig 3.2`
  - `python3 tools/cli.py prepare-figures --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json`
  - `python3 tools/cli.py release-preflight --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json`
  - `python3 tools/cli.py release-build --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --output-name thesis-workspace_ai-usecase-check.docx`
  - `python3 tools/cli.py release-verify --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --output-name thesis-workspace_ai-usecase-check.docx`
  - 已确认 `figure_map.3.2.renderer = ai-image`，并确认 `word_output/figure_insert_log.csv` 将 `图3-2` 插入自 `docs/images/generated_ai/fig3-2-ai.png`。

## 2026-04-18 (use-case straight-line constraint refinement)

- Purpose: 将“用例图关联线不得拐弯”沉淀为传统 UML 用例图 AI 模板的硬约束，避免 AI 在论文图中生成折线或回折连接。
- Changes:
  - 更新 `workflow/06-ai-prompt-guide.md` 的传统 UML 用例图模板，新增“所有关联线必须为单段直线，禁止折线、回折线、曲线”的明确要求。
  - 同步收紧工作区 `ai_figure_specs.3.2` 的 `style_notes` 与 `prompt_override`，强制：
    - 参与者到用例只能是一条单段直线
    - 可轻微打破绝对均匀网格，但不能为了对称而生成折线
    - 多参与者与多用例示例按同高关系布局，降低 AI 生成折线的概率
- Validation:
  - `python3 tools/cli.py prepare-ai-figures --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --fig 3.2`
  - `python3 tools/cli.py release-build --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --output-name thesis-workspace_ai-usecase-straight.docx`
  - `python3 tools/cli.py release-verify --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --output-name thesis-workspace_ai-usecase-straight.docx`

## 2026-04-18 (reference guide extraction workflow)

- Purpose: 把“直接把参考图喂给生图模型”的弱约束链路升级为“先抽取参考图规范 guide，再由 AI 生图消费 guide”的两阶段正式 workflow。
- Changes:
  - 新增 `tools/core/reference_guides.py`，实现：
    - `reference_extraction` 配置解析
    - `reference_guide_specs` 规范抽取
    - `prepare-reference-guides` 产物写出到 `docs/images/reference_guides/*.json|*.md`
    - guide 缓存与 `spec_hash` 校验
    - guide 缺失/过期时的阻断校验
  - 扩展 `tools/cli.py`，新增正式入口：
    - `python3 workflow_bundle/tools/cli.py prepare-reference-guides --config <workspace.json> [--guide <guide-name>] [--force] [--dry-run]`
  - 扩展 `tools/core/ai_image_generation.py`：
    - `ai_figure_specs.<fig>.reference_guides`
    - 生图 prompt 可消费 guide JSON 摘要
    - prompt manifest 记录 `reference_guides`
    - 当 guide JSON 缺失或相对当前 spec 已过期时，`prepare-ai-figures` / `release-preflight` 直接失败
  - 扩展 `tools/core/project_common.py`、`workflow/templates/workspace-config.template.json`、`workflow/configs/current_workspace.json` 与 `workflow/WORKSPACE_SPEC.md`，把 `reference_extraction` / `reference_guide_specs` 固化为正式 workspace contract。
  - 更新 `workflow/README.md`、`workflow/references/command-map.md`、`tools/README.md` 与 `workflow/06-ai-prompt-guide.md`，明确“guide 为主、reference_images 为辅”的推荐用法。
  - 扩展 `tools/core/selftest.py`，新增三类 fixture 回归：
    - `prepare-reference-guides --dry-run` 产物登记
    - `prepare-ai-figures` 在 guide 缺失时直接失败
    - `prepare-ai-figures` 在 guide 存在时把 `reference_guides` 正确写入 prompt manifest
- Validation:
  - `python3 -m py_compile tools/core/reference_guides.py tools/core/ai_image_generation.py tools/core/selftest.py tools/cli.py tools/core/project_common.py`
  - `bash workflow/scripts/sync_root_compat.sh`
  - `python3 tools/cli.py selftest`
  - `python3 tools/cli.py prepare-reference-guides --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --guide uml_use_case_traditional_zh --dry-run`
  - `python3 tools/cli.py prepare-reference-guides --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --guide uml_use_case_traditional_zh`
  - `python3 tools/cli.py prepare-ai-figures --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --fig 3.2 --dry-run`
  - `python3 tools/cli.py sync-workflow-assets --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json`
  - `python3 tools/cli.py release-preflight --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json`

## 2026-04-18 (non-er reference-guide rollout)

- Purpose: 将 `reference_guides` 的正式用法从单一用例图扩展到非 ER 技术图全族，统一收口架构图、流程图、功能结构图的“冻结样图 -> 抽 guide -> AI 生图”链路，同时明确 `ER` 图继续保留 `dbdia-er` 确定性渲染路径。
- Changes:
  - 更新 `tools/core/reference_guides.py`：
    - 新增 `guide_type=function_structure` 的抽取重点提示
    - 收紧 `architecture` / `flowchart` 抽取提示
    - 明确“已验收样图只用于提炼图法，不把业务标签当通用规范”
  - 更新 `tools/core/selftest.py`，新增 `function_structure` guide 的 `prepare-reference-guides --dry-run` 回归。
  - 更新 `workflow/WORKSPACE_SPEC.md`、`workflow/README.md`、`tools/README.md`、`workflow/references/command-map.md` 与 `workflow/06-ai-prompt-guide.md`：
    - 推荐非 ER AI 技术图优先启用 `reference_guides`
    - 推荐先把 guide source 冻结到 `docs/images/reference_guides_src/`
    - 明确 `ER` 图通常继续走 `er_figure_specs + dbdia-er`
    - 新增传统分层架构图、传统流程图、传统系统功能结构图模板
  - 更新 `workflow/configs/current_workspace.json` 与 `workflow/templates/workspace-config.template.json`，新增稳定 guide source 的官方示例写法。
- Validation:
  - `python3 -m py_compile tools/core/reference_guides.py tools/core/selftest.py tools/cli.py`
  - `python3 tools/cli.py prepare-reference-guides --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --dry-run`
  - `python3 tools/cli.py prepare-reference-guides --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --force`
  - `python3 tools/cli.py prepare-ai-figures --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --fig 3.2 --fig 4.1 --fig 4.3 --fig 4.4 --fig 4.5 --fig 5.1 --dry-run`
  - `python3 tools/cli.py prepare-ai-figures --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --fig 5.1 --force`
  - `python3 tools/cli.py prepare-ai-figures --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --fig 3.2 --fig 4.1 --fig 4.3 --fig 4.4 --fig 4.5 --fig 5.1`
  - `bash workflow/scripts/sync_root_compat.sh`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py sync-workflow-assets --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json`
  - `python3 tools/cli.py release-preflight --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json`
  - `python3 tools/cli.py selftest`
  - `git diff --check`

## 2026-04-18 (workspace mutation hard isolation)

- Purpose: 把“新项目不要把配置和运行时状态混回公共 bundle”从约定升级为正式 CLI 硬约束，避免用户继续在 `current_workspace.json` 或 bundle 内 workspace 上执行变更型命令。
- Changes:
  - 更新 `tools/core/runtime_state.py`，新增 `workspace_mutation_safety` / `ensure_workspace_mutation_allowed`，并将以下条件统一判定为 blocked：
    - 配置文件为 `workflow/configs/current_workspace.json`
    - manifest 为 `workflow/configs/current_project_manifest.json`
    - `workspace_root` 仍落在 `workflow_bundle/` 仓库内
  - 将 `set-active-workspace`、`refresh-handoff`、`clear-lock` 以及所有走 workspace lock 的变更型命令接入统一阻断逻辑。
  - 更新 `tools/core/workspace_checks.py` 与 `tools/core/runtime_state.py` 的 handoff/resume 输出，显式暴露：
    - `workspace_mutation_safety`
    - `workspace_mutation_reason_codes`
    - 下一步应先执行 `intake` 创建独立 workspace
  - 更新 `tools/core/selftest.py`，新增 bundle 示例配置只读回归：
    - `resume` 可读但显示 blocked
    - `set-active-workspace` / `extract` 被直接拒绝
    - `check-workspace` 会把 mutation blocking 作为阻塞项输出
  - 更新 `workflow/README.md`、`workflow/MIGRATION.md`、`workflow/WORKSPACE_SPEC.md`、`workflow/references/command-map.md` 与 `workflow/07-current-project-execution-checklist.md`，把示例配置只读化与 in-repo workspace 阻断写入正式文档。
  - 更新 `.gitignore`，忽略 bundle 根目录 `docs/workflow/` 运行时状态产物，避免 handoff/execution log 被误纳入公开仓库。
- Validation:
  - `python3 -m py_compile tools/core/runtime_state.py tools/core/workspace_checks.py tools/cli.py tools/core/selftest.py`
  - `git diff --check`
  - `python3 tools/cli.py resume --config workflow/configs/current_workspace.json`
  - `python3 tools/cli.py set-active-workspace --config workflow/configs/current_workspace.json`
  - `python3 tools/cli.py extract --config workflow/configs/current_workspace.json`
  - `python3 tools/cli.py check-workspace --config workflow/configs/current_workspace.json`
  - `bash workflow/scripts/sync_root_compat.sh`
  - `python3 tools/cli.py selftest`

## 2026-04-18 (version tag-existence clarification)

- Purpose: 修正 `version` 命令把“根据 `VERSION` 推导出的目标 tag”与“Git 仓库里真实存在的 tag”混为一谈的问题，避免发布前误判目标 semver tag 已存在，并同步修正文档中的旧版本口径。
- Changes:
  - 更新 `tools/core/bundle_version.py`，把版本读取结果拆分为：
    - `suggested_tag`
    - `tag_exists`
    - `tag_commit`
  - 更新 `tools/cli.py` 的 `version` 输出与 JSON 结构，使 CLI 能明确区分“建议发布的 tag”与“已存在的 tag”。
  - 更新 `tools/README.md`、`workflow/11-versioning-and-release.md`、`workflow/README.md`，把版本检查步骤改为先看 `suggested_tag`，再看 `tag_exists`。
  - 更新 `CHANGELOG.md` 与 release note，把这次 tag 语义澄清纳入 `0.6.0` 的正式版本说明。
- Validation:
  - `python3 -m py_compile tools/core/bundle_version.py tools/cli.py`
  - `python3 tools/cli.py version`
  - `python3 tools/cli.py version --json`
  - `bash workflow/scripts/sync_root_compat.sh`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`

## 2026-04-18 (v0.6.0 public release scope cleanup)

- Purpose: 将本轮围绕 `reference_guides`、PlantUML 与版本治理的改动收口为公共 `v0.6.0` 发版，同时剥离当前论文工作区的项目化默认值，避免将实例特例固化进 bundle。
- Changes:
  - 回退 `tools/core/build_final_thesis_docx.py` 中 chapter 3 的项目化默认图题回退，恢复 bundle 公共默认值。
  - 回退 `tools/core/chapter_profile.py` 中基于特定角色集合触发双需求图合同的逻辑，避免把单一工作区的章节合同误写成通用规则。
  - 将本地尚未发布的 `0.5.3` 草稿版本重定级为 `0.6.0`，统一更新 `VERSION`、`CHANGELOG.md`、`docs/releases/README.md`、`workflow/11-versioning-and-release.md` 与正式 release note。
  - 保留并发布本轮真正通用的能力：
    - `prepare-reference-guides`
    - `reference_extraction`
    - `reference_guide_specs`
    - `ai_figure_specs.<fig>.reference_guides`
    - `plantuml_figure_specs`
- Validation:
  - `python3 tools/cli.py version --json`
  - `bash workflow/scripts/sync_root_compat.sh`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`
  - `git diff --check`
