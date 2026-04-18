# Versioning And Release

## 1. 目标

本文件定义 `workflow_bundle` 的正式版本治理规则，解决“提交很多，但无法明确当前版本、发布批次和变更边界”的问题。

## 2. 单一真源

- 当前 bundle 版本以仓库根目录的 `VERSION` 文件为准。
- 当前正式版本：`0.6.0`
- 任何 CLI、summary、handoff 或 release 文档中需要展示版本号时，都应从 `VERSION` 读取，而不是手写常量。

## 3. 版本号规则

采用语义化版本格式：

- `MAJOR.MINOR.PATCH`
- 开发中或预发布版本可追加后缀，如 `0.5.0-dev`、`0.5.0-rc1`

推荐含义：

- `PATCH`
  - 文档修正、回归修复、小范围兼容性修正
- `MINOR`
  - 新 CLI 子命令、新配置接口、新工作流阶段能力、非破坏性增强
- `MAJOR`
  - 破坏兼容性的目录、配置 schema、CLI 语义调整

## 4. Tag 规则

- 正式 release tag 统一使用 `vX.Y.Z` 或 `vX.Y.Z-<prerelease>`
- 中文 tag 可以继续保留，但只作为阶段性 milestone / 专项修复标记，不应替代正式版本号
- 对外说明当前版本时，优先使用 `VERSION` 对应的 semver，而不是中文 tag 名称

## 5. 发版最小流程

准备一个正式版本时，至少完成以下动作：

1. 更新 `VERSION`
2. 更新 `CHANGELOG.md`
3. 运行：
   - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
   - `python3 workflow_bundle/tools/cli.py selftest`
4. 用 `python3 workflow_bundle/tools/cli.py version` 确认版本号、`suggested_tag`、`tag_exists`、commit、dirty 状态
5. 提交后创建正式 semver tag，例如：
   - `git tag v0.5.0`
   - `git push origin main --tags`

## 6. 查询入口

- `python3 workflow_bundle/tools/cli.py version`
- `python3 workflow_bundle/tools/cli.py version --json`
- `python3 workflow_bundle/tools/cli.py --version`

其中：

- `suggested_tag` 表示根据当前 `VERSION` 推导出的目标 semver tag
- `tag_exists=true` 才表示该 tag 已经实际存在于 Git 仓库中
- `latest_semver_tag` 用于查看仓库里当前最近的 semver tag，不等同于 `VERSION`

## 7. 产物追踪

以下机器可读产物应记录 bundle 版本信息：

- `word_output/build_summary.json`
- `word_output/release_summary.json`
- `final/final_summary.json`
- `selftest_summary.json`

这样可以反查“某个 DOCX 或某次回归是由哪个 workflow 版本生成的”。
