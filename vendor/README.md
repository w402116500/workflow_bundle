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

- 用途：把 `.puml` 源文件渲染为 UML / 业务流程 SVG，并进一步转换为论文使用的 PNG
- 当前在工作流中的角色：`plantuml` renderer 的运行时，供 `prepare-figures` 读取 `plantuml_figure_specs` 时使用
- 应纳管内容：
  - `lib/plantuml-lgpl-1.2026.2.jar`
  - `lib/plantuml-lgpl-1.2025.8.jar`（兼容保留）
- 运行要求：
  - 需要本机可用 Java Runtime 11+；工作流会自动优先选择满足版本要求的 `java`
  - 不要求系统额外安装 Graphviz，推荐在 `.puml` 源中显式使用 `!pragma layout smetana` 以获得更稳定的本地布局
