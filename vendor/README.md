# Vendored Figure Runtime Notes

本目录用于存放论文工作流图件链路所依赖的第三方源码快照或运行时清单，目标是让 `tools/cli.py prepare-figures` 在不依赖系统 Graphviz `dot` 的前提下，仍能稳定生成本地确定性技术图。

## `dbdia/`

- 用途：把 Chen 风格 E-R DSL（`.dbdia`）转换为 DOT
- 当前在工作流中的角色：`dbdia-er` renderer 的后端编译/生成链
- 应纳管内容：
  - `upstream/src/main/java/**`
  - `upstream/README.md`
  - `upstream/DSL.md`
  - `upstream/LICENSE.txt`
  - `lib/antlr4-runtime-4.8-1.jar`
- 不应纳管内容：
  - `build/classes/**`
  - `build/compile.ok`
  - `build/sources.txt`

## `graphviz_wasm/`

- 用途：本地 DOT -> SVG/PNG 渲染
- 当前在工作流中的角色：`dbdia-er` 生成 DOT 后的最终渲染器
- 应纳管内容：
  - `package.json`
  - `package-lock.json`
  - `render_dot.mjs`
- 不应纳管内容：
  - `node_modules/**`

工作流在缺失 `node_modules/` 时会自动执行 `npm ci` 恢复运行时。

## `plantuml/`

- 用途：保留给后续 UML 技术图链路
- 当前状态：不是本次通用 E-R 工作流底座的必需依赖

如果当前变更目标只是通用 `dbdia` E-R 工作流，不应把 `plantuml/` 混入同一次提交。
