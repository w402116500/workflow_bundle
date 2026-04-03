from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from core.project_common import CHAIN_LABELS, load_workspace_context, make_relative, read_json, write_json


AI_IMAGE_SCHEMA_VERSION = 1
DEFAULT_IMAGE_GENERATION_CONFIG = {
    "enabled": False,
    "provider": "zetatechs-gemini",
    "base_url": "https://api.zetatechs.com",
    "api_key_env": "NEWAPI_API_KEY",
    "default_model": "gemini-3.1-flash-image-preview",
    "default_quality": "high",
    "default_size": "1536x1024",
    "response_format": "b64_json",
    "gemini_image_size": "1K",
    "gemini_response_modalities": ["IMAGE", "TEXT"],
    "timeout_sec": 300,
    "output_dir": "docs/images/generated_ai",
    "auto_generate_on_prepare_figures": False,
}
BUILTIN_GENERATED_FIGURE_NUMBERS = frozenset({"4.1", "4.2", "4.3", "4.4", "4.5", "5.1"})
SUPPORTED_PROVIDERS = frozenset({"zetatechs", "zetatechs-openai-image", "zetatechs-gemini"})


def _resolve_output_dir(workspace_root: Path, raw_output_dir: str) -> Path:
    path = Path(raw_output_dir)
    if path.is_absolute():
        return path
    return (workspace_root / path).resolve()


