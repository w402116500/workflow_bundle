# 当前工作流真实状态审计

审核时间：2026-03-31

审核对象：

- 工作流优化日志：`/home/ub/thesis_materials/docs/workflow_optimization_log.md`
- 旧差异审核：`/home/ub/thesis_materials/docs/current_vs_original_article_audit_2026-03-30.md`
- 当前工作区：`/home/ub/thesis_materials/workspaces/teatrace_thesis`

## 结论

当前 Teatrace 工作区的真实状态，已经明显好于 2026-03-30 那份差异审核文档中的结论。当前工作流已经不再处于“只有模板骨架”的阶段，而是已经形成一套可稳定运行的论文写作工作区：

1. `polished_v3` 中已经是实际论文内容，而不是 scaffold 占位模板。
2. 动态章节画像、章节 packet、writer brief、引用审计和样式审计已经形成稳定链路。
3. Chapter 5 和 Chapter 6 的证据选择明显收敛，已经更接近原始优化样稿的组织方式。
4. 当前最主要的剩余问题，不是正文仍然为空，而是 Windows 终稿链路尚未在真实 Microsoft Word 环境中完成闭环验证。

因此，旧审核文档应视为“历史问题记录”，不能再直接作为当前状态结论引用。

## 已核实的当前事实

### F1. 当前正文已不再是 scaffold 占位稿

对 `workspaces/teatrace_thesis/polished_v3/` 执行占位词检索后，未再发现以下模板语句：

- `本文件由 scaffold 自动生成`
- `待补：`
- `TODO`
- `根据材料包补充`
- `Fill the English abstract`
- `待补正式参考文献`

这说明当前正文已经从模板骨架阶段恢复为实际论文文本。

同时，以下文件已确认存在实质内容，而非占位稿：

- `00-摘要.md`
- `00-Abstract.md`
- `05-系统实现.md`
- `06-系统测试.md`
- `08-致谢.md`
- `REFERENCES.md`

### F2. 当前章节执行状态整体稳定

当前 `chapter_queue.json` 显示：

- 自动章节 `00-摘要`、`00-Abstract`、`01-绪论`、`02-系统开发工具及技术介绍`、`03-需求分析`、`04-系统设计`、`05-系统实现`、`06-系统测试`、`07-结论与展望` 均为 `reviewed`
- `08-致谢.md` 为 `manual` 且状态为 `reviewed`
- `REFERENCES.md` 为 `registry` 且状态为 `managed`

同时，当前 queue 已接入新的双层写作接口：

- `chapter_packets/` 作为调试层 packet
- `chapter_briefs/` 作为写作层 brief

所有章节都已存在 `brief_md` 路径，这说明 writer brief 已经成为工作流正式组成部分，而不是临时实验产物。

### F3. Packet、Brief 与大纲同步状态正常

当前 workspace 检查结果显示：

- `packet_outline_status: current=10`
- `packet_kind: full=10`
- `Blocking packet sync issues: none`

这说明 10 个正文/写作相关章节的写作包和当前大纲是同步的，没有出现 stale/legacy/missing 的阻塞状态。

需要注意的是：

- `REFERENCES.md` 在 queue 中仍显示 `packet_kind=stub`、`outline=legacy`
- 这属于 registry 特殊章节的设计结果，不是正文写作包阻塞项

### F4. 样式和引用治理已经形成稳定约束

当前 workspace 检查中，以下告警均为 `none`：

- `style_issue_count`
- `placeholder_count`
- `style_preferred_subject_warning_count`
- `style_source_narration_warning_count`
- `style_repository_voice_warning_count`
- `style_weak_leadin_warning_count`
- `style_opening_rhythm_warning_count`
- `style_summary_recap_warning_count`
- `citation_order_warning_count`
- `citation_reuse_warning_count`
- `citation_sentence_warning_count`

这说明当前工作流在“本研究/本系统”表述、避免仓库叙事、引用顺序和单句多引控制方面，已经具备自动审计能力，并且当前工作区已通过这套审计。

### F5. Chapter 5 / Chapter 6 的证据选择已经明显收敛

根据最近日志步骤 117-127，可确认以下事实：

- Chapter 6 的 `test_artifacts` 已剔除规划、设计、部署、启动等非测试类文档
- Chapter 6 当前稳定保留的核心测试证据为：
  - `后端回归测试报告`
  - `全流程手动测试文档`
- Chapter 5 与 Chapter 6 的运行截图选择已由“整池平铺”收敛为代表性截图
- Chapter 5 第二张代表性截图已固定落到：
  - `5.5.3 公开追溯查询与结果展示实现`
- 双层输出已完成：
  - debug packet 继续保留完整调试字段
  - writer brief 去除了 `source_path`、源码路径、`render_as` 和多文档 provenance 串

这说明当前问题已经从“工作流无法组织论文材料”转变为“剩余细节是否继续打磨”，而不是主链路失败。

### F6. 接手链路已经切换到 workspace 资产同步语义

在本次审计中，对当前 Teatrace 工作区先执行 `resume`，再执行 `sync-workflow-assets`、`refresh-handoff` 与再次 `resume`，可确认：

