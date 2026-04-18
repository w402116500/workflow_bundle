# AI Prompt Guide

本文件面向“人如何提示 AI 使用这套论文工作流”这一场景，目标不是解释工作流原理，而是提供可直接复制的提示模板，让新的 AI 对话也能按既定链路接手，不依赖历史聊天上下文。

## 1. 什么时候应该用这份指南

适用于以下场景：

- 你要让一个新的 AI 对话接手已有 workspace。
- 你要把一个新项目接入论文工作流。
- 你要指定 AI 继续某一章写作、润色、发布或排查问题。
- 你希望 AI 严格按 `workflow_bundle/` 的正式入口执行，而不是自己临时猜流程。

如果你只是问一个孤立问题，例如“第 4 章这里一句话怎么改”，可以不整套复制本指南。

## 2. 提示 AI 时必须说清楚的规则

如果你希望 AI 真正按工作流执行，而不是自由发挥，提示里至少要明确这些约束：

1. 给出绝对路径。
   - 继续已有工作区时，优先给 `workspace.json` 绝对路径。
   - 接入新项目时，给 `project_root`、论文标题和 `workspace_out` 绝对路径。
2. 明确任务类型。
   - 是 `resume`、`intake`、`写某一章`、`润色某一章`、`release`，还是 `排查问题`。
3. 明确正式入口。
   - 要求 AI 以 `workflow_bundle/tools/cli.py` 为正式入口，不要手工拼 root 兼容脚本当主链路。
4. 明确冷启动规则。
   - 新对话先执行 `resume --config <workspace.json>`。
   - 如果输出 `workflow_signature_status: drifted`，先执行 `sync-workflow-assets --config <workspace.json>`，再重新 `resume`。
5. 明确正文真源。
   - 论文正文只能以 `polished_v3/` 为准。
   - `docs/materials/`、`docs/writing/` 是证据和工作流状态，不是最终正文。
6. 明确阅读顺序。
   - 先读 `handoff.*` 和 `chapter_briefs/`。
   - 只有在排查证据分配或资产合同问题时，才回看 `chapter_packets/`。
7. 明确写章约束。
   - 每章原稿完成后，应调用 `$academic-paper-crafter` 进行润色，再进入 `polished`。
   - 引言、研究现状、文献不足时，才使用 `paper-research-agent` / `paper-reader`。
8. 明确发布约束。
   - Linux 主链路使用 `release-preflight`、`release-build`、`release-verify`。
   - 如果没有真实跑过 Microsoft Word，结果只能叫 Linux 交付版，不能叫 Windows 终稿。
9. 明确日志约束。
   - 如果 AI 修改的是 workflow 工具或 workflow 文档，而不是论文正文，应把操作写入：
     - `docs/workflow_optimization_log.md`
     - `workflow_bundle/docs/workflow_optimization_log.md`
10. 明确 workflow 回归约束。
   - 如果 AI 修改的是 `workflow_bundle/` 下的工具、技能、脚本或工作流文档，结束前应运行 `python3 workflow_bundle/tools/cli.py selftest`。
   - 如需同时覆盖真实 workspace 发布链，再运行 `python3 workflow_bundle/tools/cli.py selftest --workspace-config <workspace.json>`。
11. 明确版本治理约束。
   - 如果本轮涉及 workflow 发布、bundle 打包、远端仓库清理或正式提交流程，先执行 `python3 workflow_bundle/tools/cli.py version`。
   - 需要发版时，以根目录 `VERSION` 为单一真源，并同步检查 `CHANGELOG.md` 是否已补齐本次变更。
   - 预发布版本优先使用语义化版本的 RC 形式，例如 `0.5.0-rc1`，不要再用临时中文 tag 代替正式版本号。
12. 明确 AI 插图约束。
   - 只有场景示意图、业务流程概念图、论文插画类资源才适合使用 `prepare-ai-figures`。
   - 若要替换 `prepare-figures` 的内置图号，必须在 `ai_figure_specs` 中为对应图号显式设置 `override_builtin=true`，并在发布前先运行一次 `prepare-ai-figures`。
   - 当前 workflow 默认走 `zetatechs-gemini` provider；若执行环境需要回退到 OpenAI Image 兼容链，应显式把 `image_generation.provider` 改为 `zetatechs` 或 `zetatechs-openai-image`。
   - 最好为每张 AI 图补充 `diagram_type` 和 `style_notes`，并参考 `docs/THESIS_DIAGRAMS_LIST.md` 与 `docs/images/` 中的论文技术图风格来写提示，而不是只写一句笼统的图意描述。
   - 若某张图需要“提示词 + 参考图”一起送入模型，可在 `ai_figure_specs.<fig>.reference_images` 中声明参考 PNG/JPG；当前只有 `zetatechs-gemini` provider 会真正把参考图作为多模态输入发送。
   - AI 图本体只能保留图主体，不能在 PNG 内重复写图号、图题、章节名、页眉页脚、`Fig.` / `Figure` 或边缘装饰标签；题注由正文和 DOCX 排版层负责。
   - 若某张 AI 图因额度不足、质量不稳定或不适合论文风格而失败，不要硬撑整批命令；可把该图号的 `ai_figure_specs.<fig>.enabled` 改为 `false`，再执行 `prepare-figures`，让这一张图单独回退到确定性生成。

