from __future__ import annotations

import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.code_image_renderer import build_bundled_font_candidates, render_code_lines_image

from core.project_common import (
    CODE_EVIDENCE_SCHEMA_VERSION,
    load_workspace_context,
    make_relative,
    material_output_paths,
    read_text_safe,
    write_json,
    write_text,
)

CODE_SCREENSHOT_FONT_ENV_VAR = "THESIS_CODE_SCREENSHOT_FONT"
CODE_SCREENSHOT_BUNDLED_FONT_RELATIVE_PATHS = [
    Path("assets/fonts/sarasa-mono-sc/SarasaMonoSC-Regular.ttf"),
    Path("assets/fonts/siyuan-heiti/SourceHanSansSC-Regular-2.otf"),
]
CODE_SCREENSHOT_PRIMARY_FONT_PATHS = [
    Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoMono-Regular.ttf"),
    Path("C:/Windows/Fonts/consola.ttf"),
    Path("C:/Windows/Fonts/consolab.ttf"),
    Path("C:/Windows/Fonts/Consolas.ttf"),
]
CODE_SCREENSHOT_FONT_SIZE_PX = 13
CODE_SCREENSHOT_IMAGE_PAD_PX = 12
CODE_SCREENSHOT_LINE_PAD_PX = 0
CODE_SCREENSHOT_BORDER_PX = 1
CODE_SCREENSHOT_MM_PER_PX = 0.25
CODE_SCREENSHOT_MAX_DISPLAY_WIDTH_MM = 148.0
CODE_SCREENSHOT_MAX_CONTENT_WIDTH_PX = max(
    240,
    int(round(CODE_SCREENSHOT_MAX_DISPLAY_WIDTH_MM / CODE_SCREENSHOT_MM_PER_PX))
    - (CODE_SCREENSHOT_IMAGE_PAD_PX * 2)
    - (CODE_SCREENSHOT_BORDER_PX * 2),
)
def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _slug(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "-", text).strip("-").lower() or "snippet"


def _abs_project_path(project_root: Path, raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    path = Path(raw_path)
    return path if path.is_absolute() else (project_root / path).resolve()


def _code_screenshot_font_candidates() -> list[Path]:
    candidates: list[Path] = []
    custom_font = os.environ.get(CODE_SCREENSHOT_FONT_ENV_VAR, "").strip()
    if custom_font:
        candidates.append(Path(custom_font))
    candidates.extend(build_bundled_font_candidates(Path(__file__), CODE_SCREENSHOT_BUNDLED_FONT_RELATIVE_PATHS))
    candidates.extend(path for path in CODE_SCREENSHOT_PRIMARY_FONT_PATHS if path.exists())
    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve())
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _detect_domain_key(title: str) -> str:
    lowered = title.lower()
    trace_tokens = ["trace", "tea", "batch", "logistics", "qrcode", "溯源", "茶叶", "批次", "二维码"]
    health_tokens = ["health", "medical", "ehr", "patient", "doctor", "健康", "医疗", "病历", "患者", "医生"]
    trace_score = sum(1 for token in trace_tokens if token in lowered)
    health_score = sum(1 for token in health_tokens if token in lowered)
    if trace_score > 0 and trace_score >= health_score:
        return "traceability"
    if health_score > 0:
        return "health_record"
    return "generic_blockchain"


