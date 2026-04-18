from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from core.project_common import load_workspace_context, make_relative, read_json, read_text_safe, write_json, write_text


REFERENCE_GUIDE_SCHEMA_VERSION = 1
DEFAULT_REFERENCE_EXTRACTION_CONFIG = {
    "enabled": False,
    "provider": "zetatechs-gemini",
    "base_url": "https://api.zetatechs.com",
    "api_key_env": "NEWAPI_API_KEY",
    "default_model": "gemini-3.1-flash-image-preview",
    "timeout_sec": 180,
    "output_dir": "docs/images/reference_guides",
}
SUPPORTED_REFERENCE_PROVIDERS = frozenset({"zetatechs-gemini"})


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _resolve_output_dir(workspace_root: Path, raw_output_dir: str) -> Path:
    path = Path(raw_output_dir)
    if path.is_absolute():
        return path
    return (workspace_root / path).resolve()


def _safe_output_stem(text: str) -> str:
    cleaned = re.sub(r"[\\/:\s]+", "-", str(text or "").strip())
    cleaned = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "-", cleaned)
    cleaned = cleaned.strip("-._")
    if cleaned:
        return cleaned
    return f"guide-{hashlib.sha1(str(text).encode('utf-8')).hexdigest()[:8]}"


def _guess_image_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    raise RuntimeError(f"unsupported reference guide image format: {path}")


def _infer_source_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown", ".txt"}:
        return "markdown"
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return "image"
    raise RuntimeError(f"unsupported reference guide source format: {path}")