## 3. 提示前你最好准备好的信息

为了避免 AI 开场就反复追问，建议你在提示前准备以下信息：

- `workspace.json` 绝对路径，或者 `project_root` 绝对路径。
- 论文标题或项目标题。
- 当前目标章节，例如 `05-系统实现.md`。
- 本轮目标：
  - 只接手并汇报状态
  - 继续写某章
  - 只润色
  - 只做 release
  - 修 workflow
- 是否需要 AI 场景插图，以及对应图号、图题和意图。
- 若某些 AI 图需要保留确定性 fallback，也应提前说明图号。
- 是否只走 Linux 路径。
- 是否允许 AI 修改 workflow 文档与工具代码，还是只准改 workspace 正文。
- 如果涉及发版或远端提交，当前期望版本号是什么，以及是否已经更新 `VERSION` / `CHANGELOG.md`。

## 4. 推荐的提示模板

下面这些模板可以直接复制，把尖括号内容替换成你的真实路径和目标。

### 4.1 接手已有 workspace

这是最常用的模板，适合新对话继续已经存在的论文工作区。

```text
请使用 thesis workflow orchestrator 接手这个论文工作区：

workspace_config: <绝对路径/workspace.json>

要求：
1. 不要依赖之前的聊天历史。
2. 必须以 workflow_bundle/tools/cli.py 作为正式入口。
3. 先运行 python3 workflow_bundle/tools/cli.py resume --config <绝对路径/workspace.json>。
4. 如果 workflow_signature_status 是 drifted，先运行 python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <绝对路径/workspace.json>，再重新 resume。
5. 先汇报当前 phase、next command、接下来要读的文件。
6. 先读 handoff 和 chapter_briefs，不要一开始全仓扫描。
7. 正文真源只能是 polished_v3/。
8. 如果本轮涉及 workflow 工具或 workflow 文档修改，把操作写入 docs/workflow_optimization_log.md 和 workflow_bundle/docs/workflow_optimization_log.md。
然后继续执行下一步。
```

### 4.2 接入一个新项目

适合你有前端、后端、数据库、智能合约和规划文档，但还没有 workspace 的情况。

```text
请把下面这个项目接入论文工作流，并建立新的 thesis workspace：

project_root: <绝对路径/project_root>
title: <论文标题>
workspace_out: <绝对路径/workspace_dir>

要求：
1. 使用 workflow_bundle/tools/cli.py 作为正式入口。
2. 按 intake -> extract-code -> extract -> scaffold -> literature -> prepare-outline -> prepare-writing 的顺序推进。
3. 如果文档或代码材料缺失，请在 missing_inputs 中明确列出，不要硬编。
4. 先把工作区准备完整，再讨论正文写作。
5. 如果 workflow 本身需要修改，把操作写入两个 workflow_optimization_log.md。
6. 如果本轮同时要整理 workflow bundle 仓库，先执行 `python3 workflow_bundle/tools/cli.py version`，并在输出中说明当前 bundle 版本。
完成后汇报生成的 workspace 路径、缺失项、下一步建议。
```

### 4.3 继续某一章写作

适合工作区已经准备好，你希望 AI 直接继续一章。

```text
请继续执行这一章的论文写作：

workspace_config: <绝对路径/workspace.json>
chapter_file: <例如 05-系统实现.md>

要求：
1. 先 resume --config。
2. 如果 workflow_signature_status 是 drifted，先 sync-workflow-assets，再重新 resume。
3. 先读 docs/writing/chapter_briefs/<chapter_file>，只有必要时再读 chapter_packets。
4. 写作必须以 polished_v3/<chapter_file> 为正文真源。
5. 第 5 章必须优先使用 code_evidence_pack 与已抽取的真实代码片段；若 workspace 配置了 `document_format.code_blocks.render_mode=text`，最终 DOCX 应输出文字代码块。代码截图仅作为可选证据形式，且只能内嵌到对应子功能段内，不能另起“关键代码截图”小节。
6. 第 6 章必须优先使用测试证据，不要把规划和设计文档当测试结论。
7. 完成原稿后，调用 $academic-paper-crafter 进行学术化润色，再 finalize-chapter 到 polished。
8. 引用保持顺序编号，避免一处连续堆叠多条引用。
```

