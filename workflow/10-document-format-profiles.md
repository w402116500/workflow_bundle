# Document Format Profiles

## 1. 目标

本工作流把论文版式分成两层：

- `document_format`：控制基础排版稿的页面、标题、题注、页眉页脚、编号风格和代码块导出方式
- `postprocess`：控制 Windows/Word 终排输出路径，以及 WSL -> Windows 桥接参数

这样可以避免把某一个学校模板直接写死成仓库全局默认行为。

## 2. 当前内置 profile

### `legacy`

- 保持原工作流默认输出：
  - 正文固定 23 磅
  - 页边距约 `上25 / 下20 / 左25 / 右20 mm`
  - 图表编号默认 `图4.1 / 表4.1`
  - fenced code block 默认继续转成图片
  - 默认不强制写入学校页眉页脚

### `cuit-undergrad-zh`

- 面向成都信息工程大学中文本科论文模板：
  - 正文固定 20 磅
  - 页边距约 `上25 / 下25 / 左30 / 右30 mm`
  - 一级标题：三号、加粗、居中
  - 二级标题：四号、加粗、左对齐
  - 三级标题：小四、加粗、左对齐
  - 图题/表题：五号、固定 20 磅、居中
  - 页眉：`成都信息工程大学学士学位论文`
  - 页脚：`第X页 共Y页`
  - 图表公式编号：`图4-1 / 表4-1 / 式（4-1）`
  - fenced code block 默认继续转成图片，可单独切成文字代码块

## 3. 代码块导出策略

`document_format.code_blocks` 用于控制 Markdown fenced code block 的基础排版稿导出方式。

当前支持：

- `render_mode = image`
  - 兼容旧行为，把代码块渲染为 PNG 再插入 DOCX
- `render_mode = text`
  - 直接把代码块写入 DOCX，适合论文中需要可复制源码的场景

当前支持的 `text_style`：

- `plain-paper`
  - 更接近正文内嵌源码样式，无边框、无底纹、单倍行距
- `mono-block`
  - 更强调英文字母等宽显示，适合更偏工程文档的代码观感

## 4. 差异清单（当前学校模板适配重点）

当前适配前后的关键差异集中在：

| 维度 | 旧默认 | 学校模板目标 |
|---|---|---|
| 正文行距 | 23 磅 | 20 磅 |
| 页边距 | 左25/右20 | 左30/右30 |
| 标题样式 | 一级标题偏左、字号偏大 | 按三号/四号/小四分级 |
| 图表题注 | 12pt、加粗 | 五号、单独题注样式 |
| 编号风格 | `图4.1 / 表4.1` | `图4-1 / 表4-1` |
| 代码块输出 | 默认转图片 | 可按 workspace 切换为文字代码块 |
| 页眉页脚 | 无统一学校样式 | 学校页眉 + `第X页 共Y页` |
| Windows 终排入口 | 仅本机 Windows Python | 支持 WSL 触发宿主 PowerShell/Word |

## 5. 推荐配置

```json
{
  "document_format": {
    "profile": "cuit-undergrad-zh",
    "code_blocks": {
      "render_mode": "text",
      "text_style": "plain-paper"
    }
  },
  "postprocess": {
    "windows_bridge": {
      "enabled": true,
      "powershell_exe": "powershell.exe",
      "python_launcher": "py"
    }
  }
}
```

## 6. WSL 终排说明

- 在 WSL 中执行 `python3 workflow_bundle/tools/cli.py postprocess --config <workspace.json>` 时：
  - 若本地 Python 缺少 `win32com`，CLI 会自动尝试 Windows bridge
  - 桥接链路会：
    - 用 `wslpath -w` 把输入/输出路径转成 Windows 可访问路径
    - 调用宿主 `powershell.exe`
    - 用 Windows Python 执行 `tools/windows/postprocess_word_format.py`
- 一次性 PowerShell 调用会预置 UTF-8 控制台编码，避免中文路径、日志和学校模板文案乱码