def _image_generation_config(config: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    resolved = dict(DEFAULT_IMAGE_GENERATION_CONFIG)
    resolved.update(config.get("image_generation") or {})
    resolved["output_dir_path"] = _resolve_output_dir(workspace_root, str(resolved["output_dir"]))
    resolved["timeout_sec"] = int(resolved.get("timeout_sec", 300) or 300)
    modalities = resolved.get("gemini_response_modalities") or ["IMAGE", "TEXT"]
    resolved["gemini_response_modalities"] = [str(item).strip().upper() for item in modalities if str(item).strip()]
    return resolved


def _normalize_ai_spec(figure_no: str, raw_spec: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    spec = dict(raw_spec)
    return {
        "figure_no": figure_no,
        "caption": str(spec.get("caption", "") or "").strip(),
        "chapter": str(spec.get("chapter", "") or "").strip(),
        "intent": str(spec.get("intent", "") or "").strip(),
        "diagram_type": str(spec.get("diagram_type", "") or "").strip().lower(),
        "style_notes": str(spec.get("style_notes", "") or "").strip(),
        "enabled": bool(spec.get("enabled", True)),
        "override_builtin": bool(spec.get("override_builtin", False)),
        "model": str(spec.get("model", "") or defaults["default_model"]).strip(),
        "quality": str(spec.get("quality", "") or defaults["default_quality"]).strip(),
        "size": str(spec.get("size", "") or defaults["default_size"]).strip(),
        "prompt_override": str(spec.get("prompt_override", "") or "").strip(),
    }


def _enabled_ai_specs(config: dict[str, Any], workspace_root: Path) -> dict[str, dict[str, Any]]:
    defaults = _image_generation_config(config, workspace_root)
    if not defaults["enabled"]:
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for figure_no, raw_spec in (config.get("ai_figure_specs") or {}).items():
        if not isinstance(raw_spec, dict):
            continue
        spec = _normalize_ai_spec(str(figure_no), raw_spec, defaults)
        if spec["enabled"]:
            normalized[spec["figure_no"]] = spec
    return normalized


def _output_filename(figure_no: str) -> str:
    return f"fig{figure_no.replace('.', '-')}-ai.png"


def ai_figure_output_paths(config: dict[str, Any], workspace_root: Path, figure_no: str) -> tuple[str, Path]:
    settings = _image_generation_config(config, workspace_root)
    output_path = settings["output_dir_path"] / _output_filename(figure_no)
    output_rel = make_relative(output_path, workspace_root)
    return output_rel, output_path


def _prompt_manifest_path(config: dict[str, Any], workspace_root: Path) -> Path:
    settings = _image_generation_config(config, workspace_root)
    return settings["output_dir_path"] / "prompt_manifest.json"


def _prepare_summary_path(config: dict[str, Any], workspace_root: Path) -> Path:
    output_dir = workspace_root / config.get("build", {}).get("output_dir", "word_output")
    return output_dir / "ai_figure_prepare_summary.json"


def _load_prompt_manifest(config: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    manifest_path = _prompt_manifest_path(config, workspace_root)
    if not manifest_path.exists():
        return {
            "schema_version": AI_IMAGE_SCHEMA_VERSION,
            "figures": {},
        }
    return read_json(manifest_path)


def _save_prompt_manifest(config: dict[str, Any], workspace_root: Path, manifest: dict[str, Any]) -> Path:
    manifest_path = _prompt_manifest_path(config, workspace_root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(manifest_path, manifest)
    return manifest_path


def _build_prompt(metadata: dict[str, Any], spec: dict[str, Any]) -> str:
    if spec["prompt_override"]:
        return spec["prompt_override"]

    chain_platform = str(metadata.get("chain_platform", "") or "").strip().lower()
    chain_label = CHAIN_LABELS.get(chain_platform, chain_platform.upper()) if chain_platform else "区块链"

    def _infer_diagram_type() -> str:
        explicit = spec.get("diagram_type", "")
        if explicit:
            return explicit
        text = f"{spec['caption']} {spec['intent']}".lower()
        if "用例图" in text or "use case" in text:
            return "use_case"
        if "功能结构图" in text or "功能模块图" in text or "模块结构图" in text:
            return "function_structure"
        if "时序图" in text or "sequence" in text:
            return "sequence"
        if "e-r" in text or "er图" in text or "实体关系图" in text:
            return "er"
        if "架构图" in text or "分层" in text or "architecture" in text:
            return "architecture"
        if "流程图" in text or "flow" in text:
            return "flowchart"
        return "generic_technical"

    diagram_type = _infer_diagram_type()

    parts = [
        "请绘制一张适用于计算机类毕业论文正文的规范技术图。",
        "这不是概念插画，也不是宣传海报，而是论文中的正式配图。",
        f"图题：{spec['caption']}",
        f"图类型：{diagram_type}",
        f"核心意图：{spec['intent']}",
        f"项目主题：{metadata.get('title', '')}",
        f"技术背景：{chain_label} 应用场景。",
    ]
    if spec["chapter"]:
        parts.append(f"所属章节：{spec['chapter']}")
    parts.extend(
        [
            "总体版式：横向排版，主体居中，层次清楚，留白充足，适合直接插入 A4 论文页面。",
            "统一风格：白色背景，黑色或深灰色线条，线宽统一，二维平面技术图风格，像 UML 图、流程图、E-R 图或论文架构图。",
            "文字要求：使用简体中文标签，术语准确，文字数量精简，字号统一，保证图内文字清晰可读。",
            "禁止项：不要写实场景，不要人物插画，不要渐变背景，不要发光效果，不要 3D，不要卡通化，不要网页界面截图，不要代码块，不要大段说明文字，不要水印。",
            "版面禁项：不要在图内重复写图题，不要出现“第X章”“系统设计章”等章节字样，不要添加左侧或右侧辅助栏、竖排分区标签、边缘装饰标签或无关说明框。",
            "画布边缘要求：图像四周保持空白，不要生成页眉、页脚、论文题目、章节标题、横向分隔线、图号标题、Fig.、Figure 或任何边缘说明文字。",
            "语言约束：除确实不可替代的技术专名外，全图仅使用简体中文，不要英文，不要中英混排，不要出现 Yes、No、End、Display、trace code 等英文流程词。",
        ]
    )

    if diagram_type == "use_case":
        parts.extend(
            [
                "图形规范：按照 UML 用例图绘制。",
                "参与者使用小人图标，系统边界使用大矩形框，用例使用椭圆。",
                "关系规范：普通关联用实线，<<include>> 和 <<extend>> 用虚线箭头，并清楚标注关系字样。",
                "布局要求：参与者分布在系统边界左右两侧，用例在系统边界内按角色分组排布，避免交叉线。",
            ]
        )
    elif diagram_type == "function_structure":
        parts.extend(
            [
                "图形规范：绘制树状功能结构图。",
                "顶层是系统名称，下一层是一级功能模块，再下一层是子功能点，全部使用矩形框。",
                "连线要求：使用正交连线或垂直树形连线，关系明确，不要复杂弯曲装饰。",
                "布局要求：整体左右均衡，模块间距一致，类似毕业论文中的标准功能架构图。",
            ]
        )
    elif diagram_type == "flowchart":
        parts.extend(
            [
                "图形规范：按照标准流程图绘制。",
                "开始/结束使用椭圆，处理步骤使用矩形，条件判断使用菱形，流程方向使用箭头。",
                "布局要求：以自上而下主流程为主，分支判断清晰，必要时标注“是/否”等判断结果。",
                "视觉要求：形状边框统一，节点对齐，尽量减少装饰性颜色。",
                "抽象要求：如果流程涉及多个业务阶段或链上链下协同，不要把每个微观操作都展开成独立节点，应合并重复步骤，只保留论文需要表达的主线流程。",
                "密度要求：节点总数应控制在适合单页论文插图阅读的范围内，避免过密排布；当信息较多时，宁可适度抽象，也不要把文本挤满整张图。",
                "文案要求：单个节点文字尽量精炼，优先使用短语级标签，不要在节点内堆叠过长的字段说明、参数列表或重复性的“生成ID/写入链上/返回结果”等细节。",
                "边界要求：流程图主体之外不要再加论文页眉、页脚、顶端标题行、底部图题行或侧边泳道装饰标签；如果需要分区，只能在图内部使用简短中文分组标题。",
            ]
        )
    elif diagram_type == "sequence":
        parts.extend(
            [
                "图形规范：按照 UML 时序图绘制。",
                "顶部排列参与者或系统组件，下面是垂直生命线和激活条。",
                "消息调用使用水平实线箭头，返回使用虚线箭头，时间顺序从上到下。",
                "布局要求：生命线间距均匀，消息文本贴近对应箭头，整体像规范的软件工程时序图。",
            ]
        )
    elif diagram_type == "er":
        parts.extend(
            [
                "图形规范：按照 Chen 风格 E-R 图绘制。",
                "实体使用矩形，关系使用菱形，属性使用椭圆，主键属性可通过位置或强调方式突出。",
                "关系线上标注 1、n 等基数，结构层次清楚，避免属性重叠。",
                "视觉要求：白底黑线，学术数据库设计图风格，不要拟物数据库插画。",
            ]
        )
    elif diagram_type == "architecture":
        parts.extend(
            [
                "图形规范：绘制系统架构图或技术分层图。",
                "采用分层结构，自上而下展示用户层、前端层、服务层、数据层或其他合理层次。",
                "每层中的组件使用矩形框分组，连线清晰表达依赖和数据流向。",
                "允许少量简洁的技术图标或框内英文技术名，但整体仍应以白底黑框、论文技术图风格为主，不要做成宣传海报。",
            ]
        )
    else:
        parts.extend(
            [
                "图形规范：请按照论文技术图的表达方式组织框、线、箭头和标签，不要输出概念插画。",
                "布局要求：优先使用规则网格、树形、分层或顺序布局，使结构一眼可读。",
            ]
        )

    if spec.get("style_notes"):
        parts.append(f"补充风格要求：{spec['style_notes']}")
    return "\n".join(part for part in parts if part.strip())


def _spec_hash(settings: dict[str, Any], metadata: dict[str, Any], spec: dict[str, Any], prompt: str) -> str:
    payload = {
        "schema_version": AI_IMAGE_SCHEMA_VERSION,
        "provider": settings["provider"],
        "base_url": settings["base_url"],
        "response_format": settings["response_format"],
        "gemini_image_size": settings.get("gemini_image_size", ""),
        "gemini_response_modalities": settings.get("gemini_response_modalities", []),
        "figure_no": spec["figure_no"],
        "caption": spec["caption"],
        "chapter": spec["chapter"],
        "intent": spec["intent"],
        "model": spec["model"],
        "quality": spec["quality"],
        "size": spec["size"],
        "override_builtin": spec["override_builtin"],
        "project_title": metadata.get("title", ""),
        "chain_platform": metadata.get("chain_platform", ""),
        "prompt": prompt,
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()[:16]


def _validate_prepare_request(
    config: dict[str, Any],
    workspace_root: Path,
    selected_figures: list[str] | None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    settings = _image_generation_config(config, workspace_root)
    if not settings["enabled"]:
        raise RuntimeError("image_generation.enabled is false; enable it in workspace config before running prepare-ai-figures")
    if settings["provider"] not in SUPPORTED_PROVIDERS:
        raise RuntimeError(f"unsupported image_generation.provider: {settings['provider']}")

    enabled_specs = _enabled_ai_specs(config, workspace_root)
    if not enabled_specs:
        raise RuntimeError("no enabled ai_figure_specs found in workspace config")

    requested = set(selected_figures or [])
    unknown = sorted(requested - set(enabled_specs))
    if unknown:
        raise RuntimeError(f"unknown or disabled ai figure specs: {', '.join(unknown)}")

    filtered = {
        figure_no: spec
        for figure_no, spec in enabled_specs.items()
        if not requested or figure_no in requested
    }
    for figure_no, spec in filtered.items():
        if not spec["caption"]:
            raise RuntimeError(f"ai_figure_specs.{figure_no}.caption is required")
        if not spec["prompt_override"] and not spec["intent"]:
            raise RuntimeError(f"ai_figure_specs.{figure_no}.intent is required when prompt_override is empty")
        if figure_no in BUILTIN_GENERATED_FIGURE_NUMBERS and not spec["override_builtin"]:
            raise RuntimeError(
                f"ai_figure_specs.{figure_no} conflicts with a built-in generated figure; set override_builtin=true to replace it"
            )

    return settings, filtered


def _api_key(settings: dict[str, Any]) -> str:
    env_name = str(settings.get("api_key_env", "") or "").strip()
    if not env_name:
        raise RuntimeError("image_generation.api_key_env is empty")
    api_key = os.environ.get(env_name, "").strip()
    if not api_key:
        raise RuntimeError(f"missing API key environment variable: {env_name}")
    return api_key


def _provider_kind(settings: dict[str, Any]) -> str:
    provider = str(settings.get("provider", "") or "").strip().lower()
    if provider == "zetatechs":
        return "openai-image"
    if provider == "zetatechs-openai-image":
        return "openai-image"
    if provider == "zetatechs-gemini":
        return "gemini"
    raise RuntimeError(f"unsupported image_generation.provider: {settings['provider']}")


def _zetatechs_root_base_url(settings: dict[str, Any]) -> str:
    base_url = str(settings.get("base_url", "") or "").rstrip("/")
    for suffix in ("/v1", "/v1beta"):
        if base_url.endswith(suffix):
            return base_url[: -len(suffix)]
    return base_url


def _openai_image_endpoint(settings: dict[str, Any]) -> str:
    base_url = str(settings.get("base_url", "") or "").rstrip("/")
    if base_url.endswith("/images/generations"):
        return base_url
    if base_url.endswith("/v1"):
        return base_url + "/images/generations"
    return _zetatechs_root_base_url(settings) + "/v1/images/generations"


def _gemini_generate_content_endpoint(settings: dict[str, Any], api_key: str, model: str) -> str:
    root = _zetatechs_root_base_url(settings)
    return f"{root}/v1beta/models/{quote(model, safe='')}:generateContent?key={quote(api_key, safe='')}"


def _request_openai_image(settings: dict[str, Any], api_key: str, spec: dict[str, Any], prompt: str) -> tuple[bytes, str]:
    endpoint = _openai_image_endpoint(settings)
    payload = {
        "model": spec["model"],
        "prompt": prompt,
        "quality": spec["quality"],
        "size": spec["size"],
        "n": 1,
    }
    response_format = str(settings.get("response_format", "") or "").strip()
    if response_format:
        payload["response_format"] = response_format

    def _send_request(request_payload: dict[str, Any]) -> bytes:
        request = Request(
            endpoint,
            data=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "thesis-materials-workflow/ai-image/1.0",
            },
            method="POST",
        )
        with urlopen(request, timeout=settings["timeout_sec"]) as response:
            return response.read()

    try:
        raw = _send_request(payload)
    except HTTPError as exc:
        body_bytes = exc.read()
        try:
            body = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            raise
        error = body.get("error") or {}
        message = str(error.get("message", "") or "")
        param = str(error.get("param", "") or "")
        if "not supported model for image generation" in message:
            raise RuntimeError(
                f"provider does not support image model '{spec['model']}' on {endpoint}; "
                "the current Zetatechs OpenAI image endpoint accepts dedicated image models such as gpt-image-1, "
                "while Gemini image-preview models need a different Gemini Generate Content flow"
            ) from None
        if exc.code != 400 or "response_format" not in payload:
            raise
        if param != "response_format" and "response_format" not in message:
            raise
        retry_payload = dict(payload)
        retry_payload.pop("response_format", None)
        raw = _send_request(retry_payload)

    body = json.loads(raw.decode("utf-8"))
    data = list(body.get("data") or [])
    if not data:
        raise RuntimeError("ai image API returned no data items")
    item = data[0]
    revised_prompt = str(item.get("revised_prompt", "") or "").strip()
    b64_json = str(item.get("b64_json", "") or "").strip()
    if b64_json:
        return base64.b64decode(b64_json), revised_prompt
    url = str(item.get("url", "") or "").strip()
    if not url:
        raise RuntimeError("ai image API returned neither b64_json nor url")
    download_req = Request(url, headers={"User-Agent": "thesis-materials-workflow/ai-image/1.0"})
    with urlopen(download_req, timeout=settings["timeout_sec"]) as response:
        return response.read(), revised_prompt


def _gemini_aspect_ratio(size: str) -> str:
    match = re.fullmatch(r"\s*(\d+)\s*x\s*(\d+)\s*", str(size or ""))
    if not match:
        return "4:3"
    width = int(match.group(1))
    height = int(match.group(2))
    if width <= 0 or height <= 0:
        return "4:3"

    def _gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a

    divisor = _gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def _request_gemini_generate_content(settings: dict[str, Any], api_key: str, spec: dict[str, Any], prompt: str) -> tuple[bytes, str]:
    endpoint = _gemini_generate_content_endpoint(settings, api_key, spec["model"])
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt,
                    }
                ],
            }
        ],
        "generationConfig": {
            "responseModalities": settings.get("gemini_response_modalities") or ["IMAGE", "TEXT"],
            "imageConfig": {
                "aspectRatio": _gemini_aspect_ratio(spec["size"]),
                "image_size": str(settings.get("gemini_image_size", "1K") or "1K"),
            },
        },
    }
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "thesis-materials-workflow/ai-image/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings["timeout_sec"]) as response:
            raw = response.read()
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"gemini image generation failed ({exc.code}) on {endpoint}: {body}") from None

    body = json.loads(raw.decode("utf-8"))
    candidates = list(body.get("candidates") or [])
    if not candidates:
        raise RuntimeError("gemini API returned no candidates")

    revised_lines: list[str] = []
    for candidate in candidates:
        content = candidate.get("content") or {}
        parts = list(content.get("parts") or [])
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data") or {}
            data = str(inline.get("data", "") or "").strip()
            if data:
                text = "\n".join(line for line in revised_lines if line.strip()).strip()
                return base64.b64decode(data), text
            text = str(part.get("text", "") or "").strip()
            if text:
                revised_lines.append(text)

    raise RuntimeError("gemini API returned no inline image data")