### 4.4 只做章节润色

适合正文已经基本存在，你只要 AI 做一轮论文式打磨。

```text
请只对这一章做润色，不要重写工作流：

workspace_config: <绝对路径/workspace.json>
chapter_file: <例如 04-系统设计.md>

要求：
1. 先 resume --config。
2. 读取 polished_v3/<chapter_file> 和对应 chapter_brief。
3. 使用 $academic-paper-crafter 润色现有内容。
4. 保持事实、结构和引用编号不乱。
5. 正文中优先使用“本研究”或“本系统”，避免仓库叙事、文件路径叙事和“证据路径”表述。
6. 润色完成后覆盖原 chapter 文件，并按 workflow 状态更新。
```

### 4.5 只做 Linux 发布与校验

适合你不想改正文，只想确认文档能构建并通过引用检查。

```text
请只执行 Linux 发布链路，不要改正文内容：

workspace_config: <绝对路径/workspace.json>

要求：
1. 先 resume --config。
2. 如果 workflow_signature_status 是 drifted，先 sync-workflow-assets。
3. 然后执行 release-preflight -> release-build -> release-verify。
4. 汇报 build_summary.json、release_summary.json、最终 docx 路径和引用锚点结果。
5. 如果没有跑 Windows Word 后处理，明确说明结果只是 Linux 交付版。
6. 如果本轮涉及正式发版，补充汇报当前 `VERSION`、拟使用的 tag，以及 `CHANGELOG.md` 是否与之对齐。
```

### 4.6 排查 workflow 问题

适合你怀疑流程本身有 bug，例如 packet 过期、release 失败、handoff 不一致。

```text
请排查这个 thesis workflow 问题，并优先修 workflow 本身：

workspace_config: <绝对路径/workspace.json>
problem: <用一句话描述问题>

要求：
1. 先 resume --config。
2. 如果 workflow_signature_status 是 drifted，先 sync-workflow-assets。
3. 先根据 handoff、chapter_queue、release summary 和相关 workflow 文档定位问题，不要直接重写正文。
4. 如果需要修改 workflow 工具或 workflow 文档，把每一步操作写入 docs/workflow_optimization_log.md 和 workflow_bundle/docs/workflow_optimization_log.md。
5. 修复后重新验证相关命令，并汇报结果。
6. 如果修复影响 bundle 正式行为或发版链，顺带执行 `python3 workflow_bundle/tools/cli.py version`，确认版本信息输出正常。
```

### 4.7 运行 workflow 自测

适合你刚修改了 workflow 工具、skill、脚本或执行文档，想让新的 AI 对话直接帮你跑回归。

```text
请运行这套 thesis workflow 的本地回归，不要改正文：

workspace_config: <可选，绝对路径/workspace.json>

要求：
1. 以 workflow_bundle/tools/cli.py 作为正式入口。
2. 至少执行 python3 workflow_bundle/tools/cli.py selftest。
3. 如果给了 workspace_config，再执行 python3 workflow_bundle/tools/cli.py selftest --workspace-config <绝对路径/workspace.json>。
4. 汇报 selftest_summary.json 路径、fixture 阶段结果、workspace 阶段结果。
5. 如果失败，明确是哪一步失败、对应日志文件在哪、下一条修复命令是什么。
6. 如果本轮修改过版本治理相关文件，补充汇报 `python3 workflow_bundle/tools/cli.py version` 的结果。
```

### 4.8 准备 AI 场景插图

适合你已经确定某几张论文插图更适合通过 AI 生图生成，并希望 AI 只准备这些图，不直接修改正文。

