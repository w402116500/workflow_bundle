from __future__ import annotations

from typing import Any

from core.project_common import CHAIN_LABELS, PROJECT_PROFILE_SCHEMA_VERSION


def _node(
    title: str,
    material_sections: list[str] | None = None,
    children: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "title": title,
        "material_sections": material_sections or [],
        "children": children or [],
    }


def _asset_requirement(
    asset_type: str,
    kind: str,
    title: str,
    *,
    min_count: int = 1,
    section: str = "",
    marker: str = "",
    note: str = "",
) -> dict[str, Any]:
    return {
        "asset_type": asset_type,
        "kind": kind,
        "title": title,
        "min_count": min_count,
        "section": section,
        "marker": marker or title,
        "note": note,
    }


def _subfunction_label(subfunction: Any, fallback: str) -> str:
    if isinstance(subfunction, dict):
        return str(subfunction.get("label", fallback)).strip() or fallback
    return str(subfunction or fallback).strip() or fallback


def _chapter5_module_terminal_section(module: dict[str, Any], module_pos: int) -> str:
    chapter_index = module_pos + 2
    module_label = module.get("label", f"模块{module_pos + 1}")
    subfunctions = module.get("subfunctions", [])
    if not subfunctions:
        return f"5.{chapter_index} {module_label}模块实现"
    label = _subfunction_label(subfunctions[-1], f"子功能{len(subfunctions)}")
    return f"5.{chapter_index}.{len(subfunctions)} {label}"


def _chapter5_screenshot_module_order(modules: list[dict[str, Any]]) -> list[int]:
    if not modules:
        return []

    ordered: list[int] = [0]
    candidates: list[tuple[int, int]] = []
    for index, module in enumerate(modules[1:], start=1):
        text_chunks = [module.get("key", ""), module.get("label", "")]
        text_chunks.extend(_subfunction_label(item, "") for item in module.get("subfunctions", []))
        lowered = " ".join(text_chunks).lower()
        score = 0
        # Prefer externally visible query/trace modules over internal stage/result pages.
        if any(token in lowered for token in ["tracecode", "qrcode", "二维码", "trace", "溯源", "追溯"]):
            score += 140
        if any(token in lowered for token in ["query", "audit", "查询", "审计"]):
            score += 60
        if any(token in lowered for token in ["result", "display", "结果", "展示"]):
            score += 20
        if any(token in lowered for token in ["record", "flow", "stage", "流程", "记录", "流转", "档案"]):
            score += 60
        if any(token in lowered for token in ["batch", "garden", "main", "主档", "批次"]):
            score += 40
        if any(token in lowered for token in ["warning", "regulator", "freeze", "监管", "预警"]):
            score += 20
        candidates.append((score, index))

    for _, index in sorted(candidates, key=lambda item: (-item[0], item[1])):
        if index not in ordered:
            ordered.append(index)
        if len(ordered) >= min(2, len(modules)):
            break

    if len(ordered) == 1 and len(modules) > 1:
        ordered.append(1)
    return ordered