def _module_specs(domain_key: str) -> list[dict[str, Any]]:
    if domain_key == "health_record":
        return [
            {
                "key": "identity",
                "label": "用户与身份管理",
                "backend_keywords": ["auth", "login", "register", "user", "doctor", "jwt", "profile"],
                "frontend_keywords": ["login", "register", "profile", "auth", "user"],
                "backend_preferred_paths": ["auth_service", "user", "account", "permission", "router"],
                "frontend_preferred_paths": ["login", "register", "profile", "router"],
            },
            {
                "key": "record",
                "label": "健康档案管理",
                "backend_keywords": ["record", "health", "patient", "upload", "confirm", "diagnosis"],
                "frontend_keywords": ["record", "health", "patient", "upload", "diagnosis"],
                "backend_preferred_paths": ["record_service", "patient", "health", "archive"],
                "frontend_preferred_paths": ["record", "health", "patient", "upload"],
            },
            {
                "key": "access",
                "label": "访问授权管理",
                "backend_keywords": ["grant", "revoke", "access", "permission", "acl", "authorize"],
                "frontend_keywords": ["grant", "revoke", "access", "permission", "authorize"],
                "backend_preferred_paths": ["access", "grant", "permission", "acl", "authorize"],
                "frontend_preferred_paths": ["access", "grant", "permission", "authorize"],
            },
            {
                "key": "audit",
                "label": "查询与审计追溯",
                "backend_keywords": ["audit", "trace", "query", "history", "stats"],
                "frontend_keywords": ["trace", "query", "audit", "history", "detail"],
                "backend_preferred_paths": ["audit", "trace", "query", "history"],
                "frontend_preferred_paths": ["trace", "query", "audit", "history"],
            },
            {
                "key": "message",
                "label": "消息反馈与统计分析",
                "backend_keywords": ["message", "feedback", "notice", "stats", "dashboard"],
                "frontend_keywords": ["message", "feedback", "dashboard", "stats", "notice"],
                "backend_preferred_paths": ["message", "notice", "dashboard", "stats"],
                "frontend_preferred_paths": ["message", "notice", "dashboard", "stats"],
            },
        ]
    if domain_key == "traceability":
        return [
            {
                "key": "identity",
                "label": "用户与权限管理",
                "backend_keywords": ["auth", "login", "register", "user", "org", "jwt", "role", "audit", "bind", "identity", "list", "update"],
                "frontend_keywords": ["login", "register", "profile", "auth", "user", "pendingorg", "users", "audit", "submit"],
                "backend_preferred_paths": ["auth_service.go", "admin_service.go", "admin_extra_service.go", "router.go", "middleware", "permission"],
                "frontend_preferred_paths": ["registerpage.vue", "loginpage.vue", "pendingorgspage.vue", "userspage.vue", "router/index.ts"],
            },
            {
                "key": "batch",
                "label": "批次与主档管理",
                "backend_keywords": ["batch", "garden", "category", "createbatch", "batchcode", "tracecode"],
                "frontend_keywords": ["batch", "batches", "garden", "gardens", "categories"],
                "backend_preferred_paths": ["batch_service.go", "garden_service.go", "category_service.go", "batch_lookup_service.go"],
                "frontend_preferred_paths": ["batchespage.vue", "gardenspage.vue", "categoriespage.vue"],
            },
            {
                "key": "record",
                "label": "生产流转记录管理",
                "backend_keywords": ["farm", "process", "inspection", "storage", "logistics", "sale", "record"],
                "frontend_keywords": ["farmrecords", "processrecords", "inspectionreports", "storagerecords", "logisticsrecords", "salerecords"],
                "backend_preferred_paths": ["record_service.go", "record_flow_service.go", "record_list_service.go"],
                "frontend_preferred_paths": ["farmrecordspage.vue", "processrecordspage.vue", "inspectionreportspage.vue", "storagerecordspage.vue", "logisticsrecordspage.vue", "salerecordspage.vue"],
            },
            {
                "key": "trace",
                "label": "溯源码与追溯查询",
                "backend_keywords": ["trace", "tracecode", "qrcode", "querytrace", "batchtrace"],
                "frontend_keywords": ["trace", "tracecodes", "batchtrace", "tracequery", "traceresult", "qrcode"],
                "backend_preferred_paths": ["trace_service.go", "trace_extra_service.go", "trace_timeline.go"],
                "frontend_preferred_paths": ["tracecodespage.vue", "traceresultpage.vue", "batchtracepage.vue", "tracequerypage.vue"],
            },
            {
                "key": "regulator",
                "label": "监管预警与审计分析",
                "backend_keywords": ["warning", "freeze", "unfreeze", "recall", "dashboard", "log", "tx", "blockchain"],
                "frontend_keywords": ["warnings", "dashboard", "logs", "txrecords", "blockchainstatus", "recallanalysis"],
                "backend_preferred_paths": ["admin_extra_service.go", "blockchain_service.go", "admin_config_service.go", "admin_service.go"],
                "frontend_preferred_paths": ["warningspage.vue", "dashboardpage.vue", "txrecordspage.vue", "blockchainstatuspage.vue", "recallanalysispage.vue"],
            },
        ]
    return [
        {
            "key": "identity",
            "label": "用户与身份管理",
            "backend_keywords": ["auth", "login", "register", "user", "jwt"],
            "frontend_keywords": ["login", "register", "profile", "auth", "user"],
            "backend_preferred_paths": ["auth", "user", "permission", "router"],
            "frontend_preferred_paths": ["login", "register", "profile", "router"],
        },
        {
            "key": "core",
            "label": "核心业务管理",
            "backend_keywords": ["record", "data", "batch", "business", "create", "query"],
            "frontend_keywords": ["record", "data", "batch", "business", "query"],
            "backend_preferred_paths": ["record", "batch", "business", "core"],
            "frontend_preferred_paths": ["record", "batch", "data", "business"],
        },
        {
            "key": "security",
            "label": "权限控制与审计",
            "backend_keywords": ["access", "permission", "audit", "trace", "log"],
            "frontend_keywords": ["permission", "audit", "trace", "logs", "dashboard"],
            "backend_preferred_paths": ["access", "permission", "audit", "trace"],
            "frontend_preferred_paths": ["permission", "audit", "logs", "dashboard"],
        },
    ]