```text
请为这个 thesis workspace 准备 AI 插图资源：

workspace_config: <绝对路径/workspace.json>
figures:
  - figure_no: <例如 5.1>
    caption: <图题>
    intent: <图像意图>
    override_builtin: <true|false>
    reference_images:
      - path: <可选，本地参考图路径>
        role: <可选，例如 style_layout/content_structure>
        note: <可选，告诉模型这张图只参考什么>

要求：
1. 使用 workflow_bundle/tools/cli.py 作为正式入口。
2. 先检查 workspace.json 中的 image_generation 与 ai_figure_specs 是否完整；缺字段时先补配置，再执行命令。
3. 只把 AI 图片生成到本地 PNG，不要直接手改 markdown 中的图片路径。
4. 先执行 python3 workflow_bundle/tools/cli.py prepare-ai-figures --config <绝对路径/workspace.json>。
5. 如果某个图号覆盖了内置生成图，后续发布前再执行 release-preflight，确认不会因为缺少 AI PNG 被阻断。
6. 如果本轮修改了 workflow 工具或工作流文档，把操作写入两个 workflow_optimization_log.md。
完成后汇报生成图片路径、prompt_manifest.json 路径，以及哪些图号已写回 figure_map。
```

### 4.8.1 传统 UML 用例图 AI 模板

当某张图不适合继续用 `PlantUML` 或本地 Pillow 布局，而你又希望它保持“传统 UML 用例图”画法时，推荐先把教程图和说明文档抽成 `reference_guides`，再由 `ai_figure_specs` 消费 guide 与原始参考图。

适用边界：

- 适合：论文中的规范黑白用例图，需要参考既有教程图法，但当前本地自动布局不稳定。
- 不适合：已经有稳定可重复生成的本地 UML 渲染器，且输出质量满足论文要求的场景。

模板要点：

- `diagram_type` 固定写 `use_case`
- 有教程 Markdown 或多张样图时，优先先配置 `reference_guide_specs` 并执行 `prepare-reference-guides`
- 参考图优先提供：
  - Actor 小人符号示例
  - 系统边界示例
  - 多用例排版示例
- `prompt_override` 里要明确：
  - Actor 小人
  - 系统边界矩形框
  - 用例椭圆
  - 参与者在边界外、用例在边界内
  - 只保留普通关联线
  - 所有关联线必须是单段直线，禁止折线、回折线、曲线
  - 禁止 `include / extend / 泛化 / 流程箭头 / 泳道 / 彩色教程风`

示例：

```yaml
reference_guide_specs:
  uml_use_case_traditional_zh:
    guide_type: use_case
    description: 传统 UML 用例图规范抽取
    enabled: true
    sources:
      - path: <教程 markdown>
        kind: markdown
        role: text_spec
      - path: <actor 示例图>
        kind: image
        role: symbol_style
      - path: <系统边界示例图>
        kind: image
        role: style_layout
      - path: <多用例排版示例图>
        kind: image
        role: style_layout

ai_figure_specs:
  3.2:
    caption: 图3.2 多角色协同用例关系图
    chapter: 第三章 需求分析
    diagram_type: use_case
    enabled: true
    override_builtin: false
    reference_guides:
      - uml_use_case_traditional_zh
    intent: 绘制传统 UML 用例图，展示多角色与系统核心用例之间的对应关系。
    style_notes: 白底黑线、论文黑白版、传统 UML 用例图。
    prompt_override: |
      白底黑线、二维、传统 UML 用例图风格。
      只允许使用 Actor 小人、系统边界矩形框、用例椭圆、无箭头实线关联。
      所有关联线必须为单段直线，不允许折线、L 形线、Z 形线、回折线或曲线。
      不要 include、extend、泛化、流程箭头、泳道、矩形角色框、红黄教程配色。
    reference_images:
      - path: <actor 示例图>
        role: symbol_style
        note: 只参考小人画法，不参考颜色。
      - path: <系统边界示例图>
        role: style_layout
        note: 只参考边界内外关系，不参考颜色。
      - path: <多用例排版示例图>
        role: style_layout
        note: 只参考传统排版语言，不参考旧图中的 include 虚线关系。
```

落地注意：

- `prepare-reference-guides` 负责把教程图和说明文档先抽成结构化 guide，`prepare-ai-figures` 只消费 guide，不替代 guide 抽取阶段。
- 如果该图号原来还在 `plantuml_figure_specs`、`er_figure_specs` 或其他确定性链路里，先把对应 spec 关闭，否则后续 `prepare-figures` 可能重新接管该图号。
- 如果正文 Markdown 里写死了图片路径，例如 `![图3.2 ...](../docs/images/generated/xxx.png)`，要同步把路径改到 AI 输出位置；仅修改 `figure_map` 不足以影响这种显式图片行。
- 生成顺序应为：
  - `prepare-reference-guides --config <workspace.json> --guide <guide-name>`
  - `prepare-ai-figures --config <workspace.json> --fig <图号>`
  - 再执行 `release-preflight` / `release-build` / `release-verify`

