# Historical Status Audit (Superseded)

日期：2026-03-31

本文件仅保留为一份历史标记，用来说明这套论文工作流曾经从“模板骨架阶段”演进到“可持续写作与发布”的状态。
它不再代表当前远端仓库的实时状态，也不应作为新对话接手时的默认阅读材料。

## 当前应如何判断真实状态

对任意目标 workspace，应优先使用以下正式入口判断当前状态：

- `python3 workflow_bundle/tools/cli.py resume --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py release-preflight --config <workspace.json>`
- `python3 workflow_bundle/tools/cli.py selftest`

## 仍然有效的历史结论

- `polished_v3/` 是论文正文真源，`docs/` 更偏向材料、写作状态与审计产物。
- `workflow_signature_status` 与 workspace 本地 workflow 资产同步状态应通过正式命令判断，而不是依赖旧 handoff 或旧审计文本推断。
- Linux 发布链与 Windows 终排链应分开验证，不能把 Linux 交付版误称为最终 Word 终稿。

## 归档说明

- 详细的项目级审计过程与机器路径已从公共 bundle 文档中移除，避免把远端仓库绑定到某一篇具体论文或某一台开发机器。
- 如需了解当前公共仓库的文档归档策略，请阅读 `docs/archive/README.md`。
