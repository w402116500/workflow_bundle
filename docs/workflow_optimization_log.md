# Workflow Optimization Log

本文件只记录面向公共 `workflow_bundle` 仓库的通用工作流变更。
与某个具体 workspace、某台机器或某篇论文强绑定的执行日记，不再保存在这里，而应保留在对应 workspace 的文档目录或独立 companion 仓库中。

## 记录规则

- 只写 bundle 层的正式入口、配置接口、文档约束和回归链变化。
- 不写绝对机器路径、私人目录名或具体论文项目名。
- 每次修改尽量记录：目的、影响面、验证结果。

## 2026-04-17

- Purpose: 清理远端仓库中的项目残留，使公开仓库保持“通用论文工作流 bundle”定位，而不是某个具体项目的运行快照。
- Changes:
  - 清理 `README.md`、`workflow/README.md`、`workflow/07-current-project-execution-checklist.md`、`workflow/08-dual-platform-release.md`、`workflow/09-testing-and-regression.md` 中的项目化路径与措辞。
  - 将 `workflow/configs/current_project_manifest.json` 与 `workflow/configs/current_workspace.json` 收口为官方示例实例，不再使用真实项目快照。
  - 把 `docs/current_workflow_status_audit_2026-03-31.md` 改为历史说明文件，并新增 `docs/archive/README.md` 作为归档策略入口。
  - 修复 `tools/core/extract.py` 中的项目硬编码输出文案，改为按当前技术栈生成中性环境描述。
- Validation:
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`
  - `rg` 复查公开文档与代码中的项目残留关键词

## 2026-04-17 (versioning)

- Purpose: 为 bundle 建立正式版本号治理，避免只有零散 tag 和提交记录、却无法明确回答“当前是什么版本”。
- Changes:
  - 新增 `VERSION` 与 `CHANGELOG.md`。
  - 新增 `tools/core/bundle_version.py`，把版本号、tag、commit、dirty 状态收口成统一读取入口。
  - 为 CLI 增加 `version` 子命令与 `--version`。
  - 将 bundle version 写入 handoff、build/release/final/selftest summary。
  - 新增 `workflow/11-versioning-and-release.md`，明确 semver、tag 和发版流程。
- Validation:
  - `python3 tools/cli.py version`
  - `python3 tools/cli.py version --json`
  - `python3 tools/cli.py --version`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`

## 2026-04-18 (pre-release audit)

- Purpose: 在 `v0.5.0-rc1` 推送前做最后一轮公开仓库一致性复核，修正文档中的旧版本口径，并把未发布提交的作者身份收口到仓库正式身份。
- Changes:
  - 修正 `workflow/11-versioning-and-release.md` 中仍残留的 `0.5.0-dev` 表述，统一为当前预发布版本 `0.5.0-rc1`。
  - 复核公开文档中的版本、tag 与项目化残留口径，确认当前 bundle 对外说明以 `VERSION` 和 semver 为准。
  - 将当前仓库本地 Git 身份与未发布提交作者统一为 `Geek_L <402116500@qq.com>`。
- Validation:
  - `rg` 定向扫描 `0.5.0-dev`、`0.5.0-rc1`、semver 与项目残留关键词
  - `python3 tools/cli.py version`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`

## 2026-04-18 (release notes)

- Purpose: 为 `v0.5.0-rc1` 补齐可对外引用的发布说明，并给后续 semver 版本建立固定的 release note 归档位置。
- Changes:
  - 新增 `docs/releases/README.md`，明确 release note 的目录用途、命名规则和使用边界。
  - 新增 `docs/releases/v0.5.0-rc1.md`，归档首个 semver 预发布版本的中文 release note。
  - 更新 `BUNDLE_MANIFEST.md`，把 `docs/releases/` 纳入公共 bundle 文档清单。
- Validation:
  - `git diff --check`
  - `python3 tools/cli.py selftest`

## 2026-04-18 (v0.5.0 release)

- Purpose: 将 `v0.5.0-rc1` 收口为 `workflow_bundle` 首个正式 semver 版本，并统一仓库中的正式版版本口径。
- Changes:
  - 将根目录 `VERSION`、`CHANGELOG.md` 与 `workflow/11-versioning-and-release.md` 的当前版本说明统一更新为 `0.5.0`。
  - 新增 `docs/releases/v0.5.0.md`，归档正式版 release note，并在 `docs/releases/README.md` 中登记。
  - 保留 `v0.5.0-rc1` 作为预发布历史说明与 tag，不覆盖、不移动。
- Validation:
  - `python3 tools/cli.py version`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`
  - `git diff --check`

