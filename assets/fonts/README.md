## Bundled Fonts

This directory stores fonts that are vendored into the thesis workflow so code screenshots and DOCX code blocks do not depend on host-installed fonts.

### SiYuan HeiTi / Source Han Sans SC

- Source: user-provided archive `/home/ub/thesis_materials/SiYuanHeiTi-Regular.zip`
- Included files:
  - `siyuan-heiti/SourceHanSansSC-Regular-2.otf`

This is the current default code-rendering font for the thesis workflow. Both code screenshots and DOCX code-block images prefer this bundled font first.

### Sarasa Mono SC

- Source: `https://github.com/be5invis/Sarasa-Gothic/releases/tag/v1.0.37`
- Package used: `SarasaMono-TTF-1.0.37.zip`
- Included files:
  - `sarasa-mono-sc/SarasaMonoSC-Regular.ttf`
  - `sarasa-mono-sc/SarasaMonoSC-Bold.ttf`
  - `sarasa-mono-sc/LICENSE`

The workflow renderers in `tools/core/code_evidence.py` and `tools/core/build_final_thesis_docx.py` use vendored fonts before falling back to local system fonts. `Sarasa Mono SC` remains as the secondary bundled fallback.
