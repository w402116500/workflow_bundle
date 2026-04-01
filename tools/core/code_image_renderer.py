from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont, ImageOps

CODE_RENDER_TABSIZE = 4
CODE_RENDER_WRAP_SOFT_BREAK_CHARS = set(" ,.;:)]}>/\\|=+-*&")


def build_bundled_font_candidates(anchor_file: Path, bundled_relative_paths: Iterable[Path]) -> list[Path]:
    repo_root = Path(anchor_file).resolve().parents[2]
    bundled_bases = [repo_root]
    if repo_root.name != "workflow_bundle":
        bundled_bases.append(repo_root / "workflow_bundle")

    candidates: list[Path] = []
    seen: set[str] = set()
    for base in bundled_bases:
        for rel_path in bundled_relative_paths:
            resolved = (base / rel_path).resolve()
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            if resolved.exists():
                candidates.append(resolved)
    return candidates


def load_code_font(font_candidates: Iterable[Path], font_size: int) -> tuple[ImageFont.ImageFont, str | None]:
    seen: set[str] = set()
    for candidate in font_candidates:
        path = Path(candidate).resolve()
        key = str(path)
        if key in seen or not path.exists():
            continue
        seen.add(key)
        try:
            return ImageFont.truetype(str(path), font_size), str(path)
        except Exception:
            continue
    return ImageFont.load_default(), None


def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    sample = text if text else " "
    bbox = draw.textbbox((0, 0), sample, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _fit_prefix_length(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> int:
    if not text:
        return 0
    lo, hi = 1, len(text)
    best = 1
    while lo <= hi:
        mid = (lo + hi) // 2
        width, _ = _measure_text(draw, text[:mid], font)
        if width <= max_width:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def _prefer_soft_wrap_break(text: str, hard_break: int) -> int:
    if hard_break >= len(text):
        return hard_break
    min_index = max(1, int(hard_break * 0.6))
    for idx in range(hard_break - 1, min_index - 1, -1):
        if text[idx] in CODE_RENDER_WRAP_SOFT_BREAK_CHARS:
            return idx + 1
    return hard_break


def _wrap_code_line(
    line: str,
    draw: ImageDraw.ImageDraw,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    if max_width <= 0:
        return [line]

    width, _ = _measure_text(draw, line, font)
    if width <= max_width:
        return [line]

    segments: list[str] = []
    remaining = line
    while remaining:
        hard_break = _fit_prefix_length(draw, remaining, font, max_width)
        if hard_break >= len(remaining):
            segments.append(remaining)
            break
        split_at = max(1, _prefer_soft_wrap_break(remaining, hard_break))
        segments.append(remaining[:split_at])
        remaining = remaining[split_at:]
    return segments


def render_code_lines_image(
    code_lines: list[str],
    output_path: Path,
    *,
    font_candidates: Iterable[Path],
    font_size: int,
    padding_x: int,
    padding_y: int,
    line_pad: int,
    border_px: int,
    max_content_width_px: int | None = None,
    fixed_canvas_width_px: int | None = None,
) -> str | None:
    font, selected_font = load_code_font(font_candidates, font_size)
    normalized_lines = [line.expandtabs(CODE_RENDER_TABSIZE).replace("\r", "") for line in code_lines]

    dummy = Image.new("RGB", (10, 10), "white")
    draw = ImageDraw.Draw(dummy)
    wrapped_lines: list[str] = []
    wrap_limit = max_content_width_px or 0
    if wrap_limit > 0:
        for line in normalized_lines:
            wrapped_lines.extend(_wrap_code_line(line, draw, font, wrap_limit))
    else:
        wrapped_lines = list(normalized_lines)
    safe_lines = [line if line.strip() else " " for line in wrapped_lines] or [" "]

    line_heights: list[int] = []
    max_width = 0
    for line in safe_lines:
        width, height = _measure_text(draw, line, font)
        max_width = max(max_width, width)
        line_heights.append(height)

    line_height = max(line_heights) if line_heights else font_size
    content_width = max(max_width, fixed_canvas_width_px or 0)
    img_w = content_width + padding_x * 2
    img_h = (line_height + line_pad) * len(safe_lines) - line_pad + padding_y * 2
    image = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(image)

    y = padding_y
    for line in safe_lines:
        draw.text((padding_x, y), line, fill=(0, 0, 0), font=font)
        y += line_height + line_pad

    image = ImageOps.expand(image, border=border_px, fill="black")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")
    return selected_font
