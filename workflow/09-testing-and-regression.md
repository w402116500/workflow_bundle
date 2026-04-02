# Testing And Regression

本文件定义 workflow bundle 的本地回归入口，目标是把“修改完 workflow 后如何确认没有把冷启动链和发布链弄坏”收敛成固定命令，而不是每次临时拼一组检查。

## 1. 官方入口

- `python3 workflow_bundle/tools/cli.py selftest`
- `python3 workflow_bundle/tools/cli.py selftest --workspace-config <workspace.json>`
- `bash workflow_bundle/workflow/scripts/selftest.sh`

其中：

- 默认 `selftest` 只运行 bundle 自带 fixture 的冷启动回归
- 传入 `--workspace-config` 后，会在 fixture 回归之后追加真实 workspace 的 Linux 发布回归
- 默认输出目录是系统临时目录；如需指定位置，可传 `--out-root <path>`

## 2. 覆盖范围

### 2.1 Fixture 冷启动回归

固定使用：

- `workflow/fixtures/fabric_trace_demo/`

固定覆盖：

- `smoke-intake`
- `prepare-chapter --chapter 05-系统实现.md`
- `prepare-chapter --chapter 06-系统测试.md`
- `check-workspace`

说明：

- `selftest` 在 fixture 阶段会以轻量参数运行 `smoke-intake`，把 `literature` 收敛为最小引用数并跳过重型 research sidecar 下载，目的是验证命令链和产物结构，而不是重复执行一次完整研究侧车抓取

固定断言：

- Chapter 5 brief/packet 中仍保留“代码截图内嵌、不得单列关键代码截图小节、不编号不写图题注”的规则
- Chapter 6 brief/packet 中仍保留“测试证据优先、真实测试表优先”的规则
- 目标章节的 `packet_outline_status` 仍为 `current`

### 2.2 真实 workspace 发布回归

仅在传入 `--workspace-config` 时执行。

固定覆盖：

- `resume --json`
- `release-preflight`
- `release-build --output-name selftest_release.docx`
- `release-verify --output-name selftest_release.docx`
- `lock-status --json`

固定断言：

- workspace 进入回归前必须是 `workflow_signature_status: current`
- workspace 进入回归前必须是 `lock_status: unlocked`
- `build_summary.json`、`release_summary.json`、`figure_prepare_summary.json` 和 `selftest_release.docx` 都已生成
- 引用锚点校验结果中 `anchors missing bookmarks = 0`
- 如果第 5 章正文引用了 `docs/materials/code_screenshots/`，导出的 Word 中不应再出现 `关键代码截图` 题注段落

## 3. 失败时如何解释

`selftest` 不会替你自动修复以下状态，而是直接失败并给出下一条命令：

- `workflow_signature_status: drifted`
- workspace 活动锁未释放
- `prepare-chapter` 或 `check-workspace` 报出 packet 阻塞项
- `release-build` / `release-verify` 失败
- DOCX 引用锚点校验失败
- DOCX 再次回退成带“关键代码截图”题注的导出结果

## 4. 产物

`selftest` 会写出：

- `selftest_summary.json`

其中至少包含：

- bundle 根目录
- 本次测试输出目录
- fixture 阶段命令、断言、日志路径和状态
- workspace 阶段命令、断言、日志路径和状态

日志会落到同一输出目录下的 `logs/` 子目录，便于定位失败命令的 stdout/stderr。

## 5. 推荐使用场景

以下变更完成后，建议至少执行一次 `selftest`：

- 修改 `workflow_bundle/tools/core/`
- 修改 `workflow_bundle/tools/cli.py`
- 修改 `workflow_bundle/workflow/scripts/`
- 修改 `workflow_bundle/workflow/skills/`
- 修改 `workflow_bundle/workflow/*.md`

如果本轮只改某一篇论文正文，而没有改 workflow，本文件中的回归命令不是必选项。