def _list_backend_files(backend_dir: Path | None) -> list[Path]:
    if backend_dir is None or not backend_dir.exists():
        return []
    allowed_suffixes = {".go", ".java", ".kt", ".js", ".ts"}
    candidates: list[Path] = []
    for path in sorted(backend_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue
        if path.name.lower().endswith(("_test.go", "_test.java", ".spec.ts", ".spec.js", ".test.ts", ".test.js")):
            continue
        rel = "/".join(path.relative_to(backend_dir).parts).lower()
        if any(token in rel for token in ["service", "handler", "middleware", "auth", "fabric", "router", "controller"]):
            candidates.append(path)
    return candidates


def _list_frontend_files(frontend_dir: Path | None) -> list[Path]:
    if frontend_dir is None or not frontend_dir.exists():
        return []
    allowed_suffixes = {".vue", ".tsx", ".jsx", ".ts", ".js"}
    candidates: list[Path] = []
    for path in sorted(frontend_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue
        rel = "/".join(path.relative_to(frontend_dir).parts).lower()
        if any(token in rel for token in ["pages/", "views/", "router/", "stores/", "services/", "constants/"]):
            candidates.append(path)
    return candidates


def _function_like(line: str) -> bool:
    clean = line.strip()
    if not clean:
        return False
    patterns = [
        r"^func\b",
        r"^(public|private|protected)\b",
        r"^(async\s+)?function\b",
        r"^export\s+(async\s+)?function\b",
        r"^(const|let|var)\s+[A-Za-z0-9_]+\s*=\s*(async\s*)?\([^\)]*\)\s*=>",
        r"^async\s+function\b",
        r"^router\.",
        r"^onMounted\(",
        r"^watch\(",
        r"^<script",
        r"^<template",
    ]
    return any(re.search(pattern, clean) for pattern in patterns)


def _extract_symbol(line: str, path: Path) -> str:
    patterns = [
        re.compile(r"func\s*(?:\([^\)]*\)\s*)?([A-Za-z0-9_]+)\s*\("),
        re.compile(r"(?:public|private|protected)\s+[A-Za-z0-9_<>,\[\]\s]+\s+([A-Za-z0-9_]+)\s*\("),
        re.compile(r"(?:const|let|var)\s+([A-Za-z0-9_]+)\s*="),
        re.compile(r"(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\("),
    ]
    for pattern in patterns:
        match = pattern.search(line)
        if match:
            return match.group(1)
    if "<script" in line:
        return f"{path.stem}-script"
    if "<template" in line:
        return f"{path.stem}-template"
    return path.stem


def _language_for_path(path: Path) -> str:
    mapping = {
        ".go": "go",
        ".java": "java",
        ".kt": "kotlin",
        ".ts": "ts",
        ".tsx": "tsx",
        ".js": "js",
        ".jsx": "jsx",
        ".vue": "vue",
    }
    return mapping.get(path.suffix.lower(), "text")


def _ordered_path_bonus(path_lower: str, filename_lower: str, tokens: list[str]) -> int:
    score = 0
    for index, raw_token in enumerate(tokens):
        token = raw_token.lower().strip()
        if not token:
            continue
        if token == filename_lower:
            score += max(16, 60 - index * 12)
            continue
        if token in path_lower:
            score += max(10, 36 - index * 6)
    return score


def _generic_penalty(path_lower: str, side: str) -> int:
    penalties = 0
    if side == "backend":
        if "blockchain_retry_service.go" in path_lower:
            penalties += 56
        if "retry" in path_lower:
            penalties += 24
        if path_lower.endswith("router.go"):
            penalties += 20
        if any(token in path_lower for token in ["helper", "dto", "errors", "support"]):
            penalties += 18
        if "config_service" in path_lower:
            penalties += 6
    else:
        if "/system/" in path_lower or "\\system\\" in path_lower:
            penalties += 18
    return penalties


def _score_file(path: Path, text: str, spec: dict[str, Any], side: str) -> int:
    path_lower = str(path).lower()
    filename_lower = path.name.lower()
    text_lower = text.lower()
    keywords = spec["backend_keywords"] if side == "backend" else spec["frontend_keywords"]
    preferred_paths = spec.get(f"{side}_preferred_paths", [])
    score = 0
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in filename_lower:
            score += 14
        elif keyword_lower in path_lower:
            score += 6
        score += min(text_lower.count(keyword_lower), 5)
    score += _ordered_path_bonus(path_lower, filename_lower, preferred_paths)
    score -= _generic_penalty(path_lower, side)
    if side == "backend":
        if "service" in path_lower:
            score += 10
        if "handler" in path_lower:
            score += 6
        if "middleware" in path_lower or "auth" in path_lower:
            score += 4
        if path.name.lower() == "router.go":
            score += 2
    else:
        if "/pages/" in path_lower or "\\pages\\" in path_lower:
            score += 10
        if path.name.endswith("Page.vue"):
            score += 6
        if "/stores/" in path_lower or "\\stores\\" in path_lower:
            score += 4
        if "/router/" in path_lower or "\\router\\" in path_lower:
            score += 3
    return score


def _script_range(lines: list[str]) -> tuple[int, int] | None:
    start = None
    for idx, line in enumerate(lines):
        if "<script" in line:
            start = idx
            break
    if start is None:
        return None
    for idx in range(start + 1, len(lines)):
        if "</script>" in lines[idx]:
            return start, idx
    return None


def _template_range(lines: list[str]) -> tuple[int, int] | None:
    start = None
    for idx, line in enumerate(lines):
        if "<template" in line:
            start = idx
            break
    if start is None:
        return None
    for idx in range(start + 1, len(lines)):
        if "</template>" in lines[idx]:
            return start, idx
    return None


def _choose_anchor_line(lines: list[str], allowed_start: int, allowed_end: int, keywords: list[str]) -> int:
    best_idx = allowed_start
    best_score = -1
    for idx in range(allowed_start, allowed_end):
        clean = lines[idx].strip()
        if not clean or clean.startswith("//") or clean.startswith("*"):
            continue
        score = sum(2 for keyword in keywords if keyword.lower() in clean.lower())
        if _function_like(clean):
            score += 3
        if any(token in clean for token in ["await ", "router.", "JWT", "Create", "Query", "Bind", "submit", "loadData"]):
            score += 1
        if score > best_score:
            best_score = score
            best_idx = idx
    if best_score >= 0:
        return best_idx
    for idx in range(allowed_start, allowed_end):
        if _function_like(lines[idx].strip()):
            return idx
    for idx in range(allowed_start, allowed_end):
        if lines[idx].strip():
            return idx
    return allowed_start


def _snippet_bounds(lines: list[str], allowed_start: int, allowed_end: int, anchor: int) -> tuple[int, int]:
    start = anchor
    while start > allowed_start:
        candidate = lines[start].strip()
        if _function_like(candidate):
            break
        if anchor - start > 10 and not candidate:
            start += 1
            break
        start -= 1
    if start < allowed_start:
        start = allowed_start
    if not lines[start].strip():
        start = max(allowed_start, anchor - 4)

    end = min(allowed_end, start + 24)
    brace_balance = 0
    saw_brace = False
    for idx in range(start, min(allowed_end, start + 40)):
        line = lines[idx]
        brace_balance += line.count("{") - line.count("}")
        if "{" in line:
            saw_brace = True
        if idx - start >= 7 and saw_brace and brace_balance <= 0 and line.strip().endswith("}"):
            end = idx + 1
            break
        if idx - start >= 12 and not line.strip() and not saw_brace:
            end = idx
            break
    if end - start < 8:
        end = min(allowed_end, start + 12)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return start, end


def _template_snippet_bounds(lines: list[str], allowed_start: int, allowed_end: int, anchor: int) -> tuple[int, int]:
    start = max(allowed_start, anchor - 4)
    end = min(allowed_end, anchor + 14)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return start, end


def _candidate_score(symbol: str, snippet: str, keywords: list[str]) -> int:
    symbol_lower = symbol.lower()
    snippet_lower = snippet.lower()
    score = 0
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in symbol_lower:
            score += 5
        score += min(snippet_lower.count(keyword_lower), 3)
    for token in ["login", "register", "audit", "bind", "list", "update", "query", "submit", "load", "create"]:
        if token in symbol_lower:
            score += 2
    return score


def _extract_snippet_candidates(path: Path, keywords: list[str], side: str, max_candidates: int = 2) -> list[dict[str, Any]]:
    text = read_text_safe(path)
    lines = text.splitlines()
    if not lines:
        return []

    candidates: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, int, int]] = set()

    def _append_candidate(start: int, end: int, symbol: str) -> None:
        snippet = "\n".join(lines[start:end]).strip()
        if not snippet:
            return
        key = (symbol, start, end)
        if key in seen_keys:
            return
        seen_keys.add(key)
        candidates.append(
            {
                "symbol": symbol,
                "language": _language_for_path(path),
                "snippet": snippet + "\n",
                "line_start": start + 1,
                "line_end": end,
                "score": _candidate_score(symbol, snippet, keywords),
            }
        )

    allowed_start = 0
    allowed_end = len(lines)
    if path.suffix.lower() == ".vue" and side == "frontend":
        script = _script_range(lines)
        if script:
            allowed_start = script[0] + 1
            allowed_end = script[1]

    for idx in range(allowed_start, allowed_end):
        clean = lines[idx].strip()
        if not _function_like(clean):
            continue
        start, end = _snippet_bounds(lines, allowed_start, allowed_end, idx)
        _append_candidate(start, end, _extract_symbol(lines[start].strip(), path))

    if path.suffix.lower() == ".vue" and side == "frontend":
        template = _template_range(lines)
        if template:
            tpl_start = template[0] + 1
            tpl_end = template[1]
            template_markers = ["<a-form", "<a-table", "<a-modal", "<PageIntro", "<router-link", "class=\"toolbar\"", "class='toolbar'"]
            for idx in range(tpl_start, tpl_end):
                clean = lines[idx].strip()
                if not clean or not any(marker in clean for marker in template_markers):
                    continue
                start, end = _template_snippet_bounds(lines, tpl_start, tpl_end, idx)
                _append_candidate(start, end, f"{path.stem}-template")

    if not candidates:
        fallback = _extract_snippet(path, keywords, side)
        return [fallback] if fallback else []

    candidates.sort(key=lambda item: (-item["score"], item["line_start"], item["symbol"]))
    return candidates[:max_candidates]


