# Chapter Execution

本文件定义正文逐章执行协议。当前阶段不提供一键 `write-chapter`，而是要求执行者按 packet 与本地 skill 逐章完成写作与润色。

## 固定流程

1. `python3 workflow_bundle/tools/cli.py intake --project-root <path> --title <title> --out <workspace-dir>`
2. `python3 workflow_bundle/tools/cli.py extract-code --config <workspace-dir>/workflow/configs/workspace.json`
3. `python3 workflow_bundle/tools/cli.py extract --config <workspace-dir>/workflow/configs/workspace.json`
4. `python3 workflow_bundle/tools/cli.py scaffold --config <workspace-dir>/workflow/configs/workspace.json`
   - 生成固定大章节 + 动态小节结构的 `project_profile`
   - 只初始化缺失或空白的 `polished_v3` 章节骨架，不覆盖已有正文
5. `python3 workflow_bundle/tools/cli.py literature --config <workspace-dir>/workflow/configs/workspace.json`
   - 同时生成 `literature_pack/reference_registry` 与 `research` 侧车调研包
6. `python3 workflow_bundle/tools/cli.py prepare-outline --config <workspace-dir>/workflow/configs/workspace.json`
   - 生成 `docs/writing/thesis_outline.json` 与 `docs/writing/thesis_outline.md`
   - 目录会展开到章节、小节、子小节层级，写章前先人工确认论文大纲和目录
7. `python3 workflow_bundle/tools/cli.py prepare-writing --config <workspace-dir>/workflow/configs/workspace.json`
8. 对单章循环执行：
   - 若 `resume` 或 `handoff` 显示 `workflow_signature_status: drifted`，先执行 `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`，再继续读取本地 skill 与 brief
   - `python3 workflow_bundle/tools/cli.py start-chapter --config <workspace.json> --chapter <chapter-file>`
   - 或 `python3 workflow_bundle/tools/cli.py prepare-chapter --config <workspace.json> --chapter <chapter-file>`
   - 如需确认并发占用，先执行 `python3 workflow_bundle/tools/cli.py lock-status --config <workspace.json>`
   - 默认先阅读 `docs/writing/chapter_briefs/<chapter>.md`
   - `docs/writing/chapter_packets/<chapter>.md` 仅在需要排查证据命中、路径来源或规则诊断时回看
   - 先核对 `docs/writing/thesis_outline.md`
   - 对新的 AI 对话，先阅读 `workflow/skills/thesis-workflow-orchestrator/SKILL.md`
   - 必须检查 packet 中的 `outline_sync.status`；若不是 `current`，先重新执行 `prepare-chapter`
   - 读取 chapter brief、本地 skill、material pack、literature pack、reference registry
   - 完成 raw draft 并写回 `polished_v3/<chapter>.md`
   - `python3 workflow_bundle/tools/cli.py finalize-chapter --config <workspace.json> --chapter <chapter-file> --status drafted`
   - 依据本地 `academic-paper-crafter` 规则做 polish，并覆盖写回同一文件
    - `python3 workflow_bundle/tools/cli.py finalize-chapter --config <workspace.json> --chapter <chapter-file> --status polished`
      - 同步刷新 `citation_audit.md`，自动按首次出现顺序重排全文引用编号，并检查重复引用与单句多引用
   - 人工确认通过后：
     - `python3 workflow_bundle/tools/cli.py finalize-chapter --config <workspace.json> --chapter <chapter-file> --status reviewed`
9. 全文章节完成后执行：
   - `python3 workflow_bundle/tools/cli.py prepare-figures --config <workspace-dir>/workflow/configs/workspace.json`
   - 生成第 4/5 章所需结构图、流程图和功能结构图
10. 再进入发布：
   - `python3 workflow_bundle/tools/cli.py release-build --config <workspace-dir>/workflow/configs/workspace.json`
   - `bash workflow_bundle/workflow/scripts/postprocess_release.sh <workspace-dir>/workflow/configs/workspace.json`
   - `python3 workflow_bundle/tools/cli.py release-verify --config <workspace-dir>/workflow/configs/workspace.json`
   - 如需兼容旧脚本，`build_release.sh` 与 `verify_release.sh` 仍可使用，但它们只是 CLI 发布链的薄封装
   - Windows `postprocess_release.sh` 会把终稿写到 `final/`，并生成 `final_summary.json`
11. 如果本轮修改的是 workflow 工具、workflow 技能或 workflow 文档，而不是正文章节：
   - `python3 workflow_bundle/tools/cli.py selftest`
   - 如需同时覆盖真实工作区发布链：`python3 workflow_bundle/tools/cli.py selftest --workspace-config <workspace-dir>/workflow/configs/workspace.json>`

## 推荐章节顺序

