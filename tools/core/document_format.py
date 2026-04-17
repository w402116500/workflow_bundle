from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping


DEFAULT_DOCUMENT_FORMAT_PROFILE = "legacy"
NUMBER_TOKEN_RE = r"\d+(?:[.-]\d+)+"
FIGURE_CAPTION_RE = re.compile(rf"^(?P<label>图)(?P<num>{NUMBER_TOKEN_RE})(?P<rest>\s+.+)$")
TABLE_CAPTION_RE = re.compile(rf"^(?P<label>表)(?P<num>{NUMBER_TOKEN_RE})(?P<rest>\s+.+)$")


DOCUMENT_FORMAT_PROFILES: dict[str, dict[str, Any]] = {
    "legacy": {
        "profile": "legacy",
        "page": {
            "width_mm": 210.0,
            "height_mm": 297.0,
            "top_margin_mm": 25.0,
            "bottom_margin_mm": 20.0,
            "left_margin_mm": 25.0,
            "right_margin_mm": 20.0,
        },
        "body": {
            "font_cn": "SimSun",
            "font_en": "Times New Roman",
            "size_pt": 12.0,
            "line_spacing_pt": 23.0,
            "first_line_indent_pt": 24.0,
        },
        "headings": {
            "1": {
                "font_cn": "SimHei",
                "font_en": "Times New Roman",
                "size_pt": 18.0,
                "bold": False,
                "align": "left",
                "space_before_pt": 11.5,
                "space_after_pt": 11.5,
            },
            "2": {
                "font_cn": "SimHei",
                "font_en": "Times New Roman",
                "size_pt": 15.0,
                "bold": False,
                "align": "left",
                "space_before_pt": 11.5,
                "space_after_pt": 11.5,
            },
            "3": {
                "font_cn": "SimHei",
                "font_en": "Times New Roman",
                "size_pt": 14.0,
                "bold": False,
                "align": "left",
                "space_before_pt": 11.5,
                "space_after_pt": 11.5,
            },
            "4": {
                "font_cn": "SimHei",
                "font_en": "Times New Roman",
                "size_pt": 12.0,
                "bold": False,
                "align": "left",
                "space_before_pt": 11.5,
                "space_after_pt": 11.5,
            },
        },
        "toc": {
            "1": {"font_cn": "SimHei", "font_en": "Times New Roman", "size_pt": 14.0, "bold": False},
            "2": {"font_cn": "SimSun", "font_en": "Times New Roman", "size_pt": 12.0, "bold": False},
            "3": {"font_cn": "SimSun", "font_en": "Times New Roman", "size_pt": 12.0, "bold": False},
        },
        "captions": {
            "figure": {
                "font_cn": "SimHei",
                "font_en": "Times New Roman",
                "size_pt": 12.0,
                "bold": True,
                "align": "center",
                "line_spacing_pt": 23.0,
            },
            "table": {
                "font_cn": "SimHei",
                "font_en": "Times New Roman",
                "size_pt": 12.0,
                "bold": True,
                "align": "center",
                "line_spacing_pt": 23.0,
            },
        },
        "code_blocks": {
            "render_mode": "image",
            "text_style": "plain-paper",
            "font_cn": "SimSun",
            "font_en": "Times New Roman",
            "size_pt": 10.5,
            "line_spacing": "single",
            "left_indent_pt": 10.0,
            "space_before_pt": 6.0,
            "space_after_pt": 6.0,
            "tab_size": 4,
        },
        "header_footer": {
            "enabled": False,
            "header_text": "",
            "header_font_cn": "SimSun",
            "header_font_en": "Times New Roman",
            "header_size_pt": 10.5,
            "footer_size_pt": 10.5,
            "footer_format": "第{page}页 共{total}页",
        },
        "numbering": {
            "figure": "dot",
            "table": "dot",
            "equation": "dot",
            "equation_parentheses": "ascii",
        },
    },
    "cuit-undergrad-zh": {
        "profile": "cuit-undergrad-zh",
        "page": {
            "width_mm": 210.0,
            "height_mm": 297.0,
            "top_margin_mm": 25.0,
            "bottom_margin_mm": 25.0,
            "left_margin_mm": 30.0,
            "right_margin_mm": 30.0,
        },
        "body": {
            "font_cn": "SimSun",
            "font_en": "Times New Roman",
            "size_pt": 12.0,
            "line_spacing_pt": 20.0,
            "first_line_indent_pt": 24.0,
        },
        "headings": {
            "1": {
                "font_cn": "SimSun",
                "font_en": "Times New Roman",
                "size_pt": 16.0,
                "bold": True,
                "align": "center",
                "space_before_pt": 10.0,
                "space_after_pt": 10.0,
            },
            "2": {
                "font_cn": "SimSun",
                "font_en": "Times New Roman",
                "size_pt": 14.0,
                "bold": True,
                "align": "left",
                "space_before_pt": 10.0,
                "space_after_pt": 10.0,
            },
            "3": {
                "font_cn": "SimSun",
                "font_en": "Times New Roman",
                "size_pt": 12.0,
                "bold": True,
                "align": "left",
                "space_before_pt": 10.0,
                "space_after_pt": 10.0,
            },
            "4": {
                "font_cn": "SimSun",
                "font_en": "Times New Roman",
                "size_pt": 12.0,
                "bold": True,
                "align": "left",
                "space_before_pt": 10.0,
                "space_after_pt": 10.0,
            },
        },
        "toc": {
            "1": {"font_cn": "SimSun", "font_en": "Times New Roman", "size_pt": 12.0, "bold": True},
            "2": {"font_cn": "SimSun", "font_en": "Times New Roman", "size_pt": 12.0, "bold": False},
            "3": {"font_cn": "SimSun", "font_en": "Times New Roman", "size_pt": 12.0, "bold": False},
        },
        "captions": {
            "figure": {
                "font_cn": "SimSun",
                "font_en": "Times New Roman",
                "size_pt": 10.5,
                "bold": False,
                "align": "center",
                "line_spacing_pt": 20.0,
            },
            "table": {
                "font_cn": "SimSun",
                "font_en": "Times New Roman",
                "size_pt": 10.5,
                "bold": False,
                "align": "center",
                "line_spacing_pt": 20.0,
            },
        },
        "code_blocks": {
            "render_mode": "image",
            "text_style": "plain-paper",
            "font_cn": "SimSun",
            "font_en": "Times New Roman",
            "size_pt": 10.5,
            "line_spacing": "single",
            "left_indent_pt": 10.0,
            "space_before_pt": 6.0,
            "space_after_pt": 6.0,
            "tab_size": 4,
        },
        "header_footer": {
            "enabled": True,
            "header_text": "成都信息工程大学学士学位论文",
            "header_font_cn": "SimSun",
            "header_font_en": "Times New Roman",
            "header_size_pt": 10.5,
            "footer_size_pt": 10.5,
            "footer_format": "第{page}页 共{total}页",
        },
        "numbering": {
            "figure": "hyphen",
            "table": "hyphen",
            "equation": "hyphen",
            "equation_parentheses": "fullwidth",
        },
    },
}