def _extract_snippet(path: Path, keywords: list[str], side: str) -> dict[str, Any] | None:
    text = read_text_safe(path)
    lines = text.splitlines()
    if not lines:
        return None

    allowed_start = 0
    allowed_end = len(lines)
    if path.suffix.lower() == ".vue" and side == "frontend":
        script = _script_range(lines)
        if script:
            allowed_start = script[0] + 1
            allowed_end = script[1]

    anchor = _choose_anchor_line(lines, allowed_start, allowed_end, keywords)
    start, end = _snippet_bounds(lines, allowed_start, allowed_end, anchor)
    snippet = "\n".join(lines[start:end]).strip()
    if not snippet:
        return None

    return {
        "symbol": _extract_symbol(lines[start].strip(), path),
        "language": _language_for_path(path),
        "snippet": snippet + "\n",
        "line_start": start + 1,
        "line_end": end,
    }


def _select_files(files: list[Path], spec: dict[str, Any], side: str, limit: int = 2) -> list[Path]:
    scored: list[tuple[int, Path]] = []
    for path in files:
        text = read_text_safe(path)
        score = _score_file(path, text, spec, side)
        if score <= 0:
            continue
        scored.append((score, path))
    scored.sort(key=lambda item: (-item[0], str(item[1])))
    selected: list[Path] = []
    seen: set[str] = set()
    for _, path in scored:
        rel = str(path)
        if rel in seen:
            continue
        seen.add(rel)
        selected.append(path)
        if len(selected) >= limit:
            break
    return selected