## 2026-04-18 (v0.5.1 release)

- Purpose: 以补丁版本修复 `latest_semver_tag` 在混合 tag 仓库中的误判问题，避免回改已发布的 `v0.5.0` 正式 tag。
- Changes:
  - 修复 `tools/core/bundle_version.py`，改为先过滤 semver tag 再按语义化版本规则选择最新 tag。
  - 将当前正式版本提升为 `0.5.1`，并新增 `docs/releases/v0.5.1.md` 记录补丁版 release note。
  - 保留 `v0.5.0` 与 `v0.5.0-rc1` 作为已发布历史版本，不重写既有 tag。
- Validation:
  - `python3 tools/cli.py version`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`
  - `git diff --check`

## 2026-04-18 (v0.5.1 github release copy)

- Purpose: 为 `v0.5.1` 补充可直接粘贴到 GitHub Release 页面的简版发布文案，避免每次手工从仓库 release note 再二次整理。
- Changes:
  - 在 `docs/releases/v0.5.1.md` 中新增 “GitHub Release 页面文案” 区块，提供可直接复制的 Markdown 内容。
  - 保留原有仓库内 release note 结构，不替代详细版发布说明。
- Validation:
  - `git diff --check`

## 2026-04-18 (generic er fallback hardening)

- Purpose: 修复通用 `dbdia-er` E-R fallback 在多外键场景下生成重复关系名而导致干净 `release-build` 失败的问题，并补齐对应回归覆盖。
- Changes:
  - 更新 `tools/core/figure_assets.py`，将通用 E-R fallback 的关系命名从固定 `关联` 改为基于 `target/current table` 的稳定唯一标识，避免 `dbdia` 在多关系模型中报 `can not be defined again`。
  - 更新 `tools/core/selftest.py`，新增“多关系通用 E-R DSL 唯一性”断言，防止后续修改再次产出重复关系名。
  - 运行 `bash workflow/scripts/sync_root_compat.sh`，同步根目录兼容镜像，确保 bundle 自测与 release-preflight 不会因为镜像漂移误报失败。
- Validation:
  - `python3 -m py_compile tools/core/figure_assets.py tools/core/selftest.py`
  - `bash workflow/scripts/sync_root_compat.sh`
  - `python3 tools/cli.py selftest`
  - `python3 tools/cli.py release-build --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --output-name selftest_release.docx`
  - `python3 tools/cli.py release-verify --config /home/ub/xianyu/wurenji_work/workspace/workflow/configs/workspace.json --output-name selftest_release.docx`

## 2026-04-18 (v0.5.2 release)

- Purpose: 以补丁版本正式发布通用 `dbdia-er` E-R fallback 稳定性修复，确保远端 `main`、`VERSION`、release note 和 semver tag 口径一致。
- Changes:
  - 将当前正式版本提升为 `0.5.2`，并更新 `CHANGELOG.md` 与 `workflow/11-versioning-and-release.md` 中的当前版本说明。
  - 新增 `docs/releases/v0.5.2.md`，记录本次补丁版发布说明与 GitHub Release 页面文案。
  - 更新 `docs/releases/README.md`，将 `v0.5.2` 纳入正式 release 归档清单。
- Validation:
  - `python3 tools/cli.py version`
  - `bash workflow/scripts/check_bundle_sync.sh`
  - `python3 tools/cli.py selftest`
  - `git diff --check`