### 4.8.2 传统分层架构图 AI 模板

适用边界：

- 适合：系统总体架构图、分层架构图、链上链下协同架构图等，需要保持传统论文黑白技术图风格。
- 不适合：需要复杂图标库、宣传海报式视觉或高度装饰化产品图的场景。

模板要点：

- `diagram_type` 固定写 `architecture`
- guide 来源优先使用 workspace 内冻结的已验收样图和简短规范说明，建议放在 `docs/images/reference_guides_src/architecture/`
- `reference_guides` 负责收口：
  - 分层外框
  - 标题栏
  - 层内模块横向均匀排布
  - 连线克制、避免总线和交叉
- `prompt_override` 只保留：
  - 当前项目的层名
  - 模块名
  - 必须保留的层间关系
  - 明确禁止的错误连线

### 4.8.3 传统流程图 AI 模板

适用边界：

- 适合：业务流程图、权限校验流程图、查询与审计流程图等，需要用 AI 保持传统论文黑白流程图风格。
- 不适合：已有稳定 PlantUML/Mermaid 流程源码且输出质量已满足论文要求的场景。

模板要点：

- `diagram_type` 固定写 `flowchart`
- guide 来源优先使用 workspace 内冻结的已验收样图和简短规范说明，建议放在 `docs/images/reference_guides_src/flowchart/`
- `reference_guides` 负责收口：
  - 处理框 / 判断菱形 / 箭头线的画法
  - 自上而下主线
  - 分支与回流的紧凑布局
  - 禁止横向长带、过密节点和多余折线
- `prompt_override` 只保留：
  - 当前图的节点文字
  - 判断分支文字
  - 节点顺序与回流逻辑
  - 特殊排版硬约束

### 4.8.4 传统系统功能结构图 AI 模板

适用边界：

- 适合：系统功能结构图、模块结构图、树状功能分解图等，需要保持传统论文树状技术图风格。
- 不适合：更适合用确定性 SVG/Pillow 自动排版且已经足够稳定的场景。

模板要点：

- `diagram_type` 固定写 `function_structure`
- guide 来源优先使用 workspace 内冻结的已验收样图和简短规范说明，建议放在 `docs/images/reference_guides_src/function_structure/`
- `reference_guides` 负责收口：
  - 顶层居中
  - 一级横向展开
  - 二级纵向列示
  - 矩形框与正交分支线
  - 禁止多子节点共用含混主干
- `prompt_override` 只保留：
  - 当前系统名
  - 一级模块名
  - 二级子功能名
  - 对齐、间距和分支线的项目专属硬约束

补充约束：

- 非 ER 技术图优先走 `reference_guides`；`ER` 图通常继续用 `er_figure_specs + dbdia-er`
- guide 的 `sources` 推荐只引用 workspace 内冻结资产，不要直接引用 `tmp_*` 目录或运行期 `docs/images/generated_ai/`

## 5. 最短可用提示

如果你不想每次都贴完整模板，至少可以用这一句：

```text
请按 workflow_bundle 论文工作流接手 <绝对路径/workspace.json>，先 resume --config；如果是 drifted 就先 sync-workflow-assets，再根据 handoff 和 chapter_briefs 继续，不要依赖历史聊天，正文真源只认 polished_v3/。
```

## 6. 不推荐的提问方式

以下说法在新对话里很容易让 AI 走偏：

- `继续吧`
- `接着上次做`
- `看一下这个项目然后写论文`
- `直接帮我生成完整论文`
- `你自己决定下一步`

这些说法的问题是：

- 没给 `workspace.json` 或 `project_root`
- 没说明是接手、写章、润色还是 release
- 没强调 `workflow_bundle/` 正式入口
- 没告诉 AI 不能依赖历史聊天

如果你只说这些模糊话，AI 很容易重新扫仓库、误读旧文档，或者绕开现有工作流直接自由发挥。

## 7. 如果 AI 环境不支持本地 skill 名称

有些环境不能直接识别 `thesis-workflow-orchestrator`、`$academic-paper-crafter` 等技能名称。这时不要放弃工作流，可以把规则直接写进提示里，至少保留以下句子：

- 先 `resume --config <workspace.json>`
- `drifted` 时先 `sync-workflow-assets --config <workspace.json>`
- 以 `workflow_bundle/tools/cli.py` 为正式入口
- 先读 `handoff` 和 `chapter_briefs`
- 正文真源只认 `polished_v3/`
- 每章完成后再做一轮学术化润色

这样即使没有显式 skill 路由，AI 仍然有较高概率沿着同一套工作流执行。
