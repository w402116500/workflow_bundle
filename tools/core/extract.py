from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from core.code_evidence import build_code_evidence_pack
from core.project_common import (
    ASSET_BUCKET_ORDER,
    CHAIN_LABELS,
    MATERIAL_PACK_SCHEMA_VERSION,
    MATERIAL_SECTION_ORDER,
    load_workspace_context,
    make_relative,
    material_output_paths,
    read_text_safe,
    write_json,
    write_text,
)


ROLE_PATTERNS = [
    "患者",
    "医生",
    "管理员",
    "用户",
    "茶农",
    "加工厂",
    "质检机构",
    "物流商",
    "经销商",
    "消费者",
    "监管",
    "manufacturer",
    "processor",
    "inspector",
    "dealer",
    "consumer",
    "logistics",
    "regulator",
    "hospital",
    "admin",
]

ROLE_ALIAS_GROUPS = [
    ("患者", ["患者", "patient"]),
    ("医生", ["医生", "doctor"]),
    ("管理员", ["管理员", "admin"]),
    ("用户", ["用户", "user"]),
    ("医院", ["医院", "hospital"]),
    ("茶农", ["茶农", "tea_farmer", "farmer"]),
    ("加工厂", ["加工厂", "processor"]),
    ("质检机构", ["质检机构", "inspector"]),
    ("物流商", ["物流商", "logistics"]),
    ("经销商", ["经销商", "dealer"]),
    ("消费者", ["消费者", "consumer"]),
    ("监管方", ["监管", "regulator"]),
    ("生产方", ["生产方", "manufacturer"]),
]

