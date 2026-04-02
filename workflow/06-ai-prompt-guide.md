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
- 是否只走 Linux 路径。
- 是否允许 AI 修改 workflow 文档与工具代码，还是只准改 workspace 正文。

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
5. 第 5 章必须优先使用 code_evidence_pack、代码片段和白底黑字代码截图，且代码截图只能内嵌到对应子功能段内，不能另起“关键代码截图”小节。
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
```

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