def _chapter5_screenshot_requirements(modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not modules:
        return [
            _asset_requirement("figures", "test-screenshot", "实现章节至少插入 2 张页面截图", min_count=2, section="5.1 实现总体说明")
        ]

    ordered_modules = _chapter5_screenshot_module_order(modules)
    if len(ordered_modules) == 1:
        section = _chapter5_module_terminal_section(modules[ordered_modules[0]], ordered_modules[0])
        return [
            _asset_requirement("figures", "test-screenshot", "实现章节至少插入 2 张页面截图", min_count=2, section=section)
        ]

    requirements: list[dict[str, Any]] = []
    for requirement_index, module_index in enumerate(ordered_modules[:2], start=1):
        section = _chapter5_module_terminal_section(modules[module_index], module_index)
        requirements.append(
            _asset_requirement(
                "figures",
                "test-screenshot",
                f"实现章节代表性页面截图（{requirement_index}）",
                section=section,
            )
        )
    return requirements


def _collect_text(material_pack: dict[str, Any], manifest: dict[str, Any]) -> str:
    chunks = [manifest.get("title", "")]
    for section in material_pack.get("sections", {}).values():
        chunks.extend(section.get("summary", []))
        chunks.extend(item.get("claim", "") for item in section.get("evidence", []))
    return " ".join(chunks).lower()


def derive_domain_profile(manifest: dict[str, Any], material_pack: dict[str, Any]) -> dict[str, str]:
    text = _collect_text(material_pack, manifest)
    trace_tokens = ["traceability", "trace", "batch", "supply chain", "logistics", "溯源", "批次", "物流", "供应链", "茶叶", "二维码"]
    health_tokens = ["health", "ehr", "medical", "健康档案", "病历", "医疗", "诊疗", "患者", "医生"]
    trace_score = sum(1 for token in trace_tokens if token in text)
    health_score = sum(1 for token in health_tokens if token in text)
    if trace_score > 0 and trace_score >= health_score:
        return {"key": "traceability", "label": "产品溯源"}
    if health_score > 0:
        return {"key": "health_record", "label": "健康档案"}
    return {"key": "generic_blockchain", "label": "区块链应用"}


def derive_roles(material_pack: dict[str, Any]) -> list[str]:
    text = " ".join(material_pack.get("sections", {}).get("roles_permissions", {}).get("summary", []))
    roles: list[str] = []
    mapping = [
        ("患者", "患者"),
        ("医生", "医生"),
        ("管理员", "管理员"),
        ("茶农", "茶农"),
        ("加工厂", "加工厂"),
        ("质检机构", "质检机构"),
        ("物流商", "物流商"),
        ("经销商", "经销商"),
        ("消费者", "消费者"),
        ("监管", "监管方"),
        ("tea_farmer", "茶农"),
        ("farmer", "茶农"),
        ("processor", "加工厂"),
        ("inspector", "质检机构"),
        ("logistics", "物流商"),
        ("dealer", "经销商"),
        ("consumer", "消费者"),
        ("manufacturer", "生产方"),
        ("regulator", "监管方"),
        ("admin", "管理员"),
    ]
    lowered = text.lower()
    for raw, label in mapping:
        if raw.lower() in lowered and label not in roles:
            roles.append(label)
    return roles or ["用户"]


def _detect_modules(domain_key: str, manifest: dict[str, Any], material_pack: dict[str, Any]) -> list[dict[str, Any]]:
    text = _collect_text(material_pack, manifest)
    specs: list[dict[str, Any]]

    if domain_key == "health_record":
        specs = [
            {
                "key": "identity",
                "label": "用户与身份管理",
                "patterns": ["auth", "login", "register", "user", "profile", "doctor audit"],
                "sections": ["roles_permissions", "api_interfaces"],
                "subfunctions": [
                    {"label": "注册与登录实现", "keywords": ["register", "login", "auth", "user"]},
                    {"label": "个人资料与权限控制实现", "keywords": ["profile", "permission", "acl", "token"]},
                    {"label": "医生审核与账号管理实现", "keywords": ["doctor audit", "doctor", "admin", "user"]},
                ],
            },
            {
                "key": "record",
                "label": "健康档案管理",
                "patterns": ["record", "health", "patient", "upload", "confirm", "diagnosis"],
                "sections": ["business_flows", "api_interfaces", "database_design", "blockchain_design"],
                "subfunctions": [
                    {"label": "档案登记与初诊录入实现", "keywords": ["upload", "create", "patient", "diagnosis"]},
                    {"label": "患者确认与链上存证实现", "keywords": ["confirm", "recordhash", "txhash", "contract"]},
                    {"label": "档案展示与健康数据可视化实现", "keywords": ["query", "detail", "metrics", "history"]},
                ],
            },
            {
                "key": "access",
                "label": "访问授权管理",
                "patterns": ["acl", "access", "permission", "grant", "revoke", "授权"],
                "sections": ["business_flows", "api_interfaces", "blockchain_design"],
                "subfunctions": [
                    {"label": "授权与撤销实现", "keywords": ["grant", "revoke", "authorize", "access"]},
                    {"label": "授权状态校验与反馈实现", "keywords": ["check", "permission", "acl", "status"]},
                ],
            },
            {
                "key": "audit",
                "label": "查询与审计追溯",
                "patterns": ["audit", "query", "trace", "stats", "log", "审计"],
                "sections": ["api_interfaces", "blockchain_design", "demo_test_evidence"],
                "subfunctions": [
                    {"label": "带权限查询实现", "keywords": ["query", "access", "doctor", "patient"]},
                    {"label": "查询审计与链下同步实现", "keywords": ["audit", "log", "trace", "tx"]},
                ],
            },
            {
                "key": "message",
                "label": "消息反馈与统计分析",
                "patterns": ["message", "feedback", "announce", "notice", "统计"],
                "sections": ["api_interfaces", "roles_permissions"],
                "subfunctions": [
                    {"label": "消息通知与反馈处理实现", "keywords": ["message", "feedback", "notice", "announce"]},
                    {"label": "统计分析实现", "keywords": ["stats", "count", "dashboard", "report"]},
                ],
            },
        ]
    elif domain_key == "traceability":
        specs = [
            {
                "key": "identity",
                "label": "用户与权限管理",
                "patterns": ["user", "auth", "login", "register", "permission", "权限", "审核", "机构"],
                "sections": ["roles_permissions", "api_interfaces"],
                "subfunctions": [
                    {"label": "注册登录与会话建立实现", "keywords": ["register", "login", "auth", "session", "loginpage"]},
                    {"label": "机构审核与链上身份绑定实现", "keywords": ["auditorg", "org", "msp", "identity", "bindchain", "organization"]},
                    {"label": "用户管理与权限治理实现", "keywords": ["users", "role", "permission", "user", "loaddata"]},
                ],
            },
            {
                "key": "batch",
                "label": "批次与主档管理",
                "patterns": ["batch", "garden", "category", "create", "product", "register", "批次", "茶园", "品类"],
                "sections": ["business_flows", "api_interfaces", "database_design", "blockchain_design"],
                "subfunctions": [
                    {"label": "茶园与品类主档维护实现", "keywords": ["garden", "category", "gardenspage"]},
                    {"label": "批次建档与链上登记实现", "keywords": ["batch", "createbatch", "create", "batchespage"]},
                    {"label": "批次状态维护与全流程入口实现", "keywords": ["status", "history", "trace", "freeze", "batch"]},
                ],
            },
            {
                "key": "record",
                "label": "生产流转记录管理",
                "patterns": ["farm", "process", "inspection", "storage", "logistics", "sale", "record", "农事", "加工", "质检", "仓储", "物流", "销售"],
                "sections": ["business_flows", "api_interfaces", "database_design", "blockchain_design"],
                "subfunctions": [
                    {"label": "生产环节记录录入实现", "keywords": ["farm", "process", "record", "farmrecords", "processrecords"]},
                    {"label": "仓储物流等流转记录实现", "keywords": ["storage", "logistics", "sale", "inspection", "createstoragerecord"]},
                    {"label": "批次阶段推进与结果展示实现", "keywords": ["status", "batch", "timeline", "record", "loaddata"]},
                ],
            },
            {
                "key": "trace",
                "label": "溯源码与追溯查询",
                "patterns": ["trace", "trace code", "qrcode", "二维码", "查询", "追溯", "bindtracecode"],
                "sections": ["business_flows", "api_interfaces", "blockchain_design", "demo_test_evidence"],
                "subfunctions": [
                    {"label": "溯源码绑定与二维码生成实现", "keywords": ["bind", "tracecode", "qrcode", "showqrcode"]},
                    {"label": "溯源码管理与状态控制实现", "keywords": ["listtracecodes", "tracecodes", "reissue", "invalid", "manage"]},
                    {"label": "公开追溯查询与结果展示实现", "keywords": ["query", "tracequery", "traceresult", "resultpage"]},
                ],
            },
            {
                "key": "regulator",
                "label": "监管预警与审计分析",
                "patterns": ["regulator", "query", "audit", "history", "warning", "freeze", "监管", "审计", "预警", "冻结"],
                "sections": ["api_interfaces", "blockchain_design", "demo_test_evidence"],
                "subfunctions": [
                    {"label": "质量预警发现与处置实现", "keywords": ["warningspage", "warning", "dispose", "warninglist"]},
                    {"label": "批次冻结解冻与状态恢复实现", "keywords": ["freeze", "unfreeze", "batch", "adminextra"]},
                    {"label": "交易审计与运行态分析实现", "keywords": ["dashboardpage", "dashboard", "blockchainservice", "listtxrecords", "chainstatus"]},
                ],
            },
        ]
    else:
        specs = [
            {
                "key": "identity",
                "label": "用户与身份管理",
                "patterns": ["auth", "login", "register", "user"],
                "sections": ["roles_permissions", "api_interfaces"],
                "subfunctions": [
                    {"label": "账号接入与登录实现", "keywords": ["login", "register", "auth", "user"]},
                    {"label": "角色权限与状态管理实现", "keywords": ["role", "permission", "status", "admin"]},
                ],
            },
            {
                "key": "core",
                "label": "核心业务管理",
                "patterns": ["record", "data", "batch", "business", "query", "upload", "create"],
                "sections": ["business_flows", "api_interfaces", "database_design"],
                "subfunctions": [
                    {"label": "核心数据建档与录入实现", "keywords": ["create", "record", "upload", "data"]},
                    {"label": "核心流程状态推进实现", "keywords": ["status", "flow", "process", "submit"]},
                    {"label": "查询展示与结果反馈实现", "keywords": ["query", "detail", "list", "result"]},
                ],
            },
            {
                "key": "security",
                "label": "权限控制与审计",
                "patterns": ["access", "permission", "audit", "acl", "trace"],
                "sections": ["api_interfaces", "blockchain_design", "demo_test_evidence"],
                "subfunctions": [
                    {"label": "授权校验与访问控制实现", "keywords": ["access", "permission", "acl", "guard"]},
                    {"label": "审计留痕与运行监控实现", "keywords": ["audit", "trace", "log", "monitor"]},
                ],
            },
        ]

    modules: list[dict[str, Any]] = []
    for spec in specs:
        if any(pattern in text for pattern in spec["patterns"]):
            modules.append(spec)
    if not modules:
        modules = specs[:2]
    return modules


def _core_flows(domain_key: str) -> list[str]:
    if domain_key == "health_record":
        return [
            "档案上传确认与链上存证流程",
            "授权撤销与权限校验流程",
            "带权限查询与审计追溯流程",
        ]
    if domain_key == "traceability":
        return [
            "批次创建与链上登记流程",
            "多环节记录提交与状态流转流程",
            "溯源码绑定与追溯查询流程",
        ]
    return [
        "核心业务流程",
        "权限控制与校验流程",
        "查询与审计流程",
    ]


def _numbered_children(prefix: str, labels: list[str], material_sections: list[str]) -> list[dict[str, Any]]:
    return [_node(f"{prefix}.{idx} {label}", material_sections) for idx, label in enumerate(labels, start=1)]


def _implementation_children(prefix: str, material_sections: list[str]) -> list[dict[str, Any]]:
    return [
        _node(f"{prefix}.1 后端实现", material_sections),
        _node(f"{prefix}.2 前端实现", material_sections),
        _node(f"{prefix}.3 关键代码截图", material_sections),
    ]


def _module_implementation_children(prefix: str, module: dict[str, Any]) -> list[dict[str, Any]]:
    subfunctions = module.get("subfunctions", [])
    if not subfunctions:
        return _implementation_children(prefix, module["sections"])

    children: list[dict[str, Any]] = []
    for idx, subfunction in enumerate(subfunctions, start=1):
        label = subfunction["label"] if isinstance(subfunction, dict) else str(subfunction)
        material_sections = subfunction.get("sections", module["sections"]) if isinstance(subfunction, dict) else module["sections"]
        children.append(_node(f"{prefix}.{idx} {label}", material_sections))
    children.append(_node(f"{prefix}.{len(subfunctions) + 1} 关键代码截图", module["sections"]))
    return children


def flatten_section_titles(sections: list[dict[str, Any]]) -> list[str]:
    titles: list[str] = []
    for section in sections:
        titles.append(section["title"])
        titles.extend(flatten_section_titles(section.get("children", [])))
    return titles


def flatten_section_outline(sections: list[dict[str, Any]], depth: int = 1) -> list[dict[str, Any]]:
    outline: list[dict[str, Any]] = []
    for section in sections:
        outline.append(
            {
                "title": section["title"],
                "depth": depth,
                "material_sections": section.get("material_sections", []),
            }
        )
        outline.extend(flatten_section_outline(section.get("children", []), depth + 1))
    return outline


def _base_required_assets(domain_key: str) -> dict[str, list[dict[str, Any]]]:
    if domain_key == "health_record":
        design_figures = [
            _asset_requirement("figures", "architecture-diagram", "图4.1 系统总体架构图", section="4.1 系统架构设计"),
            _asset_requirement("figures", "er-diagram", "图4.2 数据库E-R图", section="4.3.2 概念模型 E-R"),
            _asset_requirement("figures", "flow-diagram", "图4.3 上传确认链上存证流程图", section="4.5.1 上传确认链上存证流程"),
            _asset_requirement("figures", "flow-diagram", "图4.4 授权撤销权限校验流程图", section="4.5.2 授权撤销权限校验流程"),
            _asset_requirement("figures", "flow-diagram", "图4.5 带权限查询与审计追溯流程图", section="4.5.3 带权限查询与审计追溯流程"),
        ]
        design_tables = [
            _asset_requirement("tables", "database-table-summary", "表4.1 核心数据表摘要", section="4.3.3 主要数据表结构描述"),
            _asset_requirement("tables", "blockchain-transaction-table", "表4.2 链码事务与关键链上能力清单", section="4.4 区块链与链码设计"),
        ]
    elif domain_key == "traceability":
        design_figures = [
            _asset_requirement("figures", "architecture-diagram", "图4.1 系统总体架构图", section="4.1 系统架构设计"),
            _asset_requirement("figures", "er-diagram", "图4.2 数据库E-R图", section="4.3.2 概念模型 E-R"),
            _asset_requirement("figures", "flow-diagram", "图4.3 核心业务流程图一", section="4.5.1 批次创建与链上登记流程"),
            _asset_requirement("figures", "flow-diagram", "图4.4 核心业务流程图二", section="4.5.2 多环节记录提交与状态流转流程"),
            _asset_requirement("figures", "flow-diagram", "图4.5 核心业务流程图三", section="4.5.3 溯源码绑定与追溯查询流程"),
        ]
        design_tables = [
            _asset_requirement("tables", "module-design-mapping-table", "表4.1 功能模块—设计落点映射", section="4.2.1 模块划分与分层落点"),
            _asset_requirement("tables", "database-table-structure-sys-org", "表4.2-1 机构表 sys_org", section="4.3.3 主要数据表结构描述"),
            _asset_requirement("tables", "database-table-structure-sys-user", "表4.2-2 用户表 sys_user", section="4.3.3 主要数据表结构描述"),
            _asset_requirement("tables", "database-table-structure-tea-batch", "表4.2-3 茶叶批次表 tea_batch", section="4.3.3 主要数据表结构描述"),
            _asset_requirement("tables", "database-table-structure-tea-farm-record", "表4.2-4 农事记录表 tea_farm_record", section="4.3.3 主要数据表结构描述"),
            _asset_requirement("tables", "database-table-structure-tea-inspection-report", "表4.2-5 质检报告表 tea_inspection_report", section="4.3.3 主要数据表结构描述"),
            _asset_requirement("tables", "database-table-structure-tea-trace-code", "表4.2-6 溯源码表 tea_trace_code", section="4.3.3 主要数据表结构描述"),
            _asset_requirement("tables", "database-table-structure-bc-tx-record", "表4.2-7 链上交易映射表 bc_tx_record", section="4.3.3 主要数据表结构描述"),
            _asset_requirement("tables", "database-table-structure-log-trace-query", "表4.2-8 溯源查询日志表 log_trace_query", section="4.3.3 主要数据表结构描述"),
            _asset_requirement("tables", "blockchain-transaction-table", "表4.3 链码事务与关键链上能力清单", section="4.4 区块链与链码设计"),
            _asset_requirement("tables", "security-risk-summary-table", "表4.4 安全机制—风险—落点汇总", section="4.6.2 安全机制汇总"),
        ]
    else:
        design_figures = [
            _asset_requirement("figures", "architecture-diagram", "图4.1 系统总体架构图", section="4.1 系统架构设计"),
            _asset_requirement("figures", "er-diagram", "图4.2 数据库E-R图", section="4.3.2 概念模型 E-R"),
            _asset_requirement("figures", "flow-diagram", "图4.3 核心业务流程图一", section="4.5.1 批次创建与链上登记流程"),
            _asset_requirement("figures", "flow-diagram", "图4.4 核心业务流程图二", section="4.5.2 多环节记录提交与状态流转流程"),
            _asset_requirement("figures", "flow-diagram", "图4.5 核心业务流程图三", section="4.5.3 溯源码绑定与追溯查询流程"),
        ]
        design_tables = [
            _asset_requirement("tables", "database-table-summary", "表4.1 核心数据表摘要", section="4.3.3 主要数据表结构描述"),
            _asset_requirement("tables", "blockchain-transaction-table", "表4.2 链码事务与关键链上能力清单", section="4.4 区块链与链码设计"),
        ]

    return {
        "02-系统开发工具及技术介绍.md": [
            _asset_requirement("tables", "tech-stack-summary", "表2.1 技术栈与关键组件清单", section="2.1 技术栈与选型概览"),
        ],
        "03-需求分析.md": [
            _asset_requirement("tables", "role-matrix", "表3.1 系统角色与职责摘要", section="3.3 角色与用例分析"),
        ],
        "04-系统设计.md": [
            *design_figures,
            *design_tables,
        ],
        "05-系统实现.md": [
            _asset_requirement("figures", "system-function-structure", "图5.1 系统功能结构图", section="5.1 实现总体说明"),
        ],
        "06-系统测试.md": [
            _asset_requirement("tables", "server-hardware-config", "表6.1 服务器端硬件配置表", section="6.1.1 服务器端"),
            _asset_requirement("tables", "server-software-config", "表6.2 服务器端软件配置表", section="6.1.1 服务器端"),
            _asset_requirement("tables", "client-hardware-config", "表6.3 客户端硬件配置表", section="6.1.2 客户端"),
            _asset_requirement("tables", "client-software-config", "表6.4 客户端软件配置表", section="6.1.2 客户端"),
            _asset_requirement("tables", "identity-test-table", "表6.5 用户与权限管理功能测试表", section="6.2.1 用户与权限管理功能测试"),
            _asset_requirement("tables", "batch-test-table", "表6.6 批次与主档管理功能测试表", section="6.2.2 批次与主档管理功能测试"),
            _asset_requirement("tables", "record-test-table", "表6.7 生产流转记录管理功能测试表", section="6.2.3 生产流转记录管理功能测试"),
            _asset_requirement("tables", "trace-test-table", "表6.8 溯源码与追溯查询功能测试表", section="6.2.4 溯源码与追溯查询功能测试"),
            _asset_requirement("tables", "regulator-test-table", "表6.9 监管预警与审计分析功能测试表", section="6.2.5 监管预警与审计分析功能测试"),
            _asset_requirement("tables", "core-flow-test-table", "表6.10 功能测试用例（核心流程汇总）", section="6.2.6 核心流程用例汇总"),
            _asset_requirement("tables", "nonfunctional-test-table", "表6.11 非功能测试项", section="6.3 非功能测试"),
            _asset_requirement("test_artifacts", "test-document", "测试章节至少引用 2 项测试证据", min_count=2, section="6.2 功能测试"),
        ],
    }


def _preferred_assets() -> dict[str, list[dict[str, Any]]]:
    return {
        "04-系统设计.md": [
            _asset_requirement("tables", "tech-stack-summary", "可补充技术栈映射表", section="4.2 功能模块设计"),
        ],
        "06-系统测试.md": [
            _asset_requirement("figures", "test-screenshot", "可补充功能测试截图", min_count=2, section="6.2 功能测试"),
        ],
    }


def _chapter_profile_for(
    manifest: dict[str, Any],
    material_pack: dict[str, Any],
    domain: dict[str, str],
    roles: list[str],
    modules: list[dict[str, Any]],
) -> dict[str, Any]:
    chain_platform = manifest["chain_platform"]
    chain_label = CHAIN_LABELS.get(chain_platform, chain_platform)
    module_labels = [module["label"] for module in modules]
    role_labels = [f"{role}用例分析" for role in roles]
    flow_labels = _core_flows(domain["key"])
    required_assets = _base_required_assets(domain["key"])
    preferred_assets = _preferred_assets()
    required_assets["05-系统实现.md"] = [
        _asset_requirement("figures", "system-function-structure", "图5.1 系统功能结构图", section="5.1 实现总体说明"),
        *_chapter5_screenshot_requirements(modules),
    ]

    if chain_platform == "fisco":
        chapter_44_children = _numbered_children("4.4", ["链上数据结构与职责划分", "合约—业务功能映射", "链上/链下协同数据流"], ["blockchain_design"])
        tech_23_title = "2.3 智能合约技术"
        tech_23_children = _numbered_children("2.3", ["合约职责与接口摘要", "合约接口可用性说明"], ["blockchain_design"])
        tech_22_title = "2.2 FISCO BCOS 联盟链平台"
        tech_22_children = _numbered_children("2.2", ["本系统的链上职责"], ["blockchain_design"])
    else:
        chapter_44_children = _numbered_children("4.4", ["组织、通道与链码职责划分", "链码事务与账本数据设计", "链上/链下协同数据流"], ["blockchain_design"])
        tech_23_title = "2.3 链码技术"
        tech_23_children = _numbered_children("2.3", ["链码职责与接口摘要", "链码事务说明"], ["blockchain_design"])
        tech_22_title = f"2.2 {chain_label} 区块链平台"
        tech_22_children = _numbered_children("2.2", ["本系统的链上职责"], ["blockchain_design"])

    def _chapter_entry(
        title: str,
        sections: list[dict[str, Any]],
        material_sections: list[str],
        filename: str,
        module_implementation_policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        req_assets = required_assets.get(filename, [])
        preferred = preferred_assets.get(filename, [])
        entry = {
            "title": title,
            "sections": sections,
            "material_sections": material_sections,
            "structure_source": "dynamic-profile",
            "required_assets": req_assets,
            "preferred_assets": preferred,
            "required_table_types": [item["kind"] for item in req_assets if item["asset_type"] == "tables"],
            "required_appendix_items": [item["title"] for item in req_assets if item["asset_type"] == "appendix_items"],
            "placeholder_policy": {
                "mode": "explicit-placeholder-required" if req_assets else "optional",
                "rule": "若未抽取到真实资产，章节必须保留图题/表题/附录标题并显式写出待补占位。",
            },
        }
        if module_implementation_policy:
            entry["module_implementation_policy"] = module_implementation_policy
        return entry

    chapter5_sections = [
        _node("5.1 实现总体说明", ["architecture", "business_flows"]),
        *[
            _node(
                f"5.{idx + 2} {label}模块实现",
                module["sections"],
                _module_implementation_children(f"5.{idx + 2}", module),
            )
            for idx, (label, module) in enumerate(zip(module_labels, modules))
        ],
        _node(f"5.{len(module_labels) + 2} 本章小结", ["api_interfaces", "business_flows"]),
    ]

    chapter_profile = {
        "00-摘要.md": _chapter_entry("摘要", [], ["project_objective"], "00-摘要.md"),
        "00-Abstract.md": _chapter_entry("Abstract", [], ["project_objective"], "00-Abstract.md"),
        "01-绪论.md": _chapter_entry(
            "1 绪论",
            [
                _node("1.1 研究背景与意义", ["project_objective", "architecture"]),
                _node("1.2 国内外研究现状", ["project_objective"]),
                _node("1.3 研究内容", ["project_objective", "business_flows"]),
                _node("1.4 论文组织结构", ["project_objective"]),
                _node("1.5 本章小结", ["project_objective"]),
            ],
            ["project_objective", "architecture", "risks_conflicts_missing"],
            "01-绪论.md",
        ),
        "02-系统开发工具及技术介绍.md": _chapter_entry(
            "2 系统开发工具及技术介绍",
            [
                _node("2.1 技术栈与选型概览", ["architecture"]),
                _node(tech_22_title, ["blockchain_design"], tech_22_children),
                _node(tech_23_title, ["blockchain_design"], tech_23_children),
                _node("2.4 后端开发框架与关键技术", ["architecture", "api_interfaces"], _numbered_children("2.4", ["分层架构", "鉴权与接口交互方式"], ["architecture", "api_interfaces"])),
                _node("2.5 前端开发框架与页面组织", ["architecture", "api_interfaces"]),
                _node("2.6 数据库与存储技术", ["database_design"]),
                _node("2.7 本章小结", ["architecture", "blockchain_design"]),
            ],
            ["architecture", "blockchain_design", "deployment_runtime"],
            "02-系统开发工具及技术介绍.md",
        ),
        "03-需求分析.md": _chapter_entry(
            "3 需求分析",
            [
                _node("3.1 业务需求分析", ["roles_permissions", "business_flows"]),
                _node("3.2 功能需求分析", ["business_flows", "api_interfaces"], _numbered_children("3.2", [f"{label}模块需求" for label in module_labels], ["business_flows", "api_interfaces"])),
                _node("3.3 角色与用例分析", ["roles_permissions"], _numbered_children("3.3", role_labels, ["roles_permissions"])),
                _node("3.4 本章小结", ["roles_permissions", "business_flows"]),
            ],
            ["roles_permissions", "business_flows", "api_interfaces"],
            "03-需求分析.md",
        ),
        "04-系统设计.md": _chapter_entry(
            "4 系统设计",
            [
                _node("4.1 系统架构设计", ["architecture"]),
                _node("4.2 功能模块设计", ["architecture", "business_flows"], _numbered_children("4.2", ["模块划分与分层落点", "关键模块协同关系"], ["architecture", "business_flows"])),
                _node("4.3 数据库设计", ["database_design"], _numbered_children("4.3", ["数据库设计概述", "概念模型 E-R", "主要数据表结构描述"], ["database_design"])),
                _node("4.4 区块链与合约设计" if chain_platform == "fisco" else "4.4 区块链与链码设计", ["blockchain_design"], chapter_44_children),
                _node("4.5 核心业务流程", ["business_flows"], _numbered_children("4.5", flow_labels, ["business_flows", "blockchain_design"])),
                _node("4.6 安全与隐私设计", ["risks_conflicts_missing", "blockchain_design"], _numbered_children("4.6", ["威胁与风险分析", "安全机制汇总"], ["risks_conflicts_missing", "blockchain_design"])),
                _node("4.7 本章小结", ["architecture", "database_design", "blockchain_design"]),
            ],
            ["architecture", "database_design", "blockchain_design", "business_flows"],
            "04-系统设计.md",
        ),
        "05-系统实现.md": _chapter_entry(
            "5 系统实现",
            chapter5_sections,
            ["api_interfaces", "database_design", "blockchain_design", "business_flows", "demo_test_evidence"],
            "05-系统实现.md",
            module_implementation_policy={
                "structure_mode": "module-subfunctions-with-code-screenshots",
                "require_subfunction_sections": True,
                "require_code_screenshot_section": True,
                "integrate_backend_and_frontend_in_subfunctions": True,
                "min_subfunctions_per_module": 2,
                "min_backend_entries_per_module": 1,
                "min_frontend_entries_per_module": 1,
                "preferred_backend_entries_per_module": 2,
                "preferred_frontend_entries_per_module": 2,
                "min_code_screenshots_per_module": 2,
            },
        ),
        "06-系统测试.md": _chapter_entry(
            "6 系统测试",
            [
                _node("6.1 系统测试环境", ["deployment_runtime"], _numbered_children("6.1", ["服务器端", "客户端"], ["deployment_runtime"])),
                _node(
                    "6.2 功能测试",
                    ["demo_test_evidence"],
                    [
                        *_numbered_children("6.2", [f"{label}功能测试" for label in module_labels], ["demo_test_evidence", "business_flows"]),
                        _node("6.2.6 核心流程用例汇总", ["demo_test_evidence", "business_flows"]),
                    ],
                ),
                _node("6.3 非功能测试", ["demo_test_evidence", "risks_conflicts_missing"]),
                _node("6.4 本章小结", ["demo_test_evidence"]),
            ],
            ["demo_test_evidence", "deployment_runtime", "risks_conflicts_missing", "api_interfaces"],
            "06-系统测试.md",
        ),
        "07-结论与展望.md": _chapter_entry(
            "7 结论与展望",
            [
                _node("7.1 研究总结", ["project_objective"]),
                _node("7.2 不足与展望", ["risks_conflicts_missing"]),
            ],
            ["project_objective", "risks_conflicts_missing"],
            "07-结论与展望.md",
        ),
        "08-致谢.md": _chapter_entry("8 致谢", [], [], "08-致谢.md"),
        "REFERENCES.md": _chapter_entry("参考文献", [], [], "REFERENCES.md"),
    }
    return chapter_profile


def build_project_profile(manifest: dict[str, Any], material_pack: dict[str, Any]) -> dict[str, Any]:
    domain = derive_domain_profile(manifest, material_pack)
    roles = derive_roles(material_pack)
    modules = _detect_modules(domain["key"], manifest, material_pack)
    chapter_profile = _chapter_profile_for(manifest, material_pack, domain, roles, modules)
    return {
        "metadata": {
            "schema_version": PROJECT_PROFILE_SCHEMA_VERSION,
            "title": manifest["title"],
            "chain_platform": manifest["chain_platform"],
            "chain_label": CHAIN_LABELS.get(manifest["chain_platform"], manifest["chain_platform"]),
            "domain_key": domain["key"],
            "domain_label": domain["label"],
        },
        "roles": roles,
        "core_modules": modules,
        "chapter_profile": chapter_profile,
    }


def chapter_profile_map(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return profile.get("chapter_profile", {})


def chapter_definition(profile: dict[str, Any], chapter: str) -> dict[str, Any]:
    return chapter_profile_map(profile).get(chapter, {})


def chapter_title(profile: dict[str, Any], chapter: str, fallback: str = "") -> str:
    return chapter_definition(profile, chapter).get("title", fallback)


def chapter_sections(profile: dict[str, Any], chapter: str) -> list[dict[str, Any]]:
    return chapter_definition(profile, chapter).get("sections", [])


def chapter_material_sections(profile: dict[str, Any], chapter: str) -> list[str]:
    return chapter_definition(profile, chapter).get("material_sections", [])


def chapter_required_subsections(profile: dict[str, Any], chapter: str) -> list[str]:
    return flatten_section_titles(chapter_sections(profile, chapter))


def chapter_structure_source(profile: dict[str, Any], chapter: str, fallback: str = "static") -> str:
    return chapter_definition(profile, chapter).get("structure_source", fallback)


def chapter_required_assets(profile: dict[str, Any], chapter: str) -> list[dict[str, Any]]:
    return chapter_definition(profile, chapter).get("required_assets", [])


def chapter_preferred_assets(profile: dict[str, Any], chapter: str) -> list[dict[str, Any]]:
    return chapter_definition(profile, chapter).get("preferred_assets", [])


def chapter_required_table_types(profile: dict[str, Any], chapter: str) -> list[str]:
    return chapter_definition(profile, chapter).get("required_table_types", [])


def chapter_required_appendix_items(profile: dict[str, Any], chapter: str) -> list[str]:
    return chapter_definition(profile, chapter).get("required_appendix_items", [])


def chapter_placeholder_policy(profile: dict[str, Any], chapter: str) -> dict[str, Any]:
    return chapter_definition(profile, chapter).get("placeholder_policy", {"mode": "optional"})


def chapter_module_implementation_policy(profile: dict[str, Any], chapter: str) -> dict[str, Any]:
    return chapter_definition(profile, chapter).get("module_implementation_policy", {})


def render_project_profile_md(profile: dict[str, Any]) -> str:
    lines = [
        "# Project Profile",
        "",
        f"- schema_version: {profile['metadata'].get('schema_version', 'unknown')}",
        f"- title: {profile['metadata']['title']}",
        f"- chain_platform: {profile['metadata']['chain_platform']}",
        f"- domain_label: {profile['metadata']['domain_label']}",
        "",
        "## Roles",
        "",
    ]
    lines.extend([f"- {role}" for role in profile.get("roles", [])] or ["- none"])
    lines.extend(["", "## Core Modules", ""])
    for module in profile.get("core_modules", []):
        lines.append(f"- {module['label']} ({', '.join(module['sections'])})")
        for subfunction in module.get("subfunctions", []):
            label = subfunction["label"] if isinstance(subfunction, dict) else str(subfunction)
            lines.append(f"  - subfunction: {label}")
    lines.extend(["", "## Chapter Structure", ""])
    for chapter, chapter_info in profile.get("chapter_profile", {}).items():
        lines.append(f"### {chapter}")
        lines.append(f"- title: {chapter_info['title']}")
        lines.append(f"- structure_source: {chapter_info['structure_source']}")
        lines.append(f"- required_assets: {len(chapter_info.get('required_assets', []))}")
        lines.append(f"- placeholder_policy: {chapter_info.get('placeholder_policy', {}).get('mode', 'optional')}")
        if chapter_info.get("module_implementation_policy"):
            lines.append(f"- module_implementation_policy: {chapter_info['module_implementation_policy']}")
        for title in flatten_section_titles(chapter_info.get("sections", [])):
            lines.append(f"  - {title}")
        for asset in chapter_info.get("required_assets", []):
            lines.append(f"  - asset: [{asset['asset_type']}] {asset['title']} -> {asset.get('section', '')}")
        lines.append("")
    return "\n".join(lines) + "\n"