def _deep_merge_dict(base: dict[str, Any], override: Mapping[str, Any] | None) -> dict[str, Any]:
    if not override:
        return deepcopy(base)
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), dict):
            result[key] = _deep_merge_dict(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def resolve_document_format(config: Mapping[str, Any] | None) -> dict[str, Any]:
    raw = dict((config or {}).get("document_format") or {})
    profile_name = str(raw.get("profile") or DEFAULT_DOCUMENT_FORMAT_PROFILE).strip() or DEFAULT_DOCUMENT_FORMAT_PROFILE
    base = DOCUMENT_FORMAT_PROFILES.get(profile_name, DOCUMENT_FORMAT_PROFILES[DEFAULT_DOCUMENT_FORMAT_PROFILE])
    overrides = {key: value for key, value in raw.items() if key != "profile"}
    resolved = _deep_merge_dict(base, overrides)
    resolved["profile"] = base.get("profile", profile_name)
    return resolved


def normalize_internal_figure_number(token: str) -> str:
    return str(token or "").strip().replace("-", ".")


def _normalize_number_token(token: str, style: str) -> str:
    token = normalize_internal_figure_number(token)
    if style == "hyphen":
        return token.replace(".", "-")
    return token


def normalize_caption_text(text: str, kind: str, document_format: Mapping[str, Any]) -> str:
    if not text:
        return text
    numbering = document_format.get("numbering", {})
    style = str(numbering.get(kind, "dot") or "dot")
    pattern = FIGURE_CAPTION_RE if kind == "figure" else TABLE_CAPTION_RE
    match = pattern.match(text.strip())
    if not match:
        return text
    normalized = _normalize_number_token(match.group("num"), style)
    return f"{match.group('label')}{normalized}{match.group('rest')}"


def normalize_inline_reference_text(text: str, document_format: Mapping[str, Any]) -> str:
    if not text:
        return text

    numbering = document_format.get("numbering", {})
    figure_style = str(numbering.get("figure", "dot") or "dot")
    table_style = str(numbering.get("table", "dot") or "dot")
    equation_style = str(numbering.get("equation", "dot") or "dot")
    equation_parens = str(numbering.get("equation_parentheses", "ascii") or "ascii")

    def _replace_figure(match: re.Match[str]) -> str:
        return f"图{_normalize_number_token(match.group('num'), figure_style)}"

    def _replace_table(match: re.Match[str]) -> str:
        return f"表{_normalize_number_token(match.group('num'), table_style)}"

    def _replace_equation(match: re.Match[str]) -> str:
        left = "（" if equation_parens == "fullwidth" else "("
        right = "）" if equation_parens == "fullwidth" else ")"
        label = match.group("label")
        return f"{label}{left}{_normalize_number_token(match.group('num'), equation_style)}{right}"

    value = re.sub(rf"图(?P<num>{NUMBER_TOKEN_RE})", _replace_figure, text)
    value = re.sub(rf"表(?P<num>{NUMBER_TOKEN_RE})", _replace_table, value)
    value = re.sub(rf"(?P<label>式|公式)\s*[（(](?P<num>{NUMBER_TOKEN_RE})[）)]", _replace_equation, value)
    return value


def resolve_numbered_caption(text: str, kind: str, document_format: Mapping[str, Any]) -> str:
    normalized = normalize_caption_text(text, kind, document_format)
    return normalize_inline_reference_text(normalized, document_format)