def _reference_extraction_config(config: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    resolved = dict(DEFAULT_REFERENCE_EXTRACTION_CONFIG)
    resolved.update(config.get("reference_extraction") or {})
    resolved["output_dir_path"] = _resolve_output_dir(workspace_root, str(resolved["output_dir"]))
    resolved["timeout_sec"] = int(resolved.get("timeout_sec", 180) or 180)
    return resolved


def _normalize_guide_sources(raw_items: Any, workspace_root: Path) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw in raw_items or []:
        if not isinstance(raw, dict):
            continue
        raw_path = str(raw.get("path", "") or "").strip()
        if not raw_path:
            continue
        path = Path(raw_path)
        resolved = path if path.is_absolute() else (workspace_root / path).resolve()
        kind = str(raw.get("kind", "") or "").strip().lower() or _infer_source_kind(resolved)
        if kind not in {"image", "markdown"}:
            raise RuntimeError(f"unsupported reference guide source kind '{kind}' for {resolved}")
        payload = {
            "path": make_relative(resolved, workspace_root),
            "abs_path": resolved,
            "kind": kind,
            "role": str(raw.get("role", "") or "").strip(),
            "note": str(raw.get("note", "") or "").strip(),
        }
        if kind == "image":
            payload["mime_type"] = _guess_image_mime_type(resolved)
        normalized.append(payload)
    return normalized


def _normalize_reference_guide_spec(guide_name: str, raw_spec: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    spec = dict(raw_spec)
    workspace_root = defaults["workspace_root"]
    return {
        "guide_name": guide_name,
        "guide_type": str(spec.get("guide_type", "") or "").strip().lower(),
        "description": str(spec.get("description", "") or "").strip(),
        "enabled": bool(spec.get("enabled", True)),
        "model": str(spec.get("model", "") or defaults["default_model"]).strip(),
        "extract_focus": [str(item).strip() for item in (spec.get("extract_focus") or []) if str(item).strip()],
        "sources": _normalize_guide_sources(spec.get("sources") or [], workspace_root),
    }


def _enabled_reference_guide_specs(config: dict[str, Any], workspace_root: Path) -> dict[str, dict[str, Any]]:
    defaults = _reference_extraction_config(config, workspace_root)
    defaults["workspace_root"] = workspace_root
    if not defaults["enabled"]:
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for raw_guide_name, raw_spec in (config.get("reference_guide_specs") or {}).items():
        if not isinstance(raw_spec, dict):
            continue
        guide_name = str(raw_guide_name or "").strip()
        if not guide_name:
            continue
        spec = _normalize_reference_guide_spec(guide_name, raw_spec, defaults)
        if spec["enabled"]:
            normalized[guide_name] = spec
    return normalized


def _guide_manifest_path(config: dict[str, Any], workspace_root: Path) -> Path:
    settings = _reference_extraction_config(config, workspace_root)
    return settings["output_dir_path"] / "manifest.json"


def _prepare_summary_path(config: dict[str, Any], workspace_root: Path) -> Path:
    output_dir = workspace_root / config.get("build", {}).get("output_dir", "word_output")
    return output_dir / "reference_guide_prepare_summary.json"


def reference_guide_output_paths(config: dict[str, Any], workspace_root: Path, guide_name: str) -> dict[str, Path | str]:
    settings = _reference_extraction_config(config, workspace_root)
    stem = _safe_output_stem(guide_name)
    json_path = settings["output_dir_path"] / f"{stem}.json"
    md_path = settings["output_dir_path"] / f"{stem}.md"
    return {
        "json_path": json_path,
        "md_path": md_path,
        "json_rel": make_relative(json_path, workspace_root),
        "md_rel": make_relative(md_path, workspace_root),
    }


def _load_guide_manifest(config: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    manifest_path = _guide_manifest_path(config, workspace_root)
    if not manifest_path.exists():
        return {"schema_version": REFERENCE_GUIDE_SCHEMA_VERSION, "guides": {}}
    return read_json(manifest_path)


def _save_guide_manifest(config: dict[str, Any], workspace_root: Path, manifest: dict[str, Any]) -> Path:
    manifest_path = _guide_manifest_path(config, workspace_root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(manifest_path, manifest)
    return manifest_path


def _source_hashes(spec: dict[str, Any]) -> list[dict[str, str]]:
    hashes: list[dict[str, str]] = []
    for source in spec.get("sources") or []:
        abs_path = Path(source["abs_path"])
        content_hash = hashlib.sha1(abs_path.read_bytes()).hexdigest()[:16] if abs_path.exists() else "missing"
        hashes.append(
            {
                "path": str(source.get("path", "") or ""),
                "kind": str(source.get("kind", "") or ""),
                "hash": content_hash,
            }
        )
    return hashes


def _guide_type_hints(guide_type: str) -> list[str]:
    if guide_type == "use_case":
        return [
            "重点抽取：参与者符号、用例椭圆、系统边界、关系线样式、是否允许 include/extend/泛化、布局位置约束。",
            "不要把具体业务角色名或示例系统名当成通用规范。",
        ]
    if guide_type == "flowchart":
        return [
            "重点抽取：流程节点形状、判断节点样式、箭头方向、主线布局、分支布局、禁止的拥挤排版方式。",
            "不要把当前项目的具体节点文案、判断文案或返回结果文案直接上升为通用图法规范。",
        ]
    if guide_type == "architecture":
        return [
            "重点抽取：分层结构、模块框样式、层标题位置、连线克制程度、技术图而非海报的风格约束。",
            "忽略具体技术产品名或业务模块名，只提炼传统论文分层架构图的稳定表达方式。",
        ]
    if guide_type == "function_structure":
        return [
            "重点抽取：树状层级、模块框样式、一级/二级功能排布、正交连接线、避免多子节点共用含混主干的布局规则。",
            "不要把当前项目的具体模块名和子功能名直接上升为通用图法规范。",
        ]
    if guide_type == "er":
        return [
            "重点抽取：Chen 风格符号、实体/关系/属性形状、基数标注方式、中文命名约束、避免属性重叠的布局规则。",
        ]
    return [
        "重点抽取：符号规范、布局规范、线型规范、文字规范、禁止项、常见误画方式。",
    ]


def _schema_example() -> str:
    example = {
        "summary": "一句话概括该类技术图的传统论文规范。",
        "symbol_rules": ["规则1", "规则2"],
        "layout_rules": ["规则1", "规则2"],
        "relationship_rules": ["规则1", "规则2"],
        "text_rules": ["规则1", "规则2"],
        "forbidden_rules": ["禁止项1", "禁止项2"],
        "common_failure_modes": ["常见错误1", "常见错误2"],
        "prompt_fragments": {
            "must": ["必须项1", "必须项2"],
            "avoid": ["禁止项1", "禁止项2"],
            "layout": ["布局项1"],
            "style": ["风格项1"],
            "text": ["文字项1"],
        },
    }
    return json.dumps(example, ensure_ascii=False, indent=2)


def _build_extraction_prompt(spec: dict[str, Any]) -> str:
    parts = [
        "你是论文技术图规范抽取器。",
        "任务不是复述示例图内容，而是从教程文字和参考图中提炼“可复用的制图规范”。",
        f"guide 名称：{spec['guide_name']}",
        f"guide 类型：{spec.get('guide_type', '') or 'generic_technical'}",
    ]
    if spec.get("description"):
        parts.append(f"目标说明：{spec['description']}")
    if spec.get("extract_focus"):
        parts.append("本轮重点：" + "、".join(spec["extract_focus"]))
    parts.extend(
        [
            "抽取优先级：明确文字规范 > 多张示例图重复出现的稳定视觉规范 > 单张示例图中的局部表现。",
            "请忽略：教程配色、示例业务名称、具体角色名、图号、图题、页眉页脚、教学说明语气、局部噪点。",
            "如果某张来源图来自当前项目已验收图，只把它当作排版和图法样本，不要把图中文字逐字当成通用规范。",
            "如果文字规范和图片细节冲突，以文字规范为准；如果图片之间冲突，以重复出现的稳定表达为准。",
            "输出必须是单个 JSON 对象，不要 Markdown 代码块，不要额外解释，不要前后缀。",
            "JSON 字段必须包含：summary、symbol_rules、layout_rules、relationship_rules、text_rules、forbidden_rules、common_failure_modes、prompt_fragments。",
            "其中所有规则字段都使用简体中文短句数组；prompt_fragments 必须是对象，至少包含 must、avoid、layout、style、text 五个数组字段。",
        ]
    )
    parts.extend(_guide_type_hints(str(spec.get("guide_type", "") or "").strip().lower()))
    parts.append("输出 JSON 示例：")
    parts.append(_schema_example())
    return "\n".join(part for part in parts if part.strip())


def _source_prompt_parts(spec: dict[str, Any]) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    for index, source in enumerate(spec.get("sources") or [], start=1):
        kind = str(source.get("kind", "") or "")
        role = str(source.get("role", "") or "").strip()
        note = str(source.get("note", "") or "").strip()
        label = f"参考源 {index}"
        if role:
            label += f"；角色：{role}"
        if note:
            label += f"；说明：{note}"
        if kind == "markdown":
            text = read_text_safe(Path(source["abs_path"])).strip()
            if len(text) > 16000:
                text = text[:16000].rstrip() + "\n\n[内容已截断，抽取时优先依据已提供片段归纳通用规范。]"
            parts.append({"text": f"{label}；类型：markdown\n\n{text}"})
            continue
        parts.append({"text": f"{label}；类型：image"})
        parts.append(
            {
                "inlineData": {
                    "mimeType": str(source.get("mime_type", "") or "image/png"),
                    "data": base64.b64encode(Path(source["abs_path"]).read_bytes()).decode("utf-8"),
                }
            }
        )
    return parts


def _api_key(settings: dict[str, Any]) -> str:
    env_name = str(settings.get("api_key_env", "") or "").strip()
    if not env_name:
        raise RuntimeError("reference_extraction.api_key_env is empty")
    api_key = os.environ.get(env_name, "").strip()
    if not api_key:
        raise RuntimeError(f"missing API key environment variable: {env_name}")
    return api_key


def _zetatechs_root_base_url(settings: dict[str, Any]) -> str:
    base_url = str(settings.get("base_url", "") or "").rstrip("/")
    for suffix in ("/v1", "/v1beta"):
        if base_url.endswith(suffix):
            return base_url[: -len(suffix)]
    return base_url


def _gemini_generate_content_endpoint(settings: dict[str, Any], api_key: str, model: str) -> str:
    root = _zetatechs_root_base_url(settings)
    return f"{root}/v1beta/models/{quote(model, safe='')}:generateContent?key={quote(api_key, safe='')}"


def _request_reference_extraction(settings: dict[str, Any], api_key: str, spec: dict[str, Any], prompt: str) -> str:
    if settings["provider"] not in SUPPORTED_REFERENCE_PROVIDERS:
        raise RuntimeError(f"unsupported reference_extraction.provider: {settings['provider']}")
    endpoint = _gemini_generate_content_endpoint(settings, api_key, spec["model"])
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}, *_source_prompt_parts(spec)],
            }
        ],
        "generationConfig": {
            "responseModalities": ["TEXT"],
        },
    }
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "thesis-materials-workflow/reference-guide/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings["timeout_sec"]) as response:
            raw = response.read()
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"reference guide extraction failed ({exc.code}) on {endpoint}: {body}") from None

    body = json.loads(raw.decode("utf-8"))
    candidates = list(body.get("candidates") or [])
    if not candidates:
        raise RuntimeError("reference guide extraction returned no candidates")

    text_parts: list[str] = []
    for candidate in candidates:
        content = candidate.get("content") or {}
        for part in list(content.get("parts") or []):
            text = str(part.get("text", "") or "").strip()
            if text:
                text_parts.append(text)
    merged = "\n".join(item for item in text_parts if item.strip()).strip()
    if not merged:
        raise RuntimeError("reference guide extraction returned no text payload")
    return merged


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = str(text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        candidate = cleaned[start : end + 1]
        data = json.loads(candidate)
        if isinstance(data, dict):
            return data
    raise RuntimeError("reference guide extraction did not return a valid JSON object")


def _normalize_text_list(value: Any) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        segments = [seg.strip(" -\u2022\t") for seg in re.split(r"[\n；;]+", stripped) if seg.strip()]
        return [seg for seg in segments if seg]
    return []


def _normalize_prompt_fragments(raw: Any) -> dict[str, list[str]]:
    payload = raw if isinstance(raw, dict) else {}
    return {
        "must": _normalize_text_list(payload.get("must")),
        "avoid": _normalize_text_list(payload.get("avoid")),
        "layout": _normalize_text_list(payload.get("layout")),
        "style": _normalize_text_list(payload.get("style")),
        "text": _normalize_text_list(payload.get("text")),
    }


def _normalize_extraction_payload(spec: dict[str, Any], raw_text: str, source_hashes: list[dict[str, str]]) -> dict[str, Any]:
    payload = _extract_json_object(raw_text)
    guide = {
        "schema_version": REFERENCE_GUIDE_SCHEMA_VERSION,
        "guide_name": spec["guide_name"],
        "guide_type": spec.get("guide_type", "") or "",
        "description": spec.get("description", "") or "",
        "sources": [
            {
                "path": str(source.get("path", "") or ""),
                "kind": str(source.get("kind", "") or ""),
                "role": str(source.get("role", "") or ""),
                "note": str(source.get("note", "") or ""),
            }
            for source in spec.get("sources") or []
        ],
        "source_hashes": source_hashes,
        "summary": str(payload.get("summary", "") or "").strip(),
        "symbol_rules": _normalize_text_list(payload.get("symbol_rules")),
        "layout_rules": _normalize_text_list(payload.get("layout_rules")),
        "relationship_rules": _normalize_text_list(payload.get("relationship_rules")),
        "text_rules": _normalize_text_list(payload.get("text_rules")),
        "forbidden_rules": _normalize_text_list(payload.get("forbidden_rules")),
        "common_failure_modes": _normalize_text_list(payload.get("common_failure_modes")),
        "prompt_fragments": _normalize_prompt_fragments(payload.get("prompt_fragments")),
    }
    if not guide["summary"]:
        raise RuntimeError(f"reference guide '{spec['guide_name']}' extraction returned an empty summary")
    return guide


def _guide_spec_hash(settings: dict[str, Any], spec: dict[str, Any], prompt: str, source_hashes: list[dict[str, str]]) -> str:
    payload = {
        "schema_version": REFERENCE_GUIDE_SCHEMA_VERSION,
        "provider": settings["provider"],
        "base_url": settings["base_url"],
        "guide_name": spec["guide_name"],
        "guide_type": spec["guide_type"],
        "description": spec["description"],
        "model": spec["model"],
        "extract_focus": list(spec.get("extract_focus") or []),
        "sources": [
            {
                "path": str(source.get("path", "") or ""),
                "kind": str(source.get("kind", "") or ""),
                "role": str(source.get("role", "") or ""),
                "note": str(source.get("note", "") or ""),
            }
            for source in spec.get("sources") or []
        ],
        "source_hashes": source_hashes,
        "prompt": prompt,
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()[:16]


def _render_guide_markdown(guide: dict[str, Any]) -> str:
    lines = [
        f"# {guide['guide_name']}",
        "",
        f"- 类型：`{guide.get('guide_type', '') or 'generic_technical'}`",
        f"- 说明：{guide.get('description', '') or '无'}",
        f"- 生成时间：{guide.get('extracted_at', '') or 'unknown'}",
        f"- spec_hash：`{guide.get('spec_hash', '') or 'unknown'}`",
        "",
        "## 摘要",
        "",
        guide.get("summary", "") or "无",
        "",
        "## 来源",
        "",
    ]
    for source in guide.get("sources") or []:
        role = str(source.get("role", "") or "").strip() or "unspecified"
        lines.append(f"- `{source.get('kind', '')}` | `{source.get('path', '')}` | role=`{role}`")
    sections = [
        ("符号规范", guide.get("symbol_rules") or []),
        ("布局规范", guide.get("layout_rules") or []),
        ("关系规范", guide.get("relationship_rules") or []),
        ("文字规范", guide.get("text_rules") or []),
        ("禁止项", guide.get("forbidden_rules") or []),
        ("常见误判点", guide.get("common_failure_modes") or []),
    ]
    for title, items in sections:
        lines.extend(["", f"## {title}", ""])
        if items:
            lines.extend([f"- {item}" for item in items])
        else:
            lines.append("- 无")
    lines.extend(["", "## 推荐 Prompt 片段", ""])
    prompt_fragments = guide.get("prompt_fragments") or {}
    for key in ("must", "avoid", "layout", "style", "text"):
        items = prompt_fragments.get(key) or []
        lines.append(f"### {key}")
        lines.append("")
        if items:
            lines.extend([f"- {item}" for item in items])
        else:
            lines.append("- 无")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _validate_prepare_request(
    config: dict[str, Any],
    workspace_root: Path,
    selected_guides: list[str] | None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    settings = _reference_extraction_config(config, workspace_root)
    if not settings["enabled"]:
        raise RuntimeError("reference_extraction.enabled is false; enable it in workspace config before running prepare-reference-guides")
    if settings["provider"] not in SUPPORTED_REFERENCE_PROVIDERS:
        raise RuntimeError(f"unsupported reference_extraction.provider: {settings['provider']}")

    enabled_specs = _enabled_reference_guide_specs(config, workspace_root)
    if not enabled_specs:
        raise RuntimeError("no enabled reference_guide_specs found in workspace config")

    requested = set(selected_guides or [])
    unknown = sorted(requested - set(enabled_specs))
    if unknown:
        raise RuntimeError(f"unknown or disabled reference guide specs: {', '.join(unknown)}")

    filtered = {
        guide_name: spec
        for guide_name, spec in enabled_specs.items()
        if not requested or guide_name in requested
    }
    for guide_name, spec in filtered.items():
        if not spec["model"]:
            raise RuntimeError(f"reference_guide_specs.{guide_name}.model is required")
        if not spec["sources"]:
            raise RuntimeError(f"reference_guide_specs.{guide_name}.sources is required")
        for source in spec["sources"]:
            if not Path(source["abs_path"]).exists():
                raise RuntimeError(f"reference_guide_specs.{guide_name}.source path does not exist: {source['path']}")
    return settings, filtered


def _manifest_entry_summary(spec: dict[str, Any], prompt: str, spec_hash: str, status: str) -> dict[str, Any]:
    return {
        "guide_name": spec["guide_name"],
        "guide_type": spec["guide_type"],
        "description": spec["description"],
        "model": spec["model"],
        "sources": [
            {
                "path": str(source.get("path", "") or ""),
                "kind": str(source.get("kind", "") or ""),
                "role": str(source.get("role", "") or ""),
                "note": str(source.get("note", "") or ""),
            }
            for source in spec.get("sources") or []
        ],
        "prompt": prompt,
        "spec_hash": spec_hash,
        "status": status,
    }


def read_reference_guide_payload(config: dict[str, Any], workspace_root: Path, guide_name: str) -> dict[str, Any]:
    paths = reference_guide_output_paths(config, workspace_root, guide_name)
    json_path = Path(paths["json_path"])
    if not json_path.exists():
        raise RuntimeError(f"reference guide JSON is missing: {paths['json_rel']}")
    payload = read_json(json_path)
    if not isinstance(payload, dict):
        raise RuntimeError(f"reference guide JSON is invalid: {paths['json_rel']}")
    return payload


def reference_guide_dependency_entries(
    config: dict[str, Any],
    workspace_root: Path,
    guide_names: list[str] | None,
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    settings = _reference_extraction_config(config, workspace_root)
    enabled_specs = _enabled_reference_guide_specs(config, workspace_root)
    for guide_name in guide_names or []:
        paths = reference_guide_output_paths(config, workspace_root, guide_name)
        json_path = Path(paths["json_path"])
        if not json_path.exists():
            entries.append(
                {
                    "guide_name": guide_name,
                    "expected_path": str(paths["json_rel"]),
                    "reason": "missing-reference-guide",
                }
            )
            continue
        try:
            payload = read_json(json_path)
        except Exception:
            entries.append(
                {
                    "guide_name": guide_name,
                    "expected_path": str(paths["json_rel"]),
                    "reason": "invalid-reference-guide",
                }
            )
            continue
        configured = enabled_specs.get(guide_name)
        if not configured:
            continue
        source_hashes = _source_hashes(configured)
        prompt = _build_extraction_prompt(configured)
        expected_hash = _guide_spec_hash(settings, configured, prompt, source_hashes)
        actual_hash = str(payload.get("spec_hash", "") or "").strip()
        if actual_hash != expected_hash:
            entries.append(
                {
                    "guide_name": guide_name,
                    "expected_path": str(paths["json_rel"]),
                    "reason": "stale-reference-guide",
                }
            )
    return entries


def load_reference_guides_for_names(
    config: dict[str, Any],
    workspace_root: Path,
    guide_names: list[str] | None,
) -> list[dict[str, Any]]:
    entries = reference_guide_dependency_entries(config, workspace_root, guide_names)
    if entries:
        formatted = ", ".join(f"{item['guide_name']} ({item['reason']})" for item in entries)
        raise RuntimeError(f"reference guides are missing or stale; run prepare-reference-guides first: {formatted}")
    guides: list[dict[str, Any]] = []
    for guide_name in guide_names or []:
        guides.append(read_reference_guide_payload(config, workspace_root, guide_name))
    return guides


def run_prepare_reference_guides(
    config_path: Path,
    selected_guides: list[str] | None = None,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    ctx = load_workspace_context(config_path)
    config = ctx["config"]
    workspace_root = ctx["workspace_root"]

    settings, specs = _validate_prepare_request(config, workspace_root, selected_guides)
    settings["output_dir_path"].mkdir(parents=True, exist_ok=True)
    manifest = _load_guide_manifest(config, workspace_root)
    manifest_guides = dict(manifest.get("guides") or {})

    api_key = ""
    if not dry_run:
        api_key = _api_key(settings)

    prepared: list[dict[str, Any]] = []
    for guide_name in sorted(specs):
        spec = specs[guide_name]
        prompt = _build_extraction_prompt(spec)
        source_hashes = _source_hashes(spec)
        spec_hash = _guide_spec_hash(settings, spec, prompt, source_hashes)
        paths = reference_guide_output_paths(config, workspace_root, guide_name)
        json_path = Path(paths["json_path"])
        md_path = Path(paths["md_path"])
        existing_manifest = manifest_guides.get(guide_name, {})
        status = "generated"

        if dry_run:
            status = "dry-run"
        elif (not force) and json_path.exists() and str(existing_manifest.get("spec_hash", "") or "") == spec_hash:
            status = "cached"
        else:
            raw_text = _request_reference_extraction(settings, api_key, spec, prompt)
            guide_payload = _normalize_extraction_payload(spec, raw_text, source_hashes)
            guide_payload["provider"] = settings["provider"]
            guide_payload["model"] = spec["model"]
            guide_payload["extracted_at"] = _now_iso()
            guide_payload["spec_hash"] = spec_hash
            guide_payload["extraction_prompt"] = prompt
            guide_payload["output_json"] = str(paths["json_rel"])
            guide_payload["output_md"] = str(paths["md_rel"])
            json_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(json_path, guide_payload)
            write_text(md_path, _render_guide_markdown(guide_payload))
            status = "updated" if existing_manifest else "generated"

        manifest_entry = _manifest_entry_summary(spec, prompt, spec_hash, status)
        manifest_entry["output_json"] = str(paths["json_rel"])
        manifest_entry["output_md"] = str(paths["md_rel"])
        manifest_guides[guide_name] = manifest_entry
        prepared.append(
            {
                **manifest_entry,
                "source_hashes": source_hashes,
            }
        )

    manifest_payload = {
        "schema_version": REFERENCE_GUIDE_SCHEMA_VERSION,
        "provider": settings["provider"],
        "base_url": settings["base_url"],
        "output_dir": make_relative(settings["output_dir_path"], workspace_root),
        "guides": manifest_guides,
    }
    manifest_path = _save_guide_manifest(config, workspace_root, manifest_payload)

    summary_path = _prepare_summary_path(config, workspace_root)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema_version": REFERENCE_GUIDE_SCHEMA_VERSION,
        "config_path": str(ctx["config_path"]),
        "provider": settings["provider"],
        "base_url": settings["base_url"],
        "dry_run": dry_run,
        "force": force,
        "prepared_guides": prepared,
        "manifest_json": str(manifest_path),
    }
    write_json(summary_path, summary)
    return {
        "config_path": str(ctx["config_path"]),
        "output_dir": str(settings["output_dir_path"]),
        "prepared_guides": prepared,
        "manifest_json": str(manifest_path),
        "summary_json": str(summary_path),
        "dry_run": dry_run,
    }