def _snippet_filename(entry_id: str, path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".") or "txt"
    return f"{entry_id}.snippet.{suffix}"


def _render_code_screenshot(snippet: str, source_path: Path, output_path: Path) -> str | None:
    _ = source_path
    return render_code_lines_image(
        snippet.splitlines(),
        output_path,
        font_candidates=_code_screenshot_font_candidates(),
        font_size=CODE_SCREENSHOT_FONT_SIZE_PX,
        padding_x=CODE_SCREENSHOT_IMAGE_PAD_PX,
        padding_y=CODE_SCREENSHOT_IMAGE_PAD_PX,
        line_pad=CODE_SCREENSHOT_LINE_PAD_PX,
        border_px=CODE_SCREENSHOT_BORDER_PX,
        max_content_width_px=CODE_SCREENSHOT_MAX_CONTENT_WIDTH_PX,
        fixed_canvas_width_px=CODE_SCREENSHOT_MAX_CONTENT_WIDTH_PX,
    )


def _render_pack_md(pack: dict[str, Any]) -> str:
    lines = [
        "# Code Evidence Pack",
        "",
        f"- schema_version: {pack['metadata']['schema_version']}",
        f"- generated_at: {pack['metadata']['generated_at']}",
        f"- title: {pack['metadata']['title']}",
        f"- code_screenshot_font: {pack['metadata'].get('code_screenshot_font', 'default')}",
        f"- total_entries: {len(pack['entries'])}",
        "",
    ]
    for module in pack["modules"]:
        lines.append(f"## {module['label']}")
        lines.append("")
        lines.append(f"- module_key: {module['key']}")
        lines.append(f"- backend_entries: {module['backend_count']}")
        lines.append(f"- frontend_entries: {module['frontend_count']}")
        lines.append("")
        lines.append("| id | side | symbol | source | lines | screenshot |")
        lines.append("|---|---|---|---|---|---|")
        module_entries = [entry for entry in pack["entries"] if entry["module_key"] == module["key"]]
        if not module_entries:
            lines.append("| none | - | - | - | - | - |")
        for entry in module_entries:
            line_span = f"{entry['line_start']}-{entry['line_end']}"
            lines.append(
                f"| {entry['id']} | {entry['side']} | {entry['symbol']} | `{entry['source_path']}` | "
                f"{line_span} | `{entry['screenshot_path']}` |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def build_code_evidence_pack(ctx: dict[str, Any], output_paths: dict[str, Path] | None = None) -> dict[str, Any]:
    workspace_root = ctx["workspace_root"]
    manifest = ctx["manifest"]
    project_root = Path(manifest["project_root"]).resolve()
    output_paths = output_paths or material_output_paths(ctx["config"], workspace_root)

    for generated_dir in (output_paths["code_snippets_dir"], output_paths["code_screenshots_dir"]):
        if generated_dir.exists():
            shutil.rmtree(generated_dir)
        generated_dir.mkdir(parents=True, exist_ok=True)

    source_paths = manifest.get("source_paths", {})
    backend_dir = _abs_project_path(project_root, source_paths.get("backend"))
    frontend_dir = _abs_project_path(project_root, source_paths.get("frontend"))
    backend_files = _list_backend_files(backend_dir)
    frontend_files = _list_frontend_files(frontend_dir)

    domain_key = _detect_domain_key(manifest.get("title", ""))
    module_specs = _module_specs(domain_key)
    entries: list[dict[str, Any]] = []
    module_summary: list[dict[str, Any]] = []
    selected_code_screenshot_font: str | None = None

    for module_index, spec in enumerate(module_specs, start=1):
        backend_selected = _select_files(backend_files, spec, "backend", limit=int(spec.get("backend_file_limit", 4) or 4))
        frontend_selected = _select_files(frontend_files, spec, "frontend", limit=int(spec.get("frontend_file_limit", 4) or 4))
        module_summary.append(
            {
                "key": spec["key"],
                "label": spec["label"],
                "backend_count": 0,
                "frontend_count": 0,
            }
        )
        side_entry_counts = {"backend": 0, "frontend": 0}
        for side, selected_files in [("backend", backend_selected), ("frontend", frontend_selected)]:
            keywords = spec["backend_keywords"] if side == "backend" else spec["frontend_keywords"]
            for idx, path in enumerate(selected_files, start=1):
                snippet_candidates = _extract_snippet_candidates(
                    path,
                    keywords,
                    side,
                    max_candidates=int(spec.get(f"{side}_snippets_per_file", 2) or 2),
                )
                for snippet_info in snippet_candidates:
                    side_entry_counts[side] += 1
                    entry_id = f"{module_index:02d}-{spec['key']}-{side}-{side_entry_counts[side]:02d}-{_slug(snippet_info['symbol'])}"
                    snippet_filename = _snippet_filename(entry_id, path)
                    screenshot_filename = f"{entry_id}.png"
                    snippet_path = output_paths["code_snippets_dir"] / snippet_filename
                    screenshot_path = output_paths["code_screenshots_dir"] / screenshot_filename
                    write_text(snippet_path, snippet_info["snippet"])
                    used_font = _render_code_screenshot(snippet_info["snippet"], path, screenshot_path)
                    if selected_code_screenshot_font is None and used_font:
                        selected_code_screenshot_font = used_font
                    entries.append(
                        {
                            "id": entry_id,
                            "module_key": spec["key"],
                            "module_label": spec["label"],
                            "side": side,
                            "language": snippet_info["language"],
                            "source_path": make_relative(path, project_root),
                            "symbol": snippet_info["symbol"],
                            "line_start": snippet_info["line_start"],
                            "line_end": snippet_info["line_end"],
                            "snippet_path": make_relative(snippet_path, workspace_root),
                            "screenshot_path": make_relative(screenshot_path, workspace_root),
                            "caption": f"{spec['label']}模块{('后端' if side == 'backend' else '前端')}关键实现代码截图",
                            "selected_reason": f"根据模块关键词 {', '.join(keywords[:4])} 从真实源码中摘录。",
                            "chapter_candidates": ["05-系统实现.md"],
                            "section_candidates": [spec["label"]],
                        }
                    )
        module_summary[-1]["backend_count"] = side_entry_counts["backend"]
        module_summary[-1]["frontend_count"] = side_entry_counts["frontend"]

    pack = {
        "metadata": {
            "schema_version": CODE_EVIDENCE_SCHEMA_VERSION,
            "generated_at": _now_iso(),
            "title": manifest["title"],
            "project_root": str(project_root),
            "domain_key": domain_key,
            "code_screenshot_font": selected_code_screenshot_font or "default",
        },
        "modules": module_summary,
        "entries": entries,
    }
    write_json(output_paths["code_evidence_pack_json"], pack)
    write_text(output_paths["code_evidence_pack_md"], _render_pack_md(pack))
    return pack


def run_extract_code(config_path: Path) -> dict[str, Path]:
    ctx = load_workspace_context(config_path)
    output_paths = material_output_paths(ctx["config"], ctx["workspace_root"])
    build_code_evidence_pack(ctx, output_paths)
    return {
        "code_evidence_pack_json": output_paths["code_evidence_pack_json"],
        "code_evidence_pack_md": output_paths["code_evidence_pack_md"],
        "code_snippets_dir": output_paths["code_snippets_dir"],
        "code_screenshots_dir": output_paths["code_screenshots_dir"],
    }
