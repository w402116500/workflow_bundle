# Draft 与 Polished 对齐说明

## 当前仓库现状

当前内置示例实例没有独立的 `draft/` 目录，直接以 `polished_v3/` 作为正文真源。

## 标准约定

若后续新项目接入时存在 `draft/` 与 `polished_v3/` 双层结构，建议遵循：

- 结构性改写先在 `draft/` 完成
- 准备发布和构建时同步到 `polished_v3/`
- 发布脚本只从 `polished_v3/` 读取正文

## 当前示例实例的处理

- 不需要再寻找 `draft/`
- 当前写作、构建、导出全部以 `polished_v3/` 为准