def _request_generation(settings: dict[str, Any], api_key: str, spec: dict[str, Any], prompt: str) -> tuple[bytes, str]:
    provider = _provider_kind(settings)
    if provider == "gemini":
        return _request_gemini_generate_content(settings, api_key, spec, prompt)
    return _request_openai_image(settings, api_key, spec, prompt)


def ai_override_blocking_entries(config_path: Path) -> list[dict[str, Any]]:
    ctx = load_workspace_context(config_path)
    config = ctx["config"]
    workspace_root = ctx["workspace_root"]
    overrides = [
        spec
        for spec in _enabled_ai_specs(config, workspace_root).values()
        if spec["override_builtin"] and spec["figure_no"] in BUILTIN_GENERATED_FIGURE_NUMBERS
    ]
    entries: list[dict[str, Any]] = []
    for spec in overrides:
        output_rel, output_path = ai_figure_output_paths(config, workspace_root, spec["figure_no"])
        if output_path.exists():
            continue
        entries.append(
            {
                "figure_no": spec["figure_no"],
                "caption": spec["caption"],
                "expected_path": output_rel,
                "reason": "missing-ai-image",
            }
        )
    return entries


def ai_override_map(config: dict[str, Any], workspace_root: Path) -> dict[str, dict[str, Any]]:
    settings = _image_generation_config(config, workspace_root)
    overrides: dict[str, dict[str, Any]] = {}
    for spec in _enabled_ai_specs(config, workspace_root).values():
        if not spec["override_builtin"] or spec["figure_no"] not in BUILTIN_GENERATED_FIGURE_NUMBERS:
            continue
        prompt = _build_prompt(config.get("metadata", {}) or {}, spec)
        spec_hash = _spec_hash(settings, config.get("metadata", {}) or {}, spec, prompt)
        output_rel, output_path = ai_figure_output_paths(config, workspace_root, spec["figure_no"])
        overrides[spec["figure_no"]] = {
            "figure_no": spec["figure_no"],
            "caption": spec["caption"],
            "path": output_rel,
            "output_path": output_path,
            "renderer": "ai-image",
            "spec_hash": spec_hash,
        }
    return overrides


