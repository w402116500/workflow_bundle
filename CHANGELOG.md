# Changelog

本文件从 `0.5.0` 开始维护结构化版本记录。
更早的历史提交与中文 milestone tag 仍然存在于 Git 历史中，但未形成统一 changelog；从当前版本起，正式 release 以语义化版本号为准。

## [0.5.0] - 2026-04-18

说明：

- 本版本基于 `v0.5.0-rc1` 收口为正式版，核心能力与 RC 保持一致。
- 正式版主要确认版本治理、公共仓库清理与发布识别链路已稳定可用。

### Added

- 新增 `VERSION` 作为 bundle 当前版本的单一真源。
- 新增 `CHANGELOG.md`，用于维护正式版本变更记录。
- 新增 `python3 workflow_bundle/tools/cli.py version` 与 `--version`，可查询当前版本、建议 tag、Git 提交和 dirty 状态。
- 新增 `workflow/11-versioning-and-release.md`，明确版本号、tag 和发版规则。

### Changed

- `build_summary.json`、`release_summary.json`、`final_summary.json`、`selftest_summary.json` 现会记录生成它们时的 bundle 版本信息。
- `resume` / handoff 现会显示当前 bundle version，便于区分不同工作流资产批次。
- 公开文档中的远端仓库说明已去项目化，并开始区分“正式 semver 版本”和“历史中文 milestone tag”。

## Historical Tags

- `v0.4.0`
- `v0.3.0`
- `v0.2.0`
- `v0.5.0-rc1`

说明：

- 以上历史 tag 继续有效，但缺少统一 changelog 支撑。
- 中文 tag 可继续作为阶段性里程碑或专项修复标记保留；正式 release 版本建议统一使用 `vX.Y.Z` 或 `vX.Y.Z-<prerelease>`。
