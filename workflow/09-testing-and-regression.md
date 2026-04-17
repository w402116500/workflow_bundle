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

### 2.3 AI 插图覆盖回归

仅在本轮改动涉及 `prepare-ai-figures`、`figure_map` 覆盖逻辑或 `release-preflight` 的 AI 图检查时执行。

固定覆盖：

- `python3 workflow_bundle/tools/cli.py prepare-ai-figures --config <workspace.json> --dry-run`
- `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>`

固定断言：

- `prepare-ai-figures --dry-run` 可以正确读取 `image_generation` 与 `ai_figure_specs`，并生成 `ai_figure_prepare_summary.json`
- 若某个内置图号在 `ai_figure_specs` 中声明了 `override_builtin=true`，但对应本地 PNG 尚未准备完成，`release-preflight` 必须直接失败，而不是静默回退到旧图
- 当覆盖图已经准备完成时，后续 `prepare-figures` 必须保留 `figure_map` 中的 AI 条目，而不是重新覆盖为内置渲染结果
- 抽查 AI PNG 时，图内不应出现图号、图题、章节标题、页眉页脚、`Fig.` / `Figure`、边缘竖排标签或其他非图主体装饰文字
- 若某张图因为额度不足或质量不合格改回确定性生成，应验证该图号在 `figure_map` 中已切回 `renderer=mermaid`、`graphviz-dot`、`dbdia-er` 或其他非 `ai-image` 渲染器，同时其他 AI 图号保持不变

### 2.4 确定性图件与 E-R 回归

当本轮改动涉及 `prepare-figures`、`figure_map.renderer`、`er_figure_specs` 或 vendored 图形运行时时执行。

固定命令：

- `rm -rf workflow_bundle/vendor/dbdia/build`
- `rm -rf workflow_bundle/vendor/graphviz_wasm/node_modules`
- `python3 workflow_bundle/tools/cli.py prepare-figures --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>`

固定断言：

- `prepare-figures` 能在干净运行时自动恢复 `vendor/dbdia/build/` 与 `vendor/graphviz_wasm/node_modules/`
- 对显式声明为 `graphviz-dot` 或 `dbdia-er` 的图号，`figure_map.<fig>.renderer` 必须回写为对应渲染器
- 对已启用的 `er_figure_specs.<fig>`，对应的 `docs/images/generated_src/<stem>.dbdia/.dot/.svg` 必须存在
- 发布链不能把显式声明的确定性图件静默回退为 Mermaid 或手绘 fallback 结果
- 若本轮仅整理 E-R 正式链路，`selftest` 不应再因为未执行与本轮无关的旧样例准备步骤而失败

### 2.5 WSL -> Windows Word 终排桥接回归

当本轮改动涉及 `postprocess`、`tools/windows/postprocess_word_format.ps1`、PowerShell UTF-8 输出，或 Windows 终稿标题/图题编号时执行。

推荐做法：

- 保持真实 workspace 仍在 WSL 路径
- 另外准备一个 Windows-backed probe 目录，例如 `/mnt/<drive>/workspace_probe/win_release_probe`
- 把基础排版稿和图日志复制到 probe 目录后，再调用宿主 PowerShell/Word 终排

固定断言：

- 宿主 PowerShell 可以正确输出 UTF-8 中文，不出现 `参考文献`、图题、表题乱码
- `postprocess_word_format.ps1` 在 Windows-backed 目录中可成功生成终稿 DOCX
- 终稿内必须存在 `参考文献` 一级标题
- 图表编号风格保持当前 profile 约定；例如成都信息工程大学本科模板应保留 `图5-1`，不应回退成 `图5.1`
- 正文中的文献交叉引用在 Windows 终稿中仍必须保持上标；`doc.Fields.Update()` 之后不能把 `REF ref_x` 的显示结果降回正文基线
- `figure_insert_log_final.csv` 已生成且能回填图题条目

## 3. 失败时如何解释

`selftest` 不会替你自动修复以下状态，而是直接失败并给出下一条命令：

- `workflow_signature_status: drifted`
- workspace 活动锁未释放
- `prepare-chapter` 或 `check-workspace` 报出 packet 阻塞项
- AI override 图号声明了 `override_builtin=true`，但尚未通过 `prepare-ai-figures` 准备本地 PNG
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
- 修改 AI 插图配置接口、`ai_figure_specs` 使用说明或 `release-preflight` 的 AI 图约束

如果本轮只改某一篇论文正文，而没有改 workflow，本文件中的回归命令不是必选项。