- 当 workspace 本地 `workflow/*.md` 与 `workflow/skills/*` 落后于当前 bundle 时，`resume` 会直接报告 `workflow_signature_status: drifted`
- 此时 `next_commands` 首位会明确给出 `sync-workflow-assets --config ...`
- `read_first` 会优先加入：
  - `workflow/README.md`
  - `docs/workflow/workflow_assets_state.json`
- 只有执行 `sync-workflow-assets` 后，`workflow_signature_status` 才会恢复为 `current`
- 单独执行 `refresh-handoff` 不会把 `drifted` 自动改回 `current`

这说明接手流程已经不再依赖“最近是否刷新过 handoff”这种弱信号，而是改为检查 workspace 本地工作流资产是否真的与当前 bundle 同步。

## 与旧差异审核文档的关系

2026-03-30 的旧审核文档在当时是成立的，但对当前状态已经部分失效，具体如下：

### 已失效的结论

- “当前 `polished_v3` 大部分章节已被 scaffold 占位稿覆盖”
- “摘要与参考文献仍处于占位状态”
- “第 2-6 章只有材料来源与待补提示，不是论文正文”

这些结论与当前工作区现状不再一致。

### 仍然有参考价值的部分

- 其“根因定位”和“优先级划分”仍可视为历史修复背景
- 其对“结构层成功、正文落地曾失败”的分析，仍然解释了为什么后来需要优先修工作流，而不是只改文章

因此，该文档更适合作为“历史问题审计”，不应继续被当成“当前状态报告”使用。

## 当前仍未闭环的问题

### P1. Windows 终稿链路尚无实际产物

当前 `workspaces/teatrace_thesis/final/` 目录为空，说明：

- Windows 后处理接口与审计摘要机制已经在日志中设计并验证过逻辑
- 但当前工作区没有实际 `Windows终稿` 文件

因此，严格意义上说，“最终提交级终稿”仍未完成真实环境验证。

### P2. 当前缺少一份替代旧审核文档的正式状态说明

旧的 `current_vs_original_article_audit_2026-03-30.md` 仍然存在，而且结论已经落后。如果后续继续直接阅读它，容易产生两个误判：

- 误以为当前正文仍然是模板骨架
- 误以为当前工作流还停留在严重回退状态

本文件的作用，就是作为新的状态基线，替代旧文档承担“当前真实情况说明”。

## 当前最准确的整体判断

如果把当前工作流拆成三层来判断：

1. 材料抽取与项目画像层：已完成，状态稳定。
2. 写作输入与章节生成层：已完成，状态稳定，且已经升级为 debug packet + writer brief 双层输出。
3. 发布与终稿层：Linux 路径已基于最新工作区状态重新发布并完成校验；Windows 终稿仍未完成真实环境闭环。

因此，当前工作流最准确的定性是：

- 写作主链路已经打通，当前工作区可以视为“可持续写作、可持续校验”的论文工作区。
- 当前主要剩余工作已经从“能不能写出论文”转变为“能不能完成最终提交级终稿闭环”。
- 工作流总体完成度可评估为高，但如果以最终提交为标准，仍需补一次真实 Windows 终稿验证。

## 审核后新增确认

在本次审计完成后，已按新的 CLI-first 接手与发布链路重新执行当前工作区：

- `python3 workflow_bundle/tools/cli.py resume --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
- `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
- `python3 workflow_bundle/tools/cli.py refresh-handoff --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
- `python3 workflow_bundle/tools/cli.py release-preflight --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
- `python3 workflow_bundle/tools/cli.py release-build --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
- `python3 workflow_bundle/tools/cli.py release-verify --config workspaces/teatrace_thesis/workflow/configs/workspace.json`

同时，也补做了兼容入口验证：

- `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
- `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`
- `bash workflow_bundle/workflow/scripts/build_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
- `bash workflow_bundle/workflow/scripts/verify_release.sh workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`

刷新后，以下事实已确认成立：

- `workflow_signature_status` 已在 `sync-workflow-assets` 后恢复为 `current`
- 当前工作区最终 `resume` 输出为：
  - `phase: linux-release-ready`
  - `workflow_signature_status: current`
  - `lock_status: unlocked`
  - `next_commands: none`
- `check_bundle_sync.sh` 通过，说明 root 兼容层与 bundle 当前一致
- `verify_release.sh <docx-path>` 仍可作为直接引用校验兼容入口使用
- 并发时锁机制仍有效：
  - 在 `release-build` 持锁期间启动 `release-verify` 会抛出 workspace lock 错误
  - 串行重跑后 `release-verify` 成功通过

以下产物已与当前工作区状态重新对齐：

- `word_output/hyperledger-fabric.docx`
- `word_output/build_summary.json`
- `word_output/release_summary.json`
- `docs/workflow/workflow_assets_state.json`

其最新时间戳已更新到 2026-03-31 19:39 区间，其中：

- `workflow_assets_state.json`：19:39:01
- `build_summary.json`：19:39:38
- `release_summary.json`：19:39:57

这说明当前 Linux 交付链路、接手链路和兼容镜像链路已经同时与最新 bundle 状态对齐。
