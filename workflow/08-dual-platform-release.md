# Dual Platform Release

## 1. 发布类型

本工作流区分两类交付件：

- `基础排版稿`：可由 `python3 workflow_bundle/tools/cli.py build ...` 直接生成；标准发布链路默认通过 `release-build`
- `Windows 终稿`：在 Microsoft Word 环境中完成最终样式和域刷新后得到的交付件

在继续已有工作区前，推荐先执行：

- `python3 workflow_bundle/tools/cli.py resume --config <workspace.json>`
- 若输出 `workflow_signature_status: drifted`：`python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`
- 如需刷新 handoff 再执行：`python3 workflow_bundle/tools/cli.py refresh-handoff --config <workspace.json>`

## 2. Linux 路径

Linux 路径适合完成：

- Markdown 到 DOCX 的基础生成
- 图表插入
- 引用锚点校验

推荐命令：

- `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>`
- `bash workflow_bundle/workflow/scripts/check_workspace.sh <workspace.json>`
- `bash workflow_bundle/workflow/scripts/postprocess_release_linux.sh`

其中：

- `sync-workflow-assets` 是 Linux 发布前的工作流资产同步入口；`refresh-handoff` 不会替代它把 drifted 状态改回 current
- `release-preflight` 是统一发布前检查入口，会先执行 compat sync 校验，再检查章节 packet 是否仍与当前论文大纲同步
- 若 `ai_figure_specs` 对内置图号开启了 `override_builtin=true`，`release-preflight` 还会检查对应的 AI PNG 是否已经通过 `prepare-ai-figures` 显式准备完成；缺失时会直接阻断发布链路
- `check_workspace.sh` 现在保留为 `release_preflight.sh` 的兼容别名
- `release-build` 与 `release-verify` 在使用 workspace config 时会自动执行这一步 preflight；若存在 `stale / legacy / missing` 的 packet，同步校验会直接中止发布链路
- `prepare-figures` 现已支持未变化图资源的缓存复用，因此重复执行 Linux 发布链路时不会再为同一张 Mermaid 图重复走网络渲染
- `build_release.sh` 与 `verify_release.sh` 现在只是 `release-build` 与 `release-verify` 的 shell 转发层
- `build_release_docx.sh` 仅保留为内部兼容 helper，用于输出构建后的 DOCX 路径
- `build_release.sh` 完成后会在 `word_output/` 中留下 build summary 审计文件，记录 preflight、图缓存状态和基础排版稿 DOCX 时间戳
- `verify_release.sh` 完成后会在 `word_output/` 中留下 release summary 审计文件，记录 preflight、图缓存状态、DOCX 时间戳和引用锚点校验结果

## 3. Windows 路径

Windows 路径适合完成：

- Word 域刷新
- 模板终排
- 依赖 Microsoft Word 的样式修正

推荐入口：

- `bash workflow_bundle/workflow/scripts/postprocess_release.sh`
- `powershell -File workflow_bundle/workflow/scripts/postprocess_release.ps1 <workspace.json>`
- 或直接在 Windows 下调用 `python3 workflow_bundle/tools/cli.py postprocess --config <workspace.json>`

其中：

- `postprocess_release.sh <workspace.json>` 在 Windows 下会自动解析：
  - 基础排版稿输入 DOCX
  - 终稿输出 DOCX
  - 终稿图页码日志输出
- 在 WSL 下执行 `postprocess_release.sh <workspace.json>` 时，若本地缺少 `win32com`，CLI 会自动桥接到宿主 `powershell.exe` + Windows Python/Word 终排
- Windows 终排成功后会在 `final/` 中写出：
  - `final_summary.json`
  - `final_runs/final_summary_<timestamp>.json`
- `final_summary.json` 记录：
  - workspace metadata
  - latest preflight snapshot
  - latest figure-prepare summary
  - base DOCX / final DOCX metadata
  - final figure-log metadata

## 3.1 自动分发入口

如果不想区分平台，可以统一使用：

- `bash workflow_bundle/workflow/scripts/postprocess_release.sh`

## 3.2 WSL 到宿主 Windows 的推荐做法

如果当前论文工作区仍放在 WSL 的 Linux 路径下，可以继续这样运行；CLI 会把 `workspace.json`、基础排版稿和日志路径自动桥接给宿主 Windows。

如果本轮目标是：

- 验证宿主 Windows 的 Word 终排能力
- 用宿主侧 Office / 文件管理器直接检查导出结果
- 在 WSL 中先生成，再把结果交给 Windows 侧流程复核

推荐额外准备一个 Windows 盘符映射目录，例如：

- `/mnt/<drive>/workspace_probe`

建议：

- bundle 和 workspace 真源仍可保留在 WSL 路径
- 仅把用于宿主复核的 probe / 发布产物放到 `/mnt/<drive>/...`
- 需要给 PowerShell 传路径时，统一先执行 `wslpath -w <path>`
- PowerShell 单次命令涉及中文输出时，先设置 UTF-8 控制台编码，避免 `参考文献`、图题等中文字段乱码

推荐的 probe 目录形态：

- WSL 路径：`/mnt/<drive>/workspace_probe/win_release_probe`
- Windows 路径：`<DRIVE>:\\workspace_probe\\win_release_probe`

建议至少核对以下结果：

- `参考文献` 标题存在
- `图5-1` 等连字符编号保留正确
- 正文中的文献交叉引用仍保持上标格式
- `figure_insert_log_final.csv` 成功回填

## 4. 对外说明

如果只跑了 Linux 生成链路，应明确说明产物是 Linux 交付版，不应误称为最终 Word 终稿。对外描述推荐优先使用 CLI 链路名称：`release-preflight`、`release-build`、`release-verify`；shell 脚本仅作为兼容入口说明。
