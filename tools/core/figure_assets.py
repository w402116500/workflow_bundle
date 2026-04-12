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
from PIL import Image, ImageChops, ImageDraw, ImageFont

from core.ai_image_generation import ai_override_blocking_entries, ai_override_map
from core.page_screenshot_assets import stage_chapter5_test_screenshots
from core.project_common import load_workspace_context, make_relative, material_output_paths, read_json, write_json, writing_output_paths


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
USE_CASE_RENDERER_VERSION = "v3-clustered-uml-use-case"
ARCHITECTURE_RENDERER_VERSION = "v1-layered-domain-fallback-architecture"
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


def _use_case_system_name(system_name: str) -> str:
    match = re.match(r"^基于.+?的(.+系统)$", system_name)
    if match:
        return match.group(1).strip()
    return system_name

def _load_project_profile(config: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    profile_path = writing_output_paths(config, workspace_root)["project_profile_json"]
    if not profile_path.exists():
        return {}
    return read_json(profile_path)

def _use_case_node(node_id: str, label: str) -> dict[str, str]:
    return {"id": node_id, "label": label}

def _use_case_cluster(actor: str, *nodes: tuple[str, str]) -> dict[str, Any]:
    return {
        "actor": actor,
        "use_cases": [_use_case_node(node_id, label) for node_id, label in nodes],
    }

def _traceability_use_case_payload(system_name: str) -> dict[str, Any]:
    return {
        "chart_title": "系统用例图",
        "system_name": _use_case_system_name(system_name),
        "left_clusters": [
            _use_case_cluster(
                "茶农",
                ("farmer_login", "注册登录"),
                ("garden_manage", "茶园管理"),
                ("batch_create", "批次建档"),
                ("farm_record", "农事记录提交"),
                ("trace_bind", "溯源码绑定"),
            ),
            _use_case_cluster(
                "加工厂",
                ("processor_login", "注册登录"),
                ("batch_receive", "批次接收"),
                ("process_record", "加工记录提交"),
            ),
            _use_case_cluster(
                "质检机构",
                ("inspector_login", "注册登录"),
                ("inspection_submit", "质检报告提交"),
                ("warning_report", "异常上报"),
            ),
            _use_case_cluster(
                "物流商",
                ("logistics_login", "注册登录"),
                ("storage_submit", "仓储物流提交"),
            ),
        ],
        "right_clusters": [
            _use_case_cluster(
                "经销商",
                ("dealer_login", "注册登录"),
                ("sale_submit", "销售记录提交"),
            ),
            _use_case_cluster(
                "消费者",
                ("public_trace_query", "公开追溯查询"),
            ),
            _use_case_cluster(
                "管理员",
                ("org_audit", "机构审核"),
                ("user_manage", "用户管理"),
                ("full_supervision", "全流程监管"),
                ("warning_handle", "预警处置"),
            ),
            _use_case_cluster(
                "监管方",
                ("supervision_query", "监管查询"),
                ("abnormal_review", "异常复核"),
            ),
        ],
        "floating_use_cases": [
            {"id": "identity_bind", "label": "链上身份绑定", "anchor": "org_audit", "placement": "left", "distance": 420, "dy": 0},
            {"id": "trace_result", "label": "结果展示/真伪校验", "anchor": "public_trace_query", "placement": "left", "distance": 420, "dy": 0},
            {"id": "freeze_dispose", "label": "冻结/解冻处置", "anchor": "warning_handle", "placement": "left", "distance": 420, "dy": 0},
        ],
        "relations": [
            {"type": "include", "from": "org_audit", "to": "identity_bind"},
            {"type": "include", "from": "public_trace_query", "to": "trace_result"},
            {"type": "extend", "from": "freeze_dispose", "to": "warning_handle"},
        ],
    }

def _health_record_use_case_payload(system_name: str) -> dict[str, Any]:
    return {
        "chart_title": "系统用例图",
        "system_name": _use_case_system_name(system_name),
        "left_clusters": [
            _use_case_cluster(
                "患者",
                ("patient_login", "注册登录"),
                ("patient_profile", "修改个人信息"),
                ("patient_view_record", "查看档案"),
                ("auth_manage", "授权管理"),
                ("patient_notice", "查看消息/公告"),
                ("patient_feedback", "提交问题反馈"),
            ),
            _use_case_cluster(
                "医生",
                ("doctor_login", "注册登录"),
                ("qualification_upload", "资质上传"),
                ("patient_query", "查询患者"),
                ("diagnosis_upload", "上传诊断记录"),
                ("doctor_notice", "查看消息/公告"),
                ("doctor_feedback", "提交问题反馈"),
            ),
        ],
        "right_clusters": [
            _use_case_cluster(
                "管理员",
                ("user_manage", "用户管理"),
                ("doctor_review", "医生审核"),
                ("publish_notice", "发布公告"),
                ("audit_log", "查看审计日志"),
                ("feedback_handle", "反馈处理"),
            ),
        ],
        "floating_use_cases": [
            {"id": "report_medication", "label": "检查报告/用药记录", "anchor": "patient_view_record", "placement": "right", "distance": 470, "dy": 0},
            {"id": "revoke_auth", "label": "撤销授权", "anchor": "auth_manage", "placement": "right", "distance": 420, "dy": 0},
            {"id": "apply_auth", "label": "申请授权", "anchor": "patient_query", "placement": "right", "distance": 420, "dy": 0},
            {"id": "confirm_patient", "label": "确认患者信息", "anchor": "diagnosis_upload", "placement": "right", "distance": 420, "dy": 0},
            {"id": "feedback_reply", "label": "回复/标记处理", "anchor": "feedback_handle", "placement": "below", "distance": 170, "dy": 0},
        ],
        "relations": [
            {"type": "include", "from": "patient_view_record", "to": "report_medication"},
            {"type": "extend", "from": "revoke_auth", "to": "auth_manage"},
            {"type": "extend", "from": "patient_query", "to": "apply_auth"},
            {"type": "include", "from": "diagnosis_upload", "to": "confirm_patient"},
            {"type": "include", "from": "feedback_handle", "to": "feedback_reply"},
        ],
    }

def _generic_use_case_payload(system_name: str, modules: list[dict[str, Any]], roles: list[str]) -> dict[str, Any]:
    labels: list[str] = []
    for module in modules[: max(2, min(6, len(roles)))]:
        label = str(module.get("label", "")).strip()
        if not label:
            continue
        label = re.sub(r"模块$", "", label).strip()
        if label not in labels:
            labels.append(label)
    if not labels:
        labels = ["注册登录", "业务处理", "结果查询"]

    left_roles = roles[: math.ceil(len(roles) / 2)]
    right_roles = roles[math.ceil(len(roles) / 2) :]
    left_clusters = []
    right_clusters = []
    for role in left_roles:
        left_clusters.append(
            _use_case_cluster(role, *[(f"{_slug(role)}_{idx}", label) for idx, label in enumerate(labels[: min(3, len(labels))], start=1)])
        )
    for role in right_roles:
        right_clusters.append(
            _use_case_cluster(role, *[(f"{_slug(role)}_{idx}", label) for idx, label in enumerate(labels[: min(3, len(labels))], start=1)])
        )

    return {
        "chart_title": "系统用例图",
        "system_name": _use_case_system_name(system_name),
        "left_clusters": left_clusters,
        "right_clusters": right_clusters,
        "floating_use_cases": [],
        "relations": [],
    }

def _build_use_case_payload(config: dict[str, Any], manifest: dict[str, Any], workspace_root: Path) -> dict[str, Any] | None:
    project_profile = _load_project_profile(config, workspace_root)
    roles = [str(item).strip() for item in project_profile.get("roles", []) if str(item).strip()]
    if not roles:
        return None

    core_modules = list(project_profile.get("core_modules", []) or [])
    metadata = project_profile.get("metadata", {}) or {}
    domain_key = _infer_domain_key(config, manifest, workspace_root, roles)

    system_name = _root_system_label(config.get("metadata", {}).get("title") or manifest.get("title", "系统"))
    if domain_key == "traceability":
        return _traceability_use_case_payload(system_name)
    if domain_key == "health_record":
        return _health_record_use_case_payload(system_name)
    return _generic_use_case_payload(system_name, core_modules, roles)

def _infer_domain_key(
    config: dict[str, Any],
    manifest: dict[str, Any],
    workspace_root: Path,
    roles: list[str] | None = None,
) -> str:
    project_profile = _load_project_profile(config, workspace_root)
    metadata = project_profile.get("metadata", {}) or {}
    raw_domain = str(metadata.get("domain_key") or config.get("metadata", {}).get("domain_key") or "").strip().lower()
    if raw_domain:
        return raw_domain

    title = f"{config.get('metadata', {}).get('title', '')} {manifest.get('title', '')}".lower()
    role_text = " ".join(str(item).strip().lower() for item in (roles or project_profile.get("roles", []) or []))
    text = f"{title} {role_text}"

    health_tokens = ("health", "ehr", "medical", "doctor", "patient", "健康", "病历", "医疗", "患者", "医生")
    trace_tokens = ("traceability", "trace", "batch", "tea", "logistics", "溯源", "批次", "茶叶", "物流", "经销")
    if any(token in text for token in health_tokens):
        return "health_record"
    if any(token in text for token in trace_tokens):
        return "traceability"
    return "generic_blockchain"

def _health_record_architecture_payload(system_name: str, chain_platform: str) -> dict[str, Any]:
    chain_label = "FISCO BCOS 联盟链" if chain_platform == "fisco" else "联盟链可信存证层"
    return {
        "system_name": system_name,
        "top_label": "统一业务入口",
        "top_note": "患者、医生与管理员通过前端页面进入同一业务体系",
        "presentation": {
            "title": "表现层",
            "items": ["患者端页面", "医生端页面", "管理员后台"],
        },
        "business": {
            "title": "业务层",
            "items": ["身份鉴权与会话管理", "健康档案管理服务", "授权与撤销服务", "合约调用与审计回写"],
        },
        "data": {
            "title": "数据层",
            "items": ["账户与资料数据", "健康档案密文", "授权 / 日志 / 交易记录"],
        },
        "chain": {
            "title": "可信存证层",
            "items": [chain_label, "EhrAccessRegistry 合约", "档案摘要 / 授权状态 / 时间戳"],
        },
        "links": [
            {"label": "页面访问与结果回显", "from": "top", "to": "presentation"},
            {"label": "业务请求 / 权限判断", "from": "presentation", "to": "business"},
            {"label": "链下数据持久化", "from": "business", "to": "data"},
            {"label": "链上存证 / 状态校验", "from": "business", "to": "chain"},
        ],
    }

def _traceability_architecture_payload(system_name: str, chain_platform: str) -> dict[str, Any]:
    chain_label = "联盟链网络" if chain_platform == "fabric" else "联盟链平台"
    return {
        "system_name": system_name,
        "top_label": "多角色协同入口",
        "top_note": "业务工作台、公开查询端与监管分析端共享同一后端服务",
        "presentation": {
            "title": "表现层",
            "items": ["业务工作台", "公开追溯页面", "监管分析页面"],
        },
        "business": {
            "title": "业务层",
            "items": ["身份鉴权与流程编排", "批次 / 流转记录服务", "追溯查询与预警服务", "链码 / 合约调用适配"],
        },
        "data": {
            "title": "数据层",
            "items": ["机构与用户数据", "批次与阶段记录", "日志与交易映射"],
        },
        "chain": {
            "title": "可信存证层",
            "items": [chain_label, "链码 / 合约能力", "批次状态 / 追溯凭证"],
        },
        "links": [
            {"label": "业务操作与结果展示", "from": "top", "to": "presentation"},
            {"label": "请求编排 / 状态控制", "from": "presentation", "to": "business"},
            {"label": "链下数据持久化", "from": "business", "to": "data"},
            {"label": "链上登记 / 状态校验", "from": "business", "to": "chain"},
        ],
    }

def _generic_architecture_payload(
    system_name: str,
    manifest: dict[str, Any],
    chain_platform: str,
) -> dict[str, Any]:
    stack = manifest.get("detected_stack", {}) or {}
    frontend = str(stack.get("frontend_framework") or "前端页面").strip()
    backend = str(stack.get("backend_framework") or "后端服务").strip()
    database = str(stack.get("database_kind") or "关系数据库").strip()
    chain_sdk = str(stack.get("chain_sdk") or "链交互组件").strip()
    chain_label = "区块链平台" if chain_platform == "auto" else chain_platform.upper()
    return {
        "system_name": system_name,
        "top_label": "统一业务入口",
        "top_note": "前端请求经后端编排后分别落入数据库与链上可信状态",
        "presentation": {
            "title": "表现层",
            "items": [frontend, "业务页面交互", "结果展示与反馈"],
        },
        "business": {
            "title": "业务层",
            "items": [backend, "权限判断与业务编排", "链交互适配", "日志与状态回写"],
        },
        "data": {
            "title": "数据层",
            "items": [database, "主业务数据", "审计与交易日志"],
        },
        "chain": {
            "title": "可信存证层",
            "items": [chain_label, chain_sdk, "关键状态 / 摘要存证"],
        },
        "links": [
            {"label": "访问请求", "from": "top", "to": "presentation"},
            {"label": "接口调用", "from": "presentation", "to": "business"},
            {"label": "链下存储", "from": "business", "to": "data"},
            {"label": "链上校验", "from": "business", "to": "chain"},
        ],
    }

def _build_architecture_payload(config: dict[str, Any], manifest: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    domain_key = _infer_domain_key(config, manifest, workspace_root)
    system_name = _root_system_label(config.get("metadata", {}).get("title") or manifest.get("title", "系统"))
    chain_platform = str(config.get("metadata", {}).get("chain_platform") or manifest.get("chain_platform") or "auto").strip().lower()
    if domain_key == "health_record":
        return _health_record_architecture_payload(system_name, chain_platform)
    if domain_key == "traceability":
        return _traceability_architecture_payload(system_name, chain_platform)
    return _generic_architecture_payload(system_name, manifest, chain_platform)

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


def _draw_titled_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    items: list[str],
    *,
    title_font: ImageFont.ImageFont,
    item_font: ImageFont.ImageFont,
    outline: tuple[int, int, int] = (0, 0, 0),
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=14, outline=outline, fill=(255, 255, 255), width=2)
    title_height = 42
    draw.line((x1, y1 + title_height, x2, y1 + title_height), fill=outline, width=2)
    _center_text(draw, (x1 + 8, y1 + 4, x2 - 8, y1 + title_height - 4), title, title_font, outline)

    body_top = y1 + title_height + 18
    body_bottom = y2 - 18
    if not items:
        return

    count = len(items)
    gap = 22
    left_padding = 22
    usable_width = (x2 - x1) - left_padding * 2 - gap * max(count - 1, 0)
    item_width = max(120, int(usable_width / max(count, 1)))
    item_height = min(74, max(58, body_bottom - body_top))
    item_top = body_top + max(0, (body_bottom - body_top - item_height) // 2)
    wrap_width = 9 if item_width <= 180 else 11 if item_width <= 230 else 13

    for idx, item in enumerate(items):
        bx1 = x1 + left_padding + idx * (item_width + gap)
        bx2 = min(bx1 + item_width, x2 - left_padding)
        item_box = (bx1, item_top, bx2, item_top + item_height)
        draw.rounded_rectangle(item_box, radius=9, outline=outline, fill=(255, 255, 255), width=2)
        _center_text(draw, item_box, _wrap_text(item, wrap_width), item_font, outline)

def _panel_center_top(box: tuple[int, int, int, int]) -> tuple[int, int]:
    return ((box[0] + box[2]) // 2, box[1])

def _panel_center_bottom(box: tuple[int, int, int, int]) -> tuple[int, int]:
    return ((box[0] + box[2]) // 2, box[3])

def _draw_centered_label(draw: ImageDraw.ImageDraw, center: tuple[int, int], text: str, font: ImageFont.ImageFont) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = int(center[0] - w / 2)
    y = int(center[1] - h / 2)
    draw.rectangle((x - 4, y - 2, x + w + 4, y + h + 2), fill=(255, 255, 255))
    draw.text((x, y), text, font=font, fill=(0, 0, 0))

def _crop_white_margin(image: Image.Image, *, padding: int = 48) -> Image.Image:
    background = Image.new(image.mode, image.size, (255, 255, 255))
    diff = ImageChops.difference(image, background)
    bbox = diff.getbbox()
    if not bbox:
        return image
    x1, y1, x2, y2 = bbox
    return image.crop(
        (
            max(0, x1 - padding),
            max(0, y1 - padding),
            min(image.size[0], x2 + padding),
            min(image.size[1], y2 + padding),
        )
    )

def _box_from_center(center: tuple[int, int], size: tuple[int, int]) -> tuple[int, int, int, int]:
    cx, cy = center
    width, height = size
    return (cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2)

def _ellipse_anchor_towards(box: tuple[int, int, int, int], target: tuple[int, int]) -> tuple[int, int]:
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    dx = target[0] - cx
    dy = target[1] - cy
    rx = max((x2 - x1) / 2, 1.0)
    ry = max((y2 - y1) / 2, 1.0)
    if dx == 0 and dy == 0:
        return (int(cx), int(cy))
    scale = 1.0 / math.sqrt((dx * dx) / (rx * rx) + (dy * dy) / (ry * ry))
    return (int(cx + dx * scale), int(cy + dy * scale))

def _draw_attribute_ellipse(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
    *,
    fill: tuple[int, int, int] = (255, 255, 255),
    outline: tuple[int, int, int] = (0, 0, 0),
    underline: bool = False,
) -> None:
    draw.ellipse(box, fill=fill, outline=outline, width=3)
    x1, y1, x2, y2 = box
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x1 + (x2 - x1 - tw) / 2
    ty = y1 + (y2 - y1 - th) / 2
    draw.text((tx, ty), text, font=font, fill=outline)
    if underline:
        underline_y = ty + th + 2
        draw.line((tx, underline_y, tx + tw, underline_y), fill=outline, width=2)

def _evenly_spaced_values(start: int, end: int, count: int) -> list[int]:
    if count <= 0:
        return []
    if count == 1:
        return [int((start + end) / 2)]
    gap = (end - start) / (count - 1)
    return [int(start + gap * index) for index in range(count)]

def _draw_actor(draw: ImageDraw.ImageDraw, center: tuple[int, int], name: str, font: ImageFont.ImageFont) -> None:
    cx, cy = center
    head_r = 24
    head_box = (cx - head_r, cy - 78, cx + head_r, cy - 30)
    draw.ellipse(head_box, fill=(255, 255, 255), outline=(0, 0, 0), width=3)
    draw.line((cx, cy - 30, cx, cy + 38), fill=(0, 0, 0), width=3)
    draw.line((cx - 34, cy - 2, cx + 34, cy - 2), fill=(0, 0, 0), width=3)
    draw.line((cx, cy + 38, cx - 30, cy + 92), fill=(0, 0, 0), width=3)
    draw.line((cx, cy + 38, cx + 30, cy + 92), fill=(0, 0, 0), width=3)
    label_box = draw.textbbox((0, 0), name, font=font)
    label_width = label_box[2] - label_box[0]
    draw.text((cx - label_width / 2, cy + 106), name, font=font, fill=(0, 0, 0))

def _actor_anchor(center: tuple[int, int], side: str) -> tuple[int, int]:
    cx, cy = center
    if side == "right":
        return (cx - 28, cy - 2)
    return (cx + 28, cy - 2)

def _draw_dashed_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    color: tuple[int, int, int] = (0, 0, 0),
    width: int = 3,
    dash: int = 20,
    gap: int = 12,
    head: int = 14,
) -> None:
    x1, y1 = start
    x2, y2 = end
    total = math.hypot(x2 - x1, y2 - y1)
    if total < 1:
        return
    dx = (x2 - x1) / total
    dy = (y2 - y1) / total
    drawn = 0.0
    while drawn < total:
        segment = min(dash, total - drawn)
        sx = x1 + dx * drawn
        sy = y1 + dy * drawn
        ex = x1 + dx * (drawn + segment)
        ey = y1 + dy * (drawn + segment)
        draw.line((sx, sy, ex, ey), fill=color, width=width)
        drawn += dash + gap
    angle = math.atan2(y2 - y1, x2 - x1)
    a1 = angle + math.pi * 0.85
    a2 = angle - math.pi * 0.85
    p3 = (x2 + head * math.cos(a1), y2 + head * math.sin(a1))
    p4 = (x2 + head * math.cos(a2), y2 + head * math.sin(a2))
    draw.polygon([end, p3, p4], fill=color)

def _use_case_node_centers(cluster_center_y: int, count: int, *, box_height: int, gap: int) -> list[int]:
    if count <= 0:
        return []
    total = count * box_height + (count - 1) * gap
    start = cluster_center_y - total / 2 + box_height / 2
    return [int(start + idx * (box_height + gap)) for idx in range(count)]

def _floating_center(anchor: tuple[int, int], placement: str, distance: int, dy: int) -> tuple[int, int]:
    x, y = anchor
    if placement == "left":
        return (x - distance, y + dy)
    if placement == "right":
        return (x + distance, y + dy)
    if placement == "above":
        return (x, y - distance + dy)
    return (x, y + distance + dy)

def _use_case_relation_label_center(start: tuple[int, int], end: tuple[int, int]) -> tuple[int, int]:
    mid_x = int((start[0] + end[0]) / 2)
    mid_y = int((start[1] + end[1]) / 2)
    dx = abs(end[0] - start[0])
    dy = abs(end[1] - start[1])
    if dx >= dy:
        return (mid_x, mid_y - 28)
    return (mid_x + 24, mid_y)

def _render_use_case_diagram_png(spec_payload: dict[str, Any], output_path: Path) -> None:
    canvas_width = 3200
    canvas_height = 2200
    image = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    boundary_box = (560, 180, 2640, 2060)
    left_use_case_x = 1120
    right_use_case_x = 2080
    actor_left_x = 150
    actor_right_x = 3050
    use_case_size = (420, 96)
    title_font = _load_font(56)
    actor_font = _load_font(28)
    use_case_font = _load_font(28)
    system_font = _load_font(40)
    relation_font = _load_font(26)

    left_clusters = list(spec_payload.get("left_clusters", []) or [])
    right_clusters = list(spec_payload.get("right_clusters", []) or [])
    floating_use_cases = list(spec_payload.get("floating_use_cases", []) or [])
    relations = list(spec_payload.get("relations", []) or [])
    chart_title = str(spec_payload.get("chart_title", "系统用例图")).strip() or "系统用例图"
    system_name = str(spec_payload.get("system_name", "系统")).strip() or "系统"

    if not left_clusters and not right_clusters:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        return

    node_boxes: dict[str, tuple[int, int, int, int]] = {}
    actor_entries: list[tuple[str, tuple[int, int], str, list[str]]] = []

    left_centers = _evenly_spaced_values(boundary_box[1] + 320, boundary_box[3] - 220, len(left_clusters))
    right_centers = _evenly_spaced_values(boundary_box[1] + 320, boundary_box[3] - 220, len(right_clusters))

    for cluster, center_y in zip(left_clusters, left_centers):
        actor_name = str(cluster.get("actor", "")).strip()
        use_cases = list(cluster.get("use_cases", []) or [])
        y_positions = _use_case_node_centers(center_y, len(use_cases), box_height=use_case_size[1], gap=28)
        node_ids: list[str] = []
        for node, node_y in zip(use_cases, y_positions):
            node_id = str(node.get("id", "")).strip()
            if not node_id:
                continue
            node_ids.append(node_id)
            node_boxes[node_id] = _box_from_center((left_use_case_x, node_y), use_case_size)
        actor_entries.append((actor_name, (actor_left_x, center_y), "left", node_ids))

    for cluster, center_y in zip(right_clusters, right_centers):
        actor_name = str(cluster.get("actor", "")).strip()
        use_cases = list(cluster.get("use_cases", []) or [])
        y_positions = _use_case_node_centers(center_y, len(use_cases), box_height=use_case_size[1], gap=28)
        node_ids: list[str] = []
        for node, node_y in zip(use_cases, y_positions):
            node_id = str(node.get("id", "")).strip()
            if not node_id:
                continue
            node_ids.append(node_id)
            node_boxes[node_id] = _box_from_center((right_use_case_x, node_y), use_case_size)
        actor_entries.append((actor_name, (actor_right_x, center_y), "right", node_ids))

    for node in floating_use_cases:
        node_id = str(node.get("id", "")).strip()
        anchor_id = str(node.get("anchor", "")).strip()
        if not node_id or anchor_id not in node_boxes:
            continue
        anchor_box = node_boxes[anchor_id]
        anchor_center = ((anchor_box[0] + anchor_box[2]) // 2, (anchor_box[1] + anchor_box[3]) // 2)
        placement = str(node.get("placement", "right"))
        distance = int(node.get("distance", 420))
        dy = int(node.get("dy", 0))
        center = _floating_center(anchor_center, placement, distance, dy)
        node_boxes[node_id] = _box_from_center(center, use_case_size)

    _center_text(draw, (0, 20, canvas_width, 100), chart_title, title_font, (0, 0, 0))
    draw.rounded_rectangle(boundary_box, radius=36, outline=(0, 0, 0), width=4, fill=(255, 255, 255))
    _center_text(draw, (boundary_box[0] + 260, boundary_box[1] + 10, boundary_box[2] - 260, boundary_box[1] + 78), system_name, system_font, (0, 0, 0))

    label_lookup: dict[str, str] = {}
    for cluster in left_clusters + right_clusters:
        for node in cluster.get("use_cases", []) or []:
            node_id = str(node.get("id", "")).strip()
            if node_id:
                label_lookup[node_id] = str(node.get("label", "")).strip()
    for node in floating_use_cases:
        node_id = str(node.get("id", "")).strip()
        if node_id:
            label_lookup[node_id] = str(node.get("label", "")).strip()

    for node_id, box in node_boxes.items():
        _draw_attribute_ellipse(draw, box, _wrap_text(label_lookup.get(node_id, ""), 10), use_case_font)

    for actor_name, center, side, node_ids in actor_entries:
        _draw_actor(draw, center, actor_name, actor_font)
        actor_anchor = _actor_anchor(center, side)
        for node_id in node_ids:
            node_box = node_boxes.get(node_id)
            if not node_box:
                continue
            node_anchor = _ellipse_anchor_towards(node_box, actor_anchor)
            draw.line((actor_anchor, node_anchor), fill=(0, 0, 0), width=3)

    for relation in relations:
        source_id = str(relation.get("from", "")).strip()
        target_id = str(relation.get("to", "")).strip()
        if source_id not in node_boxes or target_id not in node_boxes:
            continue
        source_box = node_boxes[source_id]
        target_box = node_boxes[target_id]
        source_center = ((source_box[0] + source_box[2]) // 2, (source_box[1] + source_box[3]) // 2)
        target_center = ((target_box[0] + target_box[2]) // 2, (target_box[1] + target_box[3]) // 2)
        start = _ellipse_anchor_towards(source_box, target_center)
        end = _ellipse_anchor_towards(target_box, source_center)
        _draw_dashed_arrow(draw, start, end)
        label_center = _use_case_relation_label_center(start, end)
        _draw_centered_label(draw, label_center, f"<<{relation.get('type', '')}>>", relation_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _crop_white_margin(image, padding=32).save(output_path)

def _render_architecture_png(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width = 1700
    height = 930
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    title_font = _load_font(30)
    label_font = _load_font(20)
    panel_title_font = _load_font(24)
    item_font = _load_font(20)
    note_font = _load_font(18)
    color = (0, 0, 0)

    root_box = (460, 34, 1240, 104)
    draw.rounded_rectangle(root_box, radius=12, outline=color, fill=(255, 255, 255), width=2)
    _center_text(draw, root_box, _wrap_text(str(payload.get("system_name") or "系统总体架构"), 18), title_font, color)

    top_label_box = (490, 128, 1210, 176)
    draw.rounded_rectangle(top_label_box, radius=10, outline=color, fill=(255, 255, 255), width=2)
    _center_text(draw, top_label_box, str(payload.get("top_label") or "统一业务入口"), label_font, color)

    top_note = str(payload.get("top_note") or "").strip()
    if top_note:
        note_box = (330, 182, 1370, 218)
        _center_text(draw, note_box, _wrap_text(top_note, 34), note_font, color)

    presentation_box = (150, 250, 1550, 410)
    business_box = (150, 452, 1550, 632)
    data_box = (150, 694, 780, 878)
    chain_box = (920, 694, 1550, 878)

    _draw_titled_panel(
        draw,
        presentation_box,
        str((payload.get("presentation") or {}).get("title") or "表现层"),
        list((payload.get("presentation") or {}).get("items") or []),
        title_font=panel_title_font,
        item_font=item_font,
    )
    _draw_titled_panel(
        draw,
        business_box,
        str((payload.get("business") or {}).get("title") or "业务层"),
        list((payload.get("business") or {}).get("items") or []),
        title_font=panel_title_font,
        item_font=item_font,
    )
    _draw_titled_panel(
        draw,
        data_box,
        str((payload.get("data") or {}).get("title") or "数据层"),
        list((payload.get("data") or {}).get("items") or []),
        title_font=panel_title_font,
        item_font=item_font,
    )
    _draw_titled_panel(
        draw,
        chain_box,
        str((payload.get("chain") or {}).get("title") or "可信存证层"),
        list((payload.get("chain") or {}).get("items") or []),
        title_font=panel_title_font,
        item_font=item_font,
    )

    _arrow(draw, _panel_center_bottom(root_box), _panel_center_top(top_label_box), color=color, width=2, head=8)
    _arrow(draw, _panel_center_bottom(top_label_box), _panel_center_top(presentation_box), color=color, width=2, head=8)
    _arrow(draw, _panel_center_bottom(presentation_box), _panel_center_top(business_box), color=color, width=2, head=8)

    business_bottom = _panel_center_bottom(business_box)
    branch_y = business_bottom[1] + 18
    data_top = _panel_center_top(data_box)
    chain_top = _panel_center_top(chain_box)
    draw.line((business_bottom[0], business_bottom[1], business_bottom[0], branch_y), fill=color, width=2)
    draw.line((data_top[0], branch_y, chain_top[0], branch_y), fill=color, width=2)
    _arrow(draw, (data_top[0], branch_y), data_top, color=color, width=2, head=8)
    _arrow(draw, (chain_top[0], branch_y), chain_top, color=color, width=2, head=8)

    link_map = {str(item.get("to") or "").strip(): str(item.get("label") or "").strip() for item in list(payload.get("links") or [])}
    for label, box, y in [
        (link_map.get("presentation", ""), presentation_box, 226),
        (link_map.get("business", ""), business_box, 426),
        (link_map.get("data", ""), data_box, 666),
        (link_map.get("chain", ""), chain_box, 666),
    ]:
        if not label:
            continue
        cx = (box[0] + box[2]) // 2
        _draw_centered_label(draw, (cx, y), label, note_font)

    image.save(output_path)

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
    project_profile_path = writing_output_paths(config, workspace_root)["project_profile_json"]
    use_case_payload = _build_use_case_payload(config, manifest, workspace_root)
    architecture_payload = _build_architecture_payload(config, manifest, workspace_root)

    specs: list[FigureSpec] = []
    if use_case_payload:
        specs.append(
            FigureSpec(
                "3.1",
                "图3.1 系统用例图",
                "generated/fig3-1-use-case-diagram.png",
                json.dumps(use_case_payload, ensure_ascii=False, sort_keys=True),
                renderer="use_case",
                source_paths=(project_profile_path,) if project_profile_path.exists() else (),
            )
        )
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
    else:
        specs.append(
            FigureSpec(
                "4.1",
                "图4.1 系统总体架构图",
                "generated/fig4-1-architecture.png",
                json.dumps(architecture_payload, ensure_ascii=False, sort_keys=True),
                renderer="pillow-architecture",
                source_paths=(project_profile_path,) if project_profile_path.exists() else (),
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
    elif spec.renderer == "use_case":
        payload["renderer_version"] = USE_CASE_RENDERER_VERSION
        payload["use_case_payload"] = json.loads(spec.code) if spec.code else {}
    elif spec.renderer == "pillow-architecture":
        payload["renderer_version"] = ARCHITECTURE_RENDERER_VERSION
        payload["architecture_payload"] = json.loads(spec.code) if spec.code else {}
    else:
        payload["code"] = spec.code
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()[:16]


def _can_adopt_existing_output(spec: FigureSpec, output_path: Path) -> bool:
    if not output_path.exists():
        return False
    if spec.renderer in {"pillow", "use_case", "pillow-architecture"}:
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
            elif spec.renderer == "use_case":
                _render_use_case_diagram_png(json.loads(spec.code), output_path)
            elif spec.renderer == "pillow-architecture":
                _render_architecture_png(json.loads(spec.code), output_path)
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