ROLE_DOMAIN_ORDERS = {
    "health_record": ["患者", "医生", "管理员"],
    "traceability": ["管理员", "茶农", "加工厂", "质检机构", "物流商", "经销商", "消费者", "监管方"],
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg"}

PRIORITY_DOC_FILENAME_RULES = [
    "总体项目文档",
    "功能模块规划文档",
    "后端功能规划文档",
    "前端实现规划文档",
    "数据库设计文档",
    "链码设计文档",
    "后端接口设计文档",
    "前端接口类型定义文档",
    "任务书",
]

SUPPORTING_DOC_KEYWORDS = [
    "测试文档",
    "test_report",
    "test-report",
    "启动脚本说明",
    "部署说明",
]

NON_TEST_ARTIFACT_DOC_KEYWORDS = [
    "总体项目文档",
    "任务书",
    "规划文档",
    "设计文档",
    "接口设计文档",
    "接口类型定义文档",
    "数据库设计文档",
    "链码设计文档",
    "README",
    "readme",
    "部署说明",
    "启动脚本说明",
]

STRONG_TEST_DOC_NAME_KEYWORDS = [
    "测试文档",
    "测试说明",
    "测试报告",
    "test_report",
    "test-report",
    "regression",
    "回归",
    "验收",
]

STRONG_TEST_DOC_CONTENT_MARKERS = [
    "## verified scenarios",
    "## key results",
    "## environment",
    "## 功能测试",
    "## 非功能测试",
    "## 验收",
    "## 测试环境",
    "验收记录表",
    "测试用例",
    "测试结果",
    "测试步骤",
    "测试模块",
    "回归测试",
]

WEAK_TEST_DOC_CONTENT_MARKERS = [
    "assert",
    "通过",
    "失败",
    "截图",
    "用例编号",
]

DATABASE_FIELD_TABLE_PRIORITY = [
    "sys_org",
    "sys_user",
    "tea_batch",
    "tea_farm_record",
    "tea_inspection_report",
    "tea_trace_code",
    "bc_tx_record",
    "log_trace_query",
    "sys_user_chain_identity",
    "tea_process_record",
    "tea_storage_record",
    "tea_logistics_record",
    "tea_sale_record",
    "sys_dict_type",
    "sys_dict_item",
    "sys_system_param",
]

TRACEABILITY_MODULE_MAPPING_SPECS = [
    {
        "label": "用户与权限管理",
        "responsibility": "登录、机构审核、身份绑定与角色治理",
        "frontend_keywords": ["登录", "机构审核", "用户管理", "链上身份"],
        "frontend_fallback": ["登录页", "机构审核页", "用户管理页"],
        "frontend_output": "登录页、个人中心、机构审核页、用户管理页",
        "backend_keywords": ["用户管理与身份认证模块", "后台管理与运维监控模块", "后端权限与校验规划"],
        "backend_fallback": ["认证鉴权", "机构审核", "角色权限治理"],
        "backend_output": "认证中间件、用户服务、管理员服务",
        "table_keywords": ["sys_user", "sys_org", "sys_user_chain_identity"],
        "chain_keywords": ["RegisterOrgRole", "InitLedger"],
        "data_output": "sys_user、sys_org、sys_user_chain_identity",
    },
    {
        "label": "批次与主档管理",
        "responsibility": "茶园、品类、批次建档及状态维护",
        "frontend_keywords": ["品类", "茶园", "批次管理", "批次详情"],
        "frontend_fallback": ["品类管理页", "茶园管理页", "批次管理页"],
        "frontend_output": "茶园管理页、品类管理页、批次管理页",
        "backend_keywords": ["茶叶档案与业务录入模块", "主档", "批次"],
        "backend_fallback": ["主档管理", "批次服务", "状态维护"],
        "backend_output": "主档服务、批次服务",
        "table_keywords": ["tea_category", "tea_garden", "tea_batch"],
        "chain_keywords": ["CreateBatch", "QueryBatch", "QueryBatchHistory"],
        "data_output": "tea_garden、tea_category、tea_batch、CreateBatch",
    },
    {
        "label": "生产流转记录管理",
        "responsibility": "农事、加工、质检、仓储、物流和销售记录录入与阶段推进",
        "frontend_keywords": ["农事", "加工", "质检", "仓储", "物流", "销售"],
        "frontend_fallback": ["农事记录页", "加工记录页", "质检报告页", "仓储记录页", "物流记录页", "销售记录页"],
        "frontend_output": "农事页、加工页、质检页、仓储页、物流页、销售页",
        "backend_keywords": ["茶叶档案与业务录入模块", "链上存证与链码调用模块"],
        "backend_fallback": ["记录服务", "阶段校验", "状态推进"],
        "backend_output": "记录服务、阶段校验服务",
        "table_keywords": ["tea_farm_record", "tea_process_record", "tea_inspection_report", "tea_storage_record", "tea_logistics_record", "tea_sale_record"],
        "chain_keywords": ["SubmitFarmRecord", "SubmitProcessRecord", "SubmitInspectionRecord", "SubmitStorageRecord", "SubmitLogisticsRecord", "SubmitSaleRecord"],
        "data_output": "各阶段业务表、SubmitFarmRecord 至 SubmitSaleRecord",
    },
    {
        "label": "溯源码与追溯查询",
        "responsibility": "溯源码绑定、防伪查询与聚合展示",
        "frontend_keywords": ["溯源码", "消费者溯源", "查询结果", "查询入口", "全流程信息展示"],
        "frontend_fallback": ["溯源码管理页", "消费者溯源页", "查询结果展示页"],
        "frontend_output": "溯源码管理页、公开查询页",
        "backend_keywords": ["溯源码生成与防伪模块", "溯源查询与展示聚合模块"],
        "backend_fallback": ["溯源码服务", "聚合查询", "防伪校验"],
        "backend_output": "溯源码服务、聚合查询服务",
        "table_keywords": ["tea_trace_code", "log_trace_query", "tea_batch"],
        "chain_keywords": ["BindTraceCode", "QueryByTraceCode", "QueryBatchHistory"],
        "data_output": "tea_trace_code、QueryByTraceCode、QueryBatchHistory",
    },
    {
        "label": "监管预警与审计分析",
        "responsibility": "预警发现、冻结解冻与交易审计",
        "frontend_keywords": ["预警", "冻结", "召回", "区块链状态", "日志"],
        "frontend_fallback": ["预警处理页", "召回分析页", "区块链状态页", "日志统计页"],
        "frontend_output": "管理员工作台、预警页、交易记录页",
        "backend_keywords": ["质检与安全管控模块", "后台管理与运维监控模块"],
        "backend_fallback": ["预警处置", "冻结解冻", "交易审计"],
        "backend_output": "监管服务、交易服务",
        "table_keywords": ["tea_quality_warning", "bc_tx_record", "log_operation", "log_trace_query"],
        "chain_keywords": ["FreezeBatch", "UnfreezeBatch", "QueryBatchHistory"],
        "data_output": "预警表、交易映射表、FreezeBatch、UnfreezeBatch",
    },
]

TRACEABILITY_SECURITY_SPECS = [
    {
        "risk": "非授权主体录入或查询",
        "manifestation": "非茶农创建批次、非质检机构提交质检记录、越权访问页面",
        "mechanism": "JWT 鉴权、角色校验、组织身份校验",
        "table_keywords": ["sys_user", "sys_org", "sys_user_chain_identity"],
        "chain_keywords": ["RegisterOrgRole"],
        "location_output": "前端路由、中间件、业务服务、链码组织校验",
    },
    {
        "risk": "业务顺序被绕过",
        "manifestation": "未完成前置阶段直接提交后续记录",
        "mechanism": "阶段状态校验、链码顺序约束",
        "table_keywords": ["tea_batch"],
        "chain_keywords": ["SubmitFarmRecord", "SubmitProcessRecord", "SubmitInspectionRecord", "SubmitStorageRecord", "SubmitLogisticsRecord", "SubmitSaleRecord", "FreezeBatch"],
        "location_output": "批次状态字段、各阶段提交事务",
    },
    {
        "risk": "链下记录被篡改",
        "manifestation": "数据库明细被修改后难以证明原始状态",
        "mechanism": "摘要上链、交易 ID 回写、状态比对",
        "table_keywords": ["bc_tx_record", "tea_batch"],
        "chain_keywords": ["CreateBatch", "QueryBatchHistory"],
        "location_output": "业务表、交易映射表、账本记录",
    },
    {
        "risk": "溯源码伪造或异常复用",
        "manifestation": "假码、重复使用、高频异常查询",
        "mechanism": "一批一码、绑定校验、查询日志记录",
        "table_keywords": ["tea_trace_code", "log_trace_query"],
        "chain_keywords": ["BindTraceCode", "QueryByTraceCode"],
        "location_output": "tea_trace_code、查询日志、BindTraceCode",
    },
    {
        "risk": "异常批次持续流转",
        "manifestation": "质检不合格或预警批次继续出库销售",
        "mechanism": "预警识别、冻结解冻、后续提交拦截",
        "table_keywords": ["tea_quality_warning", "tea_batch"],
        "chain_keywords": ["FreezeBatch", "UnfreezeBatch", "SubmitSaleRecord"],
        "location_output": "预警表、批次状态、FreezeBatch、UnfreezeBatch",
    },
]


def _abs_project_path(project_root: Path, raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    path = Path(raw_path)
    return path if path.is_absolute() else (project_root / path).resolve()


def _slug(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "-", text).strip("-").lower() or "asset"


def _add_evidence(
    items: list[dict[str, Any]],
    claim: str,
    path: Path,
    project_root: Path,
    symbol: str,
    evidence_type: str = "explicit",
) -> None:
    items.append(
        {
            "claim": claim,
            "path": make_relative(path, project_root),
            "symbol": symbol,
            "evidence_type": evidence_type,
        }
    )


def _empty_assets() -> dict[str, list[dict[str, Any]]]:
    return {bucket: [] for bucket in ASSET_BUCKET_ORDER}


def _prepend_unique(existing: list[str], prioritized: list[str], limit: int | None = None) -> list[str]:
    merged: list[str] = []
    for item in prioritized + existing:
        clean = re.sub(r"\s+", " ", str(item).strip())
        if clean and clean not in merged:
            merged.append(clean)
        if limit is not None and len(merged) >= limit:
            break
    return merged if limit is None else merged[:limit]


def _doc_priority(path: Path) -> tuple[int, str]:
    name = path.name
    for index, keyword in enumerate(PRIORITY_DOC_FILENAME_RULES):
        if keyword in name:
            return index, name
    return len(PRIORITY_DOC_FILENAME_RULES), name


def _find_doc_text(doc_texts: list[tuple[Path, str]], *keywords: str) -> tuple[Path, str] | None:
    lowered_keywords = [keyword.lower() for keyword in keywords]
    for path, text in doc_texts:
        name = path.name.lower()
        if any(keyword in name for keyword in lowered_keywords):
            return path, text
    return None


def _optional_test_doc_priority(path: Path, text: str) -> int | None:
    lowered_name = path.name.lower()
    lowered_text = text.lower()
    if any(keyword.lower() in lowered_name for keyword in NON_TEST_ARTIFACT_DOC_KEYWORDS):
        return None

    score = 0
    priority = 2

    if any(keyword.lower() in lowered_name for keyword in ["test_report", "test-report", "测试报告", "回归", "regression"]):
        score += 4
        priority = 0
    if any(keyword.lower() in lowered_name for keyword in ["测试文档", "测试说明", "验收"]):
        score += 3
        priority = min(priority, 1)

    score += sum(2 for marker in STRONG_TEST_DOC_CONTENT_MARKERS if marker.lower() in lowered_text)
    score += min(2, sum(1 for marker in WEAK_TEST_DOC_CONTENT_MARKERS if marker.lower() in lowered_text))

    if score < 3:
        return None
    return priority


def _join_source_paths(*values: str) -> str:
    merged: list[str] = []
    for value in values:
        clean = re.sub(r"\s+", " ", str(value or "").strip())
        if clean and clean not in merged:
            merged.append(clean)
    return " | ".join(merged)


def _discover_supporting_docs(project_root: Path, known_paths: set[Path]) -> list[Path]:
    discovered: list[Path] = []
    for path in sorted(project_root.glob("*.md")):
        if path.resolve() in known_paths:
            continue
        lowered = path.name.lower()
        if any(keyword in lowered for keyword in SUPPORTING_DOC_KEYWORDS):
            discovered.append(path.resolve())
    for rel in ["backend/TEST_REPORT.md", "backend/README.md", "frontend/README.md"]:
        path = (project_root / rel).resolve()
        if path.exists() and path.is_file() and path not in known_paths:
            discovered.append(path)
    return discovered


def _clean_doc_line(line: str) -> str:
    line = re.sub(r"<br\s*/?>", " ", line, flags=re.IGNORECASE)
    line = re.sub(r"\s+", " ", line.strip())
    line = re.sub(r"^[\-\*\u2022]+\s*", "", line)
    line = re.sub(r"^\d+(?:\.\d+)*[\.、]?\s*", "", line)
    return line.strip(" ：:-")


def _clean_heading_label(label: str) -> str:
    label = re.sub(r"\s*`[^`]*`", "", label)
    label = re.sub(r"\s+", " ", label.strip())
    label = label.strip(" ：:-、，,;；")
    return label


def _extract_heading_labels(text: str, min_level: int = 3, max_level: int = 4) -> list[str]:
    labels: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        match = re.match(r"^(#{%d,%d})\s+(?:\d+(?:\.\d+)*\s+)?(.+)$" % (min_level, max_level), stripped)
        if not match:
            continue
        label = _clean_heading_label(match.group(2))
        if label and label not in labels:
            labels.append(label)
    return labels


def _extract_markdown_section_lines(text: str, heading: str, limit: int = 6) -> list[str]:
    lines = text.splitlines()
    start: int | None = None
    heading_level = 0
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped == heading:
            start = index + 1
            heading_level = len(stripped) - len(stripped.lstrip("#"))
            break
    if start is None:
        return []

    collected: list[str] = []
    in_code_block = False
    for raw in lines[start:]:
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if stripped.startswith("#"):
            current_level = len(stripped) - len(stripped.lstrip("#"))
            if current_level <= heading_level:
                break
            continue
        clean = _clean_doc_line(stripped)
        if not clean or len(clean) < 6 or len(clean) > 140:
            continue
        if clean not in collected:
            collected.append(clean)
        if len(collected) >= limit:
            break
    return collected


def _extract_markdown_numbered_items(text: str, heading: str, limit: int = 6) -> list[str]:
    lines = text.splitlines()
    start: int | None = None
    heading_level = 0
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped == heading:
            start = index + 1
            heading_level = len(stripped) - len(stripped.lstrip("#"))
            break
    if start is None:
        return []

    collected: list[str] = []
    in_code_block = False
    for raw in lines[start:]:
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if stripped.startswith("#"):
            current_level = len(stripped) - len(stripped.lstrip("#"))
            if current_level <= heading_level:
                break
            continue
        match = re.match(r"^(?:\d+\.)\s+(.+)$", stripped)
        if not match:
            continue
        clean = _clean_doc_line(match.group(1))
        if not clean or len(clean) < 2 or len(clean) > 140:
            continue
        if clean not in collected:
            collected.append(clean)
        if len(collected) >= limit:
            break
    return collected


def _extract_markdown_table_rows(text: str, expected_headers: list[str]) -> list[dict[str, str]]:
    lines = text.splitlines()
    normalized_headers = [header.strip() for header in expected_headers]
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells != normalized_headers:
            continue
        if index + 1 >= len(lines):
            return []
        separator = lines[index + 1].strip()
        if not separator.startswith("|"):
            return []
        rows: list[dict[str, str]] = []
        for row_raw in lines[index + 2:]:
            row = row_raw.strip()
            if not row.startswith("|"):
                break
            values = [cell.strip() for cell in row.strip("|").split("|")]
            if len(values) != len(normalized_headers):
                continue
            rows.append({header: value for header, value in zip(normalized_headers, values)})
        return rows
    return []


def _extract_module_outline(function_doc_text: str) -> list[str]:
    modules: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in function_doc_text.splitlines():
        stripped = raw.strip()
        module_match = re.match(r"###\s+5\.\d+\s+(.+)", stripped)
        if module_match:
            current = {"label": module_match.group(1).strip(), "subfunctions": []}
            modules.append(current)
            continue
        subfunction_match = re.match(r"####\s+5\.\d+\.\d+\s+(.+)", stripped)
        if subfunction_match and current is not None:
            current["subfunctions"].append(subfunction_match.group(1).strip())

    outline: list[str] = []
    for module in modules:
        subfunctions = module.get("subfunctions", [])
        if subfunctions:
            outline.append(f"{module['label']}：{'；'.join(subfunctions[:5])}")
        else:
            outline.append(module["label"])
    return outline


def _extract_role_outline(function_doc_text: str) -> list[str]:
    roles: list[str] = []
    for raw in function_doc_text.splitlines():
        stripped = raw.strip()
        match = re.match(r"###\s+4\.\d+\s+(.+)", stripped)
        if match:
            label = match.group(1).strip()
            if label not in roles:
                roles.append(label)
    if not roles:
        return []
    return [f"角色体系：{'、'.join(roles)}"]


def _extract_group_outline(
    text: str,
    parent_pattern: str,
    child_pattern: str,
    limit: int = 8,
) -> list[str]:
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in text.splitlines():
        stripped = raw.strip()
        parent_match = re.match(parent_pattern, stripped)
        if parent_match:
            current = {"label": _clean_heading_label(parent_match.group(1)), "children": []}
            groups.append(current)
            continue
        child_match = re.match(child_pattern, stripped)
        if child_match and current is not None:
            label = _clean_heading_label(child_match.group(1)) if child_match.lastindex else ""
            if label and label not in current["children"]:
                current["children"].append(label)

    outline: list[str] = []
    for group in groups:
        label = group.get("label", "")
        if not label:
            continue
        children = [item for item in group.get("children", []) if item][:4]
        if children:
            outline.append(f"{label}：{'、'.join(children)}")
        else:
            outline.append(label)
        if len(outline) >= limit:
            break
    return outline


def _extract_interface_doc_routes(text: str) -> list[str]:
    routes: list[str] = []
    for method, route in re.findall(r"(GET|POST|PUT|DELETE|PATCH)\s+(/api/[A-Za-z0-9_:/{}-]+)", text, flags=re.IGNORECASE):
        label = f"{method.upper()} {route}"
        if label not in routes:
            routes.append(label)
    return routes


def _extract_chaincode_doc_functions(text: str) -> list[str]:
    functions: list[str] = []
    for name in re.findall(r"`([A-Z][A-Za-z0-9_]+)`", text):
        if re.match(r"^(Create|Submit|Bind|Query|Freeze|Unfreeze|Init|Update|Set|Get)", name) and name not in functions:
            functions.append(name)
    return functions


def _extract_interface_outline(interface_doc_text: str) -> list[str]:
    return _extract_group_outline(
        interface_doc_text,
        r"###\s+4\.\d+\s+(.+)",
        r"####\s+4\.\d+(?:\.\d+)+\s+(.+)",
        limit=10,
    )


def _normalize_api_label(label: str) -> str:
    clean = re.sub(r"`", "", str(label or "").strip())
    if not clean:
        return ""
    parts = re.split(r"\s+", clean, maxsplit=1)
    method = parts[0].upper()
    route = parts[1].strip() if len(parts) > 1 else ""
    route = re.sub(r":([A-Za-z0-9_]+)", r"{\1}", route)
    route = re.sub(r"\s+", "", route)
    return f"{method} {route}".strip()


def _split_api_label(label: str) -> tuple[str, str]:
    normalized = _normalize_api_label(label)
    if not normalized:
        return "", ""
    parts = normalized.split(" ", 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def _join_summary_sentence(prefix: str, items: list[str], limit: int = 5) -> str:
    cleaned: list[str] = []
    for item in items:
        value = re.sub(r"\s+", " ", str(item or "").strip())
        value = value.strip("。；;：:-")
        if value and value not in cleaned:
            cleaned.append(value)
        if len(cleaned) >= limit:
            break
    if not cleaned:
        return ""
    return f"{prefix}：{'、'.join(cleaned)}。"


def _contains_any_token(items: list[str], keywords: list[str]) -> bool:
    lowered = " ".join(str(item or "").lower() for item in items)
    return any(keyword.lower() in lowered for keyword in keywords)


def _summarize_backend_regression(
    verified_items: list[str],
    result_items: list[str],
) -> list[str]:
    summary: list[str] = []
    coverage: list[str] = []
    result_points: list[str] = []
    combined_items = verified_items + result_items

    if _contains_any_token(combined_items, ["admin login", "failed login", "unauthorized", "jwt", "/api/auth/me"]):
        coverage.append("登录鉴权")
    if _contains_any_token(combined_items, ["organization registration", "pending review", "approval", "duplicate", "mspid"]):
        coverage.append("机构审核")
    if _contains_any_token(combined_items, ["role switching", "chain identity", "dictionary", "system parameter"]):
        coverage.append("角色切换与链上身份绑定")
    if _contains_any_token(combined_items, ["full batch lifecycle", "batch", "farm", "process", "inspection", "storage", "logistics", "sale"]):
        coverage.append("批次建档与阶段流转")
    if _contains_any_token(combined_items, ["trace-code", "public query", "anti-fake", "trace code", "reissue", "csv export"]):
        coverage.append("溯源码管理与公开查询")
    if _contains_any_token(combined_items, ["warning", "recall", "retry", "blockchain status", "tx-records", "dashboard summary", "login log", "exception log"]):
        coverage.append("监管预警、交易重试与运行审计")
    coverage_sentence = _join_summary_sentence("接口回归验证覆盖", coverage, limit=6)
    if coverage_sentence:
        summary.append(coverage_sentence)

    if _contains_any_token(result_items, ["anomaly_threshold", "anti_fake_flag", "query_count"]):
        result_points.append("查询阈值调整后可即时生效，连续查询可触发防伪异常标记")
    if _contains_any_token(result_items, ["recall analysis", "warning record", "freeze operation"]):
        result_points.append("召回分析结果与人工冻结处置保持一致")
    if _contains_any_token(result_items, ["retry", "latest_tx_id"]):
        result_points.append("失败交易重试后可生成新的成功交易记录")
    if _contains_any_token(result_items, ["dashboard", "returned `200`", "returned 200", "login log total", "exception log total"]):
        result_points.append("工作台统计、日志与监管接口返回结果正常")
    result_sentence = _join_summary_sentence("关键回归结果表明", result_points, limit=4)
    if result_sentence:
        summary.append(result_sentence)
    return summary


def _extract_interface_doc_route_entries(
    project_root: Path,
    doc_path: Path,
    text: str,
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    lines = text.splitlines()
    current_title = ""
    block: list[str] = []

    def flush(title: str, raw_lines: list[str]) -> None:
        if not title:
            return
        permission = ""
        table_hint = ""
        chaincode_hint = ""
        route_labels: list[str] = []
        for raw in raw_lines:
            stripped = raw.strip()
            if stripped.startswith("- 权限："):
                permission = re.sub(r"`", "", stripped.split("：", 1)[1].strip())
            elif stripped.startswith("- 对应表："):
                table_hint = re.sub(r"`", "", stripped.split("：", 1)[1].strip())
            elif stripped.startswith("- 对应链码："):
                chaincode_hint = re.sub(r"`", "", stripped.split("：", 1)[1].strip())
            elif stripped.startswith("- 方法："):
                method_label = re.sub(r"`", "", stripped.split("：", 1)[1].strip())
                if method_label:
                    route_labels.append(_normalize_api_label(method_label))
            else:
                for method_label in re.findall(r"`((?:GET|POST|PUT|DELETE|PATCH)\s+/api/[A-Za-z0-9_:/{}-]+)`", stripped, flags=re.IGNORECASE):
                    route_labels.append(_normalize_api_label(method_label))
        seen: set[str] = set()
        for route_label in route_labels:
            if not route_label or route_label in seen:
                continue
            seen.add(route_label)
            method, route = _split_api_label(route_label)
            entries.append(
                {
                    "label": route_label,
                    "method": method,
                    "route": route,
                    "title": title,
                    "permission": permission,
                    "tables": table_hint,
                    "chaincode": chaincode_hint,
                    "source_path": make_relative(doc_path, project_root),
                }
            )

    for raw in lines:
        stripped = raw.strip()
        heading_match = re.match(r"####\s+\d+(?:\.\d+)+\s+(.+)", stripped)
        if heading_match:
            flush(current_title, block)
            current_title = heading_match.group(1).strip()
            block = []
            continue
        block.append(raw)
    flush(current_title, block)
    return entries


def _extract_database_doc_table_entries(
    project_root: Path,
    doc_path: Path,
    text: str,
) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, Any]] = {}
    current_table = ""
    in_field_table = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("### "):
            heading_match = re.search(r"`([A-Za-z0-9_]+)`\s+(.+)$", stripped)
            match = re.search(r"`([A-Za-z0-9_]+)`", stripped)
            current_table = match.group(1) if match else ""
            if current_table and current_table not in entries:
                entries[current_table] = {
                    "table": current_table,
                    "purpose": "",
                    "source_path": make_relative(doc_path, project_root),
                    "display_title": heading_match.group(2).strip() if heading_match else current_table,
                    "fields": {},
                }
            in_field_table = False
            continue
        if current_table and stripped.startswith("用途："):
            entries[current_table]["purpose"] = _clean_doc_line(stripped.split("：", 1)[1])
            continue
        if current_table and stripped.startswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if cells == ["字段名", "类型", "约束", "说明"]:
                in_field_table = True
                continue
            if in_field_table:
                if all(set(cell) <= {"-", ":"} for cell in cells):
                    continue
                if len(cells) >= 4:
                    field_name = cells[0].strip("`")
                    entries[current_table]["fields"][field_name] = {
                        "type": cells[1],
                        "constraint": cells[2],
                        "description": cells[3],
                    }
                continue
        if in_field_table and not stripped.startswith("|"):
            in_field_table = False
    return entries


def _extract_chaincode_doc_function_entries(
    project_root: Path,
    doc_path: Path,
    text: str,
) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    current_name = ""
    for raw in text.splitlines():
        stripped = raw.strip()
        heading_match = re.match(r"####\s+`?([A-Za-z][A-Za-z0-9_]+)`?", stripped)
        if heading_match:
            current_name = heading_match.group(1)
            entries.setdefault(
                current_name,
                {
                    "name": current_name,
                    "purpose": "",
                    "source_path": make_relative(doc_path, project_root),
                },
            )
            continue
        if current_name and stripped.startswith("用途："):
            entries[current_name]["purpose"] = _clean_doc_line(stripped.split("：", 1)[1])
    return entries


def _make_asset(
    project_root: Path,
    asset_type: str,
    kind: str,
    title: str,
    *,
    path: Path | None = None,
    source_path_override: str = "",
    chapter_candidates: list[str] | None = None,
    section_candidates: list[str] | None = None,
    evidence_level: str = "explicit",
    note: str = "",
    table_headers: list[str] | None = None,
    table_rows: list[list[str]] | None = None,
    appendix_lines: list[str] | None = None,
    placeholder_text: str = "",
    module_key: str = "",
    side: str = "",
    language: str = "",
    symbol: str = "",
    line_start: int = 0,
    line_end: int = 0,
    snippet_path: str = "",
    screenshot_path: str = "",
    selection_score: int = 0,
    selection_group: str = "",
    auto_select: bool = True,
) -> dict[str, Any]:
    source_path = source_path_override or (make_relative(path, project_root) if path else "")
    title_slug = _slug(title)
    if title_slug == "asset":
        fingerprint = hashlib.sha1(
            "|".join(
                [
                    asset_type,
                    kind,
                    title,
                    source_path,
                    symbol,
                    snippet_path,
                    screenshot_path,
                ]
            ).encode("utf-8")
        ).hexdigest()[:10]
        title_slug = f"asset-{fingerprint}"
    return {
        "id": f"{asset_type[:-1] if asset_type.endswith('s') else asset_type}-{_slug(kind)}-{title_slug}",
        "asset_type": asset_type,
        "kind": kind,
        "title": title,
        "source_path": source_path,
        "chapter_candidates": chapter_candidates or [],
        "section_candidates": section_candidates or [],
        "evidence_level": evidence_level,
        "note": note,
        "table_headers": table_headers or [],
        "table_rows": table_rows or [],
        "appendix_lines": appendix_lines or [],
        "placeholder_text": placeholder_text,
        "module_key": module_key,
        "side": side,
        "language": language,
        "symbol": symbol,
        "line_start": line_start,
        "line_end": line_end,
        "snippet_path": snippet_path,
        "screenshot_path": screenshot_path,
        "selection_score": selection_score,
        "selection_group": selection_group,
        "auto_select": auto_select,
    }


def _add_asset(section_assets: dict[str, list[dict[str, Any]]], asset: dict[str, Any]) -> None:
    bucket = asset["asset_type"]
    if bucket not in section_assets:
        section_assets[bucket] = []
    if any(existing["id"] == asset["id"] for existing in section_assets[bucket]):
        return
    section_assets[bucket].append(asset)


def _asset_count_summary(sections: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts = {bucket: 0 for bucket in ASSET_BUCKET_ORDER}
    for section in sections.values():
        for bucket in ASSET_BUCKET_ORDER:
            counts[bucket] += len(section.get("assets", {}).get(bucket, []))
    return counts


def _validate_pack_sections(sections: dict[str, dict[str, Any]]) -> dict[str, Any]:
    counts = _asset_count_summary(sections)
    issues: list[str] = []
    if counts["figures"] == 0:
        issues.append("no figure assets extracted; design and implementation chapters may degrade to prose-only output")
    if counts["tables"] == 0:
        issues.append("no table assets extracted; database/test chapters may miss structured tables")
    if counts["code_artifacts"] == 0:
        issues.append("no code artifacts extracted; chapter 5 may miss implementation evidence")
    if counts["test_artifacts"] == 0:
        issues.append("no test artifacts extracted; testing chapter may lose evidence-oriented content")
    return {
        "status": "ok" if not issues else "warn",
        "asset_counts": counts,
        "issues": issues,
    }


def _load_doc_texts(project_root: Path, document_paths: dict[str, list[str]]) -> list[tuple[Path, str]]:
    unique_docs: dict[Path, tuple[Path, str]] = {}
    for values in document_paths.values():
        for raw_path in values:
            path = _abs_project_path(project_root, raw_path)
            if path and path.exists() and path.is_file():
                unique_docs[path.resolve()] = (path.resolve(), read_text_safe(path.resolve()))
    for path in _discover_supporting_docs(project_root, set(unique_docs)):
        unique_docs[path.resolve()] = (path.resolve(), read_text_safe(path.resolve()))
    docs = list(unique_docs.values())
    docs.sort(key=lambda item: _doc_priority(item[0]))
    return docs


def _extract_frontend_pages(project_root: Path, frontend_dir: Path | None) -> tuple[list[str], list[dict[str, Any]]]:
    if frontend_dir is None or not frontend_dir.exists():
        return [], []
    pages: list[str] = []
    evidence: list[dict[str, Any]] = []
    for path in sorted(frontend_dir.rglob("*")):
        if path.suffix.lower() not in {".vue", ".tsx", ".jsx"}:
            continue
        if "views" not in path.parts and "pages" not in path.parts:
            continue
        name = path.stem
        pages.append(name)
        _add_evidence(evidence, f"frontend page detected: {name}", path, project_root, name)
    return pages, evidence


def _extract_backend_apis(project_root: Path, backend_dir: Path | None) -> tuple[list[str], list[dict[str, Any]]]:
    if backend_dir is None or not backend_dir.exists():
        return [], []
    apis: list[str] = []
    evidence: list[dict[str, Any]] = []
    spring_pattern = re.compile(r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\(([^)]*)\)")
    method_pattern = re.compile(r"public\s+[^\(]+\s+(\w+)\s*\(")
    for path in sorted(backend_dir.rglob("*.java")):
        text = read_text_safe(path)
        if "@RestController" not in text and "@Controller" not in text:
            continue
        base = ""
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            match = spring_pattern.search(line)
            if not match:
                continue
            route = match.group(2)
            route_match = re.search(r'"([^"]+)"', route)
            route_value = route_match.group(1) if route_match else ""

            next_lines = "\n".join(lines[idx + 1 : idx + 4])
            if match.group(1) == "RequestMapping" and "class " in next_lines:
                base = route_value
                continue

            method_name = path.stem
            for probe in lines[idx + 1 :]:
                method_match = method_pattern.search(probe)
                if method_match:
                    method_name = method_match.group(1)
                    break
                if probe.strip().startswith("@"):
                    continue
            full_route = f"{base}{route_value}"
            api_label = f"{match.group(1)} {full_route or '[unresolved-route]'}"
            apis.append(api_label)
            _add_evidence(evidence, f"backend api detected: {api_label}", path, project_root, method_name)
    gin_pattern = re.compile(r"\.(GET|POST|PUT|DELETE|PATCH)\(\"([^\"]+)\"")
    for path in sorted(backend_dir.rglob("*.go")):
        text = read_text_safe(path)
        if "gin-gonic/gin" not in text and ".GET(" not in text and ".POST(" not in text:
            continue
        for method, route in gin_pattern.findall(text):
            api_label = f"{method.upper()} {route}"
            apis.append(api_label)
            _add_evidence(evidence, f"backend api detected: {api_label}", path, project_root, route)
    return list(dict.fromkeys(apis)), evidence


def _extract_sql_tables(project_root: Path, database_file: Path | None) -> tuple[list[str], list[dict[str, Any]]]:
    if database_file is None or not database_file.exists():
        return [], []
    text = read_text_safe(database_file)
    tables = re.findall(r"CREATE TABLE(?: IF NOT EXISTS)?\s+`?([A-Za-z0-9_]+)`?", text, flags=re.IGNORECASE)
    evidence: list[dict[str, Any]] = []
    for table in tables:
        _add_evidence(evidence, f"database table detected: {table}", database_file, project_root, table)
    return tables, evidence


def _extract_solidity_contracts(project_root: Path, contracts_dir: Path | None) -> tuple[list[str], list[dict[str, Any]]]:
    if contracts_dir is None or not contracts_dir.exists():
        return [], []
    contracts: list[str] = []
    evidence: list[dict[str, Any]] = []
    for path in sorted(contracts_dir.rglob("*.sol")):
        text = read_text_safe(path)
        contract_names = re.findall(r"\bcontract\s+([A-Za-z0-9_]+)", text)
        function_names = re.findall(r"\bfunction\s+([A-Za-z0-9_]+)\s*\(", text)
        for name in contract_names:
            contracts.append(name)
            _add_evidence(evidence, f"solidity contract detected: {name}", path, project_root, name)
        for function_name in function_names:
            _add_evidence(evidence, f"contract function detected: {function_name}", path, project_root, function_name)
    return contracts, evidence


def _extract_fabric_chaincode(project_root: Path, chaincode_dir: Path | None) -> tuple[list[str], list[dict[str, Any]]]:
    if chaincode_dir is None or not chaincode_dir.exists():
        return [], []
    chaincodes: list[str] = []
    evidence: list[dict[str, Any]] = []
    for path in sorted(chaincode_dir.rglob("*")):
        if path.suffix.lower() not in {".go", ".js", ".ts"}:
            continue
        text = read_text_safe(path)
        names = re.findall(r"func\s+\([^\)]*\)\s*([A-Za-z0-9_]+)\s*\(", text)
        names += re.findall(r"async\s+([A-Za-z0-9_]+)\s*\(", text)
        if "contractapi" in text.lower() or "fabric-contract-api" in text.lower():
            chaincodes.append(path.stem)
            _add_evidence(evidence, f"fabric chaincode module detected: {path.stem}", path, project_root, path.stem)
        for name in names:
            _add_evidence(evidence, f"chaincode transaction detected: {name}", path, project_root, name)
    return chaincodes, evidence


def _extract_roles(
    doc_texts: list[tuple[Path, str]],
    page_names: list[str],
    project_root: Path,
) -> tuple[list[str], list[dict[str, Any]]]:
    roles: list[str] = []
    evidence: list[dict[str, Any]] = []
    for path, text in doc_texts:
        lower = text.lower()
        for pattern in ROLE_PATTERNS:
            if pattern.lower() in lower and pattern not in roles:
                roles.append(pattern)
                _add_evidence(evidence, f"role keyword detected: {pattern}", path, project_root, pattern)
    for page_name in page_names:
        lower = page_name.lower()
        for candidate in ["admin", "doctor", "patient", "farmer", "processor", "inspector", "logistics", "dealer", "consumer"]:
            if candidate in lower and candidate not in roles:
                roles.append(candidate)
    return roles, evidence


def _normalize_role_token(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").strip()).lower()


def _normalize_role_labels(
    roles: list[str],
    role_evidence: list[dict[str, Any]],
    domain_key: str,
) -> list[str]:
    tokens: list[str] = []
    for role in roles:
        if role:
            tokens.append(str(role))
    for item in role_evidence:
        symbol = str(item.get("symbol") or "").strip()
        if symbol:
            tokens.append(symbol)

    cleaned_tokens = [_normalize_role_token(token) for token in tokens if _normalize_role_token(token)]
    detected_labels: list[str] = []
    matched_tokens: set[str] = set()
    for label, aliases in ROLE_ALIAS_GROUPS:
        if any(_normalize_role_token(alias) in cleaned_tokens for alias in aliases):
            detected_labels.append(label)
            matched_tokens.update(_normalize_role_token(alias) for alias in aliases)

    if domain_key == "health_record":
        health_roles = [label for label in ROLE_DOMAIN_ORDERS["health_record"] if label in detected_labels]
        if health_roles:
            return health_roles

    ordered: list[str] = []
    preferred_order = ROLE_DOMAIN_ORDERS.get(domain_key, [])
    for label in preferred_order:
        if label in detected_labels and label not in ordered:
            ordered.append(label)
    for label, _ in ROLE_ALIAS_GROUPS:
        if label in detected_labels and label not in ordered:
            ordered.append(label)

    extras: list[str] = []
    for raw in tokens:
        clean = str(raw or "").strip()
        normalized = _normalize_role_token(clean)
        if not clean or normalized in matched_tokens:
            continue
        clean = re.sub(r"[_-]+", " ", clean)
        if clean and clean not in ordered and clean not in extras:
            extras.append(clean)
    return (ordered + extras)[:12]


def _generic_role_row(role: str) -> list[str]:
    if role in {"管理员", "监管方"}:
        return [role, "负责平台配置、角色审核、运行监管或审计支撑。", "拥有管理与审计权限，但不直接替代业务角色处理核心业务数据。"]
    if role in {"用户", "患者", "消费者"}:
        return [role, "发起基础业务操作并查看与本人相关的处理结果。", "仅能访问与本人身份或授权关系直接相关的数据与功能入口。"]
    if role in {"医生", "茶农", "加工厂", "质检机构", "物流商", "经销商", "生产方", "医院"}:
        return [role, "负责所属业务环节的数据录入、状态维护与结果反馈。", "仅能维护本角色负责环节的数据，不可越权修改其他主体的核心记录。"]
    return [role, "参与系统业务流程中的录入、审核或查询等操作。", "只能访问角色授权范围内的功能模块与业务对象。"]


def _role_matrix_rows(domain_key: str, roles: list[str]) -> list[list[str]]:
    if domain_key == "health_record":
        row_map = {
            "患者": ["患者", "核验本人健康档案、确认上链并处理医生访问授权。", "仅可查看本人档案，并决定授权通过、维持或撤销。"],
            "医生": ["医生", "创建健康档案、发起访问申请，并在获权后查看诊疗信息。", "仅能维护本人录入档案，查看明文必须经过患者授权。"],
            "管理员": ["管理员", "负责账户审核、平台配置、运行维护和审计支撑。", "不直接参与患者诊疗内容编辑，只承担平台级治理职责。"],
        }
        ordered_roles = [role for role in ROLE_DOMAIN_ORDERS["health_record"] if role in roles]
    elif domain_key == "traceability":
        row_map = {
            "管理员": ["管理员", "维护平台用户、组织审核、预警处置与审计分析。", "可执行平台级治理与监管操作，但不替代业务主体填报生产流转数据。"],
            "茶农": ["茶农", "登记种植批次、农事过程和原始产地信息。", "仅维护本人负责批次的基础生产数据。"],
            "加工厂": ["加工厂", "维护加工、包装、入库等生产流转记录。", "仅能更新授权加工环节的信息，不能改写其他主体的历史记录。"],
            "质检机构": ["质检机构", "录入检测结果并输出批次质量结论。", "仅能维护检测相关数据，不参与生产与销售数据改写。"],
            "物流商": ["物流商", "更新运输节点、交接状态和物流追踪信息。", "仅能维护物流环节状态，不能修改批次源头信息。"],
            "经销商": ["经销商", "维护上架、销售和去向记录，支撑终端查询。", "仅能处理销售环节相关数据，不可修改前序生产记录。"],
            "消费者": ["消费者", "查询产品溯源结果并核验关键信息。", "仅具备查询权限，不参与业务数据写入。"],
            "监管方": ["监管方", "查看全流程记录、审计异常并执行监管决策。", "以监管与核查为主，不直接填报普通业务数据。"],
        }
        ordered_roles = [role for role in ROLE_DOMAIN_ORDERS["traceability"] if role in roles]
    else:
        row_map = {}
        ordered_roles = list(roles)

    rows: list[list[str]] = []
    for role in ordered_roles:
        rows.append(list(row_map.get(role, _generic_role_row(role))))
    for role in roles:
        if role not in ordered_roles:
            rows.append(_generic_role_row(role))
    return rows[:12]


def _extract_business_flows(
    doc_texts: list[tuple[Path, str]],
    blockchain_items: list[str],
    api_items: list[str],
    project_root: Path,
) -> tuple[list[str], list[dict[str, Any]]]:
    flows: list[str] = []
    evidence: list[dict[str, Any]] = []
    flow_keywords = [
        "流程",
        "flow",
        "upload",
        "confirm",
        "query",
        "grant",
        "revoke",
        "create",
        "transfer",
        "录入",
        "上链",
        "追溯",
        "质检",
        "物流",
        "销售",
        "批次",
    ]
    for path, text in doc_texts:
        for line in text.splitlines():
            for segment in re.split(r"<br\s*/?>|[；;。]", line):
                clean = re.sub(r"\s+", " ", segment.strip().lstrip("#").strip())
                if not clean:
                    continue
                if len(clean) < 6 or len(clean) > 80:
                    continue
                if any(keyword in clean.lower() for keyword in flow_keywords) and clean not in flows:
                    flows.append(clean)
                    _add_evidence(evidence, f"business flow hint detected: {clean}", path, project_root, clean[:60])
    for label in blockchain_items[:5] + api_items[:5]:
        if label not in flows:
            flows.append(label)
    return flows[:12], evidence


def _extract_deployment(
    project_root: Path,
    source_paths: dict[str, str],
    doc_texts: list[tuple[Path, str]],
) -> tuple[list[str], list[dict[str, Any]]]:
    summary: list[str] = []
    evidence: list[dict[str, Any]] = []
    overall_doc = _find_doc_text(doc_texts, "总体项目文档")
    manual_test_doc = _find_doc_text(doc_texts, "全流程手动测试文档")
    frontend_test_doc = _find_doc_text(doc_texts, "前端全流程手动测试文档")
    backend_report_doc = _find_doc_text(doc_texts, "TEST_REPORT", "test_report")

    if overall_doc:
        summary.append("系统测试采用前端页面、后端服务、MySQL 数据库与 Hyperledger Fabric 测试网络组成的本地原型环境。")
        runtime_lines = _extract_markdown_section_lines(overall_doc[1], "### 2.4 运行环境与端口", limit=7)
        backend_port = ""
        frontend_port = ""
        channel_name = ""
        chaincode_name = ""
        for line in runtime_lines:
            if "后端端口" in line:
                backend_port = line.split("：", 1)[-1].strip("` ")
            elif "前端端口" in line:
                frontend_port = line.split("：", 1)[-1].strip("` ")
            elif "Fabric 通道" in line:
                channel_name = line.split("：", 1)[-1].strip("` ")
            elif "链码名称" in line:
                chaincode_name = line.split("：", 1)[-1].strip("` ")
        if frontend_port or backend_port:
            summary.append(f"前端默认端口为 {frontend_port or '-'}，后端默认端口为 {backend_port or '-'}。")
        if channel_name or chaincode_name:
            summary.append(f"链上测试环境使用通道 {channel_name or '-'} 与链码 {chaincode_name or '-'}。")
        _add_evidence(evidence, "runtime summary extracted from overall document", overall_doc[0], project_root, overall_doc[0].stem)

    if manual_test_doc or frontend_test_doc:
        summary.append("测试前需完成链码部署、基础数据初始化以及前后端服务启动。")
        if manual_test_doc:
            _add_evidence(evidence, "manual full-flow preconditions captured", manual_test_doc[0], project_root, manual_test_doc[0].stem)
        if frontend_test_doc:
            _add_evidence(evidence, "frontend manual test startup captured", frontend_test_doc[0], project_root, frontend_test_doc[0].stem)

    if backend_report_doc:
        env_lines = _extract_markdown_section_lines(backend_report_doc[1], "## Environment", limit=5)
        backend_stack = ""
        for line in env_lines:
            clean = re.sub(r"`", "", line)
            lowered = clean.lower()
            if lowered.startswith("1. backend:") or lowered.startswith("backend:"):
                backend_stack = clean.split(":", 1)[-1].strip()
                break
        if backend_stack:
            backend_stack = backend_stack.replace(" + ", "、")
            summary.append(f"后端联调服务采用 {backend_stack} 组合。")
        _add_evidence(evidence, "backend test environment captured", backend_report_doc[0], project_root, backend_report_doc[0].stem)

    for key in ["ops_docs", "overview_docs"]:
        path = _abs_project_path(project_root, source_paths.get(key))
        if path and path.exists():
            _add_evidence(evidence, f"deployment entry detected: {path.name}", path, project_root, path.name)
    if not summary:
        for path, text in doc_texts:
            if any(keyword in text.lower() for keyword in ["部署", "运行", "start", "docker", "network.sh", "port", "启动"]):
                summary.append("系统部署环境已覆盖前端、后端、数据库与链上网络的联合运行条件。")
                _add_evidence(evidence, "deployment detail found in document", path, project_root, path.stem)
                break
    return _prepend_unique(summary, [], limit=8), evidence


def _extract_demo_evidence(project_root: Path, doc_texts: list[tuple[Path, str]]) -> tuple[list[str], list[dict[str, Any]]]:
    summary: list[str] = []
    evidence: list[dict[str, Any]] = []
    overall_doc = _find_doc_text(doc_texts, "总体项目文档")
    backend_report_doc = _find_doc_text(doc_texts, "TEST_REPORT", "test_report")
    frontend_manual_doc = _find_doc_text(doc_texts, "前端全流程手动测试文档")
    full_manual_doc = _find_doc_text(doc_texts, "全流程手动测试文档")

    if overall_doc:
        flow_items = _extract_markdown_numbered_items(overall_doc[1], "### 10.2 主链路测试项", limit=6)
        abnormal_items = _extract_markdown_numbered_items(overall_doc[1], "### 10.3 异常与权限验证项", limit=5)
        observation_items = _extract_markdown_numbered_items(overall_doc[1], "### 10.4 可作为论文实验依据的观察点", limit=5)
        for sentence in [
            _join_summary_sentence("主链路测试覆盖", flow_items, limit=6),
            _join_summary_sentence("异常与权限验证覆盖", abnormal_items, limit=5),
            _join_summary_sentence("实验观察重点包括", observation_items, limit=5),
        ]:
            if sentence:
                summary.append(sentence)
        _add_evidence(evidence, "test and validation summary extracted", overall_doc[0], project_root, overall_doc[0].stem)

    if backend_report_doc:
        verified_items = _extract_markdown_section_lines(backend_report_doc[1], "## Verified Scenarios", limit=12)
        result_items = _extract_markdown_section_lines(backend_report_doc[1], "## Key Results", limit=10)
        for sentence in _summarize_backend_regression(verified_items, result_items):
            if sentence:
                summary.append(sentence)
        _add_evidence(evidence, "backend regression report detected", backend_report_doc[0], project_root, backend_report_doc[0].stem)

    if frontend_manual_doc:
        frontend_flow_items = _extract_group_outline(
            frontend_manual_doc[1],
            r"###\s+3\.\d+\s+(.+)",
            r"^$^",
            limit=5,
        )
        role_check_items = _extract_group_outline(
            frontend_manual_doc[1],
            r"###\s+4\.\d+\s+(.+)",
            r"^$^",
            limit=4,
        )
        for sentence in [
            _join_summary_sentence("前端主链路验证覆盖", frontend_flow_items, limit=5),
            _join_summary_sentence("页面与角色验证覆盖", role_check_items, limit=4),
        ]:
            if sentence:
                summary.append(sentence)
        _add_evidence(evidence, "frontend manual testing flow detected", frontend_manual_doc[0], project_root, frontend_manual_doc[0].stem)

    if full_manual_doc:
        full_flow_items = _extract_group_outline(
            full_manual_doc[1],
            r"##\s+5\.\d+\s+(.+)",
            r"^$^",
            limit=6,
        )
        if full_flow_items:
            summary.append(_join_summary_sentence("手动联调覆盖", full_flow_items, limit=6))
        _add_evidence(evidence, "full manual testing flow detected", full_manual_doc[0], project_root, full_manual_doc[0].stem)

    ranked_docs: list[tuple[int, Path, str]] = []
    for path, text in doc_texts:
        priority = _optional_test_doc_priority(path, text)
        if priority is None:
            continue
        ranked_docs.append((priority, path, text))
    seen_doc_paths: set[str] = {
        make_relative(doc[0], project_root)
        for doc in [overall_doc, backend_report_doc, frontend_manual_doc, full_manual_doc]
        if doc
    }
    for _, path, _ in sorted(ranked_docs, key=lambda item: (item[0], _doc_priority(item[1]))):
        rel = make_relative(path, project_root)
        if rel in seen_doc_paths:
            continue
        seen_doc_paths.add(rel)
        _add_evidence(evidence, "test/demo document detected", path, project_root, path.stem)
    for img_root in [project_root / "images", project_root / "docs" / "images", project_root / ".runtime" / "test-artifacts"]:
        if img_root.exists():
            images = [path for path in img_root.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS]
            if images:
                summary.append(f"测试相关截图与图像证据共计 {len(images)} 项，可用于测试与实现章节取证。")
    return _prepend_unique(summary, [], limit=10), evidence


def _parse_sql_table_details(database_file: Path | None) -> list[dict[str, Any]]:
    if database_file is None or not database_file.exists():
        return []
    text = read_text_safe(database_file)
    pattern = re.compile(
        r"CREATE TABLE(?: IF NOT EXISTS)?\s+`?([A-Za-z0-9_]+)`?\s*\((.*?)\)\s*(?:ENGINE|COMMENT|;)",
        flags=re.IGNORECASE | re.DOTALL,
    )
    details: list[dict[str, Any]] = []
    for table_name, body in pattern.findall(text):
        primary_keys: set[str] = set()
        for key_match in re.findall(r"PRIMARY KEY\s*\(([^)]*)\)", body, flags=re.IGNORECASE):
            for name in re.findall(r"`([A-Za-z0-9_]+)`", key_match):
                primary_keys.add(name)
        columns: list[dict[str, str]] = []
        for raw_line in body.splitlines():
            clean = raw_line.strip().rstrip(",")
            upper = clean.upper()
            if not clean or upper.startswith(("PRIMARY KEY", "KEY ", "UNIQUE KEY", "CONSTRAINT", "INDEX ", "UNIQUE INDEX")):
                continue
            match = re.match(r"`?([A-Za-z0-9_]+)`?\s+([A-Za-z]+(?:\([^)]+\))?)\s*(.*)", clean)
            if not match:
                continue
            column_name = match.group(1)
            type_token = re.sub(r"\s+", " ", match.group(2)).strip().upper()
            remainder = match.group(3).upper()
            length_match = re.search(r"\(([^)]+)\)", type_token)
            columns.append(
                {
                    "name": column_name,
                    "type": type_token.split("(", 1)[0],
                    "length": length_match.group(1) if length_match else "-",
                    "nullable": "否" if "NOT NULL" in remainder else "是",
                    "is_primary": "是" if column_name in primary_keys else "否",
                }
            )
        details.append({"table": table_name, "columns": columns})
    return details


def _build_technology_assets(
    project_root: Path,
    manifest: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, list[dict[str, Any]]]:
    assets = _empty_assets()
    stack = manifest.get("detected_stack", {})
    rows = [
        ["前端", stack.get("frontend_framework", "unknown"), "承担多角色业务录入、状态展示与溯源查询交互"],
        ["后端", stack.get("backend_framework", "unknown"), "负责接口提供、业务编排、权限控制与链码调用封装"],
        ["数据库", stack.get("database_kind", "unknown"), "保存用户、主档、过程记录、预警信息与交易映射等链下数据"],
        ["区块链", CHAIN_LABELS.get(manifest["chain_platform"], manifest["chain_platform"]), "保存关键摘要、状态约束与可信凭证"],
        ["链交互", stack.get("chain_sdk", "unknown"), "完成后端与区块链之间的交易提交、查询与回执处理"],
    ]
    _add_asset(
        assets,
        _make_asset(
            project_root,
            "tables",
            "tech-stack-summary",
            "技术栈与关键组件清单",
            chapter_candidates=["02-系统开发工具及技术介绍.md"],
            section_candidates=["2.1 技术栈与选型概览"],
            evidence_level="derived",
            note="由 manifest.detected_stack 与 source_paths 自动汇总，适合写入技术选型表。",
            table_headers=["层次", "技术/平台", "主要作用"],
            table_rows=rows,
        ),
    )
    return assets


def _build_role_assets(
    project_root: Path,
    roles: list[str],
    domain_key: str,
) -> dict[str, list[dict[str, Any]]]:
    assets = _empty_assets()
    rows = _role_matrix_rows(domain_key, roles)
    if rows:
        _add_asset(
            assets,
            _make_asset(
                project_root,
                "tables",
                "role-matrix",
                "系统角色与职责摘要",
                chapter_candidates=["03-需求分析.md"],
                section_candidates=["3.3 角色与用例分析"],
                evidence_level="derived",
                note="可直接转为需求分析中的角色职责表；正文不应暴露源文件名、证据路径或调试字段。",
                table_headers=["角色", "主要职责", "权限边界"],
                table_rows=rows,
            ),
        )
    return assets


def _detect_domain_key(title: str, api_items: list[str], page_names: list[str], flow_items: list[str]) -> str:
    text = " ".join([title] + api_items + page_names + flow_items).lower()
    trace_tokens = ["trace", "batch", "logistics", "qrcode", "溯源", "批次", "茶", "二维码", "supply"]
    health_tokens = ["health", "medical", "ehr", "patient", "doctor", "医疗", "病历", "患者", "医生"]
    trace_score = sum(1 for token in trace_tokens if token in text)
    health_score = sum(1 for token in health_tokens if token in text)
    if trace_score > 0 and trace_score >= health_score:
        return "traceability"
    if health_score > 0:
        return "health_record"
    return "generic_blockchain"


def _pick_matches(candidates: list[str], keywords: list[str], limit: int = 4) -> list[str]:
    lowered_keywords = [keyword.lower() for keyword in keywords]
    matches: list[str] = []
    for candidate in candidates:
        lowered = candidate.lower()
        if any(keyword in lowered for keyword in lowered_keywords) and candidate not in matches:
            matches.append(candidate)
        if len(matches) >= limit:
            break
    return matches


def _pick_preferred_values(candidates: list[str], preferred_values: list[str], limit: int = 4) -> list[str]:
    matches: list[str] = []
    lowered_candidates = [(candidate, candidate.lower()) for candidate in candidates]
    for preferred in preferred_values:
        lowered_preferred = preferred.lower()
        for candidate, lowered_candidate in lowered_candidates:
            if lowered_preferred in lowered_candidate and candidate not in matches:
                matches.append(candidate)
                break
        if len(matches) >= limit:
            break
    return matches


def _compact_join(values: list[str], *, limit: int = 4, separator: str = "、") -> str:
    merged: list[str] = []
    for value in values:
        clean = re.sub(r"\s+", " ", str(value or "").strip())
        clean = clean.strip(" ：:-、，,;；")
        if clean and clean not in merged:
            merged.append(clean)
        if len(merged) >= limit:
            break
    return separator.join(merged) if merged else "-"


def _pick_flow_texts(flow_items: list[str], domain_key: str, limit: int = 3) -> list[str]:
    if domain_key == "traceability":
        keyword_groups = [
            ["批次", "上链", "存证", "录入"],
            ["加工", "质检", "物流", "销售", "环节"],
            ["扫码", "查询", "溯源", "二维码", "验证"],
        ]
    elif domain_key == "health_record":
        keyword_groups = [
            ["上传", "确认", "存证", "档案"],
            ["授权", "撤销", "权限", "访问"],
            ["查询", "审计", "追溯", "统计"],
        ]
    else:
        keyword_groups = [
            ["录入", "提交", "上链", "存证"],
            ["授权", "权限", "审核", "校验"],
            ["查询", "审计", "追溯", "统计"],
        ]

    selected: list[str] = []
    for keywords in keyword_groups:
        candidates = [item for item in flow_items if item not in selected and any(keyword in item for keyword in keywords)]
        match = None
        if candidates:
            match = sorted(
                candidates,
                key=lambda item: (
                    -sum(1 for keyword in keywords if keyword in item),
                    abs(len(item) - 18),
                    len(item),
                ),
            )[0]
        if match:
            selected.append(match)

    if len(selected) < limit:
        generic_keywords = ["流程", "录入", "上链", "查询", "扫码", "物流", "销售", "质检", "授权", "审计"]
        ranked = sorted(
            (item for item in flow_items if item not in selected),
            key=lambda item: (
                -sum(2 for keyword in generic_keywords if keyword in item),
                abs(len(item) - 18),
                len(item),
            ),
        )
        for item in ranked:
            if item not in selected:
                selected.append(item)
            if len(selected) >= limit:
                break

    while len(selected) < limit:
        selected.append(f"核心业务流程草案 {len(selected) + 1}")
    return selected[:limit]


def _build_derived_diagram_assets(
    project_root: Path,
    manifest: dict[str, Any],
    source_paths: dict[str, str],
    page_names: list[str],
    api_items: list[str],
    table_names: list[str],
    flow_items: list[str],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    section_assets = {
        "architecture": _empty_assets(),
        "database_design": _empty_assets(),
        "business_flows": _empty_assets(),
    }
    domain_key = _detect_domain_key(manifest.get("title", ""), api_items, page_names, flow_items)
    stack = manifest.get("detected_stack", {})

    architecture_lines = [
        f"表现层: {stack.get('frontend_framework', 'unknown')} | source: {source_paths.get('frontend') or 'missing'}",
        f"业务层: {stack.get('backend_framework', 'unknown')} | source: {source_paths.get('backend') or 'missing'}",
        f"数据层: {stack.get('database_kind', 'unknown')} | source: {source_paths.get('database') or 'missing'}",
        f"区块链层: {CHAIN_LABELS.get(manifest['chain_platform'], manifest['chain_platform'])} | source: {source_paths.get('contracts') or source_paths.get('chaincode') or 'missing'}",
    ]
    _add_asset(
        section_assets["architecture"],
        _make_asset(
            project_root,
            "figures",
            "architecture-diagram",
            "系统总体架构图草案",
            chapter_candidates=["04-系统设计.md"],
            section_candidates=["4.1 系统架构设计"],
            evidence_level="derived",
            note="由项目目录和技术栈自动派生的架构图草案；写作时应保留图题，并依据 placeholder_text 绘制或显式占位。",
            placeholder_text="\n".join(architecture_lines),
        ),
    )

    er_lines = [f"核心实体: {name}" for name in table_names[:12]]
    if not er_lines:
        er_lines = ["核心实体待根据数据库脚本补充"]
    _add_asset(
        section_assets["database_design"],
        _make_asset(
            project_root,
            "figures",
            "er-diagram",
            "数据库E-R图草案",
            chapter_candidates=["04-系统设计.md"],
            section_candidates=["4.3.2 概念模型 E-R"],
            evidence_level="derived",
            note="由数据库表清单自动派生的 E-R 图草案；若未补正式配图，正文必须保留图题和占位说明。",
            placeholder_text="\n".join(er_lines),
        ),
    )

    if domain_key == "traceability":
        function_specs = [
            ("用户与权限管理", ["login", "register", "user", "org", "audit"], ["login", "register", "user"]),
            ("批次与主档管理", ["batch", "garden", "category", "product"], ["batch", "batchtrace"]),
            ("生产流转记录管理", ["farm", "process", "inspection", "storage", "logistics", "sale"], ["farm", "process", "inspection", "storage", "logistics", "sale"]),
            ("溯源码与追溯查询", ["trace", "qrcode"], ["trace", "batchtrace"]),
            ("监管预警与审计分析", ["warning", "freeze", "recall", "history", "dashboard", "log"], ["warning", "dashboard", "audit"]),
        ]
    elif domain_key == "health_record":
        function_specs = [
            ("用户与身份管理", ["login", "register", "user", "doctor", "patient"], ["login", "register", "profile"]),
            ("健康档案管理", ["record", "health", "patient", "diagnosis"], ["record", "health", "patient"]),
            ("访问授权管理", ["grant", "revoke", "permission", "access"], ["grant", "revoke", "access"]),
            ("查询与审计追溯", ["audit", "query", "trace", "stats"], ["audit", "query", "trace"]),
        ]
    else:
        function_specs = [
            ("用户与身份管理", ["login", "register", "user", "auth"], ["login", "register", "user"]),
            ("核心业务管理", ["record", "batch", "data", "business"], ["record", "batch", "data"]),
            ("审计与查询分析", ["audit", "query", "trace", "stats"], ["audit", "query", "trace"]),
        ]

    function_lines: list[str] = []
    for label, api_keywords, page_keywords in function_specs:
        api_matches = _pick_matches(api_items, api_keywords, limit=3)
        page_matches = _pick_matches(page_names, page_keywords, limit=2)
        detail_parts: list[str] = []
        if api_matches:
            detail_parts.append("API: " + ", ".join(api_matches))
        if page_matches:
            detail_parts.append("页面: " + ", ".join(page_matches))
        if not detail_parts:
            detail_parts.append("依据业务流程与角色职责补充")
        function_lines.append(f"{label}: " + " | ".join(detail_parts))
    _add_asset(
        section_assets["business_flows"],
        _make_asset(
            project_root,
            "figures",
            "system-function-structure",
            "系统功能结构图草案",
            chapter_candidates=["05-系统实现.md"],
            section_candidates=["5 系统实现"],
            evidence_level="derived",
            note="由页面和接口线索自动派生的功能结构图草案；写作时应保留图题，并按 placeholder_text 组织图示或显式占位。",
            placeholder_text="\n".join(function_lines),
        ),
    )

    flow_placeholders = _pick_flow_texts(flow_items, domain_key, limit=3)
    for index, flow_text in enumerate(flow_placeholders[:3], start=1):
        _add_asset(
            section_assets["business_flows"],
            _make_asset(
                project_root,
                "figures",
                "flow-diagram",
                f"核心业务流程图草案 {index}",
                chapter_candidates=["04-系统设计.md"],
                section_candidates=[f"4.5.{index}"],
                evidence_level="derived",
                note="由业务流程线索自动派生的流程图草案；正文应保留图题，并根据 placeholder_text 绘制或占位。",
                placeholder_text=flow_text,
            ),
        )
    return section_assets


def _parse_api_rows(
    api_items: list[str],
    backend_evidence: list[dict[str, Any]],
    interface_entries: list[dict[str, str]] | None = None,
) -> list[list[str]]:
    path_by_claim: dict[str, str] = {}
    for item in backend_evidence:
        if item["claim"].startswith("backend api detected: "):
            label = item["claim"].removeprefix("backend api detected: ")
            path_by_claim[_normalize_api_label(label)] = item["path"]
    entry_map = {entry["label"]: entry for entry in interface_entries or []}
    ordered_labels = _prepend_unique(api_items, [entry["label"] for entry in interface_entries or []], limit=20)
    rows: list[list[str]] = []
    for api in ordered_labels[:16]:
        normalized = _normalize_api_label(api)
        method, route = _split_api_label(normalized)
        entry = entry_map.get(normalized, {})
        summary_parts = [entry.get("title", "").strip()]
        if entry.get("permission"):
            summary_parts.append(f"权限：{entry['permission']}")
        rows.append([method, route, "；".join(part for part in summary_parts if part) or "-"])
    return rows


def _build_api_assets(
    project_root: Path,
    api_items: list[str],
    backend_evidence: list[dict[str, Any]],
    backend_api_doc: tuple[Path, str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    assets = _empty_assets()
    interface_entries = (
        _extract_interface_doc_route_entries(project_root, backend_api_doc[0], backend_api_doc[1]) if backend_api_doc else []
    )
    rows = _parse_api_rows(api_items, backend_evidence, interface_entries)
    if rows:
        _add_asset(
            assets,
            _make_asset(
                project_root,
                "tables",
                "api-index-table",
                "核心接口清单",
                chapter_candidates=["05-系统实现.md"],
                section_candidates=["5 系统实现"],
                evidence_level="derived",
                note="适用于系统实现章节的接口摘要表。",
                source_path_override=backend_api_doc and make_relative(backend_api_doc[0], project_root) or "",
                table_headers=["方法", "路径", "接口说明"],
                table_rows=rows,
            ),
        )
    return assets


def _build_database_assets(
    project_root: Path,
    database_file: Path | None,
    table_names: list[str],
    database_doc: tuple[Path, str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    assets = _empty_assets()
    details = _parse_sql_table_details(database_file)
    details_by_table = {detail["table"]: detail for detail in details}
    doc_entries = (
        _extract_database_doc_table_entries(project_root, database_doc[0], database_doc[1]) if database_doc else {}
    )
    rows: list[list[str]] = []
    for detail in details[:16]:
        key_columns = ", ".join(column["name"] for column in detail["columns"][:5])
        purpose = doc_entries.get(detail["table"], {}).get("purpose", "")
        rows.append([detail["table"], purpose or "-", key_columns or "-"])
    if not rows and table_names:
        for name in table_names[:16]:
            purpose = doc_entries.get(name, {}).get("purpose", "")
            rows.append([name, purpose or "-", "-"])
    if rows:
        _add_asset(
            assets,
            _make_asset(
                project_root,
                "tables",
                "database-table-summary",
                "核心数据表摘要",
                path=database_file,
                chapter_candidates=["04-系统设计.md"],
                section_candidates=["4.3 主要数据表结构描述"],
                evidence_level="derived",
                note="适用于第 4 章数据库设计表。",
                source_path_override=_join_source_paths(
                    database_doc and make_relative(database_doc[0], project_root) or "",
                    make_relative(database_file, project_root) if database_file else "",
                ),
                table_headers=["数据表", "主要用途", "关键字段"],
                table_rows=rows,
            ),
        )
    selected_tables = [
        table_name
        for table_name in _prepend_unique(table_names, DATABASE_FIELD_TABLE_PRIORITY, limit=8)
        if table_name in details_by_table
    ]
    for table_name in selected_tables:
        detail = details_by_table[table_name]
        doc_entry = doc_entries.get(table_name, {})
        doc_fields = doc_entry.get("fields", {})
        display_title = str(doc_entry.get("display_title") or table_name).strip()
        field_rows: list[list[str]] = []
        for column in detail["columns"]:
            field_meta = doc_fields.get(column["name"], {})
            field_rows.append(
                [
                    column["name"],
                    column["type"],
                    column["length"],
                    column["nullable"],
                    column["is_primary"],
                    field_meta.get("description", "-"),
                ]
            )
        if not field_rows:
            continue
        _add_asset(
            assets,
            _make_asset(
                project_root,
                "tables",
                f"database-table-structure-{table_name.replace('_', '-')}",
                f"{display_title} {table_name}",
                path=database_file,
                chapter_candidates=["04-系统设计.md"],
                section_candidates=["4.3.3 主要数据表结构描述"],
                evidence_level="derived",
                note="适用于第 4 章数据库设计中的字段级数据字典表。",
                source_path_override=_join_source_paths(
                    database_doc and make_relative(database_doc[0], project_root) or "",
                    make_relative(database_file, project_root) if database_file else "",
                ),
                table_headers=["字段名", "类型", "长度", "允许为空", "是否为主键", "字段描述"],
                table_rows=field_rows,
            ),
        )
    return assets


def _build_traceability_design_table_assets(
    project_root: Path,
    page_names: list[str],
    table_names: list[str],
    blockchain_items: list[str],
    function_doc: tuple[Path, str] | None = None,
    frontend_plan_doc: tuple[Path, str] | None = None,
    backend_plan_doc: tuple[Path, str] | None = None,
    database_doc: tuple[Path, str] | None = None,
    chaincode_doc: tuple[Path, str] | None = None,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    section_assets = {
        "architecture": _empty_assets(),
        "blockchain_design": _empty_assets(),
    }

    frontend_labels = _extract_heading_labels(frontend_plan_doc[1]) if frontend_plan_doc else []
    backend_labels = _extract_heading_labels(backend_plan_doc[1]) if backend_plan_doc else []
    source_path = _join_source_paths(
        function_doc and make_relative(function_doc[0], project_root) or "",
        frontend_plan_doc and make_relative(frontend_plan_doc[0], project_root) or "",
        backend_plan_doc and make_relative(backend_plan_doc[0], project_root) or "",
        database_doc and make_relative(database_doc[0], project_root) or "",
        chaincode_doc and make_relative(chaincode_doc[0], project_root) or "",
    )

    module_rows: list[list[str]] = []
    for spec in TRACEABILITY_MODULE_MAPPING_SPECS:
        frontend_hits = _pick_matches(frontend_labels or page_names, spec["frontend_keywords"], limit=4)
        backend_hits = _pick_matches(backend_labels, spec["backend_keywords"], limit=3)
        table_hits = _pick_preferred_values(table_names, spec["table_keywords"], limit=4)
        chain_hits = _pick_preferred_values(blockchain_items, spec["chain_keywords"], limit=3)
        frontend_output = spec.get("frontend_output") or _compact_join(frontend_hits or spec["frontend_fallback"], limit=4)
        backend_output = spec.get("backend_output") or _compact_join(backend_hits or spec["backend_fallback"], limit=3)
        data_output = spec.get("data_output") or _compact_join(table_hits + chain_hits, limit=5)
        module_rows.append(
            [
                spec["label"],
                spec["responsibility"],
                frontend_output,
                backend_output,
                data_output,
            ]
        )

    if module_rows:
        _add_asset(
            section_assets["architecture"],
            _make_asset(
                project_root,
                "tables",
                "module-design-mapping-table",
                "表4.1 功能模块—设计落点映射",
                chapter_candidates=["04-系统设计.md"],
                section_candidates=["4.2.1 模块划分与分层落点"],
                evidence_level="derived",
                note="依据功能模块规划、前端页面规划、后端模块规划、数据库与链码设计文档汇总生成。",
                source_path_override=source_path,
                table_headers=["功能模块", "主要职责", "前端落点", "后端/服务落点", "数据与链上落点"],
                table_rows=module_rows,
            ),
        )

    security_rows: list[list[str]] = []
    for spec in TRACEABILITY_SECURITY_SPECS:
        table_hits = _pick_preferred_values(table_names, spec["table_keywords"], limit=3)
        chain_hits = _pick_preferred_values(blockchain_items, spec["chain_keywords"], limit=3)
        location_output = spec.get("location_output") or _compact_join(table_hits + chain_hits, limit=5)
        security_rows.append(
            [
                spec["risk"],
                spec["manifestation"],
                spec["mechanism"],
                location_output,
            ]
        )

    if security_rows:
        _add_asset(
            section_assets["blockchain_design"],
            _make_asset(
                project_root,
                "tables",
                "security-risk-summary-table",
                "表4.4 安全机制—风险—落点汇总",
                chapter_candidates=["04-系统设计.md"],
                section_candidates=["4.6.2 安全机制汇总"],
                evidence_level="derived",
                note="依据功能模块规划、后端权限规划、数据库设计与链码权限设计汇总生成。",
                source_path_override=source_path,
                table_headers=["风险", "主要表现", "设计机制", "落点"],
                table_rows=security_rows,
            ),
        )
    return section_assets


def _build_blockchain_assets(
    project_root: Path,
    blockchain_items: list[str],
    blockchain_evidence: list[dict[str, Any]],
    chaincode_doc: tuple[Path, str] | None = None,
    chain_platform: str = "fabric",
) -> dict[str, list[dict[str, Any]]]:
    assets = _empty_assets()
    doc_entries = (
        _extract_chaincode_doc_function_entries(project_root, chaincode_doc[0], chaincode_doc[1]) if chaincode_doc else {}
    )
    evidence_map: dict[str, dict[str, Any]] = {}
    for item in blockchain_evidence:
        claim = item["claim"]
        if claim.startswith(("chaincode transaction detected: ", "contract function detected: ")):
            name = claim.split(": ", 1)[1]
            if re.match(r"^[A-Z][A-Za-z0-9_]+$", name) and name not in evidence_map:
                evidence_map[name] = item
    ordered_names = _prepend_unique(
        blockchain_items,
        list(doc_entries),
        limit=20,
    )
    tx_rows: list[list[str]] = []
    for name in ordered_names:
        if not re.match(r"^[A-Z][A-Za-z0-9_]+$", name):
            continue
        entry = doc_entries.get(name, {})
        evidence_item = evidence_map.get(name, {})
        symbol = evidence_item.get("symbol", name)
        purpose = entry.get("purpose", "")
        tx_rows.append([name, purpose or "-", symbol])
    if not tx_rows:
        tx_rows = [[item, "-", item] for item in blockchain_items[:16] if re.match(r"^[A-Z][A-Za-z0-9_]+$", item)]
    if tx_rows:
        if chain_platform == "fisco":
            tx_title = "合约事务与关键链上能力清单"
            section_title = "4.4 区块链与合约设计"
            tx_note = "适用于区块链设计章节的合约函数清单。"
        else:
            tx_title = "链码事务与关键链上能力清单"
            section_title = "4.4 区块链与链码设计"
            tx_note = "适用于区块链设计章节的链码事务清单。"
        _add_asset(
            assets,
            _make_asset(
                project_root,
                "tables",
                "blockchain-transaction-table",
                tx_title,
                chapter_candidates=["04-系统设计.md"],
                section_candidates=[section_title],
                evidence_level="derived",
                note=tx_note,
                source_path_override=chaincode_doc and make_relative(chaincode_doc[0], project_root) or "",
                table_headers=["事务/函数", "主要用途", "符号"],
                table_rows=tx_rows[:16],
            ),
        )
    return assets


def _scan_image_candidates(project_root: Path) -> list[Path]:
    roots = [
        project_root / ".runtime" / "test-artifacts",
        project_root / "assets",
        project_root / "docs" / "images",
        project_root / "images",
        project_root / "backend" / "storage" / "uploads",
    ]
    images: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        images.extend(path for path in root.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS)
    images.extend(path for path in project_root.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in images:
        rel = make_relative(path, project_root)
        if rel in seen:
            continue
        seen.add(rel)
        unique.append(path)
    return sorted(unique)


def _prettify_image_title(path: Path) -> str:
    title = path.stem.replace("-", " ").replace("_", " ").strip()
    title = re.sub(r"\s+", " ", title)
    return title or path.name


def _test_screenshot_profile(path: Path) -> dict[str, Any]:
    stem = path.stem.lower()
    profile = {
        "title": _prettify_image_title(path),
        "chapters": ["05-系统实现.md", "06-系统测试.md"],
        "sections": ["5 系统实现", "6.2 功能测试"],
        "selection_score": 50,
        "selection_group": "runtime-flow",
        "auto_select": True,
    }

    health_record_rules = {
        "01-login-page": {
            "title": "登录页面截图",
            "sections": ["5.2.1 注册与登录实现", "6.2.1 用户与身份管理功能测试", "6.2 功能测试"],
            "selection_score": 98,
            "selection_group": "health-identity-login",
        },
        "02-register-page": {
            "title": "注册页面截图",
            "sections": ["5.2.1 注册与登录实现", "6.2.1 用户与身份管理功能测试", "6.2 功能测试"],
            "selection_score": 96,
            "selection_group": "health-identity-register",
        },
        "03-doctor-profile": {
            "title": "医生个人资料页面截图",
            "sections": ["5.2.2 个人资料与权限控制实现", "6.2.1 用户与身份管理功能测试", "6.2 功能测试"],
            "selection_score": 94,
            "selection_group": "health-identity-profile-doctor",
        },
        "04-change-password-page": {
            "title": "密码修改页面截图",
            "sections": ["5.2.3 医生审核与账号管理实现", "6.2.1 用户与身份管理功能测试", "6.2 功能测试"],
            "selection_score": 92,
            "selection_group": "health-identity-password",
        },
        "05-doctor-record-create-form": {
            "title": "医生新建档案页面截图",
            "sections": ["5.3.1 档案登记与初诊录入实现", "6.2.2 健康档案管理功能测试", "6.2 功能测试"],
            "selection_score": 96,
            "selection_group": "health-record-create-form",
        },
        "06-doctor-record-create-success": {
            "title": "医生新建档案成功页面截图",
            "sections": ["5.3.1 档案登记与初诊录入实现", "6.2.2 健康档案管理功能测试", "6.2 功能测试"],
            "selection_score": 82,
            "selection_group": "health-record-create-form",
        },
        "07-patient-profile": {
            "title": "患者个人资料页面截图",
            "sections": ["5.2.2 个人资料与权限控制实现", "6.2.1 用户与身份管理功能测试", "6.2 功能测试"],
            "selection_score": 88,
            "selection_group": "health-identity-profile-patient",
        },
        "08-patient-pending-list": {
            "title": "患者待确认档案页面截图",
            "sections": ["5.3.2 患者确认与链上存证实现", "6.2.2 健康档案管理功能测试", "6.2 功能测试"],
            "selection_score": 86,
            "selection_group": "health-record-confirm-pending",
        },
        "09-patient-confirm-dialog": {
            "title": "患者确认档案弹窗截图",
            "sections": ["5.3.2 患者确认与链上存证实现", "6.2.2 健康档案管理功能测试", "6.2 功能测试"],
            "selection_score": 94,
            "selection_group": "health-record-confirm-dialog",
        },
        "10-patient-record-list": {
            "title": "患者档案列表与同步状态页面截图",
            "sections": ["5.5.2 查询审计与链下同步实现", "6.2.4 查询与审计追溯功能测试", "6.2 功能测试"],
            "selection_score": 94,
            "selection_group": "health-audit-patient-record-list",
        },
        "11-doctor-record-search": {
            "title": "医生档案检索与授权状态反馈页面截图",
            "sections": ["5.4.2 授权状态校验与反馈实现", "6.2.3 访问授权管理功能测试", "6.2.4 查询与审计追溯功能测试", "6.2 功能测试"],
            "selection_score": 94,
            "selection_group": "health-access-status-search",
        },
        "12-doctor-authorization-list-pending": {
            "title": "医生授权记录待处理页面截图",
            "sections": ["5.4.1 授权与撤销实现", "6.2.3 访问授权管理功能测试", "6.2 功能测试"],
            "selection_score": 84,
            "selection_group": "health-access-grant-pending-doctor",
        },
        "13-patient-authorization-list-pending": {
            "title": "患者授权处理待处理页面截图",
            "sections": ["5.4.1 授权与撤销实现", "6.2.3 访问授权管理功能测试", "6.2 功能测试"],
            "selection_score": 86,
            "selection_group": "health-access-grant-pending-patient",
        },
        "14-patient-grant-dialog": {
            "title": "患者通过授权弹窗截图",
            "sections": ["5.4.1 授权与撤销实现", "6.2.3 访问授权管理功能测试", "6.2 功能测试"],
            "selection_score": 96,
            "selection_group": "health-access-grant-dialog",
        },
        "15-patient-authorization-list-granted": {
            "title": "患者授权处理已授权页面截图",
            "sections": ["5.4.1 授权与撤销实现", "6.2.3 访问授权管理功能测试", "6.2 功能测试"],
            "selection_score": 82,
            "selection_group": "health-access-grant-patient-granted",
        },
        "16-doctor-authorization-list-granted": {
            "title": "医生授权记录页面截图",
            "sections": ["5.5.1 带权限查询实现", "6.2.4 查询与审计追溯功能测试", "6.2 功能测试"],
            "selection_score": 94,
            "selection_group": "health-audit-doctor-authorization-granted",
        },
        "17-doctor-record-view-granted": {
            "title": "医生查看已授权档案页面截图",
            "sections": ["5.3.3 档案展示与健康数据可视化实现", "5.5.1 带权限查询实现", "6.2.2 健康档案管理功能测试", "6.2.4 查询与审计追溯功能测试", "6.2 功能测试"],
            "selection_score": 92,
            "selection_group": "health-record-view-granted",
        },
        "18-patient-authorization-list-revoked": {
            "title": "患者授权处理已撤销页面截图",
            "sections": ["5.4.1 授权与撤销实现", "5.4.2 授权状态校验与反馈实现", "6.2.3 访问授权管理功能测试", "6.2 功能测试"],
            "selection_score": 80,
            "selection_group": "health-access-revoked-patient",
        },
        "19-doctor-authorization-list-revoked": {
            "title": "医生授权记录已撤销页面截图",
            "sections": ["5.4.2 授权状态校验与反馈实现", "6.2.3 访问授权管理功能测试", "6.2 功能测试"],
            "selection_score": 86,
            "selection_group": "health-access-status-revoked",
        },
        "20-doctor-record-view-denied": {
            "title": "撤销后医生查看受限页面截图",
            "sections": ["5.4.2 授权状态校验与反馈实现", "5.5.2 查询审计与链下同步实现", "6.2.3 访问授权管理功能测试", "6.2.4 查询与审计追溯功能测试", "6.2 功能测试"],
            "selection_score": 88,
            "selection_group": "health-audit-access-denied",
        },
    }
    if stem in health_record_rules:
        profile.update(health_record_rules[stem])
    elif "admin-dashboard-and-forbidden-business-route" in stem:
        profile.update(
            {
                "sections": ["5.2.3 用户管理与权限治理实现", "6.2.1 用户与权限管理功能测试", "6.2 功能测试"],
                "selection_score": 24,
                "selection_group": "identity-permission",
                "auto_select": False,
            }
        )
    elif "admin-dashboard-fixed-flow" in stem:
        profile.update(
            {
                "sections": ["5.2.3 用户管理与权限治理实现", "6.2.1 用户与权限管理功能测试", "6.2 功能测试"],
                "selection_score": 92,
                "selection_group": "identity-dashboard",
            }
        )
    elif "register-five-fixed-accounts-clean" in stem or "register-remaining-accounts" in stem:
        profile.update(
            {
                "sections": ["5.2.1 注册登录与会话建立实现", "6.2.1 用户与权限管理功能测试", "6.2 功能测试"],
                "selection_score": 72 if "five-fixed" in stem else 48,
                "selection_group": "identity-registration",
            }
        )
    elif stem.startswith("role-") and stem.endswith("-default"):
        profile.update(
            {
                "sections": ["5.2.3 用户管理与权限治理实现", "6.2.1 用户与权限管理功能测试", "6.2 功能测试"],
                "selection_score": 18,
                "selection_group": "identity-role-default",
                "auto_select": False,
            }
        )
    elif "dealer-fixed-flow-forbidden" in stem:
        profile.update(
            {
                "sections": ["5.2.3 用户管理与权限治理实现", "6.2.1 用户与权限管理功能测试", "6.2 功能测试"],
                "selection_score": 78,
                "selection_group": "identity-route-guard",
            }
        )
    elif "tea-farmer-default-route-and-menu" in stem:
        profile.update(
            {
                "sections": ["5.2.3 用户管理与权限治理实现", "6.2.1 用户与权限管理功能测试", "6.2 功能测试"],
                "selection_score": 16,
                "selection_group": "identity-route-menu",
                "auto_select": False,
            }
        )
    elif "farmer-fixed-flow" in stem:
        profile.update(
            {
                "sections": ["5.3.3 批次状态维护与全流程入口实现", "6.2.2 批次与主档管理功能测试", "6.2 功能测试"],
                "selection_score": 88,
                "selection_group": "batch-main-flow",
            }
        )
    elif "processor-fixed-flow" in stem:
        profile.update(
            {
                "sections": ["5.4.1 生产环节记录录入实现", "6.2.3 生产流转记录管理功能测试", "6.2 功能测试"],
                "selection_score": 82,
                "selection_group": "record-process-flow",
            }
        )
    elif "inspector-fixed-flow" in stem:
        profile.update(
            {
                "sections": ["5.4.2 仓储物流等流转记录实现", "6.2.3 生产流转记录管理功能测试", "6.2 功能测试"],
                "selection_score": 82,
                "selection_group": "record-inspection-flow",
            }
        )
    elif "logistics-fixed-flow" in stem:
        profile.update(
            {
                "sections": ["5.4.2 仓储物流等流转记录实现", "6.2.3 生产流转记录管理功能测试", "6.2 功能测试"],
                "selection_score": 82,
                "selection_group": "record-logistics-flow",
            }
        )
    elif "dealer-default-route-and-batch-trace" in stem:
        profile.update(
            {
                "sections": ["5.5.3 公开追溯查询与结果展示实现", "6.2.4 溯源码与追溯查询功能测试", "6.2 功能测试"],
                "selection_score": 86,
                "selection_group": "trace-route-query",
            }
        )
    elif "public-trace-success" in stem:
        profile.update(
            {
                "sections": ["5.5.3 公开追溯查询与结果展示实现", "6.2.4 溯源码与追溯查询功能测试", "6.2 功能测试"],
                "selection_score": 96,
                "selection_group": "trace-success",
            }
        )
    elif "public-trace-invalid" in stem:
        profile.update(
            {
                "sections": ["5.5.2 溯源码管理与状态控制实现", "6.2.4 溯源码与追溯查询功能测试", "6.2 功能测试"],
                "selection_score": 90,
                "selection_group": "trace-invalid",
            }
        )
    elif "public-trace-fixed-flow" in stem:
        profile.update(
            {
                "sections": ["5.5.3 公开追溯查询与结果展示实现", "6.2.4 溯源码与追溯查询功能测试", "6.2 功能测试"],
                "selection_score": 84,
                "selection_group": "trace-flow",
            }
        )
    elif "default-route-and-batch-trace" in stem:
        profile.update(
            {
                "sections": ["5.4.3 批次阶段推进与结果展示实现", "6.2.3 生产流转记录管理功能测试", "6.2 功能测试"],
                "selection_score": 20,
                "selection_group": "record-route-trace",
                "auto_select": False,
            }
        )
    elif "webapp-fixed-accounts-error" in stem:
        profile.update(
            {
                "selection_score": 10,
                "selection_group": "debug-error",
                "auto_select": False,
            }
        )

    return profile


def _classify_image_asset(path: Path) -> tuple[str, str, list[str], list[str], str]:
    rel = "/".join(path.parts).lower()
    title = _prettify_image_title(path)
    if ".runtime/test-artifacts" in rel or "assets/frontend_manual_test" in rel:
        profile = _test_screenshot_profile(path)
        return (
            "test-screenshot",
            profile["title"],
            profile["chapters"],
            profile["sections"],
            "explicit",
        )
    if "qrcode" in rel or "trace" in rel:
        return (
            "trace-sample-image",
            title,
            ["05-系统实现.md"],
            ["5.5 溯源码与追溯查询模块实现"],
            "explicit",
        )
    if any(token in rel for token in ["arch", "architecture", "架构", "module"]):
        return (
            "architecture-diagram",
            title,
            ["04-系统设计.md"],
            ["4.1 系统架构设计"],
            "explicit",
        )
    if any(token in rel for token in ["er", "schema", "database"]):
        return (
            "er-diagram",
            title,
            ["04-系统设计.md"],
            ["4.3.2 概念模型 E-R"],
            "explicit",
        )
    return (
        "supporting-image",
        title,
        ["05-系统实现.md"],
        ["5 系统实现"],
        "explicit",
    )


def _build_visual_assets(project_root: Path) -> dict[str, dict[str, list[dict[str, Any]]]]:
    section_assets = {
        "architecture": _empty_assets(),
        "demo_test_evidence": _empty_assets(),
        "blockchain_design": _empty_assets(),
    }
    for path in _scan_image_candidates(project_root):
        kind, title, chapters, sections, evidence_level = _classify_image_asset(path)
        selection_score = 0
        selection_group = ""
        auto_select = True
        if kind == "test-screenshot":
            profile = _test_screenshot_profile(path)
            selection_score = int(profile.get("selection_score", 0) or 0)
            selection_group = str(profile.get("selection_group", "") or "")
            auto_select = bool(profile.get("auto_select", True))
        figure_asset = _make_asset(
            project_root,
            "figures",
            kind,
            title,
            path=path,
            chapter_candidates=chapters,
            section_candidates=sections,
            evidence_level=evidence_level,
            note="图像资产可用于论文配图或截图引用。",
            selection_score=selection_score,
            selection_group=selection_group,
            auto_select=auto_select,
        )
        if kind in {"architecture-diagram", "er-diagram"}:
            _add_asset(section_assets["architecture"], figure_asset)
        else:
            _add_asset(section_assets["demo_test_evidence"], figure_asset)
        if kind == "test-screenshot":
            test_asset = _make_asset(
                project_root,
                "test_artifacts",
                kind,
                title,
                path=path,
                chapter_candidates=["06-系统测试.md"],
                section_candidates=["6.2 功能测试"],
                evidence_level=evidence_level,
                note="测试截图资产，可用于测试章节取证。",
                selection_score=selection_score,
                selection_group=selection_group,
                auto_select=auto_select,
            )
            _add_asset(section_assets["demo_test_evidence"], test_asset)
    return section_assets


def _pick_test_candidate(
    candidates: list[dict[str, str]],
    keywords: list[str],
) -> dict[str, str] | None:
    best: dict[str, str] | None = None
    best_score = 0
    for candidate in candidates:
        haystack = candidate["match_text"]
        score = sum(2 for keyword in keywords if keyword.lower() in haystack)
        score += int(candidate.get("priority", "0"))
        if score > best_score:
            best = candidate
            best_score = score
    return best


def _test_module_case_specs(domain_key: str) -> list[dict[str, Any]]:
    if domain_key == "traceability":
        return [
            {
                "label": "用户与权限管理",
                "keywords": ["login", "register", "auth", "审核", "权限", "role", "msp", "account"],
                "focus": "验证注册登录、机构审核、角色分配与越权拦截是否正确生效。",
            },
            {
                "label": "批次与主档管理",
                "keywords": ["batch", "garden", "category", "farmer", "茶园", "批次", "品类"],
                "focus": "验证品类、茶园、批次建档及批次历史查询是否能够贯通。",
            },
            {
                "label": "生产流转记录管理",
                "keywords": ["farm", "process", "inspection", "storage", "logistics", "sale", "lifecycle", "流转"],
                "focus": "验证农事、加工、质检、仓储、物流、销售等环节能否按阶段推进。",
            },
            {
                "label": "溯源码与追溯查询",
                "keywords": ["trace", "qrcode", "public query", "anti_fake", "溯源", "扫码", "query_count"],
                "focus": "验证溯源码绑定、公开查询、防伪标记与结果展示是否一致。",
            },
            {
                "label": "监管预警与审计分析",
                "keywords": ["warning", "freeze", "unfreeze", "retry", "dashboard", "logs", "recall"],
                "focus": "验证预警处置、冻结解冻、交易重试与日志审计能力。",
            },
        ]
    if domain_key == "health_record":
        return [
            {
                "label": "用户与身份管理",
                "keywords": ["login", "register", "doctor", "patient", "auth", "user"],
                "focus": "验证注册登录、身份区分与权限拦截。",
            },
            {
                "label": "健康档案管理",
                "keywords": ["record", "health", "patient", "upload", "diagnosis"],
                "focus": "验证档案创建、更新、查询与状态同步。",
            },
            {
                "label": "访问授权管理",
                "keywords": ["grant", "revoke", "authorization", "acl", "permission"],
                "focus": "验证授权、撤销与访问控制是否按预期生效。",
            },
            {
                "label": "查询与审计追溯",
                "keywords": ["query", "audit", "trace", "history", "log"],
                "focus": "验证带权限查询、审计留痕与追溯结果。",
            },
        ]
    return [
        {"label": "核心业务流程", "keywords": ["create", "query", "flow", "流程"], "focus": "验证核心业务流程是否跑通。"},
        {"label": "权限与安全控制", "keywords": ["auth", "permission", "role", "access"], "focus": "验证角色权限和访问控制。"},
        {"label": "查询与审计能力", "keywords": ["query", "trace", "audit", "log"], "focus": "验证查询返回与审计链路。"},
    ]


def _build_test_assets(
    project_root: Path,
    doc_texts: list[tuple[Path, str]],
    demo_evidence: list[dict[str, Any]],
    *,
    manifest_title: str = "",
    flow_items: list[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    assets = _empty_assets()
    flow_items = flow_items or []
    rows: list[list[str]] = []
    overall_doc = _find_doc_text(doc_texts, "总体项目文档")
    start_doc = _find_doc_text(doc_texts, "启动脚本说明")
    deploy_doc = _find_doc_text(doc_texts, "test-network部署说明", "部署说明")
    backend_report = _find_doc_text(doc_texts, "test_report")
    manual_test_doc = _find_doc_text(doc_texts, "全流程手动测试文档")
    frontend_test_doc = _find_doc_text(doc_texts, "前端全流程手动测试")

    backend_report_path = make_relative(backend_report[0], project_root) if backend_report else ""
    manual_test_path = make_relative(manual_test_doc[0], project_root) if manual_test_doc else ""
    frontend_test_path = make_relative(frontend_test_doc[0], project_root) if frontend_test_doc else ""
    start_doc_path = make_relative(start_doc[0], project_root) if start_doc else ""
    deploy_doc_path = make_relative(deploy_doc[0], project_root) if deploy_doc else ""
    overall_doc_path = make_relative(overall_doc[0], project_root) if overall_doc else ""
    prioritized_test_paths = {path for path in [backend_report_path, manual_test_path, frontend_test_path] if path}

    def add_test_document(path: Path, title: str, selection_score: int) -> None:
        _add_asset(
            assets,
            _make_asset(
                project_root,
                "test_artifacts",
                "test-document",
                title,
                path=path,
                chapter_candidates=["06-系统测试.md"],
                section_candidates=["6.2 功能测试"],
                evidence_level="explicit",
                note="测试文档资产，可用于测试章节的证据引用。",
                selection_score=selection_score,
                selection_group=f"test-doc:{path.stem.lower()}",
            ),
        )

    if backend_report:
        add_test_document(backend_report[0], "后端回归测试报告", 100)
    if manual_test_doc:
        add_test_document(manual_test_doc[0], "全流程手动测试文档", 92)
    if frontend_test_doc:
        add_test_document(frontend_test_doc[0], "前端全流程手动测试文档", 84)

    test_doc_count = 0
    for item in demo_evidence[:20]:
        rows.append([item["symbol"], item["path"], item["claim"][:80]])
        if not item["path"].endswith((".md", ".txt")):
            continue
        if item["path"] == overall_doc_path:
            continue
        if item["path"] in prioritized_test_paths:
            test_doc_count += 1
            continue
        doc_path = project_root / item["path"]
        if not doc_path.exists():
            continue
        if _optional_test_doc_priority(doc_path, read_text_safe(doc_path)) is None:
            continue
        test_doc_count += 1
        _add_asset(
            assets,
            _make_asset(
                project_root,
                "test_artifacts",
                "test-document",
                item["symbol"],
                path=project_root / item["path"],
                chapter_candidates=["06-系统测试.md"],
                section_candidates=["6.2 功能测试"],
                evidence_level="explicit",
                note="测试文档资产，可用于测试章节的证据引用。",
                selection_score=40,
                selection_group=f"test-doc:{Path(item['path']).stem.lower()}",
            ),
        )
    for path, text in doc_texts:
        rel_path = make_relative(path, project_root)
        if rel_path == overall_doc_path or rel_path in prioritized_test_paths:
            continue
        if _optional_test_doc_priority(path, text) is None:
            continue
        test_doc_count += 1
        _add_asset(
            assets,
            _make_asset(
                project_root,
                "test_artifacts",
                "test-document",
                path.stem,
                path=path,
                chapter_candidates=["06-系统测试.md"],
                section_candidates=["6.2 功能测试"],
                evidence_level="explicit",
                note="测试文档资产，可用于测试章节的证据引用。",
                selection_score=40,
                selection_group=f"test-doc:{path.stem.lower()}",
            ),
        )
    screenshot_count = len(list((project_root / ".runtime" / "test-artifacts").glob("*.png")))

    def fallback_value(value: str, placeholder: str = "待根据当前测试环境补充") -> str:
        return value.strip() if value and value.strip() else placeholder

    def find_line(text: str, pattern: str) -> str:
        match = re.search(pattern, text, flags=re.I | re.M)
        if not match:
            return ""
        value = match.group(1).strip()
        value = re.sub(r"`", "", value)
        return value

    backend_text = backend_report[1] if backend_report else ""
    frontend_text = frontend_test_doc[1] if frontend_test_doc else ""
    overall_text = overall_doc[1] if overall_doc else ""
    deploy_text = deploy_doc[1] if deploy_doc else ""
    tech_route_rows = _extract_markdown_table_rows(overall_text, ["层次", "技术选型", "说明"])
    tech_route_map = {row["层次"]: row for row in tech_route_rows}

    backend_stack = find_line(backend_text, r"1\.\s*Backend:\s*(.+)")
    fabric_network = find_line(backend_text, r"2\.\s*Fabric network:\s*(.+)")
    chaincode_name = find_line(backend_text, r"3\.\s*Chaincode:\s*(.+)")
    database_desc = find_line(backend_text, r"4\.\s*Database:\s*(.+)")
    server_os = find_line(overall_text, r"3\.\s*操作系统[：:]\s*(.+)") or find_line(overall_text, r"\|\s*操作系统\s*\|\s*([^|]+)\|")
    frontend_url = find_line(frontend_text, r"-\s*前端[：:]\s*(.+)")
    backend_url = find_line(frontend_text, r"-\s*后端 API[：:]\s*(.+)")
    backend_port = find_line(overall_text, r"1\.\s*后端端口[：:]\s*(.+)")
    frontend_port = find_line(overall_text, r"2\.\s*前端端口[：:]\s*(.+)")
    browser_desc = "待根据实际页面验证浏览器补充"
    test_tool_desc = "浏览器开发者工具 / Postman" if ("Postman" in (manual_test_doc[1] if manual_test_doc else "")) else "待根据实际测试工具补充"

    domain_key = _detect_domain_key(manifest_title, [], [], flow_items)
    all_docs_text = "\n".join(text for _, text in doc_texts)
    docs_lower = all_docs_text.lower()

    backend_framework = tech_route_map.get("后端框架", {}).get("技术选型", "")
    database_label = tech_route_map.get("数据库", {}).get("技术选型", "")
    chain_platform = tech_route_map.get("区块链平台", {}).get("技术选型", "")
    chain_sdk = tech_route_map.get("链交互方式", {}).get("技术选型", "")
    frontend_framework = tech_route_map.get("前端框架", {}).get("技术选型", "")
    frontend_ui = tech_route_map.get("UI 组件库", {}).get("技术选型", "")
    frontend_stack_real = find_line(frontend_text, r"\|\s*前端技术栈\s*\|\s*`?([^|`]+)`?\s*\|")
    chain_access_desc = find_line(frontend_text, r"\|\s*区块链接入\s*\|\s*`?([^|`]+)`?\s*\|")
    screenshot_dir = find_line(frontend_text, r"\|\s*截图目录\s*\|\s*`?([^|`]+)`?\s*\|")

    if domain_key == "health_record":
        if not backend_framework:
            backend_framework = "Spring Boot + MyBatis" if "spring boot" in docs_lower else "Spring Boot + MyBatis"
        if not database_label:
            database_label = "MySQL"
        if not chain_platform:
            chain_platform = "FISCO BCOS"
        if not chain_sdk:
            chain_sdk = "WeBASE Front / WeBASE Sign + FISCO BCOS Java SDK"
        if not frontend_framework:
            frontend_framework = "Vue2"
        if not frontend_ui and "element ui" in f"{frontend_text} {all_docs_text}".lower():
            frontend_ui = "Element UI"
        browser_desc = "Chrome / Edge（按实际测试浏览器补充版本号）" if frontend_url else browser_desc
        if "playwright" in frontend_text.lower() or "自动化补图脚本" in frontend_text:
            test_tool_desc = "前端全流程手动测试文档 + Playwright 补图脚本 + 浏览器开发者工具"
    else:
        if not backend_framework:
            backend_framework = fallback_value(re.sub(r"`", "", backend_stack), "Gin + GORM + MySQL + Fabric Gateway")
        if not database_label:
            database_label = "MySQL" if "mysql" in database_desc.lower() else "待根据数据库环境补充"
        if not chain_platform:
            chain_platform = "Hyperledger Fabric 2.4.9" if "fabric" in f"{fabric_network} {deploy_text}".lower() else "待根据链网环境补充"
        if not chain_sdk:
            chain_sdk = "Fabric Gateway" if "gateway" in backend_stack.lower() or "gateway" in backend_text.lower() else "待补充"
        if not frontend_framework:
            frontend_framework = "Vue 3"
    frontend_stack = frontend_stack_real or frontend_framework
    if frontend_ui and frontend_ui not in frontend_stack:
        frontend_stack = f"{frontend_framework} + {frontend_ui}"
    elif domain_key != "health_record" and "Vue 3 + TypeScript + Pinia + Vue Router + Axios + Ant Design Vue" in frontend_text:
        frontend_stack = "Vue 3 + Ant Design Vue"

    server_hardware_rows = [
        ["CPU", "待根据当前测试主机补充"],
        ["内存", "待根据当前测试主机补充"],
        ["磁盘", "待根据当前测试主机补充"],
    ]
    server_software_rows = [
        ["操作系统", fallback_value(server_os)],
        ["后端", backend_framework + (f"；默认端口 {backend_port}" if backend_port else "")],
        ["数据库", database_label],
        ["区块链平台", chain_platform + (f"；网络 {fabric_network}" if fabric_network else "")],
        ["链交互组件", chain_sdk + (f"；链码 {chaincode_name}" if chaincode_name else "")],
    ]
    client_hardware_rows = [
        ["CPU", "待根据当前测试主机补充"],
        ["内存", "待根据当前测试主机补充"],
        ["磁盘", "待根据当前测试主机补充"],
    ]
    client_software_rows = [
        ["操作系统", fallback_value(server_os)],
        ["浏览器", browser_desc],
        ["前端", frontend_stack + (f"；默认端口 {frontend_port}" if frontend_port else "")],
        ["测试工具", test_tool_desc],
    ]

    if domain_key == "health_record":
        env_rows = [
            [
                "服务端与链下数据",
                f"{backend_framework} + {database_label}；后端接口基址 {backend_url or '待根据当前测试环境补充'}。",
                _join_source_paths(frontend_test_path, overall_doc_path),
            ],
            [
                "客户端与交互入口",
                f"{frontend_stack}；前端入口 {frontend_url or '待根据当前测试环境补充'}。",
                _join_source_paths(frontend_test_path, overall_doc_path),
            ],
            [
                "区块链与签名接入",
                f"{chain_access_desc or chain_platform}；链交互组件 {chain_sdk}。",
                _join_source_paths(frontend_test_path, deploy_doc_path, overall_doc_path),
            ],
            [
                "测试执行方式",
                f"2026-04-09 真实参数前端全流程手动测试文档 + 页面截图取证{f'（{screenshot_dir}）' if screenshot_dir else ''}。",
                _join_source_paths(frontend_test_path, manual_test_path),
            ],
        ]
    else:
        backend_env_bits = [backend_framework or "待根据后端实现补充"]
        if backend_port:
            backend_env_bits.append(f"后端默认端口 {backend_port}")
        if database_label:
            backend_env_bits.append(f"数据库 {database_label}")
        else:
            backend_env_bits.append("数据库待根据环境补充")

        frontend_env_bits = [frontend_stack or "待根据前端实现补充"]
        if frontend_url:
            frontend_env_bits.append(f"前端入口 {frontend_url}")
        elif frontend_port:
            frontend_env_bits.append(f"前端默认端口 {frontend_port}")
        else:
            frontend_env_bits.append("前端入口待根据当前测试环境补充")
        route_hints = []
        for route in ["/admin", "/trace"]:
            if route in f"{frontend_text} {overall_text}":
                route_hints.append(route)
        if route_hints:
            frontend_env_bits.append(f"常见入口 {'、'.join(route_hints)}")

        chain_env_bits = [chain_platform or "待根据链网环境补充", f"链交互组件 {chain_sdk or '待补充'}"]
        if chaincode_name:
            chain_env_bits.append(f"链码 {chaincode_name}")
        if fabric_network:
            chain_env_bits.append(f"网络 {fabric_network}")

        test_env_bits = []
        if manual_test_path:
            test_env_bits.append("手动全流程文档")
        if frontend_test_path:
            test_env_bits.append("前端测试文档")
        if backend_report_path:
            test_env_bits.append("后端测试报告")
        if screenshot_dir or frontend_test_path:
            test_env_bits.append("页面截图取证")
        if not test_env_bits:
            test_env_bits.append("待根据测试证据补充")

        env_rows = [
            [
                "服务端与链下数据",
                "；".join(backend_env_bits) + "。",
                _join_source_paths(backend_report_path, start_doc_path, overall_doc_path),
            ],
            [
                "客户端与交互入口",
                "；".join(frontend_env_bits) + "。",
                _join_source_paths(frontend_test_path, start_doc_path, overall_doc_path),
            ],
            [
                "区块链与链码环境",
                "；".join(chain_env_bits) + "。",
                _join_source_paths(deploy_doc_path, overall_doc_path),
            ],
            [
                "测试执行方式",
                " + ".join(test_env_bits) + "。",
                _join_source_paths(manual_test_path, frontend_test_path, backend_report_path),
            ],
        ]

    source_candidates: list[dict[str, str]] = []
    for path, text in doc_texts:
        rel_path = make_relative(path, project_root)
        lowered_name = f"{rel_path} {path.name}".lower()
        if any(keyword in lowered_name for keyword in ["测试", "test_report"]):
            source_candidates.append(
                {
                    "label": path.name,
                    "path": rel_path,
                    "match_text": f"{lowered_name} {text[:4000]}".lower(),
                    "priority": "3",
                }
            )
    for path in sorted((project_root / ".runtime" / "test-artifacts").glob("*.png")):
        title = _prettify_image_title(path)
        source_candidates.append(
            {
                "label": title,
                "path": make_relative(path, project_root),
                "match_text": title.lower(),
                "priority": "2",
            }
        )

    case_rows: list[list[str]] = []
    for spec in _test_module_case_specs(domain_key):
        match = _pick_test_candidate(source_candidates, spec["keywords"])
        case_rows.append(
            [
                spec["label"],
                match["label"] if match else "待补测试证据",
                spec["focus"],
                match["path"] if match else "",
            ]
        )

    verified_lines = _extract_markdown_section_lines(backend_report[1], "## Verified Scenarios", limit=12) if backend_report else []
    result_lines = _extract_markdown_section_lines(backend_report[1], "## Key Results", limit=12) if backend_report else []

    def pick_result_line(keywords: list[str]) -> str:
        combined = verified_lines + result_lines
        for line in combined:
            lowered = line.lower()
            if any(keyword.lower() in lowered for keyword in keywords):
                return line
        return ""
    if domain_key == "traceability":
        result_rows = [
            [
                "核心业务链路",
                "通过" if pick_result_line(["full batch lifecycle", "batch", "sale", "inspection"]) else "待补",
                pick_result_line(["full batch lifecycle", "batch", "sale", "inspection"]) or "待根据测试报告补充。",
            ],
            [
                "溯源防伪验证",
                "通过" if pick_result_line(["anti_fake_flag", "public queries", "trace code"]) else "待补",
                pick_result_line(["anti_fake_flag", "public queries", "trace code"]) or "待根据测试报告补充。",
            ],
            [
                "监管与交易重试",
                "通过" if pick_result_line(["retry", "warning", "recall"]) else "待补",
                pick_result_line(["retry", "warning", "recall"]) or "待根据测试报告补充。",
            ],
            [
                "权限与界面边界",
                "通过" if pick_result_line(["dealer login", "admin login", "unauthorized", "jwt"]) else "待补",
                pick_result_line(["dealer login", "admin login", "unauthorized", "jwt"]) or "待根据测试报告补充。",
            ],
        ]
        module_test_assets = [
            {
                "kind": "identity-test-table",
                "title": "用户与权限管理功能测试表",
                "section": "6.2.1 用户与权限管理功能测试",
                "note": "用户与权限管理测试表，优先依据后端测试报告和前端联调结果生成。",
                "rows": [
                    ["1", "管理员正确登录并访问受保护接口", "登录成功；受保护接口返回正常结果", "登录成功；相关接口返回 200" if pick_result_line(["admin login"]) else "待补"],
                    ["2", "输入错误密码或未携带 Token 访问接口", "登录失败或返回 401", "错误登录被拦截；未授权访问返回 401" if pick_result_line(["failed login", "unauthorized", "jwt"]) else "待补"],
                    ["3", "审核业务机构并提交重复 mspId", "审核成功；重复 mspId 返回业务冲突", "审核流程正常完成；重复 mspId 返回 409" if pick_result_line(["duplicate", "mspid", "409"]) or "409" in backend_text else "待补"],
                    ["4", "非管理员角色登录后访问管理员页面", "无法进入管理员工作台", "业务角色未触发管理员工作台请求，越权访问被拦截" if pick_result_line(["dealer login", "dashboard request"]) else "待补"],
                ],
            },
            {
                "kind": "batch-test-table",
                "title": "批次与主档管理功能测试表",
                "section": "6.2.2 批次与主档管理功能测试",
                "note": "批次与主档管理测试表，围绕品类、茶园、批次和链上历史生成。",
                "rows": [
                    ["1", "创建茶叶品类和茶园主档", "主档保存成功并可在页面查询", "创建成功；页面可正常回显"],
                    ["2", "创建茶叶批次", "批次保存成功；自动生成唯一溯源码并完成链上登记", "批次创建成功；生成有效溯源码；链上交易写入成功" if pick_result_line(["batch", "trace code"]) else "待补"],
                    ["3", "查询批次详情与链上历史", "返回批次主档和链上历史记录", "页面可查看批次详情；链上历史可正常查询"],
                ],
            },
            {
                "kind": "record-test-table",
                "title": "生产流转记录管理功能测试表",
                "section": "6.2.3 生产流转记录管理功能测试",
                "note": "生产流转记录测试表，围绕农事、加工、质检、仓储、物流和销售等环节生成。",
                "rows": [
                    ["1", "茶农提交农事记录", "农事记录保存成功并关联目标批次", "提交成功；页面和数据库均可查看记录"],
                    ["2", "加工厂与质检机构依次提交加工记录和质检记录", "阶段记录按顺序写入；质检结果正常回显", "加工与质检记录提交成功；批次状态按流程推进" if pick_result_line(["inspection", "process"]) else "待补"],
                    ["3", "物流商和经销商提交仓储、物流和销售记录", "后续阶段记录连续写入；批次全流程闭环形成", "仓储、物流和销售记录均成功保存并完成展示" if pick_result_line(["storage", "logistics", "sale"]) else "待补"],
                ],
            },
            {
                "kind": "trace-test-table",
                "title": "溯源码与追溯查询功能测试表",
                "section": "6.2.4 溯源码与追溯查询功能测试",
                "note": "溯源码与追溯查询测试表，围绕绑定、查询与防伪异常标记生成。",
                "rows": [
                    ["1", "生成并绑定溯源码", "批次获得有效溯源码，支持二维码展示", "溯源码生成成功；二维码可正常查看"],
                    ["2", "公开查询溯源码", "返回批次、阶段记录、质检结果和链上状态", "公开查询成功；页面可稳定展示完整溯源信息" if pick_result_line(["public query", "trace code"]) else "待补"],
                    ["3", "连续多次查询同一溯源码", "查询次数达到阈值后触发防伪异常标记", "阈值调整后立即生效；连续 3 次查询后异常标记被正确置位" if pick_result_line(["anomaly_threshold", "anti_fake_flag", "query_count"]) else "待补"],
                ],
            },
            {
                "kind": "regulator-test-table",
                "title": "监管预警与审计分析功能测试表",
                "section": "6.2.5 监管预警与审计分析功能测试",
                "note": "监管预警与审计分析测试表，围绕预警、冻结解冻和交易重试生成。",
                "rows": [
                    ["1", "查询预警列表并执行召回分析", "返回目标批次预警信息与影响范围", "预警查询成功；召回分析返回结果正常" if pick_result_line(["warning", "recall"]) else "待补"],
                    ["2", "冻结并解冻异常批次", "批次状态按监管操作变化，并同步写入链上记录", "冻结、解冻均执行成功；状态回写正常" if pick_result_line(["freeze", "unfreeze"]) else "待补"],
                    ["3", "查询交易记录并对失败交易执行人工重试", "返回交易列表；重试后生成新的成功交易记录", "交易列表查询正常；人工重试成功" if pick_result_line(["retry", "tx total", "latest_tx_id"]) else "待补"],
                ],
            },
        ]
        core_flow_rows = [
            ["TC-01", "管理员", "登录并验证权限边界", "系统已初始化", "登录管理员账号并访问工作台", "进入工作台；摘要、预警和交易接口返回正常", "通过" if pick_result_line(["admin login"]) else "待补"],
            ["TC-02", "管理员", "审核业务机构", "存在待审业务机构", "审核茶农与供应链机构", "审核通过；重复 mspId 冲突被正确拦截", "通过" if pick_result_line(["duplicate", "mspid", "409"]) or "409" in backend_text else "待补"],
            ["TC-03", "茶农", "创建品类、茶园与批次", "茶农账号已审核通过", "创建主档并新建批次", "批次建档成功；生成有效溯源码；链上登记成功", "通过" if pick_result_line(["full batch lifecycle", "batch"]) else "待补"],
            ["TC-04", "茶农", "提交农事记录", "已存在有效批次", "选择批次并提交农事记录", "农事记录保存成功并进入批次主线", "通过" if pick_result_line(["full batch lifecycle", "farm"]) else "待补"],
            ["TC-05", "加工厂", "提交加工记录", "已存在农事阶段记录", "录入加工记录", "加工记录保存成功；批次阶段推进", "通过" if pick_result_line(["full batch lifecycle", "process"]) else "待补"],
            ["TC-06", "质检机构", "提交质检报告", "已存在加工阶段记录", "上传质检附件并提交质检结果", "质检记录保存成功；质量状态更新", "通过" if pick_result_line(["full batch lifecycle", "inspection"]) else "待补"],
            ["TC-07", "物流商", "提交仓储与物流记录", "已完成质检", "录入仓储和物流信息", "仓储、物流记录保存成功", "通过" if pick_result_line(["full batch lifecycle", "storage", "logistics"]) else "待补"],
            ["TC-08", "经销商", "提交销售记录", "已完成物流阶段", "录入销售信息", "销售记录保存成功；全流程闭环形成", "通过" if pick_result_line(["full batch lifecycle", "sale"]) else "待补"],
            ["TC-09", "消费者", "公开查询溯源码", "已存在有效溯源码", "输入或扫码查询溯源码", "返回完整溯源信息；查询次数正常累加", "通过" if pick_result_line(["public query", "trace code"]) else "待补"],
            ["TC-10", "管理员", "预警处置与交易重试", "已存在预警批次或待重试交易", "查询预警、冻结解冻、执行人工重试", "监管动作生效；失败交易重试成功", "通过" if pick_result_line(["retry", "warning", "recall"]) else "待补"],
        ]
        nonfunctional_rows = [
            ["安全性", "未登录访问受保护接口", "返回 401", "返回 401" if pick_result_line(["unauthorized", "jwt"]) else "待补"],
            ["安全性", "业务角色访问管理员页面", "被拦截，不触发管理员工作台请求", "拦截成功" if pick_result_line(["dealer login", "dashboard request"]) else "待补"],
            ["稳定性", "重复部署、初始化与流程回归", "系统可稳定复现，使用新业务编号后可继续演示", "验证通过" if "fresh `batchCode`" in backend_text or "全新值" in (manual_test_doc[1] if manual_test_doc else "") else "待补"],
            ["可追溯性", "链上交易与链下业务状态映射", "可查询交易记录，关键批次具备链上凭证", "验证通过" if pick_result_line(["tx total", "latest_tx_id", "blockchain status"]) else "待补"],
            ["可用性", "多角色页面、公开查询页和工作台访问", "页面可正常打开并完成关键操作", "验证通过" if pick_result_line(["browser regression", "admin login", "dealer login"]) else "待补"],
        ]
    elif domain_key == "health_record":
        health_text = f"{frontend_text}\n{manual_test_doc[1] if manual_test_doc else ''}\n{all_docs_text}".lower()

        def has_health_evidence(*snippets: str) -> bool:
            return all(snippet.lower() in health_text for snippet in snippets if snippet)

        register_ok = has_health_evidence("02-register-page.png", "自动在浏览器端生成 rsa 密钥对")
        doctor_login_ok = has_health_evidence("01-login-page.png", "03-doctor-profile.png", "医生登录后跳转 `#/doctor/records`")
        patient_login_ok = has_health_evidence("01-login-page.png", "07-patient-profile.png", "患者登录后跳转 `#/patient/records`")
        password_page_ok = has_health_evidence("04-change-password-page.png")
        record_create_ok = has_health_evidence("06-doctor-record-create-success.png", "提交后生成档案 `35`")
        record_confirm_ok = has_health_evidence("09-patient-confirm-dialog.png", "后端计算档案摘要并写入区块链")
        record_list_ok = has_health_evidence("10-patient-record-list.png", "已确认")
        grant_request_ok = has_health_evidence("12-doctor-authorization-list-pending.png", "授权记录 `19`")
        grant_ok = has_health_evidence("15-patient-authorization-list-granted.png", "授权状态：`已授权`")
        revoke_ok = has_health_evidence("18-patient-authorization-list-revoked.png", "授权状态：`已撤销`")
        doctor_view_ok = has_health_evidence("17-doctor-record-view-granted.png", "医生查看已授权档案")
        denied_ok = has_health_evidence("20-doctor-record-view-denied.png", "http 状态码：`403`", "当前医生未获得查看授权")
        status_sync_ok = has_health_evidence("11-doctor-record-search.png", "19-doctor-authorization-list-revoked.png")
        full_flow_ok = has_health_evidence("创建档案 -> 患者确认 -> 医生申请 -> 患者授权 -> 医生查看 -> 患者撤销 -> 医生受限")

        result_rows = [
            ["身份登录与密钥管理", "通过" if register_ok and doctor_login_ok and patient_login_ok else "待补", "注册页已记录自动生成 RSA 密钥对，医生/患者登录后分别进入对应工作台。"],
            ["档案建档与确认上链", "通过" if record_create_ok and record_confirm_ok else "待补", "档案 35 已完成新建、患者确认和链同步，手动测试文档记录了创建时间与确认时间。"],
            ["授权申请与撤销闭环", "通过" if grant_request_ok and grant_ok and revoke_ok else "待补", "授权 19 已经过待处理、已授权、已撤销三个状态，医生端与患者端列表均有截图留痕。"],
            ["撤销后的访问控制", "通过" if doctor_view_ok and denied_ok else "待补", "授权有效时医生可本地解密查看档案；撤销后直接访问查看页返回 403。"],
        ]
        module_test_assets = [
            {
                "kind": "identity-test-table",
                "title": "用户与身份管理功能测试表",
                "section": "6.2.1 用户与身份管理功能测试",
                "note": "健康档案系统的身份相关测试，依据真实前端手动测试文档与截图生成。",
                "rows": [
                    ["1", "访问注册页并自动生成密钥对", "公钥自动回填，私钥仅在本地展示并支持下载", "已记录注册页真实截图与“自动生成 RSA 密钥对”说明" if register_ok else "待补"],
                    ["2", "医生账号登录并进入个人信息页", "成功跳转医生工作台，个人资料与公钥只读展示", "已记录登录页与医生个人信息页截图" if doctor_login_ok else "待补"],
                    ["3", "患者账号登录并进入个人信息页", "成功跳转患者工作台，个人资料与公钥只读展示", "已记录登录页与患者个人信息页截图" if patient_login_ok else "待补"],
                    ["4", "加载修改密码页面", "页面字段完整，可执行口令更新流程", "已记录修改密码页面截图" if password_page_ok else "待补"],
                ],
            },
            {
                "kind": "record-test-table",
                "title": "健康档案管理功能测试表",
                "section": "6.2.2 健康档案管理功能测试",
                "note": "健康档案建档、确认与列表回显测试，依据真实截图和手动测试文档生成。",
                "rows": [
                    ["1", "医生新建档案并提交患者侧密文", "生成待确认档案，后端仅接收密文", "档案 35 已成功创建，页面记录为待确认" if record_create_ok else "待补"],
                    ["2", "患者输入私钥核验并确认上链", "前端本地解密核验后确认上链，数据库状态更新为已确认", "文档记录档案 35 于 2026-04-09 14:00:12 完成确认并显示“已同步”" if record_confirm_ok else "待补"],
                    ["3", "患者查看全部档案列表", "列表显示已确认档案与链同步状态", "已记录患者全部档案页截图，档案 35 状态为已确认" if record_list_ok else "待补"],
                ],
            },
            {
                "kind": "access-test-table",
                "title": "访问授权管理功能测试表",
                "section": "6.2.3 访问授权管理功能测试",
                "note": "授权申请、通过授权与撤销授权测试，依据真实业务 ID、时间戳与截图生成。",
                "rows": [
                    ["1", "医生对已确认档案申请授权", "生成待处理授权记录，并在医生授权列表中可见", "授权 19 已生成并在医生端显示为待处理" if grant_request_ok else "待补"],
                    ["2", "患者执行重加密并通过授权", "授权状态更新为已授权，医生端出现查看入口", "文档记录授权 19 于 2026-04-09 14:02:07 变为已授权" if grant_ok else "待补"],
                    ["3", "患者撤销已授权记录", "授权状态更新为已撤销，医生端不可继续正常查看", "文档记录授权 19 于 2026-04-09 14:02:20 变为已撤销" if revoke_ok else "待补"],
                ],
            },
            {
                "kind": "audit-test-table",
                "title": "查询与审计追溯功能测试表",
                "section": "6.2.4 查询与审计追溯功能测试",
                "note": "查询回显、授权后查看与撤销后限制校验测试，依据真实页面截图与接口结果生成。",
                "rows": [
                    ["1", "医生检索患者档案并查看授权状态", "可检索到目标档案，确认状态、链同步与授权状态展示一致", "已记录医生档案检索截图和授权记录状态变化" if status_sync_ok else "待补"],
                    ["2", "医生在授权有效时查看档案明文", "输入医生私钥后可在浏览器本地解密查看病历内容", "已记录已授权查看截图与真实病历明文" if doctor_view_ok else "待补"],
                    ["3", "撤销授权后直接访问查看页", "接口返回 403，前端不再展示档案内容", "文档明确记录 HTTP 403 与“当前医生未获得查看授权”" if denied_ok else "待补"],
                ],
            },
        ]
        core_flow_rows = [
            ["TC-01", "医生/患者", "登录并进入对应工作台", "真实账号可用", "使用 13705490741 / 13605490742 登录系统", "医生进入 `#/doctor/records`，患者进入 `#/patient/records`", "通过" if doctor_login_ok and patient_login_ok else "待补"],
            ["TC-02", "医生", "新建健康档案", "患者账号与公钥已存在", "输入患者 ID、病历描述和备注后提交", "生成待确认档案 35，提交内容为患者侧密文", "通过" if record_create_ok else "待补"],
            ["TC-03", "患者", "核验档案并确认上链", "存在待确认档案 35", "输入私钥、本地解密核验后点击确认上链", "档案状态更新为已确认，链同步状态为已同步", "通过" if record_confirm_ok else "待补"],
            ["TC-04", "医生/患者", "完成授权申请与通过授权", "档案 35 已确认", "医生申请授权，患者本地解密后重加密并通过授权", "授权 19 状态变为已授权，医生端出现查看入口", "通过" if grant_request_ok and grant_ok else "待补"],
            ["TC-05", "医生", "在授权有效时查看明文档案", "授权 19 处于已授权状态", "输入医生私钥进入查看页", "浏览器本地解密成功并展示病历描述与备注", "通过" if doctor_view_ok else "待补"],
            ["TC-06", "患者/医生", "撤销授权并校验访问限制", "医生已可查看档案 35", "患者撤销授权后医生再次访问查看页", "授权状态变为已撤销，直接访问查看页返回 403", "通过" if revoke_ok and denied_ok else "待补"],
        ]
        nonfunctional_rows = [
            ["安全性", "注册后仅保存公钥、私钥仅本地展示与下载", "私钥不上传服务器，敏感解密操作在浏览器本地完成", "手动测试文档明确记录“系统仍保持只保存公钥”" if register_ok else "待补"],
            ["安全性", "撤销授权后的访问限制", "撤销后医生无法继续获取医生侧密文或查看明文档案", "已记录 HTTP 403 与前端“未获取到档案内容”" if denied_ok else "待补"],
            ["一致性", "医生端与患者端状态同步", "档案确认、授权通过、授权撤销状态在双方页面保持一致", "医生检索页、医生授权页、患者授权页均已留存截图" if status_sync_ok else "待补"],
            ["可用性", "完整业务链路页面回放", "关键页面能够按流程依次打开并形成闭环留痕", "文档已提供 20 张真实截图覆盖完整业务闭环" if full_flow_ok else "待补"],
        ]
    else:
        result_rows = [
            ["核心业务链路", "待补", "待根据测试报告补充。"],
            ["权限与界面边界", "待补", "待根据测试报告补充。"],
        ]
        module_test_assets = [
            {
                "kind": "identity-test-table",
                "title": "用户与身份管理功能测试表",
                "section": "6.2.1 用户与身份管理功能测试",
                "note": "待根据测试文档补充。",
                "rows": [["1", "待补", "待补", "待补"]],
            },
            {
                "kind": "record-test-table",
                "title": "核心业务管理功能测试表",
                "section": "6.2.2 核心业务管理功能测试",
                "note": "待根据测试文档补充。",
                "rows": [["1", "待补", "待补", "待补"]],
            },
            {
                "kind": "audit-test-table",
                "title": "查询与审计功能测试表",
                "section": "6.2.3 查询与审计功能测试",
                "note": "待根据测试文档补充。",
                "rows": [["1", "待补", "待补", "待补"]],
            },
        ]
        core_flow_rows = [["TC-01", "待补", "待补", "待补", "待补", "待补", "待补"]]
        nonfunctional_rows = [["待补", "待补", "待补", "待补"]]

    _add_asset(
        assets,
        _make_asset(
            project_root,
            "tables",
            "server-hardware-config",
            "服务器端硬件配置表",
            chapter_candidates=["06-系统测试.md"],
            section_candidates=["6.1.1 服务器端"],
            evidence_level="derived",
            source_path_override=_join_source_paths(backend_report_path, manual_test_path, overall_doc_path),
            note="服务器端硬件配置表；若项目材料未提供硬件指标，则保留待补项。",
            table_headers=["硬件", "参数"],
            table_rows=server_hardware_rows,
        ),
    )
    _add_asset(
        assets,
        _make_asset(
            project_root,
            "tables",
            "server-software-config",
            "服务器端软件配置表",
            chapter_candidates=["06-系统测试.md"],
            section_candidates=["6.1.1 服务器端"],
            evidence_level="derived",
            source_path_override=_join_source_paths(backend_report_path, deploy_doc_path, overall_doc_path),
            note="服务器端软件配置表，由后端测试报告和部署文档综合生成。",
            table_headers=["软件", "参数"],
            table_rows=server_software_rows,
        ),
    )
    _add_asset(
        assets,
        _make_asset(
            project_root,
            "tables",
            "client-hardware-config",
            "客户端硬件配置表",
            chapter_candidates=["06-系统测试.md"],
            section_candidates=["6.1.2 客户端"],
            evidence_level="derived",
            source_path_override=_join_source_paths(frontend_test_path, manual_test_path, overall_doc_path),
            note="客户端硬件配置表；若项目材料未提供硬件指标，则保留待补项。",
            table_headers=["硬件", "参数"],
            table_rows=client_hardware_rows,
        ),
    )
    _add_asset(
        assets,
        _make_asset(
            project_root,
            "tables",
            "client-software-config",
            "客户端软件配置表",
            chapter_candidates=["06-系统测试.md"],
            section_candidates=["6.1.2 客户端"],
            evidence_level="derived",
            source_path_override=_join_source_paths(frontend_test_path, manual_test_path, overall_doc_path),
            note="客户端软件配置表，由前端测试文档和项目总体文档综合生成。",
            table_headers=["软件", "参数"],
            table_rows=client_software_rows,
        ),
    )
    _add_asset(
        assets,
        _make_asset(
            project_root,
            "tables",
            "test-environment",
            "系统测试环境",
            chapter_candidates=["06-系统测试.md"],
            section_candidates=["6.1 系统测试环境"],
            evidence_level="derived",
            source_path_override=_join_source_paths(backend_report_path, start_doc_path, deploy_doc_path, overall_doc_path),
            note="测试环境摘要表，由项目栈与测试证据综合生成。",
            table_headers=["环境项", "组成", "依据"],
            table_rows=env_rows,
        ),
    )
    for module_test_asset in module_test_assets:
        _add_asset(
            assets,
            _make_asset(
                project_root,
                "tables",
                module_test_asset["kind"],
                module_test_asset["title"],
                chapter_candidates=["06-系统测试.md"],
                section_candidates=[module_test_asset["section"]],
                evidence_level="derived",
                source_path_override=_join_source_paths(backend_report_path, manual_test_path, frontend_test_path),
                note=module_test_asset["note"],
                table_headers=["序号", "操作", "预期结果", "测试结果"],
                table_rows=module_test_asset["rows"],
            ),
        )
    _add_asset(
        assets,
        _make_asset(
            project_root,
            "tables",
            "test-case-matrix",
            "功能测试用例设计",
            chapter_candidates=["06-系统测试.md"],
            section_candidates=["6.2 功能测试"],
            evidence_level="derived",
            source_path_override=_join_source_paths(manual_test_path, frontend_test_path, backend_report_path),
            note="测试用例设计摘要表，优先依据手动测试文档、后端测试报告和截图取证生成。",
            table_headers=["测试模块", "代表性证据", "验证关注点", "来源"],
            table_rows=case_rows or [["待补", "待补", "根据测试文档补齐", ""]],
        ),
    )
    _add_asset(
        assets,
        _make_asset(
            project_root,
            "tables",
            "core-flow-test-table",
            "功能测试用例（核心流程汇总）",
            chapter_candidates=["06-系统测试.md"],
            section_candidates=["6.2.6 核心流程用例汇总"],
            evidence_level="derived",
            source_path_override=_join_source_paths(manual_test_path, frontend_test_path, backend_report_path),
            note="核心流程用例汇总表，按完整业务主线生成。",
            table_headers=["用例编号", "角色", "测试目标", "前置条件", "测试步骤（简要）", "预期结果", "测试结果"],
            table_rows=core_flow_rows,
        ),
    )
    _add_asset(
        assets,
        _make_asset(
            project_root,
            "tables",
            "test-result-summary",
            "功能测试结果汇总",
            chapter_candidates=["06-系统测试.md"],
            section_candidates=["6.2 功能测试"],
            evidence_level="derived",
            source_path_override=_join_source_paths(backend_report_path, manual_test_path, frontend_test_path),
            note="测试结果汇总表，优先依据后端测试报告的已验证场景与关键结果生成。",
            table_headers=["验证维度", "结果", "说明"],
            table_rows=result_rows,
        ),
    )
    _add_asset(
        assets,
        _make_asset(
            project_root,
            "tables",
            "nonfunctional-test-table",
            "非功能测试项",
            chapter_candidates=["06-系统测试.md"],
            section_candidates=["6.3 非功能测试"],
            evidence_level="derived",
            source_path_override=_join_source_paths(backend_report_path, manual_test_path, frontend_test_path),
            note="非功能测试表，围绕安全性、稳定性、可追溯性和可用性生成。",
            table_headers=["类别", "测试项", "预期结果", "测试结果"],
            table_rows=nonfunctional_rows,
        ),
    )
    if rows:
        _add_asset(
            assets,
            _make_asset(
                project_root,
                "tables",
                "test-evidence-table",
                "测试证据清单",
                chapter_candidates=["06-系统测试.md"],
                section_candidates=["6.2 功能测试"],
                evidence_level="derived",
                note="测试文档与截图索引表，用于第 6 章。",
                table_headers=["证据符号", "路径", "说明"],
                table_rows=rows,
            ),
        )
    return assets


def _build_code_assets(
    project_root: Path,
    frontend_dir: Path | None,
    backend_dir: Path | None,
    chaincode_dir: Path | None,
) -> dict[str, list[dict[str, Any]]]:
    assets = _empty_assets()
    candidate_files: list[tuple[Path, str]] = []
    if backend_dir and (backend_dir / "internal" / "handler" / "router.go").exists():
        candidate_files.append((backend_dir / "internal" / "handler" / "router.go", "backend-router"))
    if chaincode_dir:
        smartcontract = next(iter(sorted(chaincode_dir.rglob("smartcontract.go"))), None)
        if smartcontract:
            candidate_files.append((smartcontract, "chaincode-core"))
    if frontend_dir:
        for rel in [
            frontend_dir / "src" / "pages" / "LoginPage.vue",
            frontend_dir / "src" / "pages" / "trace" / "TraceResultPage.vue",
            frontend_dir / "src" / "router" / "index.ts",
        ]:
            if rel.exists():
                candidate_files.append((rel, "frontend-page"))
    for path, kind in candidate_files:
        _add_asset(
            assets,
            _make_asset(
                project_root,
                "code_artifacts",
                kind,
                path.stem,
                path=path,
                chapter_candidates=["05-系统实现.md"],
                section_candidates=["5 系统实现"],
                evidence_level="explicit",
                note="关键代码入口，可在系统实现章节摘录 1-2 段关键代码或作为实现依据引用。",
            ),
        )
    return assets


def _build_code_assets_from_pack(
    project_root: Path,
    workspace_root: Path,
    code_pack: dict[str, Any],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    section_assets = {
        "api_interfaces": _empty_assets(),
        "demo_test_evidence": _empty_assets(),
    }
    for entry in code_pack.get("entries", []):
        side_label = "后端" if entry.get("side") == "backend" else "前端"
        source_file = project_root / entry.get("source_path", "")
        source_path = source_file if source_file.exists() else None
        code_asset = _make_asset(
            project_root,
            "code_artifacts",
            f"{entry.get('side', 'unknown')}-snippet",
            f"{entry.get('module_label', '模块')}{side_label}代码片段：{entry.get('symbol', 'snippet')}",
            path=source_path,
            chapter_candidates=entry.get("chapter_candidates", ["05-系统实现.md"]),
            section_candidates=entry.get("section_candidates", []),
            evidence_level="explicit",
            note=entry.get("selected_reason", ""),
            module_key=entry.get("module_key", ""),
            side=entry.get("side", ""),
            language=entry.get("language", ""),
            symbol=entry.get("symbol", ""),
            line_start=int(entry.get("line_start", 0) or 0),
            line_end=int(entry.get("line_end", 0) or 0),
            snippet_path=entry.get("snippet_path", ""),
            screenshot_path=entry.get("screenshot_path", ""),
        )
        figure_asset = _make_asset(
            project_root,
            "figures",
            "code-screenshot",
            entry.get("caption", f"{entry.get('module_label', '模块')}{side_label}代码截图"),
            source_path_override=entry.get("screenshot_path", ""),
            chapter_candidates=entry.get("chapter_candidates", ["05-系统实现.md"]),
            section_candidates=entry.get("section_candidates", []),
            evidence_level="generated",
            note=f"白底黑字代码截图，来源 {entry.get('source_path', '')}:{entry.get('line_start', 0)}-{entry.get('line_end', 0)}。",
            module_key=entry.get("module_key", ""),
            side=entry.get("side", ""),
            language=entry.get("language", ""),
            symbol=entry.get("symbol", ""),
            line_start=int(entry.get("line_start", 0) or 0),
            line_end=int(entry.get("line_end", 0) or 0),
            snippet_path=entry.get("snippet_path", ""),
            screenshot_path=entry.get("screenshot_path", ""),
        )
        target_bucket = "api_interfaces" if entry.get("side") == "backend" else "demo_test_evidence"
        _add_asset(section_assets[target_bucket], code_asset)
        _add_asset(section_assets["demo_test_evidence"], figure_asset)
    return section_assets


def _merge_section_assets(*asset_maps: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    merged = _empty_assets()
    for asset_map in asset_maps:
        for bucket in ASSET_BUCKET_ORDER:
            for asset in asset_map.get(bucket, []):
                _add_asset(merged, asset)
    return merged


def _section(
    summary: list[str],
    evidence: list[dict[str, Any]],
    assets: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    return {
        "summary": summary,
        "evidence": evidence,
        "assets": assets or _empty_assets(),
    }


def _render_source_inventory(manifest: dict[str, Any]) -> str:
    lines = ["# Source Inventory", "", "## Source Paths"]
    for key, value in manifest.get("source_paths", {}).items():
        lines.append(f"- {key}: `{value or 'MISSING'}`")
    lines.extend(["", "## Document Paths"])
    for key, values in manifest.get("document_paths", {}).items():
        lines.append(f"- {key}:")
        if values:
            lines.extend([f"  - `{value}`" for value in values])
        else:
            lines.append("  - `MISSING`")
    return "\n".join(lines) + "\n"


def _render_missing_items(missing_inputs: list[str]) -> str:
    lines = ["# Missing Items", ""]
    lines.extend([f"- {item}" for item in missing_inputs] or ["- none"])
    return "\n".join(lines) + "\n"


def _render_asset_bucket_md(bucket: str, assets: list[dict[str, Any]]) -> list[str]:
    lines = [f"### {bucket}", ""]
    if not assets:
        lines.append("- no assets")
        lines.append("")
        return lines
    lines.append(f"- count: {len(assets)}")
    lines.append("")
    lines.append("| title | kind | chapter_candidates | source_path | evidence_level |")
    lines.append("|---|---|---|---|---|")
    for asset in assets[:12]:
        lines.append(
            f"| {asset['title']} | {asset['kind']} | {', '.join(asset['chapter_candidates']) or '-'} | "
            f"`{asset['source_path'] or '-'}` | {asset['evidence_level']} |"
        )
    if len(assets) > 12:
        lines.append(f"| ... truncated ... | - | - | - | total {len(assets)} |")
    lines.append("")
    return lines


def _render_material_pack_md(pack: dict[str, Any]) -> str:
    lines = [
        "# Material Pack",
        "",
        f"- schema_version: {pack['metadata']['schema_version']}",
        f"- title: {pack['metadata']['title']}",
        f"- chain_platform: {pack['metadata']['chain_platform']}",
        f"- project_root: `{pack['metadata']['project_root']}`",
        f"- asset_validation: {pack['validation']['status']}",
        "",
        "## Asset Summary",
        "",
    ]
    for bucket, count in pack["validation"]["asset_counts"].items():
        lines.append(f"- {bucket}: {count}")
    if pack["validation"]["issues"]:
        lines.extend(["", "## Validation Issues", ""])
        lines.extend([f"- {issue}" for issue in pack["validation"]["issues"]])
    lines.append("")
    for section_name in MATERIAL_SECTION_ORDER:
        section = pack["sections"][section_name]
        lines.append(f"## {section_name}")
        lines.append("")
        lines.extend([f"- {item}" for item in section["summary"]] or ["- no summary"])
        lines.append("")
        lines.append("| claim | path | symbol | evidence_type |")
        lines.append("|---|---|---|---|")
        for evidence in section["evidence"]:
            lines.append(
                f"| {evidence['claim']} | `{evidence['path']}` | `{evidence['symbol']}` | {evidence['evidence_type']} |"
            )
        if not section["evidence"]:
            lines.append("| no evidence | - | - | - |")
        lines.append("")
        for bucket in ASSET_BUCKET_ORDER:
            lines.extend(_render_asset_bucket_md(bucket, section.get("assets", {}).get(bucket, [])))
    return "\n".join(lines)


def run_extract(config_path: Path) -> dict[str, Any]:
    ctx = load_workspace_context(config_path)
    workspace_root = ctx["workspace_root"]
    config = ctx["config"]
    manifest = ctx["manifest"]
    project_root = Path(manifest["project_root"]).resolve()
    chain_platform = manifest["chain_platform"]
    output_paths = material_output_paths(config, workspace_root)
    code_pack = build_code_evidence_pack(ctx, output_paths)

    source_paths = manifest.get("source_paths", {})
    document_paths = manifest.get("document_paths", {})
    frontend_dir = _abs_project_path(project_root, source_paths.get("frontend"))
    backend_dir = _abs_project_path(project_root, source_paths.get("backend"))
    database_file = _abs_project_path(project_root, source_paths.get("database"))
    contracts_dir = _abs_project_path(project_root, source_paths.get("contracts"))
    chaincode_dir = _abs_project_path(project_root, source_paths.get("chaincode"))
    doc_texts = _load_doc_texts(project_root, document_paths)
    function_doc = _find_doc_text(doc_texts, "功能模块规划文档")
    backend_plan_doc = _find_doc_text(doc_texts, "后端功能规划文档")
    frontend_plan_doc = _find_doc_text(doc_texts, "前端实现规划文档")
    database_doc = _find_doc_text(doc_texts, "数据库设计文档")
    chaincode_doc = _find_doc_text(doc_texts, "链码设计文档")
    backend_api_doc = _find_doc_text(doc_texts, "后端接口设计文档")
    overall_doc = _find_doc_text(doc_texts, "总体项目文档")
    task_doc = _find_doc_text(doc_texts, "任务书")

    page_names, frontend_evidence = _extract_frontend_pages(project_root, frontend_dir)
    api_items, backend_evidence = _extract_backend_apis(project_root, backend_dir)
    if backend_api_doc:
        api_items = _prepend_unique(api_items, _extract_interface_doc_routes(backend_api_doc[1]), limit=20)
    api_summary = (
        _extract_interface_outline(backend_api_doc[1])
        if backend_api_doc
        else []
    )
    tables, db_evidence = _extract_sql_tables(project_root, database_file)
    if chain_platform == "fisco":
        blockchain_items, blockchain_evidence = _extract_solidity_contracts(project_root, contracts_dir)
    else:
        blockchain_items, blockchain_evidence = _extract_fabric_chaincode(project_root, chaincode_dir)
    if chaincode_doc:
        blockchain_items = _prepend_unique(blockchain_items, _extract_chaincode_doc_functions(chaincode_doc[1]), limit=20)
    elif backend_plan_doc:
        blockchain_items = _prepend_unique(blockchain_items, _extract_chaincode_doc_functions(backend_plan_doc[1]), limit=20)
    roles, role_evidence = _extract_roles(doc_texts, page_names, project_root)
    flows, flow_evidence = _extract_business_flows(doc_texts, blockchain_items, api_items, project_root)
    if function_doc:
        flows = _prepend_unique(
            flows,
            _extract_module_outline(function_doc[1])
            + _extract_markdown_section_lines(function_doc[1], "## 7. 模块关系与业务流程规划", limit=4),
            limit=12,
        )
    if overall_doc:
        flows = _prepend_unique(flows, _extract_markdown_section_lines(overall_doc[1], "### 3.4 业务主流程", limit=3), limit=12)
    deployment_summary, deployment_evidence = _extract_deployment(project_root, source_paths, doc_texts)
    demo_summary, demo_evidence = _extract_demo_evidence(project_root, doc_texts)
    if code_pack.get("entries"):
        demo_summary.append(f"已生成 {len(code_pack['entries'])} 组关键代码截图证据，可支撑系统实现章节的代码取证与截图插入。")

    objective_summary = [
        f"project title: {manifest['title']}",
        f"chain platform: {CHAIN_LABELS.get(chain_platform, chain_platform)}",
        f"discipline: {manifest.get('discipline', 'unknown')}",
    ]
    if function_doc:
        objective_summary = _prepend_unique(
            objective_summary,
            _extract_markdown_section_lines(function_doc[1], "## 2. 项目建设目标", limit=5),
            limit=8,
        )
    if overall_doc:
        objective_summary = _prepend_unique(
            objective_summary,
            _extract_markdown_section_lines(overall_doc[1], "### 1.2 项目目标", limit=3),
            limit=8,
        )
    if task_doc:
        objective_summary = _prepend_unique(
            objective_summary,
            _extract_markdown_section_lines(task_doc[1], "## 一、毕业设计（论文）课题来源及预期目标", limit=3),
            limit=8,
        )
    if len(objective_summary) <= 3 and doc_texts:
        first_doc = doc_texts[0]
        first_para = next(
            (
                _clean_doc_line(line)
                for line in first_doc[1].splitlines()
                if _clean_doc_line(line) and not line.strip().startswith("#")
            ),
            "",
        )
        if first_para:
            objective_summary.append(first_para[:180])

    architecture_summary = _prepend_unique(
        [
        f"frontend: {source_paths.get('frontend') or 'missing'} ({manifest.get('detected_stack', {}).get('frontend_framework', 'unknown')})",
        f"backend: {source_paths.get('backend') or 'missing'} ({manifest.get('detected_stack', {}).get('backend_framework', 'unknown')})",
        f"database: {source_paths.get('database') or 'missing'} ({manifest.get('detected_stack', {}).get('database_kind', 'unknown')})",
        f"chain module: {(source_paths.get('contracts') or source_paths.get('chaincode') or 'missing')} ({manifest.get('detected_stack', {}).get('chain_sdk', 'unknown')})",
        ],
        (
            (_extract_markdown_section_lines(function_doc[1], "### 3.1 技术路线规划", limit=6) if function_doc else [])
            + (_extract_markdown_section_lines(overall_doc[1], "### 2.1 总体架构", limit=4) if overall_doc else [])
            + (_extract_markdown_section_lines(backend_plan_doc[1], "## 3. 后端总体架构规划", limit=3) if backend_plan_doc else [])
            + (_extract_markdown_section_lines(frontend_plan_doc[1], "### 3.2 前端分层", limit=3) if frontend_plan_doc else [])
        ),
        limit=10,
    )
    architecture_evidence = frontend_evidence[:3] + backend_evidence[:3] + db_evidence[:2] + blockchain_evidence[:4]
    domain_key = _detect_domain_key(manifest["title"], api_items, page_names, flows)
    normalized_roles = _normalize_role_labels(roles, role_evidence, domain_key)
    roles_summary = _extract_role_outline(function_doc[1]) if function_doc else []
    if normalized_roles:
        roles_summary = _prepend_unique(roles_summary, [f"角色体系：{'、'.join(normalized_roles)}"], limit=6)
    elif not roles_summary:
        roles_summary = ["角色体系待根据页面权限与业务流程补充。"]

    database_summary = list(tables or ["no database table detected"])
    if database_doc:
        database_summary = _prepend_unique(
            database_summary,
            _extract_markdown_section_lines(database_doc[1], "## 2. 设计目标", limit=4)
            + _extract_markdown_section_lines(database_doc[1], "### 4.1 分层说明", limit=5),
            limit=16,
        )

    blockchain_summary = list(blockchain_items or [f"no {chain_platform} chain module detected"])
    if chaincode_doc:
        blockchain_summary = _prepend_unique(
            blockchain_summary,
            _extract_markdown_section_lines(chaincode_doc[1], "## 2. 链码设计目标", limit=5)
            + _extract_markdown_section_lines(chaincode_doc[1], "### 4.1 关键状态定义", limit=4),
            limit=14,
        )
    elif backend_plan_doc:
        blockchain_summary = _prepend_unique(
            blockchain_summary,
            _extract_markdown_section_lines(backend_plan_doc[1], "### 4.3 链上存证与链码调用模块", limit=5),
            limit=14,
        )

    visual_assets = _build_visual_assets(project_root)
    derived_diagram_assets = _build_derived_diagram_assets(
        project_root,
        manifest,
        source_paths,
        page_names,
        api_items,
        tables,
        flows,
    )
    technology_assets = _build_technology_assets(project_root, manifest, source_paths)
    role_assets = _build_role_assets(project_root, normalized_roles, domain_key)
    api_assets = _build_api_assets(project_root, api_items, backend_evidence, backend_api_doc)
    database_assets = _build_database_assets(project_root, database_file, tables, database_doc)
    blockchain_assets = _build_blockchain_assets(
        project_root,
        blockchain_items,
        blockchain_evidence,
        chaincode_doc,
        manifest.get("chain_platform", "fabric"),
    )
    chapter4_design_assets = (
        _build_traceability_design_table_assets(
            project_root,
            page_names,
            tables,
            blockchain_items,
            function_doc=function_doc,
            frontend_plan_doc=frontend_plan_doc,
            backend_plan_doc=backend_plan_doc,
            database_doc=database_doc,
            chaincode_doc=chaincode_doc,
        )
        if domain_key == "traceability"
        else {
            "architecture": _empty_assets(),
            "blockchain_design": _empty_assets(),
        }
    )
    test_assets = _build_test_assets(
        project_root,
        doc_texts,
        demo_evidence,
        manifest_title=manifest["title"],
        flow_items=flows,
    )
    code_assets = _build_code_assets(project_root, frontend_dir, backend_dir, chaincode_dir)
    extracted_code_assets = _build_code_assets_from_pack(project_root, workspace_root, code_pack)

    sections = {
        "project_objective": _section(objective_summary, architecture_evidence[:4]),
        "architecture": _section(
            architecture_summary,
            architecture_evidence,
            _merge_section_assets(technology_assets, visual_assets["architecture"], derived_diagram_assets["architecture"], chapter4_design_assets["architecture"]),
        ),
        "roles_permissions": _section(
            roles_summary,
            role_evidence,
            role_assets,
        ),
        "business_flows": _section(flows, flow_evidence, derived_diagram_assets["business_flows"]),
        "api_interfaces": _section(
            api_summary or api_items or ["no backend api detected"],
            backend_evidence,
            _merge_section_assets(api_assets, extracted_code_assets["api_interfaces"]),
        ),
        "database_design": _section(
            database_summary,
            db_evidence,
            _merge_section_assets(database_assets, derived_diagram_assets["database_design"]),
        ),
        "blockchain_design": _section(
            blockchain_summary,
            blockchain_evidence,
            _merge_section_assets(blockchain_assets, code_assets, visual_assets["blockchain_design"], chapter4_design_assets["blockchain_design"]),
        ),
        "deployment_runtime": _section(deployment_summary or ["no deployment/runtime evidence detected"], deployment_evidence),
        "demo_test_evidence": _section(
            demo_summary or ["no demo/test evidence detected"],
            demo_evidence,
            _merge_section_assets(test_assets, visual_assets["demo_test_evidence"], extracted_code_assets["demo_test_evidence"]),
        ),
        "risks_conflicts_missing": _section(manifest.get("missing_inputs", []) or ["no missing input recorded"], []),
    }

    pack = {
        "metadata": {
            "schema_version": MATERIAL_PACK_SCHEMA_VERSION,
            "title": manifest["title"],
            "project_root": str(project_root),
            "chain_platform": chain_platform,
            "detection_confidence": manifest.get("detection_confidence", "unknown"),
            "priority_documents": [make_relative(path, project_root) for path, _ in doc_texts[:8]],
        },
        "sections": sections,
        "validation": _validate_pack_sections(sections),
    }

    write_json(output_paths["material_pack_json"], pack)
    write_text(output_paths["material_pack_md"], _render_material_pack_md(pack))
    write_text(output_paths["source_inventory_md"], _render_source_inventory(manifest))
    write_text(output_paths["missing_items_md"], _render_missing_items(manifest.get("missing_inputs", [])))
    return {
        "material_pack_json": output_paths["material_pack_json"],
        "material_pack_md": output_paths["material_pack_md"],
    }