def run_prepare_ai_figures(
    config_path: Path,
    selected_figures: list[str] | None = None,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    ctx = load_workspace_context(config_path)
    config = ctx["config"]
    workspace_root = ctx["workspace_root"]
    metadata = config.get("metadata", {}) or {}

    settings, specs = _validate_prepare_request(config, workspace_root, selected_figures)
    settings["output_dir_path"].mkdir(parents=True, exist_ok=True)
    prompt_manifest = _load_prompt_manifest(config, workspace_root)
    prompt_entries = dict(prompt_manifest.get("figures") or {})
    figure_map = dict(config.get("figure_map") or {})

    api_key = ""
    if not dry_run:
        api_key = _api_key(settings)

    processed: list[dict[str, Any]] = []
    for figure_no in sorted(specs):
        spec = specs[figure_no]
        prompt = _build_prompt(metadata, spec)
        spec_hash = _spec_hash(settings, metadata, spec, prompt)
        output_rel, output_path = ai_figure_output_paths(config, workspace_root, figure_no)
        existing_manifest = prompt_entries.get(figure_no, {})
        status = "generated"
        revised_prompt = str(existing_manifest.get("revised_prompt", "") or "").strip()

        if dry_run:
            status = "dry-run"
        elif (not force) and output_path.exists() and existing_manifest.get("spec_hash") == spec_hash:
            status = "cached"
        else:
            image_bytes, revised_prompt = _request_generation(settings, api_key, spec, prompt)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image_bytes)
            status = "updated" if output_path.exists() and existing_manifest else "generated"

        prompt_entry = {
            "figure_no": figure_no,
            "caption": spec["caption"],
            "chapter": spec["chapter"],
            "intent": spec["intent"],
            "override_builtin": spec["override_builtin"],
            "model": spec["model"],
            "quality": spec["quality"],
            "size": spec["size"],
            "prompt": prompt,
            "revised_prompt": revised_prompt,
            "path": output_rel,
            "spec_hash": spec_hash,
            "status": status,
        }
        prompt_entries[figure_no] = prompt_entry
        processed.append(prompt_entry)

        if dry_run:
            continue
        figure_map[figure_no] = {
            "caption": spec["caption"],
            "path": output_rel,
            "renderer": "ai-image",
            "spec_hash": spec_hash,
        }

    prompt_manifest_payload = {
        "schema_version": AI_IMAGE_SCHEMA_VERSION,
        "provider": settings["provider"],
        "base_url": settings["base_url"],
        "output_dir": make_relative(settings["output_dir_path"], workspace_root),
        "figures": prompt_entries,
    }
    prompt_manifest_path = _save_prompt_manifest(config, workspace_root, prompt_manifest_payload)

    if not dry_run:
        config["figure_map"] = figure_map
        write_json(ctx["config_path"], config)

    summary_path = _prepare_summary_path(config, workspace_root)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema_version": AI_IMAGE_SCHEMA_VERSION,
        "config_path": str(ctx["config_path"]),
        "provider": settings["provider"],
        "base_url": settings["base_url"],
        "dry_run": dry_run,
        "force": force,
        "prepared_figures": processed,
        "prompt_manifest_json": str(prompt_manifest_path),
    }
    write_json(summary_path, summary)

    return {
        "config_path": str(ctx["config_path"]),
        "output_dir": str(settings["output_dir_path"]),
        "prepared_figures": processed,
        "prompt_manifest_json": str(prompt_manifest_path),
        "summary_json": str(summary_path),
        "dry_run": dry_run,
    }
