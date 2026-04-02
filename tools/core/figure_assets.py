from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from core.page_screenshot_assets import stage_chapter5_test_screenshots
from core.project_common import load_workspace_context, make_relative, material_output_paths, read_json, write_json


MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)\n```", re.S)
HEADING_L2_RE = re.compile(r"^##\s+5\.(?P<num>\d+)\s+(?P<title>.+?)\s*$")
HEADING_L3_RE = re.compile(r"^###\s+5\.\d+\.\d+\s+(?P<title>.+?)\s*$")


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


def _arrow(draw: ImageDraw.ImageDraw, p1: tuple[int, int], p2: tuple[int, int]) -> None:
    x1, y1 = p1
    x2, y2 = p2
    draw.line((x1, y1, x2, y2), fill=(100, 116, 139), width=3)
    head = 10
    angle = math.atan2(y2 - y1, x2 - x1)
    a1 = angle + math.pi * 0.85
    a2 = angle - math.pi * 0.85
    p3 = (x2 + head * math.cos(a1), y2 + head * math.sin(a1))
    p4 = (x2 + head * math.cos(a2), y2 + head * math.sin(a2))
    draw.polygon([p2, p3, p4], fill=(100, 116, 139))


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

    column_width = 320
    module_box_height = 70
    child_box_height = 58
    module_gap = 28
    child_gap = 16
    top_margin = 50
    left_margin = 48
    root_box = (540, 30, 1340, 110)
    width = left_margin * 2 + len(modules) * column_width + max(len(modules) - 1, 0) * module_gap
    max_children = max(len(children) for _, children in modules)
    height = top_margin + 140 + module_box_height + 40 + max_children * (child_box_height + child_gap) + 80

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (max(width, 1880), max(height, 880)), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    title_font = _load_font(26)
    module_font = _load_font(22)
    child_font = _load_font(18)

    draw.rounded_rectangle(root_box, radius=20, outline=(96, 165, 250), fill=(239, 246, 255), width=3)
    _center_text(draw, root_box, _wrap_text(project_title, 18), title_font, (15, 23, 42))

    module_y = 180
    child_y = 300
    for idx, (module, children) in enumerate(modules):
        x1 = left_margin + idx * (column_width + module_gap)
        module_box = (x1, module_y, x1 + column_width, module_y + module_box_height)
        _rounded_rect(draw, module_box)
        _center_text(draw, module_box, _wrap_text(module, 10), module_font, (15, 23, 42))

        module_center_x = (module_box[0] + module_box[2]) // 2
        _arrow(draw, ((root_box[0] + root_box[2]) // 2, root_box[3]), (module_center_x, module_box[1]))

        for child_idx, child in enumerate(children):
            cy1 = child_y + child_idx * (child_box_height + child_gap)
            child_box = (x1 + 10, cy1, x1 + column_width - 10, cy1 + child_box_height)
            draw.rounded_rectangle(child_box, radius=14, outline=(226, 232, 240), fill=(255, 255, 255), width=2)
            _center_text(draw, child_box, _wrap_text(child, 12), child_font, (51, 65, 85))
            _arrow(draw, (module_center_x, module_box[3]), (module_center_x, child_box[1]))

    image.save(output_path)


def _build_specs(config: dict[str, Any], manifest: dict[str, Any], workspace_root: Path) -> list[FigureSpec]:
    docs = _iter_manifest_documents(manifest)
    overview_doc = _pick_doc_by_keyword(docs, "总体项目文档")
    database_doc = _pick_doc_by_keyword(docs, "数据库设计文档")

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
    if sequence:
        specs.append(
            FigureSpec(
                "4.3",
                "图4.3 核心业务流程图一",
                "generated/fig4-3-batch-sequence.png",
                sequence.code,
                source_paths=(sequence.source_path,),
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
    return specs


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
        payload["project_title"] = project_title
        payload["modules"] = _extract_chapter5_modules(chapter5_path) if chapter5_path.exists() else []
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

    diagram_dir = workspace_root / config.get("build", {}).get("diagram_dir", "docs/images")
    specs = _build_specs(config, manifest, workspace_root)
    if not specs:
        raise RuntimeError("no figure specs could be generated for this workspace")

    generated: list[dict[str, str]] = []
    figure_map = dict(config.get("figure_map") or {})
    for spec in specs:
        output_path = diagram_dir / spec.output_name
        spec_hash = _figure_spec_hash(spec, config, manifest, workspace_root)
        existing_cfg = figure_map.get(spec.figure_no) if isinstance(figure_map.get(spec.figure_no), dict) else {}
        relative_output_path = make_relative(output_path, workspace_root)
        status = "rendered"

        if output_path.exists() and existing_cfg.get("spec_hash") == spec_hash and existing_cfg.get("path") == relative_output_path:
            status = "cached"
        elif output_path.exists() and _can_adopt_existing_output(spec, output_path):
            status = "adopted"
        else:
            if spec.renderer == "pillow":
                chapter5_path = workspace_root / config.get("build", {}).get("input_dir", "polished_v3") / "05-系统实现.md"
                project_title = config.get("metadata", {}).get("title") or manifest.get("title", "系统功能结构图")
                _render_function_structure_png(project_title, chapter5_path, output_path)
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
