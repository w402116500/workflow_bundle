# Release Notes

本目录用于存放 `workflow_bundle` 的正式发布说明。

## 使用规则

- 文件名统一使用 semver tag，例如 `v0.5.0-rc1.md`、`v0.5.0.md`。
- `CHANGELOG.md` 负责记录结构化变更摘要；本目录负责补充更适合对外说明的发布内容。
- 预发布版本和正式版本都可以在这里落说明，但对外版本号仍以根目录 `VERSION` 与 Git tag 为准。
- 如果某次发布只完成本地 tag、尚未推送远端，不应在这里补最终对外发布说明。

## 当前记录

- `v0.5.1.md`
  - 修复 semver tag 识别逻辑后的补丁版正式发布说明。
- `v0.5.0.md`
  - 首个采用 semver 统一治理的 bundle 正式版说明。
- `v0.5.0-rc1.md`
  - 首个采用 semver 统一治理的 bundle 预发布版本说明。
