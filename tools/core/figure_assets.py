from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from core.ai_image_generation import ai_override_blocking_entries, ai_override_map
from core.page_screenshot_assets import stage_chapter5_test_screenshots
from core.project_common import load_workspace_context, make_relative, material_output_paths, read_json, write_json


THIS_ROOT = Path(__file__).resolve().parents[2]
if THIS_ROOT.name == "workflow_bundle":
    PRIMARY_WORKFLOW_ROOT = THIS_ROOT
else:
    PRIMARY_WORKFLOW_ROOT = THIS_ROOT / "workflow_bundle" if (THIS_ROOT / "workflow_bundle").exists() else THIS_ROOT

VENDOR_ROOT = PRIMARY_WORKFLOW_ROOT / "vendor"
DBDIA_VENDOR_ROOT = VENDOR_ROOT / "dbdia"
DBDIA_UPSTREAM_ROOT = DBDIA_VENDOR_ROOT / "upstream"
DBDIA_SOURCE_ROOT = DBDIA_UPSTREAM_ROOT / "src" / "main" / "java"
DBDIA_BUILD_ROOT = DBDIA_VENDOR_ROOT / "build"
DBDIA_CLASSES_DIR = DBDIA_BUILD_ROOT / "classes"
DBDIA_COMPILE_STAMP = DBDIA_BUILD_ROOT / "compile.ok"
DBDIA_ANTLR_RUNTIME_VERSION = "4.8-1"
DBDIA_ANTLR_RUNTIME_JAR = DBDIA_VENDOR_ROOT / "lib" / f"antlr4-runtime-{DBDIA_ANTLR_RUNTIME_VERSION}.jar"
GRAPHVIZ_WASM_VENDOR_ROOT = VENDOR_ROOT / "graphviz_wasm"
GRAPHVIZ_RENDER_SCRIPT = GRAPHVIZ_WASM_VENDOR_ROOT / "render_dot.mjs"

MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)\n```", re.S)
HEADING_L2_RE = re.compile(r"^##\s+5\.(?P<num>\d+)\s+(?P<title>.+?)\s*$")
HEADING_L3_RE = re.compile(r"^###\s+5\.\d+\.\d+\s+(?P<title>.+?)\s*$")
FUNCTION_STRUCTURE_RENDERER_VERSION = "v2-monochrome-module-tree"
DBDIA_ER_RENDERER_VERSION = "v1-generic-dbdia-chen-vendor-vizjs"
SVG_RENDER_WIDTH_PX = 1665


@dataclass(frozen=True)
class MermaidBlock:
    kind: str
    code: str
    source_path: Path


@dataclass(frozen=True)
class FigureSpec:
    figure_no: str
    caption: str
    output_name: str
    code: str
    renderer: str = "mermaid"
    source_paths: tuple[Path, ...] = ()


def _iter_manifest_documents(manifest: dict[str, Any]) -> list[Path]:
    project_root = Path(manifest["project_root"]).resolve()
    seen: set[Path] = set()
    docs: list[Path] = []
    for bucket in ("design", "requirements", "writing_rules", "references"):
        for rel in manifest.get("document_paths", {}).get(bucket, []) or []:
            path = (project_root / rel).resolve()
            if path.exists() and path not in seen:
                seen.add(path)
                docs.append(path)
    return docs


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_mermaid_blocks(path: Path) -> list[MermaidBlock]:
    blocks: list[MermaidBlock] = []
    text = _read_text(path)
    for raw in MERMAID_BLOCK_RE.findall(text):
        code = raw.strip()
        if not code:
            continue
        first = next((line.strip() for line in code.splitlines() if line.strip()), "")
        kind = first.split(maxsplit=1)[0].lower() if first else ""
        blocks.append(MermaidBlock(kind=kind, code=code, source_path=path))
    return blocks


def _pick_block(blocks: list[MermaidBlock], kind: str) -> MermaidBlock | None:
    for block in blocks:
        if block.kind == kind:
            return block
    return None


def _pick_doc_by_keyword(paths: list[Path], keyword: str) -> Path | None:
    for path in paths:
        if keyword in path.name:
            return path
    return None


def _slug(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "_", text).strip("_").lower() or "node"


def _shorten_label(text: str) -> str:
    label = re.sub(r"^第?\d+(\.\d+)*\s*", "", text).strip()
    label = re.sub(r"模块实现$", "", label).strip()
    label = re.sub(r"实现$", "", label).strip()
    return label


def _root_system_label(project_title: str) -> str:
    label = re.sub(r"(的)?设计与实现$", "", project_title).strip()
    return label or "系统功能结构"


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/arphic/ukai.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    parts = [text[i : i + width] for i in range(0, len(text), width)]
    return "\n".join(parts)


def _center_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.ImageFont, fill: tuple[int, int, int]) -> None:
    x1, y1, x2, y2 = box
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=6, align="center")
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x1 + (x2 - x1 - tw) / 2
    ty = y1 + (y2 - y1 - th) / 2
    draw.multiline_text((tx, ty), text, font=font, fill=fill, spacing=6, align="center")


def _rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int = 18) -> None:
    draw.rounded_rectangle(box, radius=radius, outline=(203, 213, 225), fill=(248, 250, 252), width=2)


def _arrow(
    draw: ImageDraw.ImageDraw,
    p1: tuple[int, int],
    p2: tuple[int, int],
    *,
    color: tuple[int, int, int] = (0, 0, 0),
    width: int = 2,
    head: int = 9,
) -> None:
    x1, y1 = p1
    x2, y2 = p2
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    a1 = angle + math.pi * 0.85
    a2 = angle - math.pi * 0.85
    p3 = (x2 + head * math.cos(a1), y2 + head * math.sin(a1))
    p4 = (x2 + head * math.cos(a2), y2 + head * math.sin(a2))
    draw.polygon([p2, p3, p4], fill=color)


def _write_text_if_changed(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            if path.read_text(encoding="utf-8") == text:
                return
        except Exception:
            pass
    path.write_text(text, encoding="utf-8")


def _run_checked(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, label: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()
        details = "\n".join(part for part in [stdout, stderr] if part)
        raise RuntimeError(f"{label} failed with exit code {completed.returncode}: {details or command}")
    return completed


def _resolve_java_tool(name: str) -> str:
    candidate = shutil.which(name)
    if candidate:
        return candidate
    fallback = Path("/usr/local/jdk1.8.0_201/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required Java tool not found: {name}")


def _preferred_dbdia_font_name() -> str:
    candidates = [
        ("WenQuanYi Zen Hei", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
        ("Noto Sans CJK SC", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        ("Microsoft YaHei", "/usr/share/fonts/truetype/msyh/msyh.ttc"),
        ("SimHei", "/usr/share/fonts/truetype/arphic/ukai.ttc"),
        ("DejaVu Sans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for font_name, font_path in candidates:
        if Path(font_path).exists():
            return font_name
    return "DejaVu Sans"


def _figure_no_slug(figure_no: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "-", str(figure_no)).strip("-").lower() or "figure"


def _resolve_workspace_path(workspace_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    return candidate.resolve() if candidate.is_absolute() else (workspace_root / candidate).resolve()


def _default_er_output_name(figure_no: str) -> str:
    return f"generated/fig{_figure_no_slug(figure_no)}-er-diagram.png"


def _build_configured_er_specs(config: dict[str, Any], workspace_root: Path) -> dict[str, FigureSpec]:
    raw_specs = config.get("er_figure_specs") or {}
    if not isinstance(raw_specs, dict):
        raise RuntimeError("er_figure_specs must be an object keyed by figure number")

    existing_figure_map = config.get("figure_map") or {}
    explicit_specs: dict[str, FigureSpec] = {}
    for raw_figure_no, raw_spec in raw_specs.items():
        figure_no = str(raw_figure_no).strip()
        if not figure_no:
            raise RuntimeError("er_figure_specs contains an empty figure number key")
        if not isinstance(raw_spec, dict):
            raise RuntimeError(f"er_figure_specs.{figure_no} must be an object")
        if raw_spec.get("enabled", True) is False:
            continue

        source_rel = str(raw_spec.get("source_path") or "").strip()
        if not source_rel:
            raise RuntimeError(f"er_figure_specs.{figure_no}.source_path is required")
        source_path = _resolve_workspace_path(workspace_root, source_rel)
        if not source_path.exists():
            raise RuntimeError(f"er_figure_specs.{figure_no}.source_path not found: {source_path}")

        caption = str(raw_spec.get("caption") or "").strip()
        if not caption:
            existing_cfg = existing_figure_map.get(figure_no, {}) if isinstance(existing_figure_map.get(figure_no), dict) else {}
            caption = str(existing_cfg.get("caption") or "").strip()
        if not caption:
            raise RuntimeError(f"er_figure_specs.{figure_no}.caption is required")

        output_name = str(raw_spec.get("output_name") or "").strip() or _default_er_output_name(figure_no)
        if Path(output_name).is_absolute():
            raise RuntimeError(f"er_figure_specs.{figure_no}.output_name must be relative to build.diagram_dir")

        explicit_specs[figure_no] = FigureSpec(
            figure_no=figure_no,
            caption=caption,
            output_name=output_name,
            code=source_path.read_text(encoding="utf-8", errors="replace"),
            renderer="dbdia-er",
            source_paths=(source_path,),
        )
    return explicit_specs


def _merge_explicit_specs(default_specs: list[FigureSpec], explicit_specs: dict[str, FigureSpec]) -> list[FigureSpec]:
    if not explicit_specs:
        return default_specs

    merged: list[FigureSpec] = []
    replaced: set[str] = set()
    for spec in default_specs:
        override = explicit_specs.get(spec.figure_no)
        if override is not None:
            merged.append(override)
            replaced.add(spec.figure_no)
        else:
            merged.append(spec)

    for figure_no, spec in explicit_specs.items():
        if figure_no not in replaced:
            merged.append(spec)
    return merged


def _extract_chapter5_modules(chapter_path: Path) -> list[tuple[str, list[str]]]:
    modules: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_children: list[str] = []
    for line in _read_text(chapter_path).splitlines():
        match_l2 = HEADING_L2_RE.match(line.strip())
        if match_l2:
            number = int(match_l2.group("num"))
            if current_title and current_children:
                modules.append((current_title, current_children))
            current_title = None
            current_children = []
            if 2 <= number <= 6:
                current_title = _shorten_label(match_l2.group("title"))
            continue
        match_l3 = HEADING_L3_RE.match(line.strip())
        if match_l3 and current_title:
            title = _shorten_label(match_l3.group("title"))
            if title and "关键代码截图" not in title:
                current_children.append(title)
    if current_title and current_children:
        modules.append((current_title, current_children))
    return modules


def _build_function_structure_mermaid(project_title: str, chapter5_path: Path) -> str:
    modules = _extract_chapter5_modules(chapter5_path)
    root_label = project_title.replace("设计与实现", "").strip() or "系统功能结构"
    lines = ["graph TD", f'    ROOT["{root_label}"]']
    if not modules:
        lines.extend(
            [
                '    ROOT --> M1["用户与权限管理"]',
                '    ROOT --> M2["批次与主档管理"]',
                '    ROOT --> M3["生产流转记录管理"]',
                '    ROOT --> M4["溯源码与追溯查询"]',
                '    ROOT --> M5["监管预警与审计分析"]',
            ]
        )
        return "\n".join(lines)

    for idx, (module, children) in enumerate(modules, start=1):
        module_id = f"M{idx}"
        lines.append(f'    ROOT --> {module_id}["{module}"]')
        for child_idx, child in enumerate(children, start=1):
            child_id = f"{module_id}_{child_idx}_{_slug(child)}"
            lines.append(f'    {module_id} --> {child_id}["{child}"]')
    return "\n".join(lines)


def _build_record_flow_mermaid() -> str:
    return "\n".join(
        [
            "flowchart TD",
            '    A["茶农创建批次并录入农事记录"] --> B["加工厂提交加工记录"]',
            '    B --> C["质检机构提交质检报告"]',
            '    C --> D{"质检结果是否合格"}',
            '    D -- "否" --> E["生成质量预警并冻结批次"]',
            '    D -- "是" --> F["物流商提交仓储与物流记录"]',
            '    F --> G["经销商提交销售记录"]',
            '    G --> H["系统推进批次阶段并更新链上状态"]',
        ]
    )


def _build_batch_init_flow_mermaid() -> str:
    return "\n".join(
        [
            "flowchart TD",
            '    A["开始"] --> B["录入批次基础信息"]',
            '    B --> C{"信息是否完整"}',
            '    C -- "否" --> D["提示补全后重新提交"]',
            '    C -- "是" --> E["生成批次主档摘要"]',
            '    E --> F["调用 CreateBatch 提交链上存证"]',
            '    F --> G{"上链是否成功"}',
            '    G -- "否" --> H["返回错误并记录失败原因"]',
            '    G -- "是" --> I["写入批次主档与初始状态"]',
            '    I --> J["返回批次建档结果"]',
        ]
    )


def _build_trace_query_mermaid() -> str:
    return "\n".join(
        [
            "flowchart TD",
            '    A["批次建档完成"] --> B["生成唯一溯源码"]',
            '    B --> C["写入 tea_trace_code 表"]',
            '    C --> D["调用 BindTraceCode 完成链上绑定"]',
            '    D --> E["生成二维码并提供查询入口"]',
            '    E --> F["消费者扫码或输入溯源码"]',
            '    F --> G["后端聚合批次与阶段记录"]',
            '    G --> H["查询链上绑定信息与历史状态"]',
            '    H --> I["返回追溯结果与防伪状态"]',
        ]
    )


def _render_mermaid_png(code: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "curl",
            "-fsSL",
            "--retry",
            "4",
            "--retry-all-errors",
            "--retry-delay",
            "2",
            "--max-time",
            "120",
            "-X",
            "POST",
            "-H",
            "Content-Type: text/plain",
            "-H",
            "Accept: image/png",
            "-H",
            "User-Agent: thesis-materials-workflow/1.0",
            "--data-binary",
            "@-",
            "https://kroki.io/mermaid/png",
            "-o",
            str(output_path),
        ],
        input=code.encode("utf-8"),
        check=False,
        capture_output=True,
        timeout=120,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"failed to render mermaid via kroki: {stderr or completed.returncode}")
    with Image.open(output_path) as image:
        if image.mode == "RGBA":
            canvas = Image.new("RGB", image.size, (255, 255, 255))
            canvas.paste(image, mask=image.getchannel("A"))
            canvas.save(output_path)
        else:
            image.convert("RGB").save(output_path)


def _render_function_structure_png(project_title: str, chapter5_path: Path, output_path: Path) -> None:
    modules = _extract_chapter5_modules(chapter5_path)
    if not modules:
        raise RuntimeError(f"unable to derive chapter 5 module structure from {chapter5_path}")

    module_count = len(modules)
    column_width = 270
    module_box_height = 82
    child_box_height = 54
    module_gap = 40
    child_gap = 14
    left_margin = 52
    top_margin = 34
    root_box_height = 80
    root_box_width = 720

    content_width = left_margin * 2 + module_count * column_width + max(module_count - 1, 0) * module_gap
    max_children = max(len(children) for _, children in modules)
    canvas_width = max(content_width, root_box_width + 160, 1680)
    canvas_height = max(
        820,
        top_margin + root_box_height + 110 + module_box_height + 40 + max_children * (child_box_height + child_gap) + 80,
    )

    root_box = (
        (canvas_width - root_box_width) // 2,
        top_margin,
        (canvas_width + root_box_width) // 2,
        top_margin + root_box_height,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    root_font = _load_font(28)
    module_font = _load_font(20)
    child_font = _load_font(17)

    border_color = (0, 0, 0)
    text_color = (0, 0, 0)
    line_color = (0, 0, 0)

    draw.rounded_rectangle(root_box, radius=10, outline=border_color, fill=(255, 255, 255), width=2)
    _center_text(draw, root_box, _wrap_text(_root_system_label(project_title), 18), root_font, text_color)

    module_y = root_box[3] + 96
    module_bottom = module_y + module_box_height
    child_start_y = module_bottom + 34
    branch_bus_y = root_box[3] + 44
    root_center_x = (root_box[0] + root_box[2]) // 2

    module_boxes: list[tuple[int, int, int, int]] = []
    for idx in range(module_count):
        x1 = (canvas_width - content_width) // 2 + idx * (column_width + module_gap)
        module_boxes.append((x1, module_y, x1 + column_width, module_bottom))

    draw.line((root_center_x, root_box[3], root_center_x, branch_bus_y), fill=line_color, width=2)
    draw.line(
        (
            (module_boxes[0][0] + module_boxes[0][2]) // 2,
            branch_bus_y,
            (module_boxes[-1][0] + module_boxes[-1][2]) // 2,
            branch_bus_y,
        ),
        fill=line_color,
        width=2,
    )

    for module_box, (module, children) in zip(module_boxes, modules):
        draw.rounded_rectangle(module_box, radius=8, outline=border_color, fill=(255, 255, 255), width=2)
        _center_text(draw, module_box, _wrap_text(module, 10), module_font, text_color)

        module_center_x = (module_box[0] + module_box[2]) // 2
        _arrow(draw, (module_center_x, branch_bus_y), (module_center_x, module_box[1]))

        child_box_width = column_width - 74
        child_left = module_box[0] + (column_width - child_box_width) // 2 + 12
        spine_x = child_left - 18
        child_centers: list[int] = []

        for child_idx, child in enumerate(children):
            cy1 = child_start_y + child_idx * (child_box_height + child_gap)
            child_box = (child_left, cy1, child_left + child_box_width, cy1 + child_box_height)
            draw.rounded_rectangle(child_box, radius=8, outline=border_color, fill=(255, 255, 255), width=2)
            _center_text(draw, child_box, _wrap_text(child, 12), child_font, text_color)
            center_y = (child_box[1] + child_box[3]) // 2
            child_centers.append(center_y)
            _arrow(draw, (spine_x, center_y), (child_box[0], center_y))

        if child_centers:
            top_spine_y = child_centers[0]
            bottom_spine_y = child_centers[-1]
            draw.line((module_center_x, module_box[3], module_center_x, top_spine_y), fill=line_color, width=2)
            draw.line((module_center_x, top_spine_y, spine_x, top_spine_y), fill=line_color, width=2)
            draw.line((spine_x, top_spine_y, spine_x, bottom_spine_y), fill=line_color, width=2)

    image.save(output_path)


def _ensure_dbdia_runtime() -> tuple[Path, Path]:
    if not DBDIA_SOURCE_ROOT.exists():
        raise RuntimeError(f"dbdia vendor source is missing: {DBDIA_SOURCE_ROOT}")
    if not DBDIA_ANTLR_RUNTIME_JAR.exists():
        raise RuntimeError(f"antlr runtime jar is missing: {DBDIA_ANTLR_RUNTIME_JAR}")

    sources = sorted(path for path in DBDIA_SOURCE_ROOT.rglob("*.java") if not path.name.endswith("Test.java"))
    if not sources:
        raise RuntimeError(f"no dbdia Java sources found under {DBDIA_SOURCE_ROOT}")

    needs_compile = not DBDIA_COMPILE_STAMP.exists() or not DBDIA_CLASSES_DIR.exists()
    if not needs_compile:
        stamp_mtime = DBDIA_COMPILE_STAMP.stat().st_mtime
        latest_input = max([path.stat().st_mtime for path in sources] + [DBDIA_ANTLR_RUNTIME_JAR.stat().st_mtime])
        needs_compile = latest_input > stamp_mtime

    if needs_compile:
        if DBDIA_CLASSES_DIR.exists():
            shutil.rmtree(DBDIA_CLASSES_DIR)
        DBDIA_CLASSES_DIR.mkdir(parents=True, exist_ok=True)
        javac = _resolve_java_tool("javac")
        source_list_path = DBDIA_BUILD_ROOT / "sources.txt"
        source_list_path.parent.mkdir(parents=True, exist_ok=True)
        source_list_path.write_text("\n".join(str(path) for path in sources) + "\n", encoding="utf-8")
        _run_checked(
            [
                javac,
                "-encoding",
                "UTF-8",
                "-cp",
                str(DBDIA_ANTLR_RUNTIME_JAR),
                "-d",
                str(DBDIA_CLASSES_DIR),
                f"@{source_list_path}",
            ],
            label="dbdia javac compile",
        )
        DBDIA_COMPILE_STAMP.write_text(_now_iso() + "\n", encoding="utf-8")

    return DBDIA_CLASSES_DIR, DBDIA_ANTLR_RUNTIME_JAR


def _ensure_graphviz_wasm_runtime() -> None:
    if not GRAPHVIZ_RENDER_SCRIPT.exists():
        raise RuntimeError(f"graphviz render script is missing: {GRAPHVIZ_RENDER_SCRIPT}")
    lockfile = GRAPHVIZ_WASM_VENDOR_ROOT / "package-lock.json"
    if not lockfile.exists():
        raise RuntimeError(f"graphviz wasm lockfile is missing: {lockfile}")
    viz_module = GRAPHVIZ_WASM_VENDOR_ROOT / "node_modules" / "@viz-js" / "viz"
    if viz_module.exists():
        return
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("npm is required to install the local Graphviz WASM renderer")
    _run_checked(
        [npm, "ci", "--silent", "--no-fund", "--no-audit"],
        cwd=GRAPHVIZ_WASM_VENDOR_ROOT,
        label="graphviz wasm npm ci",
    )


def _patch_dbdia_dot(dot_text: str) -> str:
    replacements = {
        '  layout="dot"\n': '  layout="dot"\n  nodesep="0.32"\n  ranksep="0.56"\n  pad="0.06"\n  margin="0.03"\n',
        '  node [\n': '  node [\n    margin="0.10,0.06"\n',
    }
    patched = dot_text
    for source, target in replacements.items():
        if source in patched:
            patched = patched.replace(source, target, 1)
    return patched


def _render_dbdia_er_diagram_png(spec: FigureSpec, output_path: Path, workspace_root: Path) -> None:
    classes_dir, antlr_jar = _ensure_dbdia_runtime()
    _ensure_graphviz_wasm_runtime()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    stem = Path(spec.output_name).stem
    sidecar_dir = workspace_root / "docs" / "images" / "generated_src"
    dsl_path = sidecar_dir / f"{stem}.dbdia"
    dot_path = sidecar_dir / f"{stem}.dot"
    svg_path = sidecar_dir / f"{stem}.svg"

    dsl_code = spec.code.strip() + "\n"
    _write_text_if_changed(dsl_path, dsl_code)

    java = _resolve_java_tool("java")
    classpath = f"{classes_dir}:{antlr_jar}"
    _run_checked(
        [
            java,
            "-cp",
            classpath,
            "dbdia.Main",
            "-info=_",
            "-format=none",
            f"-fontname={_preferred_dbdia_font_name()}",
            "-fontsize=16",
            "-rankdir=LR",
            "-splines=line",
            "-layout=dot",
            "-color=black",
            "-fillcolor=white",
            "-fontcolor=black",
            "-style=filled",
            "er",
            str(dsl_path),
            str(dot_path),
        ],
        label="dbdia er dot generation",
    )

    patched_dot = _patch_dbdia_dot(dot_path.read_text(encoding="utf-8"))
    _write_text_if_changed(dot_path, patched_dot)

    _run_checked(
        ["node", str(GRAPHVIZ_RENDER_SCRIPT), str(dot_path), str(svg_path), "dot"],
        cwd=GRAPHVIZ_WASM_VENDOR_ROOT,
        label="graphviz wasm svg render",
    )

    cairosvg.svg2png(url=str(svg_path), write_to=str(output_path), output_width=SVG_RENDER_WIDTH_PX)
    with Image.open(output_path) as image:
        if image.mode == "RGBA":
            canvas = Image.new("RGB", image.size, (255, 255, 255))
            canvas.paste(image, mask=image.getchannel("A"))
            canvas.save(output_path)
        else:
            image.convert("RGB").save(output_path)


def _build_specs(config: dict[str, Any], manifest: dict[str, Any], workspace_root: Path) -> list[FigureSpec]:
    docs = _iter_manifest_documents(manifest)
    overview_doc = _pick_doc_by_keyword(docs, "总体项目文档")
    database_doc = _pick_doc_by_keyword(docs, "数据库设计文档")
    explicit_er_specs = _build_configured_er_specs(config, workspace_root)

    overview_blocks = _extract_mermaid_blocks(overview_doc) if overview_doc else []
    database_blocks = _extract_mermaid_blocks(database_doc) if database_doc else []

    architecture = _pick_block(overview_blocks, "graph")
    sequence = _pick_block(overview_blocks, "sequencediagram")
    flowchart = _pick_block(overview_blocks, "flowchart")
    er = _pick_block(database_blocks, "erdiagram") or _pick_block(overview_blocks, "erdiagram")

    chapter5_path = workspace_root / config.get("build", {}).get("input_dir", "polished_v3") / "05-系统实现.md"
    project_title = config.get("metadata", {}).get("title") or manifest.get("title", "系统功能结构图")

    specs: list[FigureSpec] = []
    if architecture:
        specs.append(
            FigureSpec(
                "4.1",
                "图4.1 系统总体架构图",
                "generated/fig4-1-architecture.png",
                architecture.code,
                source_paths=(architecture.source_path,),
            )
        )
    if er:
        specs.append(
            FigureSpec(
                "4.2",
                "图4.2 数据库E-R图",
                "generated/fig4-2-er-diagram.png",
                er.code,
                source_paths=(er.source_path,),
            )
        )
    specs.append(
        FigureSpec(
            "4.3",
            "图4.3 核心业务流程图一",
            "generated/fig4-3-batch-flow.png",
            _build_batch_init_flow_mermaid(),
            source_paths=(sequence.source_path,) if sequence else (),
        )
    )
    specs.append(FigureSpec("4.4", "图4.4 核心业务流程图二", "generated/fig4-4-record-flow.png", _build_record_flow_mermaid()))
    specs.append(FigureSpec("4.5", "图4.5 核心业务流程图三", "generated/fig4-5-trace-flow.png", _build_trace_query_mermaid()))
    specs.append(
        FigureSpec(
            "5.1",
            "图5.1 系统功能结构图",
            "generated/fig5-1-function-structure.png",
            "",
            renderer="pillow",
            source_paths=(chapter5_path,),
        )
    )
    if flowchart and not any(spec.figure_no == "4.4" and spec.code == flowchart.code for spec in specs):
        # Keep the original end-to-end business flow as an auxiliary fallback for future projects.
        pass
    return _merge_explicit_specs(specs, explicit_er_specs)


def _figure_spec_hash(spec: FigureSpec, config: dict[str, Any], manifest: dict[str, Any], workspace_root: Path) -> str:
    payload: dict[str, Any] = {
        "figure_no": spec.figure_no,
        "caption": spec.caption,
        "output_name": spec.output_name,
        "renderer": spec.renderer,
    }
    if spec.renderer == "pillow":
        chapter5_path = workspace_root / config.get("build", {}).get("input_dir", "polished_v3") / "05-系统实现.md"
        project_title = config.get("metadata", {}).get("title") or manifest.get("title", "系统功能结构图")
        payload["renderer_version"] = FUNCTION_STRUCTURE_RENDERER_VERSION
        payload["project_title"] = project_title
        payload["modules"] = _extract_chapter5_modules(chapter5_path) if chapter5_path.exists() else []
    elif spec.renderer == "dbdia-er":
        payload["renderer_version"] = DBDIA_ER_RENDERER_VERSION
        payload["project_title"] = config.get("metadata", {}).get("title") or manifest.get("title", "系统图")
        payload["font_name"] = _preferred_dbdia_font_name()
        payload["code"] = spec.code
    else:
        payload["code"] = spec.code
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()[:16]


def _can_adopt_existing_output(spec: FigureSpec, output_path: Path) -> bool:
    if not output_path.exists():
        return False
    if not spec.source_paths:
        return True
    output_mtime = output_path.stat().st_mtime
    for source_path in spec.source_paths:
        if source_path.exists() and source_path.stat().st_mtime > output_mtime:
            return False
    return True


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _load_chapter5_packet_assets(workspace_root: Path) -> list[dict[str, Any]]:
    packet_path = workspace_root / "docs" / "writing" / "chapter_packets" / "05-系统实现.json"
    if not packet_path.exists():
        return []
    packet = read_json(packet_path)
    return list(packet.get("chapter_assets", []))


def run_prepare_figures(config_path: Path) -> dict[str, Any]:
    context = load_workspace_context(config_path)
    config = context["config"]
    manifest = context["manifest"]
    workspace_root = context["workspace_root"]

    override_blockers = ai_override_blocking_entries(context["config_path"])
    if override_blockers:
        rendered = ", ".join(f"{item['figure_no']} -> {item['expected_path']}" for item in override_blockers)
        raise RuntimeError(f"missing AI override figure assets; run prepare-ai-figures first: {rendered}")

    diagram_dir = workspace_root / config.get("build", {}).get("diagram_dir", "docs/images")
    specs = _build_specs(config, manifest, workspace_root)
    if not specs:
        raise RuntimeError("no figure specs could be generated for this workspace")

    generated: list[dict[str, str]] = []
    figure_map = dict(config.get("figure_map") or {})
    overrides = ai_override_map(config, workspace_root)
    for spec in specs:
        output_path = diagram_dir / spec.output_name
        spec_hash = _figure_spec_hash(spec, config, manifest, workspace_root)
        existing_cfg = figure_map.get(spec.figure_no) if isinstance(figure_map.get(spec.figure_no), dict) else {}
        relative_output_path = make_relative(output_path, workspace_root)
        status = "rendered"

        override = overrides.get(spec.figure_no)
        if override:
            figure_map[spec.figure_no] = {
                "caption": override["caption"],
                "path": override["path"],
                "renderer": override["renderer"],
                "spec_hash": override["spec_hash"],
            }
            generated.append(
                {
                    "figure_no": spec.figure_no,
                    "caption": override["caption"],
                    "path": str(override["output_path"]),
                    "status": "preserved-ai",
                }
            )
            continue

        if output_path.exists() and existing_cfg.get("spec_hash") == spec_hash and existing_cfg.get("path") == relative_output_path:
            status = "cached"
        elif output_path.exists() and _can_adopt_existing_output(spec, output_path):
            status = "adopted"
        else:
            if spec.renderer == "pillow":
                chapter5_path = workspace_root / config.get("build", {}).get("input_dir", "polished_v3") / "05-系统实现.md"
                project_title = config.get("metadata", {}).get("title") or manifest.get("title", "系统功能结构图")
                _render_function_structure_png(project_title, chapter5_path, output_path)
            elif spec.renderer == "dbdia-er":
                _render_dbdia_er_diagram_png(spec, output_path, workspace_root)
            else:
                _render_mermaid_png(spec.code, output_path)
        figure_map[spec.figure_no] = {
            "caption": spec.caption,
            "path": relative_output_path,
            "renderer": spec.renderer,
            "spec_hash": spec_hash,
        }
        generated.append(
            {
                "figure_no": spec.figure_no,
                "caption": spec.caption,
                "path": str(output_path),
                "status": status,
            }
        )

    staged_chapter5_screenshots = stage_chapter5_test_screenshots(
        workspace_root,
        Path(manifest["project_root"]).resolve(),
        _load_chapter5_packet_assets(workspace_root),
    )

    config["figure_map"] = figure_map
    write_json(context["config_path"], config)

    output_dir = workspace_root / config.get("build", {}).get("output_dir", "word_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_prepare_summary = {
        "generated_at": _now_iso(),
        "config_path": str(context["config_path"]),
        "diagram_dir": str(diagram_dir),
        "generated_figures": generated,
        "staged_chapter5_screenshots": staged_chapter5_screenshots,
    }
    write_json(output_dir / "figure_prepare_summary.json", figure_prepare_summary)

    materials = material_output_paths(config, workspace_root)
    result = {
        "config_path": str(context["config_path"]),
        "diagram_dir": str(diagram_dir),
        "generated_figures": generated,
        "staged_chapter5_screenshots": staged_chapter5_screenshots,
        "material_pack_json": str(materials["material_pack_json"]),
        "figure_prepare_summary_json": str(output_dir / "figure_prepare_summary.json"),
    }
    return result