1. `02-系统开发工具及技术介绍.md`
2. `03-需求分析.md`
3. `04-系统设计.md`
4. `05-系统实现.md`
5. `06-系统测试.md`
6. `01-绪论.md`
7. `07-结论与展望.md`
8. `00-摘要.md`
9. `00-Abstract.md`

## 状态机

自动章节：

- `pending -> prepared -> drafted -> polished -> reviewed`

手工章节：

- `manual_pending -> reviewed`

特殊章节：

- `REFERENCES.md` 为 `managed`

规则：

- `prepare-chapter` 只负责把自动章节从 `pending` 推到 `prepared`
- `start-chapter` 是 `prepare-chapter` 的便利封装，会额外生成一个 `*.start.md` 的开写 brief
- `prepare-chapter` 生成的 packet 必须携带 `outline_snapshot` 与 `outline_sync`
- `prepare-chapter` 除 debug packet 外，还必须生成面向写作者的 `writer brief`
- 若 `outline_sync.status` 为 `stale` / `legacy` / `missing`，说明当前写作包不可继续直接使用
- `finalize-chapter --status drafted` 只能从 `prepared` 进入
- `finalize-chapter --status polished` 只能从 `drafted` 进入
- `finalize-chapter --status reviewed` 只能从 `polished` 进入
- 同一 workspace 上的 `prepare-writing` / `prepare-chapter` / `finalize-chapter` 按章节串行执行，不要并发改同一个 `chapter_queue.json`
- 同一 workspace 的变更型命令会写入 `docs/workflow/workspace.lock.json`；检测到活动锁时不要并发继续写作
- `08-致谢.md` 不走自动写章，人工补写后才允许标 `reviewed`
- `REFERENCES.md` 不能当普通章节执行或 finalize
- workflow 侧变更合入前，至少执行一次 `selftest`

## 输入材料

每次写章至少同时阅读：

- `docs/writing/thesis_outline.md`
- `docs/writing/chapter_briefs/<chapter>.md`
- `docs/writing/project_profile.json`
- `docs/materials/material_pack.json`
- `docs/writing/literature_pack.json`
- `docs/writing/reference_registry.json`
- `docs/writing/citation_audit.md`（若已存在）
- `docs/writing/research_index.json`
- `docs/writing/research/`
- `docs/writing/chapter_packets/<chapter>.json`（仅在需要调试或诊断映射时）
- `workflow/skills/academic-paper-crafter/SKILL.md`
- `workflow/skills/thesis-workflow-orchestrator/SKILL.md`

章节结构规则：

- 大章节顺序固定
- 小节标题与层次以 `project_profile.json` 和 chapter packet 为准
- 不允许回退到健康档案示例中的固定小节模板

## 特殊规则

### 01-绪论

- 必须优先消费 `literature_pack`
- 必须优先消费 `research sidecar`
- 研究现状的文献编号只能来自 `reference_registry.json`
- 不允许凭记忆补虚构文献

### REFERENCES.md

- 不手工写编号
- 由 `finalize-chapter` 按 registry 自动刷新

### 引用编号

- 全文引用编号必须按首次出现顺序自动重排，不允许长期保留“先出现 [8]、后出现 [3]”的状态
- `finalize-chapter` 会自动刷新 `docs/writing/citation_audit.md`
- 如需单独整理一次，可执行 `python3 workflow_bundle/tools/cli.py normalize-citations --config <workspace.json>`
- 同一文献尽量只在一个主要论证位置使用一次；若必须重复使用，允许保留，但应接受 `citation_audit.md` 中的重复引用告警
- 同一句中尽量只保留一个引用；若确需多文献支撑，应拆成相邻句分别引用，并接受 `citation_audit.md` 中的单句多引用告警

### 08-致谢.md

- 默认人工处理
- 不使用自动章执行协议直接生成正式内容

### 05-系统实现.md

- 开写前优先保证已执行 `extract-code` 或 `extract`
- 必须优先消费 `code_evidence_pack.json`、`code_snippets/` 与 `code_screenshots/`
- 必须按模块合同写出后端实现、前端实现和白底黑字真实代码截图，不允许回退成纯文字实现章
- 代码截图必须内嵌到对应子功能的后端或前端实现段内，不得再单独拆出 `5.x.4 关键代码截图` 一类小节

### 图资源

- 第 4 章和第 5 章如果存在图占位，发布前必须执行 `prepare-figures`
- 不允许继续依赖健康档案样例的默认 `figure_map`
- `prepare-figures` 会根据原始项目文档、数据库设计文档和当前 Chapter 5 标题结构生成项目专属图片资源
- 正文 Markdown 如需保持干净，可使用 `<!-- figure:4.1 -->` 这类隐藏标记代替可见“配图占位”文案
