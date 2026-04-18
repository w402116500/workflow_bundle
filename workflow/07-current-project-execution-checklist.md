# Current Project Execution Checklist

## 活动指针与示例配置

- 当前活动工作区指针：`workflow_bundle/workflow/configs/active_workspace.json`
- 示例工作区配置：`workflow/configs/current_workspace.json`（仅示例，不作为当前项目默认值）
- 项目清单：`workflow/configs/current_project_manifest.json`
- 若当前配置指向示例配置或 `workspace_root` 仍落在 `workflow_bundle/` 仓库内，变更型命令会被阻断；先用 `intake` 生成真实项目 workspace

## 推荐执行顺序

0. 冷启动接手
   - 如果是人工新开一个 AI 对话，优先复制 `workflow/06-ai-prompt-guide.md` 中对应模板
   - 如本轮涉及 bundle 整理、发版或远端提交，先执行 `python3 workflow_bundle/tools/cli.py version`
   - `python3 workflow_bundle/tools/cli.py resume`
   - 如输出 `workflow_signature_status: drifted`：`python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`
   - 如未设置当前活动工作区：`python3 workflow_bundle/tools/cli.py set-active-workspace --config <workspace.json>`
   - 如需检查并发状态：`python3 workflow_bundle/tools/cli.py lock-status --config <workspace.json>`
1. 检查工作区
   - `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>`
   - `bash workflow_bundle/workflow/scripts/check_workspace.sh`
   - 前者是官方入口，后者是兼容别名；两者都会先校验 root compatibility wrappers / `tools/core` mirror 是否与 bundle 保持同步，再执行 workspace preflight
2. 对比正文版本
   - `bash workflow_bundle/workflow/scripts/compare_versions.sh`
3. 写章前先读取写作包
   - 默认先看 `docs/workflow/handoff.md`
   - 默认优先阅读 `docs/writing/chapter_briefs/<chapter>.md`
   - 如需诊断证据来源或规则命中，再回看 `docs/writing/chapter_packets/<chapter>.md`
4. 构建 DOCX
   - `python3 workflow_bundle/tools/cli.py release-build --config <workspace.json>`
   - `bash workflow_bundle/workflow/scripts/build_release.sh`
   - shell wrapper 只是兼容入口，官方构建链以 `release-build` 为准
5. 运行平台相关后处理
   - `bash workflow_bundle/workflow/scripts/postprocess_release.sh`
   - Linux 可显式运行 `bash workflow_bundle/workflow/scripts/postprocess_release_linux.sh`
   - Windows 下如传入 `workspace.json`，会自动生成 `final/final_summary.json`
   - 后处理脚本现在也会先执行 compat sync 检查，避免在 bundle 更新后继续带着旧 root 兼容层发布
6. 校验引用锚点
   - `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>`
   - `bash workflow_bundle/workflow/scripts/verify_release.sh`
   - shell wrapper 只是兼容入口，官方校验链以 `release-verify` 为准
7. 若本轮修改的是 workflow 自身
   - 先确认 `VERSION` 与 `CHANGELOG.md` 是否已同步到本次变更范围
   - `python3 workflow_bundle/tools/cli.py selftest`
   - 如需同时覆盖真实工作区：`python3 workflow_bundle/tools/cli.py selftest --workspace-config <workspace.json>`

## 工作区的重要事实

- 正文真源：`polished_v3/`
- 证据材料：`docs/`、`code/`
- 默认产物目录：`word_output/`
- 当前 Linux 路径下无法完成 Microsoft Word 专属终排，Windows 终稿需另行后处理
