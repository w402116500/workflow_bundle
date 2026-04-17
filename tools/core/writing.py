from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.chapter_profile import (
    _chapter5_screenshot_requirements,
    build_project_profile,
    chapter_definition,
    chapter_material_sections,
    chapter_module_implementation_policy,
    chapter_placeholder_policy,
    chapter_preferred_assets,
    chapter_required_appendix_items,
    chapter_required_assets,
    chapter_required_subsections,
    chapter_required_table_types,
    chapter_structure_source,
    chapter_title,
    flatten_section_outline,
    render_project_profile_md,
)
from core.project_common import (
    ASSET_BUCKET_ORDER,
    CHAPTER_PACKET_SCHEMA_VERSION,
    CHAIN_LABELS,
    CHAPTER_BLUEPRINT,
    PROJECT_PROFILE_SCHEMA_VERSION,
    WRITING_ORDER,
    load_workspace_context,
    material_output_paths,
    read_json,
    read_text_safe,
    write_json,
    write_text,
    writing_output_paths,
)
from core.page_screenshot_assets import chapter5_test_screenshot_workspace_relpath, stage_chapter5_test_screenshots
from core.research_sidecar import (
    build_registry_fallback_index,
    build_research_index,
    research_papers_to_registry_entries,
    run_research_sidecar,
)


REFERENCE_TYPE_MAP = {
    "journal-article": "J",
    "proceedings-article": "C",
    "book-chapter": "M",
    "preprint": "EB",
}

CHAPTER_THEME_MAP = {
    "01-绪论.md": {"domain", "platform", "access_control", "audit", "privacy", "traceability"},
    "02-系统开发工具及技术介绍.md": {"platform", "smart_contract", "storage", "traceability"},
    "03-需求分析.md": {"domain", "access_control", "traceability"},
    "04-系统设计.md": {"platform", "access_control", "audit", "storage", "traceability", "privacy"},
    "05-系统实现.md": {"platform", "smart_contract", "access_control", "audit", "traceability"},
    "06-系统测试.md": {"platform", "traceability", "audit"},
    "07-结论与展望.md": {"domain", "platform"},
    "00-摘要.md": {"domain", "platform", "access_control", "audit"},
    "00-Abstract.md": {"domain", "platform", "access_control", "audit"},
}

CHAPTER_WORD_GUIDANCE = {
    "00-摘要.md": "300-500 汉字",
    "00-Abstract.md": "200-350 English words",
    "01-绪论.md": "1500-2500 字",
    "02-系统开发工具及技术介绍.md": "1200-2200 字",
    "03-需求分析.md": "1500-2500 字",
    "04-系统设计.md": "2500-4000 字",
    "05-系统实现.md": "2500-4000 字",
    "06-系统测试.md": "1500-2500 字",
    "07-结论与展望.md": "800-1500 字",
}

PLACEHOLDER_MARKERS = [
    "待补",
    "TODO",
    "本文件由 scaffold 自动生成",
    "根据材料包补充",
    "Fill the English abstract",
    "补充研究现状与参考文献",
    "配图占位",
    "待按抽取资产生成表格",
]

STYLE_AVOID_PHRASES = [
    "本文",
    "本项目",
    "证据路径",
    "需要说明的是",
    "进行了说明",
    "展开说明",
    "主要说明",
    "总体设计说明",
    "进一步说明",
    "从运行环境看",
    "从系统职责看",
    "从接口组织方式看",
    "从当前代码目录看",
    "从接口分组看",
    "从目录结构看",
    "从应用意义上看",
    "从分层落点看",
    "从概念模型看",
    "从业务流程看",
    "从测试结果看",
]

MATERIAL_VOICE_PHRASES = [
    "后端测试报告",
    "测试报告",
    "测试记录",
    "测试文档",
    "联调文档",
    "联调记录",
    "项目总体说明",
    "部署说明",
    "启动说明",
    "现有项目代码",
    "代码证据",
]

OPENING_RECITAL_PATTERNS = [
    r"^本章主要",
    r"^本章详细",
    r"^本章介绍",
    r"^本章说明",
    r"^本章阐述",
]

SUMMARY_RECAP_PATTERNS = [
    r"本章首先",
    r"本章先",
    r"其次",
    r"然后",
    r"最后",
    r"分别对",
]

AUTO_TRANSITIONS = {
    "pending": {"prepared"},
    "prepared": {"drafted"},
    "drafted": {"polished"},
    "polished": {"reviewed"},
    "reviewed": set(),
}

MANUAL_TRANSITIONS = {
    "manual_pending": {"reviewed"},
    "reviewed": set(),
}

MODE_STATUS_MAP = {
    "auto": {"pending", "prepared", "drafted", "polished", "reviewed"},
    "manual": {"manual_pending", "reviewed"},
    "registry": {"managed"},
}

OUTLINE_SYNC_BLOCKING_STATUSES = {"stale", "legacy", "missing"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _default_chapter_title_map() -> dict[str, str]:
    return {filename: title for filename, title, _ in CHAPTER_BLUEPRINT}


def _load_or_build_project_profile(
    manifest: dict[str, Any],
    material_pack: dict[str, Any],
    writing_paths: dict[str, Path],
) -> dict[str, Any]:
    profile_json = writing_paths["project_profile_json"]
    if profile_json.exists():
        profile = read_json(profile_json)
        if not _project_profile_needs_refresh(profile):
            return profile

    profile = build_project_profile(manifest, material_pack)
    write_json(profile_json, profile)
    write_text(writing_paths["project_profile_md"], render_project_profile_md(profile))
    return profile


def _project_profile_needs_refresh(profile: dict[str, Any]) -> bool:
    metadata = profile.get("metadata", {})
    if metadata.get("schema_version") != PROJECT_PROFILE_SCHEMA_VERSION:
        return True
    if "5.1 实现总体说明" in chapter_required_subsections(profile, "05-系统实现.md"):
        return True
    for chapter in {"04-系统设计.md", "05-系统实现.md", "06-系统测试.md"}:
        info = chapter_definition(profile, chapter)
        if "required_assets" not in info or "placeholder_policy" not in info:
            return True
    if "module_implementation_policy" not in chapter_definition(profile, "05-系统实现.md"):
        return True
    chapter5_policy = chapter_module_implementation_policy(profile, "05-系统实现.md")
    if chapter5_policy.get("structure_mode") != "module-subfunctions-with-inline-code":
        return True
    chapter5_required_assets = chapter_required_assets(profile, "05-系统实现.md")
    expected_chapter5_test_screenshots = len(_chapter5_screenshot_requirements(profile.get("core_modules", [])))
    current_chapter5_test_screenshots = sum(
        1
        for asset in chapter5_required_assets
        if asset.get("asset_type") == "figures" and asset.get("kind") == "test-screenshot"
    )
    if current_chapter5_test_screenshots != expected_chapter5_test_screenshots:
        return True
    if any(not module.get("subfunctions") for module in profile.get("core_modules", [])):
        return True
    return False


def _chapter_title_map(project_profile: dict[str, Any] | None = None) -> dict[str, str]:
    title_map = _default_chapter_title_map()
    if not project_profile:
        return title_map
    for filename in title_map:
        profile_title = chapter_title(project_profile, filename, title_map[filename])
        title_map[filename] = profile_title
    return title_map


def _final_chapter_order(config: dict[str, Any]) -> list[str]:
    build = config.get("build", {})
    return list(build.get("chapter_order") or [filename for filename, _, _ in CHAPTER_BLUEPRINT])


def _render_outline_tree(sections: list[dict[str, Any]], depth: int = 0) -> list[str]:
    lines: list[str] = []
    for section in sections:
        indent = "  " * depth
        lines.append(f"{indent}- {section['title']}")
        lines.extend(_render_outline_tree(section.get("children", []), depth + 1))
    return lines


def _build_outline_tree(flat_outline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tree: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []
    for item in flat_outline:
        depth = max(int(item.get("depth", 1)), 1)
        node = {"title": item["title"], "children": []}
        while len(stack) >= depth:
            stack.pop()
        if stack:
            stack[-1]["children"].append(node)
        else:
            tree.append(node)
        stack.append(node)
    return tree


def _build_thesis_outline(
    workspace_root: Path,
    config: dict[str, Any],
    manifest: dict[str, Any],
    project_profile: dict[str, Any],
    writing_paths: dict[str, Path],
) -> dict[str, Any]:
    titles = _chapter_title_map(project_profile)
    chapters: list[dict[str, Any]] = []
    for filename in _final_chapter_order(config):
        structure_source = chapter_structure_source(project_profile, filename)
        queue_stub = _initial_queue_entry(filename, titles[filename], structure_source, workspace_root, writing_paths, config)
        chapter_info = chapter_definition(project_profile, filename)
        required_assets = chapter_required_assets(project_profile, filename)
        chapters.append(
            {
                "chapter": filename,
                "title": titles[filename],
                "mode": queue_stub["mode"],
                "structure_source": structure_source,
                "required_subsections": chapter_required_subsections(project_profile, filename),
                "required_assets": [asset.get("title", "") for asset in required_assets],
                "section_outline": flatten_section_outline(chapter_info.get("sections", [])),
            }
        )
    return {
        "generated_at": _now_iso(),
        "title": manifest.get("title", ""),
        "chain_platform": manifest.get("chain_platform", ""),
        "domain_label": project_profile.get("metadata", {}).get("domain_label", ""),
        "source_of_truth": config.get("build", {}).get("input_dir", "polished_v3"),
        "lock_policy": "Review and lock the thesis outline before chapter drafting. If the outline changes, rerun prepare-writing afterwards.",
        "citation_policy": {
            "numbering_rule": "Citations are renumbered by first appearance across the thesis.",
            "reuse_rule": "Prefer one primary use per reference; repeated use is allowed only when necessary and will be reported in citation_audit.md.",
        },
        "chapter_order": _final_chapter_order(config),
        "writing_order": list(WRITING_ORDER),
        "chapters": chapters,
    }


def _render_thesis_outline_md(outline: dict[str, Any]) -> str:
    lines = [
        "# Thesis Outline",
        "",
        f"- generated_at: {outline['generated_at']}",
        f"- title: {outline['title']}",
        f"- chain_platform: {outline['chain_platform']}",
        f"- domain_label: {outline['domain_label']}",
        f"- source_of_truth: `{outline['source_of_truth']}`",
        "",
        "## Lock Rules",
        "",
        f"- {outline['lock_policy']}",
        f"- {outline['citation_policy']['numbering_rule']}",
        f"- {outline['citation_policy']['reuse_rule']}",
        "",
        "## Directory",
        "",
    ]
    for index, chapter in enumerate(outline["chapters"], start=1):
        lines.append(f"{index}. `{chapter['chapter']}` {chapter['title']}")
        for line in _render_outline_tree(_build_outline_tree(chapter.get("section_outline", []))):
            lines.append(f"   {line}")
    lines.extend(["", "## Chapter Constraints", ""])
    for chapter in outline["chapters"]:
        lines.extend(
            [
                f"### {chapter['chapter']}",
                "",
                f"- mode: {chapter['mode']}",
                f"- structure_source: {chapter['structure_source']}",
                f"- required_subsections: {', '.join(chapter['required_subsections']) or 'none'}",
                f"- required_assets: {', '.join(chapter['required_assets']) or 'none'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _write_thesis_outline(
    workspace_root: Path,
    config: dict[str, Any],
    manifest: dict[str, Any],
    project_profile: dict[str, Any],
    writing_paths: dict[str, Path],
) -> dict[str, Path]:
    outline = _build_thesis_outline(workspace_root, config, manifest, project_profile, writing_paths)
    write_json(writing_paths["thesis_outline_json"], outline)
    write_text(writing_paths["thesis_outline_md"], _render_thesis_outline_md(outline))
    return {
        "thesis_outline_json": writing_paths["thesis_outline_json"],
        "thesis_outline_md": writing_paths["thesis_outline_md"],
    }


def _outline_signature(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()[:12]


def _build_chapter_outline_snapshot(
    chapter: str,
    title: str,
    required_subsections: list[str],
    required_assets: list[str],
    section_outline: list[dict[str, Any]],
) -> dict[str, Any]:
    snapshot = {
        "chapter": chapter,
        "title": title,
        "required_subsections": list(required_subsections),
        "required_assets": list(required_assets),
        "section_outline": list(section_outline),
    }
    snapshot["signature"] = _outline_signature(snapshot)
    return snapshot


def _chapter_outline_snapshot(
    thesis_outline: dict[str, Any],
    chapter: str,
    fallback_title: str = "",
    fallback_required_subsections: list[str] | None = None,
    fallback_required_assets: list[str] | None = None,
    fallback_section_outline: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    chapter_entry = next((item for item in thesis_outline.get("chapters", []) if item.get("chapter") == chapter), None)
    if chapter_entry:
        return _build_chapter_outline_snapshot(
            chapter_entry.get("chapter", chapter),
            chapter_entry.get("title", fallback_title),
            list(chapter_entry.get("required_subsections", [])),
            list(chapter_entry.get("required_assets", [])),
            list(chapter_entry.get("section_outline", [])),
        )
    return _build_chapter_outline_snapshot(
        chapter,
        fallback_title,
        fallback_required_subsections or [],
        fallback_required_assets or [],
        fallback_section_outline or [],
    )


def _detect_packet_kind(packet: dict[str, Any]) -> str:
    if packet.get("input_files") and packet.get("output_contract"):
        return "full"
    return packet.get("packet_kind", "stub")


def _resolve_packet_outline_sync(
    packet_path: Path,
    current_snapshot: dict[str, Any],
    current_outline_generated_at: str,
) -> dict[str, Any]:
    sync_info = {
        "packet_exists": packet_path.exists(),
        "packet_kind": "missing",
        "packet_generated_at": "",
        "packet_outline_generated_at": "",
        "packet_outline_signature": "",
        "current_outline_generated_at": current_outline_generated_at,
        "current_outline_signature": current_snapshot["signature"],
        "status": "missing",
        "warning": "未找到章节 packet，需执行 prepare-chapter 生成写作包。",
    }
    if not packet_path.exists():
        return sync_info

    packet = read_json(packet_path)
    packet_kind = _detect_packet_kind(packet)
    outline_sync = packet.get("outline_sync", {})
    packet_signature = outline_sync.get("outline_signature") or packet.get("outline_snapshot", {}).get("signature", "")
    packet_outline_generated_at = outline_sync.get("outline_generated_at", "")

    sync_info.update(
        {
            "packet_kind": packet_kind,
            "packet_generated_at": packet.get("generated_at", ""),
            "packet_outline_generated_at": packet_outline_generated_at,
            "packet_outline_signature": packet_signature,
        }
    )

    if not packet_signature:
        sync_info["status"] = "legacy"
        sync_info["warning"] = "现有 packet 不含大纲快照，需重新执行 prepare-chapter 以建立目录同步信息。"
        return sync_info

    if packet_signature != current_snapshot["signature"]:
        sync_info["status"] = "stale"
        sync_info["warning"] = "当前大纲已变化，现有 packet 与最新目录不一致，需重新执行 prepare-chapter。"
        return sync_info

    sync_info["status"] = "current"
    sync_info["warning"] = ""
    return sync_info


def run_prepare_outline(config_path: Path) -> dict[str, Path]:
    ctx = load_workspace_context(config_path)
    workspace_root = ctx["workspace_root"]
    config = ctx["config"]
    manifest = ctx["manifest"]
    writing_paths = writing_output_paths(config, workspace_root)
    material_pack = read_json(material_output_paths(config, workspace_root)["material_pack_json"])
    project_profile = _load_or_build_project_profile(manifest, material_pack, writing_paths)
    return _write_thesis_outline(workspace_root, config, manifest, project_profile, writing_paths)


def _normalize_chapter_name(chapter: str) -> str:
    return Path(chapter).name


def _extract_theme_keywords(text: str) -> set[str]:
    lowered = text.lower()
    themes: set[str] = set()
    theme_rules = {
        "domain": ["health", "medical", "ehr", "record", "医疗", "病历", "档案", "traceability", "trace", "溯源", "supply chain", "供应链"],
        "platform": ["fisco", "fabric", "blockchain", "ledger", "联盟链", "区块链"],
        "access_control": ["access control", "authorization", "acl", "permission", "授权", "访问控制", "权限"],
        "audit": ["audit", "trace", "审计", "追溯"],
        "privacy": ["privacy", "secure", "隐私", "安全"],
        "storage": ["storage", "database", "off-chain", "链下", "数据库"],
        "smart_contract": ["smart contract", "chaincode", "solidity", "contractapi", "合约", "链码"],
        "traceability": ["traceability", "trace", "logistics", "溯源", "物流", "supply chain", "batch"],
    }
    for theme, keywords in theme_rules.items():
        if any(keyword in lowered for keyword in keywords):
            themes.add(theme)
    return themes or {"domain", "platform"}


def _generate_queries(manifest: dict[str, Any], material_pack: dict[str, Any]) -> list[str]:
    title = manifest["title"]
    chain_platform = manifest["chain_platform"]
    chain_label = CHAIN_LABELS.get(chain_platform, chain_platform)
    source_text = " ".join(
        [title]
        + material_pack["sections"]["project_objective"]["summary"]
        + material_pack["sections"]["business_flows"]["summary"]
        + material_pack["sections"]["blockchain_design"]["summary"]
    )
    themes = _extract_theme_keywords(source_text)

    queries: list[str] = []
    if chain_platform == "fisco":
        queries.extend(
            [
                "FISCO BCOS system design implementation",
                "FISCO BCOS blockchain application",
                "consortium blockchain access control audit",
            ]
        )
    else:
        queries.extend(
            [
                "Hyperledger Fabric system design implementation",
                "Hyperledger Fabric chaincode application",
                "Hyperledger Fabric traceability audit",
            ]
        )

    if "domain" in themes and any(token in source_text.lower() for token in ["health", "medical", "ehr", "record", "医疗", "病历", "档案"]):
        queries.extend(
            [
                "electronic health record blockchain access control",
                "healthcare blockchain audit consortium",
                "medical data sharing blockchain privacy",
            ]
        )
    if "traceability" in themes:
        queries.extend(
            [
                "blockchain traceability system supply chain",
                "Hyperledger Fabric supply chain traceability",
                "product traceability blockchain audit",
            ]
        )
    if "access_control" in themes:
        queries.append("blockchain access control smart contract")
    if "audit" in themes:
        queries.append("blockchain audit traceability")

    queries.append(f"{chain_label} blockchain system")
    unique: list[str] = []
    for query in queries:
        if query not in unique:
            unique.append(query)
    return unique[:8]


def _strip_html_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _crossref_search(query: str, rows: int = 8, from_year: int = 2019) -> list[dict[str, Any]]:
    params = {
        "query.bibliographic": query,
        "rows": str(rows),
        "filter": f"from-pub-date:{from_year}-01-01",
        "select": "DOI,title,author,issued,published-print,published-online,container-title,type,URL,abstract,publisher",
    }
    url = "https://api.crossref.org/works?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "thesis-workflow/1.0 (academic writing tooling)"})
    with urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    items = payload.get("message", {}).get("items", [])
    results: list[dict[str, Any]] = []
    for item in items:
        item_type = item.get("type", "")
        if item_type not in {"journal-article", "proceedings-article", "book-chapter"}:
            continue
        title = " ".join(item.get("title") or []).strip()
        if not title:
            continue
        authors = []
        for author in item.get("author", []):
            given = author.get("given", "").strip()
            family = author.get("family", "").strip()
            full = " ".join(part for part in [given, family] if part)
            if full:
                authors.append(full)
        date_parts = (
            item.get("issued", {}).get("date-parts")
            or item.get("published-print", {}).get("date-parts")
            or item.get("published-online", {}).get("date-parts")
            or [[0]]
        )
        year = int(date_parts[0][0]) if date_parts and date_parts[0] else 0
        venue = " ".join(item.get("container-title") or []).strip() or item.get("publisher", "")
        abstract = _strip_html_tags(item.get("abstract", ""))[:600]
        text_for_theme = " ".join([title, abstract, venue])
        results.append(
            {
                "title": title,
                "authors": authors,
                "year": year,
                "venue": venue,
                "doi": item.get("DOI", ""),
                "url": item.get("URL", ""),
                "type": item_type,
                "themes": sorted(_extract_theme_keywords(text_for_theme)),
                "abstract_excerpt": abstract,
                "source_query": query,
                "source": "crossref",
            }
        )
    return results


def _dedupe_references(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for entry in entries:
        key = (entry.get("doi", "").lower(), entry.get("title", "").lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def _render_literature_md(pack: dict[str, Any]) -> str:
    lines = [
        "# Literature Pack",
        "",
        f"- generated_at: {pack['metadata']['generated_at']}",
        f"- target_count: {pack['metadata']['target_count']}",
        f"- actual_count: {len(pack['entries'])}",
    ]
    sidecar = pack["metadata"].get("research_sidecar", {})
    if sidecar:
        lines.extend(
            [
                "## Research Sidecar",
                "",
                f"- status: {sidecar.get('status', 'unknown')}",
                f"- papers_found: {sidecar.get('papers_found', 0)}",
                f"- papers_downloaded: {sidecar.get('papers_downloaded', 0)}",
                f"- analysis_count: {sidecar.get('analysis_count', 0)}",
                f"- research_dir: {sidecar.get('research_dir', '')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Queries",
            "",
        ]
    )
    lines.extend([f"- {query}" for query in pack["queries"]] or ["- none"])
    lines.extend(["", "## Theme Summary", ""])
    for theme, count in pack.get("theme_counts", {}).items():
        lines.append(f"- {theme}: {count}")
    lines.extend(["", "| id | year | title | venue | doi | themes |", "|---|---:|---|---|---|---|"])
    for entry in pack["entries"]:
        doi = entry["doi"] or entry["url"]
        lines.append(f"| [{entry['id']}] | {entry['year']} | {entry['title']} | {entry['venue']} | {doi} | {', '.join(entry['themes'])} |")
    return "\n".join(lines) + "\n"


def _render_reference_text(entry: dict[str, Any]) -> str:
    authors = ", ".join(entry.get("authors") or ["Unknown"])
    type_code = REFERENCE_TYPE_MAP.get(entry.get("type", ""), "J")
    venue = entry.get("venue") or "Unknown venue"
    suffix = f" DOI: {entry['doi']}." if entry.get("doi") else (f" URL: {entry['url']}." if entry.get("url") else "")
    return f"[{entry['id']}] {authors}. {entry['title']}[{type_code}]. {venue}, {entry['year']}.{suffix}"


def _build_reference_registry(entries: list[dict[str, Any]]) -> dict[str, Any]:
    registry_entries = []
    for idx, entry in enumerate(entries, start=1):
        registry_entry = dict(entry)
        registry_entry["id"] = idx
        registry_entry["used_by"] = []
        registry_entries.append(registry_entry)
    return {
        "style": "numeric",
        "generated_at": _now_iso(),
        "entries": registry_entries,
    }


def run_literature(
    config_path: Path,
    min_refs: int = 15,
    max_refs: int = 18,
    enable_research_sidecar: bool = True,
) -> dict[str, Path]:
    ctx = load_workspace_context(config_path)
    workspace_root = ctx["workspace_root"]
    manifest = ctx["manifest"]
    output_paths = writing_output_paths(ctx["config"], workspace_root)
    material_pack = read_json(material_output_paths(ctx["config"], workspace_root)["material_pack_json"])

    queries = _generate_queries(manifest, material_pack)
    collected: list[dict[str, Any]] = []
    errors: list[str] = []
    rows_per_query = max(1, min(max_refs, 8))
    for query in queries:
        try:
            collected.extend(_crossref_search(query, rows=rows_per_query))
        except Exception as exc:
            errors.append(f"{query}: {exc}")
        if len(_dedupe_references(collected)) >= max_refs:
            break

    entries = _dedupe_references(collected)
    if enable_research_sidecar:
        research_summary = run_research_sidecar(
            queries=queries,
            research_dir=output_paths["research_dir"],
            max_papers=min(max_refs, 10),
            reader_script_rel="workflow/skills/paper-reader/scripts/read_paper.py",
            standards_rel="workflow/skills/paper-research-agent/references/analysis_standards.md",
        )
        research_index = build_research_index(
            summary=research_summary,
            research_dir=output_paths["research_dir"],
            research_index_json=output_paths["research_index_json"],
            research_index_md=output_paths["research_index_md"],
        )
        if research_index.get("status") == "failed" and entries:
            research_index = build_registry_fallback_index(
                registry_entries=sorted(entries, key=lambda item: (item.get("year", 0), item.get("title", "")), reverse=True),
                research_dir=output_paths["research_dir"],
                research_index_json=output_paths["research_index_json"],
                research_index_md=output_paths["research_index_md"],
                base_errors=research_index.get("errors", []),
            )
    else:
        research_index = build_registry_fallback_index(
            registry_entries=sorted(entries, key=lambda item: (item.get("year", 0), item.get("title", "")), reverse=True),
            research_dir=output_paths["research_dir"],
            research_index_json=output_paths["research_index_json"],
            research_index_md=output_paths["research_index_md"],
            base_errors=["research sidecar skipped by caller"],
        )
    if len(entries) < min_refs:
        entries.extend(research_papers_to_registry_entries(research_index.get("papers", []), _extract_theme_keywords))
        entries = _dedupe_references(entries)
    entries = sorted(entries, key=lambda item: (item.get("year", 0), item.get("doi") == "", item.get("title", "")), reverse=True)[:max_refs]

    theme_counts: dict[str, int] = {}
    for entry in entries:
        for theme in entry.get("themes", []):
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

    pack = {
        "metadata": {
            "generated_at": _now_iso(),
            "target_count": max(min_refs, 15),
            "actual_count": len(entries),
            "chain_platform": manifest["chain_platform"],
            "title": manifest["title"],
            "errors": errors,
            "research_sidecar": {
                "status": research_index.get("status", "failed"),
                "research_dir": _relative_to_workspace(output_paths["research_dir"], workspace_root),
                "queries_used": research_index.get("queries_used", []),
                "papers_found": research_index.get("papers_found", 0),
                "papers_downloaded": research_index.get("papers_downloaded", 0),
                "analysis_count": research_index.get("analysis_count", 0),
                "task_count": research_index.get("task_count", 0),
                "errors": research_index.get("errors", []),
            },
        },
        "queries": queries,
        "theme_counts": theme_counts,
        "entries": [],
    }

    registry = _build_reference_registry(entries)
    for entry in registry["entries"]:
        pack["entries"].append(
            {
                "id": entry["id"],
                "title": entry["title"],
                "authors": entry["authors"],
                "year": entry["year"],
                "venue": entry["venue"],
                "doi": entry["doi"],
                "url": entry["url"],
                "type": entry["type"],
                "themes": entry["themes"],
                "abstract_excerpt": entry["abstract_excerpt"],
                "source_query": entry["source_query"],
                "source": entry["source"],
            }
        )

    write_json(output_paths["literature_pack_json"], pack)
    write_text(output_paths["literature_pack_md"], _render_literature_md(pack))
    write_json(output_paths["reference_registry_json"], registry)
    return {
        "literature_pack_json": output_paths["literature_pack_json"],
        "literature_pack_md": output_paths["literature_pack_md"],
        "reference_registry_json": output_paths["reference_registry_json"],
        "research_index_json": output_paths["research_index_json"],
        "research_index_md": output_paths["research_index_md"],
    }

def _relative_to_workspace(path: Path, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except Exception:
        return str(path)


def _packet_slug(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "-", text).strip("-").lower() or "asset"


def _flatten_material_assets(material_pack: dict[str, Any], section_names: list[str]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    seen: set[str] = set()
    for section_name in section_names:
        section = material_pack.get("sections", {}).get(section_name, {})
        for bucket in ASSET_BUCKET_ORDER:
            for asset in section.get("assets", {}).get(bucket, []):
                asset_id = asset.get("id") or f"{bucket}-{_packet_slug(asset.get('title', 'asset'))}"
                if asset_id in seen:
                    continue
                seen.add(asset_id)
                assets.append(dict(asset))
    return assets


def _asset_matches_requirement(asset: dict[str, Any], requirement: dict[str, Any], chapter: str) -> bool:
    if asset.get("asset_type") != requirement.get("asset_type"):
        return False
    if requirement.get("kind") and asset.get("kind") != requirement["kind"]:
        return False
    chapters = asset.get("chapter_candidates") or []
    if chapters and chapter not in chapters:
        return False
    return True


def _section_number_prefix(section: str) -> str:
    match = re.match(r"^(\d+(?:\.\d+)*)", str(section or "").strip())
    return match.group(1) if match else ""


def _asset_section_match_score(asset: dict[str, Any], requirement: dict[str, Any]) -> int:
    target_section = str(requirement.get("section", "")).strip()
    if not target_section:
        return 0
    candidates = [str(item).strip() for item in asset.get("section_candidates") or [] if str(item).strip()]
    if target_section in candidates:
        return 3
    target_prefix = _section_number_prefix(target_section)
    if target_prefix:
        for candidate in candidates:
            candidate_prefix = _section_number_prefix(candidate)
            if candidate_prefix and (candidate_prefix.startswith(target_prefix) or target_prefix.startswith(candidate_prefix)):
                return 2
    return 0


def _asset_selection_sort_key(asset: dict[str, Any], requirement: dict[str, Any] | None = None) -> tuple[int, int, int, str]:
    section_score = _asset_section_match_score(asset, requirement or {})
    auto_select_score = 1 if asset.get("auto_select", True) else 0
    selection_score = int(asset.get("selection_score", 0) or 0)
    title = str(asset.get("title", "") or "")
    return (-section_score, -auto_select_score, -selection_score, title)


def _pick_ranked_asset(
    matches: list[dict[str, Any]],
    requirement: dict[str, Any],
    selected_ids: set[str],
    used_groups: set[str] | None = None,
) -> dict[str, Any] | None:
    remaining_matches = [
        asset
        for asset in sorted(matches, key=lambda item: _asset_selection_sort_key(item, requirement))
        if not asset.get("id") or asset.get("id") not in selected_ids
    ]
    if not remaining_matches:
        return None
    if used_groups is None:
        return remaining_matches[0]
    for asset in remaining_matches:
        group = str(asset.get("selection_group", "") or "")
        if group and group in used_groups:
            continue
        return asset
    return remaining_matches[0]


def _placeholder_asset(chapter: str, requirement: dict[str, Any], index: int = 0) -> dict[str, Any]:
    title = requirement.get("title", "待补资产")
    asset_type = requirement.get("asset_type", "figures")
    placeholder_text = ""
    if asset_type == "figures":
        placeholder_text = f"（配图占位，终稿插入{title}）"
    elif asset_type == "tables":
        placeholder_text = f"{title}\n\n| 待补 | 说明 |\n|---|---|\n| 待补 | 根据资产抽取结果补齐 |"
    elif asset_type == "appendix_items":
        placeholder_text = title
    return {
        "id": f"placeholder-{_packet_slug(chapter)}-{_packet_slug(title)}-{index + 1}",
        "asset_type": asset_type,
        "kind": requirement.get("kind", ""),
        "title": title,
        "source_path": "",
        "chapter_candidates": [chapter],
        "section_candidates": [requirement.get("section", "")] if requirement.get("section") else [],
        "evidence_level": "placeholder",
        "note": requirement.get("note", ""),
        "table_headers": [],
        "table_rows": [],
        "appendix_lines": [],
        "placeholder_text": placeholder_text,
    }


def _needs_literal_output_marker(requirement: dict[str, Any]) -> bool:
    title = str(requirement.get("title", "")).strip()
    if not title:
        return False
    if requirement.get("asset_type") == "figures" and requirement.get("kind") == "test-screenshot":
        return False
    if int(requirement.get("min_count", 1) or 1) > 1 and any(token in title for token in ["至少插入", "至少引用", "at least"]):
        return False
    return True


def _resolve_chapter_assets(
    material_pack: dict[str, Any],
    project_profile: dict[str, Any],
    chapter: str,
) -> dict[str, Any]:
    section_names = chapter_material_sections(project_profile, chapter)
    available_assets = _flatten_material_assets(material_pack, section_names)
    required = chapter_required_assets(project_profile, chapter)
    preferred = chapter_preferred_assets(project_profile, chapter)

    selected_assets: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    asset_to_section_map: list[dict[str, Any]] = []
    required_output_markers: list[str] = []
    table_specs: list[dict[str, Any]] = []
    appendix_titles: list[str] = []
    issues: list[str] = []

    def add_asset(asset: dict[str, Any], requirement: dict[str, Any], required_flag: bool) -> None:
        selected_asset = dict(asset)
        workspace_image_path = chapter5_test_screenshot_workspace_relpath(selected_asset)
        if workspace_image_path:
            selected_asset["workspace_image_path"] = workspace_image_path
        asset_id = selected_asset.get("id", "")
        if asset_id and asset_id not in selected_ids:
            selected_assets.append(selected_asset)
            selected_ids.add(asset_id)
        asset_to_section_map.append(
            {
                "asset_id": selected_asset.get("id", ""),
                "asset_type": selected_asset.get("asset_type", ""),
                "title": selected_asset.get("title", ""),
                "source_path": selected_asset.get("source_path", ""),
                "workspace_image_path": selected_asset.get("workspace_image_path", ""),
                "selection_group": selected_asset.get("selection_group", ""),
                "target_section": requirement.get("section", ""),
                "required": required_flag,
                "evidence_level": selected_asset.get("evidence_level", "unknown"),
            }
        )
        if selected_asset.get("asset_type") == "tables":
            table_specs.append(
                {
                    "title": selected_asset.get("title", ""),
                    "kind": selected_asset.get("kind", ""),
                    "headers": selected_asset.get("table_headers", []),
                    "rows": selected_asset.get("table_rows", []),
                    "source_path": selected_asset.get("source_path", ""),
                    "placeholder_text": selected_asset.get("placeholder_text", ""),
                }
            )
        if selected_asset.get("asset_type") == "appendix_items":
            appendix_titles.append(selected_asset.get("title", ""))

    for requirement in required:
        matches = [asset for asset in available_assets if _asset_matches_requirement(asset, requirement, chapter)]
        count = max(1, int(requirement.get("min_count", 1)))
        if _needs_literal_output_marker(requirement):
            required_output_markers.append(requirement.get("marker", requirement.get("title", "")))
        used_groups: set[str] = set()
        for idx in range(count):
            asset = _pick_ranked_asset(matches, requirement, selected_ids, used_groups)
            if asset is not None:
                group = str(asset.get("selection_group", "") or "")
                if group:
                    used_groups.add(group)
            else:
                asset = _placeholder_asset(chapter, requirement, idx)
                issues.append(f"missing required asset: {requirement.get('title', '')}")
            add_asset(asset, requirement, True)

    for requirement in preferred:
        matches = [asset for asset in available_assets if _asset_matches_requirement(asset, requirement, chapter)]
        count = max(1, int(requirement.get("min_count", 1)))
        used_groups: set[str] = set()
        for _ in range(count):
            match = _pick_ranked_asset(matches, requirement, selected_ids, used_groups)
            if match is None:
                break
            group = str(match.get("selection_group", "") or "")
            if group:
                used_groups.add(group)
            add_asset(match, requirement, False)

    auto_add_enabled = chapter not in {"05-系统实现.md", "06-系统测试.md"}
    for asset in sorted(available_assets, key=_asset_selection_sort_key):
        chapters = asset.get("chapter_candidates") or []
        if chapters and chapter not in chapters:
            continue
        asset_id = asset.get("id", "")
        if asset_id in selected_ids:
            continue
        if not auto_add_enabled:
            continue
        auto_asset_types = {"figures", "code_artifacts", "test_artifacts"}
        if chapter == "05-系统实现.md":
            auto_asset_types = {"figures", "test_artifacts"}
        if asset.get("asset_type") in auto_asset_types:
            selected_assets.append(asset)
            selected_ids.add(asset_id)

    asset_counts = {bucket: 0 for bucket in ASSET_BUCKET_ORDER}
    for asset in selected_assets:
        bucket = asset.get("asset_type")
        if bucket in asset_counts:
            asset_counts[bucket] += 1

    appendix_contract = {
        "required_titles": chapter_required_appendix_items(project_profile, chapter),
        "selected_titles": appendix_titles,
        "placeholder_policy": chapter_placeholder_policy(project_profile, chapter),
    }
    return {
        "chapter_assets": selected_assets,
        "asset_to_section_map": asset_to_section_map,
        "required_output_markers": [marker for marker in required_output_markers if marker],
        "table_specs": table_specs,
        "appendix_contract": appendix_contract,
        "validation": {
            "status": "ok" if not issues else "warn",
            "issues": issues,
            "asset_counts": asset_counts,
        },
    }


def _load_code_evidence_pack(config: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    material_paths = material_output_paths(config, workspace_root)
    code_pack_path = material_paths["code_evidence_pack_json"]
    if not code_pack_path.exists():
        return {"metadata": {}, "modules": [], "entries": []}
    return read_json(code_pack_path)


def _code_entry_payload(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry.get("id", ""),
        "module_key": entry.get("module_key", ""),
        "module_label": entry.get("module_label", ""),
        "side": entry.get("side", ""),
        "language": entry.get("language", ""),
        "source_path": entry.get("source_path", ""),
        "symbol": entry.get("symbol", ""),
        "line_start": entry.get("line_start", 0),
        "line_end": entry.get("line_end", 0),
        "snippet_path": entry.get("snippet_path", ""),
        "screenshot_path": entry.get("screenshot_path", ""),
        "caption": entry.get("caption", ""),
        "selected_reason": entry.get("selected_reason", ""),
    }


def _entry_match_text(entry: dict[str, Any]) -> str:
    return " ".join(
        str(entry.get(key, ""))
        for key in ["id", "module_label", "side", "source_path", "symbol", "caption"]
    ).lower()


def _select_preferred_entry_count(entries: list[dict[str, Any]], min_required: int, preferred: int) -> int:
    if not entries:
        return 0
    return min(len(entries), max(min_required, preferred))


def _select_entries_for_subfunction_coverage(
    entries: list[dict[str, Any]],
    subfunctions: list[dict[str, Any]],
    min_required: int,
    preferred: int,
) -> list[dict[str, Any]]:
    if not entries:
        return []

    target_count = _select_preferred_entry_count(entries, min_required, preferred)
    selected: list[dict[str, Any]] = []
    used_ids: set[str] = set()

    def _best_match(entry: dict[str, Any]) -> tuple[int | None, int]:
        if not subfunctions:
            return None, 0
        text = _entry_match_text(entry)
        best_index = 0
        best_score = -1
        for index, subfunction in enumerate(subfunctions):
            score = sum(1 for keyword in subfunction.get("keywords", []) if keyword and keyword in text)
            if score > best_score:
                best_index = index
                best_score = score
        return best_index, max(best_score, 0)

    for subfunction in subfunctions:
        keywords = [keyword for keyword in subfunction.get("keywords", []) if keyword]
        if not keywords:
            continue
        ranked: list[tuple[int, int, dict[str, Any]]] = []
        for original_index, entry in enumerate(entries):
            entry_id = entry.get("id", "")
            if entry_id in used_ids:
                continue
            text = _entry_match_text(entry)
            score = sum(1 for keyword in keywords if keyword in text)
            if score <= 0:
                continue
            ranked.append((score, original_index, entry))
        if not ranked:
            continue
        ranked.sort(key=lambda item: (-item[0], item[1]))
        chosen = ranked[0][2]
        selected.append(chosen)
        used_ids.add(chosen.get("id", ""))
        if len(selected) >= target_count:
            return selected

    subfunction_loads = [0 for _ in subfunctions]
    for entry in selected:
        best_index, best_score = _best_match(entry)
        if best_index is not None and best_score > 0:
            subfunction_loads[best_index] += 1

    ranked_remaining: list[tuple[int, int, int, dict[str, Any], int | None]] = []
    for original_index, entry in enumerate(entries):
        entry_id = entry.get("id", "")
        if entry_id in used_ids:
            continue
        best_index, best_score = _best_match(entry)
        load = subfunction_loads[best_index] if best_index is not None and best_score > 0 else 10**6
        ranked_remaining.append((best_score, load, original_index, entry, best_index))

    ranked_remaining.sort(key=lambda item: (-item[0], item[1], item[2]))
    for best_score, _, _, entry, best_index in ranked_remaining:
        entry_id = entry.get("id", "")
        if entry_id in used_ids:
            continue
        selected.append(entry)
        used_ids.add(entry_id)
        if best_index is not None and best_score > 0:
            subfunction_loads[best_index] += 1
        if len(selected) >= target_count:
            break
    return selected


def _module_subfunction_contracts(module: dict[str, Any], module_index: int) -> list[dict[str, Any]]:
    prefix = f"5.{module_index}"
    subfunctions = module.get("subfunctions", [])
    contracts: list[dict[str, Any]] = []
    for sub_index, subfunction in enumerate(subfunctions, start=1):
        if isinstance(subfunction, dict):
            label = str(subfunction.get("label", f"子功能{sub_index}")).strip()
            keywords = [str(keyword).lower() for keyword in subfunction.get("keywords", [])]
        else:
            label = str(subfunction).strip()
            keywords = []
        contracts.append(
            {
                "label": label,
                "keywords": keywords,
                "section": f"{prefix}.{sub_index} {label}",
                "entries": [],
                "backend_entries": [],
                "frontend_entries": [],
            }
        )
    return contracts


def _pick_best_subfunction_index(entry: dict[str, Any], subfunctions: list[dict[str, Any]]) -> int:
    text = _entry_match_text(entry)
    best_index = 0
    best_score = -1
    best_load = 10**6
    for index, subfunction in enumerate(subfunctions):
        score = sum(1 for keyword in subfunction.get("keywords", []) if keyword and keyword in text)
        load = len(subfunction.get("entries", []))
        if score > best_score or (score == best_score and load < best_load):
            best_index = index
            best_score = score
            best_load = load
    return best_index


def _remove_subfunction_entry(subfunction: dict[str, Any], entry_id: str) -> dict[str, Any] | None:
    removed: dict[str, Any] | None = None
    kept_entries: list[dict[str, Any]] = []
    for entry in subfunction.get("entries", []):
        if removed is None and entry.get("id") == entry_id:
            removed = entry
            continue
        kept_entries.append(entry)
    subfunction["entries"] = kept_entries
    if removed is None:
        return None
    key = "backend_entries" if removed.get("side") == "backend" else "frontend_entries"
    subfunction[key] = [entry for entry in subfunction.get(key, []) if entry.get("id") != entry_id]
    return removed


def _rebalance_subfunction_contracts(subfunctions: list[dict[str, Any]]) -> None:
    empty_subfunctions = [subfunction for subfunction in subfunctions if not subfunction.get("entries")]
    for target in empty_subfunctions:
        donor = max(subfunctions, key=lambda item: len(item.get("entries", [])), default=None)
        if donor is None or donor is target or len(donor.get("entries", [])) <= 1:
            break
        moved = _remove_subfunction_entry(donor, donor["entries"][-1].get("id", ""))
        if not moved:
            continue
        target["entries"].append(moved)
        key = "backend_entries" if moved.get("side") == "backend" else "frontend_entries"
        target[key].append(moved)


def _resolve_chapter5_code_contract(project_profile: dict[str, Any], code_pack: dict[str, Any]) -> dict[str, Any]:
    policy = chapter_module_implementation_policy(project_profile, "05-系统实现.md")
    if not policy:
        return {
            "required_code_evidence": [],
            "code_evidence_to_section_map": [],
            "required_code_screenshot_count": 0,
            "module_implementation_contract": [],
            "validation": {"status": "ok", "issues": []},
        }

    modules = project_profile.get("core_modules", [])
    entries = code_pack.get("entries", [])
    required_code_evidence: list[dict[str, Any]] = []
    code_evidence_to_section_map: list[dict[str, Any]] = []
    module_contracts: list[dict[str, Any]] = []
    issues: list[str] = []
    required_code_screenshot_count = 0

    min_backend = int(policy.get("min_backend_entries_per_module", 1) or 1)
    min_frontend = int(policy.get("min_frontend_entries_per_module", 1) or 1)
    preferred_backend = int(policy.get("preferred_backend_entries_per_module", min_backend) or min_backend)
    preferred_frontend = int(policy.get("preferred_frontend_entries_per_module", min_frontend) or min_frontend)
    require_code_screenshot_section = bool(policy.get("require_code_screenshot_section", False))
    min_screenshots = int(policy.get("min_code_screenshots_per_module", 0) or 0)

    for idx, module in enumerate(modules, start=2):
        module_key = module.get("key", "")
        module_label = module.get("label", module_key)
        parent_section = f"5.{idx} {module_label}模块实现"
        subfunction_contracts = _module_subfunction_contracts(module, idx)
        screenshot_section = f"5.{idx}.{len(subfunction_contracts) + 1} 关键代码截图" if require_code_screenshot_section else None

        backend_entries = [entry for entry in entries if entry.get("module_key") == module_key and entry.get("side") == "backend"]
        frontend_entries = [entry for entry in entries if entry.get("module_key") == module_key and entry.get("side") == "frontend"]
        selected_backend = _select_entries_for_subfunction_coverage(
            backend_entries,
            subfunction_contracts,
            min_backend,
            preferred_backend,
        )
        selected_frontend = _select_entries_for_subfunction_coverage(
            frontend_entries,
            subfunction_contracts,
            min_frontend,
            preferred_frontend,
        )
        screenshot_entries: list[dict[str, Any]] = []
        if require_code_screenshot_section and min_screenshots > 0:
            screenshot_entries = selected_backend[:1] + selected_frontend[:1]
            if len(screenshot_entries) < min_screenshots:
                extra_pool = [entry for entry in backend_entries + frontend_entries if entry not in screenshot_entries]
                screenshot_entries.extend(extra_pool[: max(0, min_screenshots - len(screenshot_entries))])
            screenshot_entries = screenshot_entries[:min_screenshots]

        if len(selected_backend) < min_backend:
            issues.append(f"chapter 5 module {module_label} missing backend code evidence")
        if len(selected_frontend) < min_frontend:
            issues.append(f"chapter 5 module {module_label} missing frontend code evidence")
        if require_code_screenshot_section and len(screenshot_entries) < min_screenshots:
            issues.append(f"chapter 5 module {module_label} missing code screenshots")

        required_code_evidence.extend(
            [
                {
                    "module_key": module_key,
                    "module_label": module_label,
                    "side": "backend",
                    "min_count": min_backend,
                    "section": parent_section,
                },
                {
                    "module_key": module_key,
                    "module_label": module_label,
                    "side": "frontend",
                    "min_count": min_frontend,
                    "section": parent_section,
                },
            ]
        )
        required_code_screenshot_count += min_screenshots if require_code_screenshot_section else 0

        for entry in selected_backend + selected_frontend:
            if subfunction_contracts:
                target_subfunction = subfunction_contracts[_pick_best_subfunction_index(entry, subfunction_contracts)]
                target_subfunction["entries"].append(_code_entry_payload(entry))
                if entry.get("side") == "backend":
                    target_subfunction["backend_entries"].append(_code_entry_payload(entry))
                else:
                    target_subfunction["frontend_entries"].append(_code_entry_payload(entry))
        if subfunction_contracts:
            _rebalance_subfunction_contracts(subfunction_contracts)

        for subfunction in subfunction_contracts:
            for entry in subfunction.get("entries", []):
                code_evidence_to_section_map.append(
                    {
                        "entry_id": entry.get("id", ""),
                        "module_key": module_key,
                        "module_label": module_label,
                        "target_section": subfunction["section"],
                        "render_as": "implementation-source",
                        "required": True,
                        "side": entry.get("side", ""),
                        "source_path": entry.get("source_path", ""),
                        "screenshot_path": entry.get("screenshot_path", ""),
                        "snippet_path": entry.get("snippet_path", ""),
                        "symbol": entry.get("symbol", ""),
                    }
                )

        if require_code_screenshot_section and screenshot_section:
            for entry in screenshot_entries:
                code_evidence_to_section_map.append(
                    {
                        "entry_id": entry.get("id", ""),
                        "module_key": module_key,
                        "module_label": module_label,
                        "target_section": screenshot_section,
                        "render_as": "code-screenshot",
                        "required": True,
                        "side": entry.get("side", ""),
                        "source_path": entry.get("source_path", ""),
                        "screenshot_path": entry.get("screenshot_path", ""),
                        "snippet_path": entry.get("snippet_path", ""),
                        "symbol": entry.get("symbol", ""),
                    }
                )

        module_contracts.append(
            {
                "module_key": module_key,
                "module_label": module_label,
                "parent_section": parent_section,
                "subfunctions": subfunction_contracts,
                "code_screenshot_section": screenshot_section,
                "backend_entries": [_code_entry_payload(entry) for entry in selected_backend],
                "frontend_entries": [_code_entry_payload(entry) for entry in selected_frontend],
                "code_screenshots": [_code_entry_payload(entry) for entry in screenshot_entries],
            }
        )

    return {
        "required_code_evidence": required_code_evidence,
        "code_evidence_to_section_map": code_evidence_to_section_map,
        "required_code_screenshot_count": required_code_screenshot_count,
        "module_implementation_contract": module_contracts,
        "validation": {
            "status": "ok" if not issues else "warn",
            "issues": issues,
        },
    }


def _research_contract(chapter: str) -> dict[str, bool]:
    return {
        "must_use_research_sidecar": chapter == "01-绪论.md",
        "research_recommended": chapter in {"01-绪论.md", "02-系统开发工具及技术介绍.md", "03-需求分析.md"},
    }


def _chapter_execution_steps(chapter: str, queue_entry: dict[str, Any], skill_rel_path: str, target_path: str) -> list[str]:
    if queue_entry["mode"] == "manual":
        return [
            f"人工补写 `{target_path}`。",
            f"如需润色，可参考 `{skill_rel_path}` 的规则手工执行。",
            f"人工复核通过后，执行 `finalize-chapter --chapter {chapter} --status reviewed`。",
        ]
    if queue_entry["mode"] == "registry":
        return [
            "不要手工编辑本章。",
            "本章由 reference registry 自动汇总生成。",
            "通过其它章节 finalize 后刷新 REFERENCES.md。",
        ]
    return [
        f"先核对 `docs/writing/thesis_outline.md`，确认当前章节标题、小节层级和目录未偏离既定大纲。",
        f"阅读 `{skill_rel_path}`、chapter packet、material_pack、literature_pack、reference_registry 和 research sidecar。",
        "若当前章节包含代码实现合同，先从工作区中的 code_evidence_pack 与 code_snippets 中取材，不要重新回源仓库摘录。",
        f"按当前章节标题、小节结构和 chapter_assets 合同，将 raw draft 写入 `{target_path}`。",
        "确保图题、表题、附录条目和测试证据不会被改写成纯叙述文本；若缺少真实资产，必须保留显式占位。",
        f"raw draft 完成后，执行 `finalize-chapter --chapter {chapter} --status drafted`。",
        f"按照 `{skill_rel_path}` 再做一次学术化润色，覆盖写回 `{target_path}`。",
        f"润色完成后，执行 `finalize-chapter --chapter {chapter} --status polished`。",
        f"人工确认通过后，执行 `finalize-chapter --chapter {chapter} --status reviewed`。",
    ]


def _output_contract(
    chapter: str,
    title: str,
    target_path: str,
    queue_entry: dict[str, Any],
    project_profile: dict[str, Any],
) -> dict[str, Any]:
    research_contract = _research_contract(chapter)
    return {
        "target_path": target_path,
        "title": title,
        "structure_source": chapter_structure_source(project_profile, chapter),
        "required_subsections": chapter_required_subsections(project_profile, chapter),
        "must_preserve_structure": chapter not in {"00-摘要.md", "00-Abstract.md", "08-致谢.md", "REFERENCES.md"},
        "must_use_reference_registry": queue_entry["polish_required"] or chapter == "REFERENCES.md",
        "must_use_research_sidecar": research_contract["must_use_research_sidecar"],
        "research_recommended": research_contract["research_recommended"],
        "required_assets": chapter_required_assets(project_profile, chapter),
        "required_table_types": chapter_required_table_types(project_profile, chapter),
        "required_appendix_items": chapter_required_appendix_items(project_profile, chapter),
        "placeholder_policy": chapter_placeholder_policy(project_profile, chapter),
        "module_implementation_policy": chapter_module_implementation_policy(project_profile, chapter),
        "manual_allowed_markers": ["待补"] if queue_entry["mode"] == "auto" else [],
    }


def _finalize_contract(queue_entry: dict[str, Any]) -> dict[str, str]:
    if queue_entry["mode"] == "manual":
        return {"after_manual_review": "reviewed"}
    if queue_entry["mode"] == "registry":
        return {"managed_by": "reference_registry.json"}
    return {
        "after_raw_draft": "drafted",
        "after_polish": "polished",
        "after_human_review": "reviewed",
    }


def _validate_prepare_mode(queue_entry: dict[str, Any], chapter: str) -> None:
    if queue_entry["mode"] == "registry":
        raise ValueError(f"{chapter} is registry-managed and should not be prepared as a normal chapter")


def _validate_transition(queue_entry: dict[str, Any], new_status: str, chapter: str) -> None:
    mode = queue_entry["mode"]
    current_status = queue_entry["status"]

    if mode == "registry":
        raise ValueError(f"{chapter} is registry-managed and cannot be finalized manually")

    if new_status == current_status:
        return

    if mode == "manual":
        if new_status not in MANUAL_TRANSITIONS.get(current_status, set()):
            raise ValueError(f"invalid transition for manual chapter {chapter}: {current_status} -> {new_status}")
        return

    if new_status not in AUTO_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"invalid transition for chapter {chapter}: {current_status} -> {new_status}")


def _initial_queue_entry(
    filename: str,
    title: str,
    structure_source: str,
    workspace_root: Path,
    writing_paths: dict[str, Path],
    config: dict[str, Any],
) -> dict[str, Any]:
    stem = Path(filename).stem
    mode = "auto"
    status = "pending"
    if filename == "08-致谢.md":
        mode = "manual"
        status = "manual_pending"
    elif filename == "REFERENCES.md":
        mode = "registry"
        status = "managed"
    return {
        "chapter": filename,
        "title": title,
        "order": WRITING_ORDER.index(filename) + 1,
        "mode": mode,
        "status": status,
        "structure_source": structure_source,
        "literature_required": filename == "01-绪论.md",
        "polish_required": filename not in {"08-致谢.md", "REFERENCES.md"},
        "target_path": _relative_to_workspace(workspace_root / config.get("build", {}).get("input_dir", "polished_v3") / filename, workspace_root),
        "packet_json": _relative_to_workspace(writing_paths["chapter_packets_dir"] / f"{stem}.json", workspace_root),
        "packet_md": _relative_to_workspace(writing_paths["chapter_packets_dir"] / f"{stem}.md", workspace_root),
        "brief_md": _relative_to_workspace(writing_paths["chapter_briefs_dir"] / f"{stem}.md", workspace_root),
        "review_md": _relative_to_workspace(writing_paths["review_dir"] / f"{stem}.md", workspace_root),
    }


def _merge_queue_entry(existing: dict[str, Any] | None, fresh: dict[str, Any]) -> dict[str, Any]:
    if not existing:
        return fresh

    merged = dict(fresh)
    allowed_statuses = MODE_STATUS_MAP.get(fresh["mode"], {fresh["status"]})
    existing_status = existing.get("status")
    if existing_status in allowed_statuses:
        merged["status"] = existing_status

    for field in [
        "prepared_at",
        "finalized_at",
        "citation_count",
        "citation_order_ok",
        "citation_order_warning_count",
        "citation_reuse_warning_count",
        "citation_sentence_warning_count",
        "placeholder_count",
        "style_issue_count",
        "style_preferred_subject_warning_count",
        "style_source_narration_warning_count",
        "style_repository_voice_warning_count",
        "style_weak_leadin_warning_count",
        "style_opening_rhythm_warning_count",
        "style_summary_recap_warning_count",
        "packet_generated_at",
        "packet_kind",
        "brief_generated_at",
        "packet_outline_generated_at",
        "packet_outline_signature",
        "packet_outline_status",
    ]:
        if field in existing:
            merged[field] = existing[field]
    return merged


def _write_packet_stub_if_missing(packet_path: Path, packet_stub: dict[str, Any]) -> None:
    if packet_path.exists():
        return
    write_json(packet_path, packet_stub)


def _write_review_stub_if_missing(review_path: Path, review_content: str) -> None:
    if review_path.exists():
        return
    write_text(review_path, review_content)


def _write_brief_stub_if_missing(brief_path: Path, chapter: str, title: str, target_path: str) -> None:
    if brief_path.exists():
        return
    write_text(
        brief_path,
        "\n".join(
            [
                f"# Writer Brief Stub: {chapter}",
                "",
                f"- title: {title}",
                f"- target_path: `{target_path}`",
                "- note: Run `prepare-chapter` to generate the full writer brief.",
                "",
            ]
        ),
    )


def run_prepare_writing(config_path: Path) -> dict[str, Path]:
    ctx = load_workspace_context(config_path)
    workspace_root = ctx["workspace_root"]
    config = ctx["config"]
    manifest = ctx["manifest"]
    writing_paths = writing_output_paths(config, workspace_root)
    writing_paths["chapter_packets_dir"].mkdir(parents=True, exist_ok=True)
    writing_paths["chapter_briefs_dir"].mkdir(parents=True, exist_ok=True)
    writing_paths["review_dir"].mkdir(parents=True, exist_ok=True)
    material_pack = read_json(material_output_paths(config, workspace_root)["material_pack_json"])
    project_profile = _load_or_build_project_profile(manifest, material_pack, writing_paths)
    _write_thesis_outline(workspace_root, config, manifest, project_profile, writing_paths)
    thesis_outline = read_json(writing_paths["thesis_outline_json"])
    titles = _chapter_title_map(project_profile)
    existing_queue = read_json(writing_paths["chapter_queue_json"]) if writing_paths["chapter_queue_json"].exists() else {}
    existing_queue_map = {
        entry.get("chapter"): entry
        for entry in existing_queue.get("chapters", [])
        if isinstance(entry, dict) and entry.get("chapter")
    }

    queue = {
        "generated_at": _now_iso(),
        "local_skill_path": _relative_to_workspace(writing_paths["local_skill_path"], workspace_root),
        "resume_skill_path": _relative_to_workspace(writing_paths["resume_skill_path"], workspace_root),
        "orchestrator_skill_path": _relative_to_workspace(writing_paths["orchestrator_skill_path"], workspace_root),
        "research_skill_path": _relative_to_workspace(writing_paths["research_skill_path"], workspace_root),
        "paper_reader_skill_path": _relative_to_workspace(writing_paths["paper_reader_skill_path"], workspace_root),
        "project_profile_json": _relative_to_workspace(writing_paths["project_profile_json"], workspace_root),
        "project_profile_md": _relative_to_workspace(writing_paths["project_profile_md"], workspace_root),
        "thesis_outline_json": _relative_to_workspace(writing_paths["thesis_outline_json"], workspace_root),
        "thesis_outline_md": _relative_to_workspace(writing_paths["thesis_outline_md"], workspace_root),
        "research_index_json": _relative_to_workspace(writing_paths["research_index_json"], workspace_root),
        "research_index_md": _relative_to_workspace(writing_paths["research_index_md"], workspace_root),
        "research_dir": _relative_to_workspace(writing_paths["research_dir"], workspace_root),
        "citation_audit_md": _relative_to_workspace(writing_paths["citation_audit_md"], workspace_root),
        "chapter_briefs_dir": _relative_to_workspace(writing_paths["chapter_briefs_dir"], workspace_root),
        "execution_protocol": "workflow/CHAPTER_EXECUTION.md",
        "chapters": [
            _merge_queue_entry(
                existing_queue_map.get(filename),
                _initial_queue_entry(
                    filename,
                    titles[filename],
                    chapter_structure_source(project_profile, filename),
                    workspace_root,
                    writing_paths,
                    config,
                ),
            )
            for filename in WRITING_ORDER
        ],
    }

    for entry in queue["chapters"]:
        outline_snapshot = _chapter_outline_snapshot(thesis_outline, entry["chapter"], entry["title"])
        packet_stub = {
            "schema_version": CHAPTER_PACKET_SCHEMA_VERSION,
            "generated_at": queue["generated_at"],
            "packet_kind": "stub",
            "chapter": entry["chapter"],
            "title": entry["title"],
            "status": entry["status"],
            "mode": entry["mode"],
            "structure_source": entry["structure_source"],
            "outline_snapshot": outline_snapshot,
            "outline_sync": {
                "packet_generated_at": queue["generated_at"],
                "outline_generated_at": thesis_outline.get("generated_at", ""),
                "outline_signature": outline_snapshot["signature"],
                "current_outline_generated_at": thesis_outline.get("generated_at", ""),
                "current_outline_signature": outline_snapshot["signature"],
                "status": "current",
                "warning": "",
            },
            "required_assets_count": len(chapter_required_assets(project_profile, entry["chapter"])),
            "research_contract": _research_contract(entry["chapter"]),
            "execution_steps": _chapter_execution_steps(entry["chapter"], entry, queue["local_skill_path"], entry["target_path"]),
            "note": "Run prepare-chapter to build the full writing packet.",
        }
        _write_packet_stub_if_missing(workspace_root / entry["packet_json"], packet_stub)
        _write_brief_stub_if_missing(
            workspace_root / entry["brief_md"],
            entry["chapter"],
            entry["title"],
            entry["target_path"],
        )
        _write_review_stub_if_missing(
            workspace_root / entry["review_md"],
            "\n".join(
                [
                    "# Review Stub",
                    "",
                    f"- chapter: {entry['chapter']}",
                    f"- status: {entry['status']}",
                    f"- mode: {entry['mode']}",
                    f"- structure_source: {entry['structure_source']}",
                    "",
                ]
            )
            + "\n",
        )

    for entry in queue["chapters"]:
        current_snapshot = _chapter_outline_snapshot(thesis_outline, entry["chapter"], entry["title"])
        packet_sync = _resolve_packet_outline_sync(
            workspace_root / entry["packet_json"],
            current_snapshot,
            thesis_outline.get("generated_at", ""),
        )
        entry["packet_generated_at"] = packet_sync["packet_generated_at"]
        entry["packet_kind"] = packet_sync["packet_kind"]
        entry["packet_outline_generated_at"] = packet_sync["packet_outline_generated_at"]
        entry["packet_outline_signature"] = packet_sync["packet_outline_signature"]
        entry["packet_outline_status"] = packet_sync["status"]

    write_json(writing_paths["chapter_queue_json"], queue)
    return {"chapter_queue_json": writing_paths["chapter_queue_json"]}


def _select_references_for_chapter(registry: dict[str, Any], chapter: str) -> list[dict[str, Any]]:
    target_themes = CHAPTER_THEME_MAP.get(chapter, {"domain", "platform"})
    entries = []
    for entry in registry.get("entries", []):
        if target_themes.intersection(set(entry.get("themes", []))):
            entries.append(entry)
    if not entries:
        entries = registry.get("entries", [])[:10]
    entries = sorted(
        entries,
        key=lambda item: (
            len(item.get("used_by", [])) > 0,
            len(item.get("used_by", [])),
            -int(item.get("year", 0) or 0),
            int(item.get("id", 0) or 0),
        ),
    )
    return entries[:12]


def _chapter_packet(
    chapter: str,
    title: str,
    queue_entry: dict[str, Any],
    thesis_outline: dict[str, Any],
    material_pack: dict[str, Any],
    code_pack: dict[str, Any],
    registry: dict[str, Any],
    project_profile: dict[str, Any],
    skill_rel_path: str,
    target_path: str,
    project_profile_rel_path: str,
    code_evidence_pack_rel_path: str,
    code_snippets_dir_rel_path: str,
    code_screenshots_dir_rel_path: str,
    thesis_outline_json_rel_path: str,
    thesis_outline_md_rel_path: str,
    research_index_json_rel_path: str,
    research_index_md_rel_path: str,
    research_dir_rel_path: str,
    research_skill_rel_path: str,
    paper_reader_skill_rel_path: str,
) -> dict[str, Any]:
    packet_generated_at = _now_iso()
    chapter_info = chapter_definition(project_profile, chapter)
    section_names = chapter_material_sections(project_profile, chapter)
    material_sections = {name: material_pack["sections"].get(name, {}) for name in section_names}
    section_outline = flatten_section_outline(chapter_info.get("sections", []))
    asset_contract = _resolve_chapter_assets(material_pack, project_profile, chapter)
    code_contract = _resolve_chapter5_code_contract(project_profile, code_pack) if chapter == "05-系统实现.md" else {
        "required_code_evidence": [],
        "code_evidence_to_section_map": [],
        "required_code_screenshot_count": 0,
        "module_implementation_contract": [],
        "validation": {"status": "ok", "issues": []},
    }
    references = _select_references_for_chapter(registry, chapter)
    research_contract = _research_contract(chapter)
    outline_text = "\n".join(
        f"- L{item['depth']}: {item['title']} | materials: {', '.join(item['material_sections']) or 'inherit'}"
        for item in section_outline
    ) or "- no required subsections"
    asset_text = "\n".join(
        f"- [{item['asset_type']}] {item['title']} | section: {item.get('target_section', '')} | evidence: {item.get('evidence_level', '')}"
        for item in asset_contract["asset_to_section_map"]
    ) or "- no asset contract"
    code_contract_text = "\n".join(
        [
            f"- {module['module_label']} | subfunctions: "
            + (
                "; ".join(
                    f"{sub['section']} -> backend[{', '.join(entry['source_path'] for entry in sub.get('backend_entries', [])) or 'none'}], "
                    f"frontend[{', '.join(entry['source_path'] for entry in sub.get('frontend_entries', [])) or 'none'}]"
                    for sub in module.get("subfunctions", [])
                )
                or "none"
            )
            + (
                " | screenshots: " + (", ".join(entry["screenshot_path"] for entry in module["code_screenshots"]) or "missing")
                if module.get("code_screenshot_section")
                else " | inline-code-only"
            )
            for module in code_contract["module_implementation_contract"]
        ]
    ) or "- no chapter-specific code evidence"
    table_specs_text = "\n".join(
        [
            "\n".join(
                [
                    f"- {table_spec['title']} | kind={table_spec['kind']} | source={table_spec['source_path'] or '-'}",
                    f"  - headers: {', '.join(table_spec['headers']) or 'none'}",
                    *(
                        [f"  - row {idx}: {' | '.join(str(cell) for cell in row)}" for idx, row in enumerate(table_spec.get('rows', []), start=1)]
                        or [f"  - placeholder: {table_spec.get('placeholder_text', '') or 'none'}"]
                    ),
                ]
            )
            for table_spec in asset_contract["table_specs"]
        ]
    ) or "- no table specs"
    validation_issues = list(asset_contract["validation"].get("issues", [])) + list(code_contract["validation"].get("issues", []))
    validation = {
        "status": "ok" if not validation_issues else "warn",
        "issues": validation_issues,
        "asset_counts": asset_contract["validation"].get("asset_counts", {}),
        "required_code_evidence_count": len(code_contract["required_code_evidence"]),
        "required_code_screenshot_count": code_contract["required_code_screenshot_count"],
    }
    outline_snapshot = _chapter_outline_snapshot(
        thesis_outline,
        chapter,
        title,
        chapter_required_subsections(project_profile, chapter),
        [asset.get("title", "") for asset in chapter_required_assets(project_profile, chapter)],
        section_outline,
    )
    chapter_specific_prompt_lines: list[str] = []
    if chapter == "01-绪论.md":
        chapter_specific_prompt_lines.extend(
            [
                "For chapter 1, write it as an introduction chapter with the sample-like logic of domain background -> structural pain points -> blockchain suitability -> research significance.\n",
                "Section 1.1 should open from the real industry/background problem first, then explain why traditional centralized or conventional traceability mechanisms cannot adequately solve authenticity, collaboration, and accountability issues.\n",
                "Section 1.2 must read as an academic literature review, grouped by research theme and development trend, rather than a project-summary or material-summary paragraph list.\n",
                "Section 1.3 should summarize the research tasks, technical route, and expected contribution boundaries in a direct thesis voice, without drifting into detailed implementation chronology or test result narration.\n",
                "Section 1.4 should stay concise and only explain the chapter-by-chapter organization of the thesis.\n",
                "Section 1.5 should be a short research-basis summary that closes the introduction and leads naturally into the technical foundation chapter, not a repeated outline recap.\n",
                "Do not let chapter 1 drift into system implementation, deployment, interface walkthrough, or testing-expression voice.\n",
            ]
        )
    if chapter == "05-系统实现.md":
        chapter_specific_prompt_lines.extend(
            [
                "For chapter 5, open the chapter by explaining the implementation organization rationale in terms of business modules and role collaboration, not by listing backend/frontend layers separately.\n",
                "For chapter 5, each core module must use business-oriented subfunction subsections derived from the project documentation.\n",
                "Each module should begin from its business responsibility and functional role in the full system flow before introducing concrete implementation details.\n",
                "In each subfunction subsection, write two explicit thesis-style implementation paragraphs in this order: `后端实现。` first, then `前端实现。`.\n",
                "Both backend and frontend paragraphs are mandatory in every chapter 5 subfunction subsection, even when one side is shorter.\n",
                "Backend paragraphs should focus on interface orchestration, role checks, database persistence, and chain interaction when applicable; frontend paragraphs should focus on page entry, form/list interaction, state feedback, and route flow.\n",
                "Do not let chapter 5 drift into a pure development chronology such as 'first backend, then frontend, then interface联调'; present the implementation as completed business capabilities.\n",
                "Prefer direct fenced code blocks inside the matching backend/frontend paragraphs instead of a separate code screenshot subsection.\n",
                "If the workspace sets `document_format.code_blocks.render_mode=text`, the final DOCX will export fenced code blocks as selectable text instead of screenshot images.\n",
                "If code screenshots are used, treat them as optional evidence only, insert them immediately after the matching backend or frontend code block inside that same subfunction, and do not create a standalone `关键代码截图` subsection.\n",
                "Code screenshots in chapter 5 are optional inline implementation evidence only; do not assign figure numbers, `图5.x` captions, or separate caption paragraphs to them.\n",
                "When real page screenshots are available, place them in the frontend implementation part of the matching subfunction instead of using code screenshots.\n",
                "Do not invent code blocks. Only use the extracted snippet and staged page-image assets already available in the workspace.\n",
                "The chapter closing paragraph should summarize the implemented business capabilities and their support for subsequent system testing, rather than repeating the section list.\n",
            ]
        )
    if chapter == "02-系统开发工具及技术介绍.md":
        chapter_specific_prompt_lines.extend(
            [
                "For chapter 2, write it as a technical-foundation chapter rather than an implementation recap.\n",
                "Section 2.1 must keep the required technology-stack table as a real markdown table before the explanatory paragraph.\n",
                "Sections 2.2 to 2.6 should explain technical roles, selection logic, and responsibility boundaries in a direct academic style, not as project walkthrough steps.\n",
                "Do not turn chapter 2 into deployment notes, route descriptions, or code/process narration; keep the focus on why each technology is used and what role it承担 in the system.\n",
                "When table specs are provided for chapter 2, render the table title, headers, and rows directly from the packet data instead of rewriting it as prose.\n",
                "The chapter closing paragraph should read like a technical-foundation summary that leads naturally into requirements/design/implementation chapters.\n",
            ]
        )
    if chapter == "06-系统测试.md":
        chapter_specific_prompt_lines.extend(
            [
                "For chapter 6, follow the sample-like testing chapter pattern rather than a compressed summary style.\n",
                "Section 6.1 must describe the environment in the order: server hardware table, server software table, client hardware table, client software table.\n",
                "Section 6.2 must keep one dedicated function-test subsection per core module, and each subsection must contain its required table as an actual markdown table before the explanatory paragraph.\n",
                "Section 6.2.6 must keep the core-flow summary table as a real table, not as prose or a generic matrix summary.\n",
                "Section 6.3 must keep the nonfunctional-test table as a real table before the analytical paragraph.\n",
                "Do not collapse required Chapter 6 tables into overview prose, and do not replace them with only high-level summaries such as 'test design' or 'result summary'.\n",
                "When table specs are provided, render the table titles, headers, and rows directly from the packet data instead of inventing new rows.\n",
                "If a Chapter 6 table row contains explicit placeholder wording such as '待根据当前测试主机补充', keep that placeholder instead of guessing missing hardware or browser facts.\n",
                "After each Chapter 6 table, add only a short thesis-style analysis paragraph that summarizes the result significance for the system.\n",
            ]
        )
    if chapter == "04-系统设计.md":
        chapter_specific_prompt_lines.extend(
            [
                "For chapter 4, write it as a system-design chapter with a clear sequence: architecture -> modules -> database -> blockchain/chaincode -> business flows -> security/privacy.\n",
                "Keep every required figure and table marker literally in the manuscript, using the required output markers as the visible captions even when the staged asset title is a draft label such as '草案'.\n",
                "In section 4.3.3, keep the packet-provided database summary table as a real markdown table before the explanatory paragraph.\n",
                "Do not invent extra design tables such as module-mapping tables, field-level data dictionaries, or risk-summary tables when the packet does not actually provide them.\n",
                "When table specs are provided for chapter 4, render their title, headers, and rows directly from the packet data instead of paraphrasing them into prose.\n",
                "In the design chapter, emphasize structural decisions, data boundaries, and inter-module coordination, rather than repeating implementation details or test conclusions.\n",
                "For each flow subsection in 4.5, keep the flow diagram caption in place and explain the business trigger, backend coordination, and chain-side effect in that order.\n",
                "For section 4.6, summarize risks and matching protection mechanisms in a design-oriented tone instead of writing it as a testing or operational checklist.\n",
                "If section 4.6 has no staged security table asset, keep the section prose-only or use an explicit placeholder rather than inventing a new table.\n",
                "The chapter closing paragraph should summarize the overall design basis for the implementation chapter, not repeat the full chapter outline.\n",
            ]
        )

    raw_prompt = (
        f"Write the chapter `{chapter}` for a computer thesis.\n"
        f"Target file: `{target_path}`.\n"
        f"Respect the locked thesis outline at `{thesis_outline_md_rel_path}`.\n"
        f"Preserve the structure source `{chapter_structure_source(project_profile, chapter)}`.\n"
        f"Use only the evidence sections: {', '.join(section_names) or 'none'}.\n"
        f"Required section outline:\n{outline_text}\n"
        f"Required asset contract:\n{asset_text}\n"
        f"Required output markers: {', '.join(asset_contract['required_output_markers']) or 'none'}.\n"
        f"Structured table specs to render literally when applicable:\n{table_specs_text}\n"
        f"Research sidecar available at `{research_dir_rel_path}`; research index: `{research_index_json_rel_path}`.\n"
        f"Research sidecar required: {research_contract['must_use_research_sidecar']}; recommended: {research_contract['research_recommended']}.\n"
        f"Use citation ids from the reference registry only: {', '.join('[' + str(ref['id']) + ']' for ref in references) or 'none'}.\n"
        "Prefer one primary use per reference unless the same source is truly needed again; citation numbering will be normalized by first appearance across the thesis.\n"
        "Prefer one citation per sentence or claim. Avoid stacked citation clusters such as [1][2][3]; if multiple sources are relevant, split the claims into adjacent sentences and assign citations separately.\n"
        "Write in thesis-manuscript voice rather than project-commentary voice. Prefer “本研究”, “本系统” or “全文” instead of “本文”, except in fixed chapter labels such as “本章”.\n"
        "Avoid repository-facing wording in the manuscript, including phrases such as “证据路径”, raw file or script paths used as evidence, and meta statements about helping the paper itself.\n"
        "Do not mention repository filenames, page component filenames, backend service filenames, or literal route paths in the manuscript; describe their business role directly in thesis language.\n"
        "Avoid lead-in patterns such as “从运行环境看”“从接口分组看”“从目录结构看”. State the design or implementation point directly.\n"
        "Avoid document-sourcing narration such as “根据链码设计文档”“根据数据库设计文档”“根据测试报告” or “测试依据主要来自……文档/报告”. Rewrite them as direct design, implementation, or test conclusions.\n"
        "For derived assets without a real source file, use the asset note/placeholder_text to keep a structured figure or table placeholder instead of deleting the asset.\n"
        f"Code evidence pack available at `{code_evidence_pack_rel_path}`; snippets dir: `{code_snippets_dir_rel_path}`; screenshots dir: `{code_screenshots_dir_rel_path}`.\n"
        f"Chapter-specific code evidence contract:\n{code_contract_text}\n"
    ) + "".join(chapter_specific_prompt_lines) + (
        "Do not collapse figures/tables/appendix items into prose-only paragraphs; if an asset is missing, keep an explicit placeholder.\n"
        f"Follow the local skill at `{skill_rel_path}` after drafting."
    )
    polish_prompt = (
        f"Polish the drafted chapter `{chapter}` using the local skill `{skill_rel_path}`.\n"
        "Keep facts intact, tighten academic style, check terminology consistency, ensure all citations correspond to the registry, "
        "preserve figure/table/appendix markers required by the packet, replace “本文” with “本研究/本系统/全文” and “本项目” with “本研究/本系统” where appropriate, "
        "remove repository-facing wording such as “证据路径” or raw script-path narration, avoid repository filenames/component filenames/service filenames/literal route paths in正文, "
        "remove document-sourcing narration such as “根据某文档/报告” or “测试依据主要来自……文档/报告”, "
        "and break stacked citations like [1][2][3] into separate claim-citation pairs."
    )
    return {
        "schema_version": CHAPTER_PACKET_SCHEMA_VERSION,
        "generated_at": packet_generated_at,
        "packet_kind": "full",
        "chapter": chapter,
        "title": title,
        "status": queue_entry["status"],
        "mode": queue_entry["mode"],
        "structure_source": chapter_structure_source(project_profile, chapter),
        "target_path": target_path,
        "word_guidance": CHAPTER_WORD_GUIDANCE.get(chapter, "按章节需要控制篇幅"),
        "outline_snapshot": outline_snapshot,
        "outline_sync": {
            "packet_generated_at": packet_generated_at,
            "outline_generated_at": thesis_outline.get("generated_at", ""),
            "outline_signature": outline_snapshot["signature"],
            "current_outline_generated_at": thesis_outline.get("generated_at", ""),
            "current_outline_signature": outline_snapshot["signature"],
            "status": "current",
            "warning": "",
        },
        "execution_steps": _chapter_execution_steps(chapter, queue_entry, skill_rel_path, target_path),
        "input_files": {
            "local_skill": skill_rel_path,
            "research_skill": research_skill_rel_path,
            "paper_reader_skill": paper_reader_skill_rel_path,
            "project_profile_json": project_profile_rel_path,
            "thesis_outline_json": thesis_outline_json_rel_path,
            "thesis_outline_md": thesis_outline_md_rel_path,
            "material_pack_json": "docs/materials/material_pack.json",
            "code_evidence_pack_json": code_evidence_pack_rel_path,
            "code_snippets_dir": code_snippets_dir_rel_path,
            "code_screenshots_dir": code_screenshots_dir_rel_path,
            "literature_pack_json": "docs/writing/literature_pack.json",
            "reference_registry_json": "docs/writing/reference_registry.json",
            "research_index_json": research_index_json_rel_path,
            "research_index_md": research_index_md_rel_path,
            "research_dir": research_dir_rel_path,
            "target_chapter": target_path,
        },
        "output_contract": _output_contract(chapter, title, target_path, queue_entry, project_profile),
        "finalize_after_write": _finalize_contract(queue_entry),
        "research_contract": research_contract,
        "chapter_material_scope": section_names,
        "section_outline": section_outline,
        "material_sections": material_sections,
        "chapter_assets": asset_contract["chapter_assets"],
        "asset_to_section_map": asset_contract["asset_to_section_map"],
        "required_code_evidence": code_contract["required_code_evidence"],
        "code_evidence_to_section_map": code_contract["code_evidence_to_section_map"],
        "required_code_screenshot_count": code_contract["required_code_screenshot_count"],
        "module_implementation_contract": code_contract["module_implementation_contract"],
        "required_output_markers": asset_contract["required_output_markers"],
        "table_specs": asset_contract["table_specs"],
        "appendix_contract": asset_contract["appendix_contract"],
        "validation": validation,
        "recommended_references": references,
        "raw_prompt": raw_prompt,
        "polish_prompt": polish_prompt,
        "local_skill_path": skill_rel_path,
        "polish_required": queue_entry["polish_required"],
    }


def _brief_style_rules(chapter: str, research_contract: dict[str, Any]) -> list[str]:
    rules = [
        "使用论文行文，不使用项目汇报或仓库说明口吻。",
        "优先使用“本研究”“本系统”“全文”，避免使用“本文”“本项目”。",
        "避免出现仓库路径、脚本名、组件文件名、服务文件名或接口路由字面量。",
        "避免使用“根据某文档/报告”“从目录结构看”“从运行环境看”这类来源导向表述。",
        "引用仅使用 reference registry 中的编号，并按首次出现顺序组织。",
        "单句尽量只使用一个引用；若需要多篇文献支撑，拆成相邻句分别引用。",
        "图表、测试证据和附录条目不得被改写成纯描述性段落；缺失时保留显式占位。",
    ]
    if research_contract.get("must_use_research_sidecar"):
        rules.append("本章必须优先消费 research sidecar 结果，不得脱离侧车材料凭空补写研究现状。")
    elif research_contract.get("research_recommended"):
        rules.append("本章建议优先参考 research sidecar 与 literature pack，再组织论文表述。")

    if chapter == "02-系统开发工具及技术介绍.md":
        rules.extend(
            [
                "第 2 章应作为技术基础与选型章节来写，不应写成实现过程回顾。",
                "如 packet 提供结构化表格，需先按表格写出真实 Markdown 表，再补解释段落。",
            ]
        )
    elif chapter == "04-系统设计.md":
        rules.extend(
            [
                "第 4 章按“架构 -> 模块 -> 数据库 -> 区块链/链码 -> 业务流程 -> 安全设计”的顺序展开。",
                "4.3.3 应先保留 packet 提供的结构化表格，再补设计解释；若 packet 未提供字段级数据字典资产，不得自行扩写为虚构字段表。",
                "4.5 业务流程小节应先写触发条件，再写后端协同与链上效果。",
            ]
        )
    elif chapter == "05-系统实现.md":
        rules.extend(
            [
                "第 5 章按业务模块组织，而不是按前端/后端开发顺序组织。",
                "每个模块先写业务职责，再写子功能实现，代码应直接嵌入对应子功能，不单独拆代码截图小节。",
                "若 workspace 配置 `document_format.code_blocks.render_mode=text`，最终 DOCX 中的 fenced code block 应直接按文字代码块导出，而不是转成图片。",
                "若使用代码截图，只能作为可选实现证据，并且必须紧跟在对应的后端或前端代码块之后插入，不能单独生成“关键代码截图”小节。",
                "代码截图仅作为可选实现证据插图使用，不编号，不写“图5.x”题注，也不单独形成图题段落。",
                "每个子功能小节都必须同时出现“后端实现。”和“前端实现。”两段，顺序固定为后端在前、前端在后。",
                "后端段落应落到接口、服务编排、角色校验、数据库写入和链上协同；前端段落应落到页面入口、表单/列表交互、状态反馈和路由跳转。",
                "优先直接嵌入工作区已抽取的真实代码片段；若存在真实页面截图，应放在对应前端实现段落之后。",
                "chapter packet 已选中的 `test-screenshot` 不得省略；若同一前端小节分配到多张真实页面图，应连续嵌入该小节的前端段落之后，再接代码证据。",
                "只能使用已抽取到工作区的真实代码证据与页面截图，不得自造代码块。",
            ]
        )
    elif chapter == "06-系统测试.md":
        rules.extend(
            [
                "第 6 章按样稿式测试章节来写，不写成压缩版测试总结。",
                "6.1 环境配置、6.2 功能测试、6.3 非功能测试均应优先保留真实表格。",
                "每个测试表后只接一小段论文式结果分析，不展开成大段过程叙述。",
            ]
        )
    return rules


def _brief_entry_ids(entries: list[dict[str, Any]]) -> str:
    ids = [entry.get("id", "").strip() for entry in entries if entry.get("id", "").strip()]
    return ", ".join(ids) or "none"


def _render_table_spec_for_brief(table_spec: dict[str, Any]) -> list[str]:
    lines = [f"- {table_spec['title']} | kind={table_spec['kind']}"]
    lines.append(f"  - headers: {', '.join(table_spec.get('headers', [])) or 'none'}")
    rows = table_spec.get("rows", [])
    if rows:
        lines.extend(
            [f"  - row {idx}: {' | '.join(str(cell) for cell in row)}" for idx, row in enumerate(rows, start=1)]
        )
    else:
        lines.append(f"  - placeholder: {table_spec.get('placeholder_text', '') or 'none'}")
    return lines


def _render_chapter_brief_md(packet: dict[str, Any], debug_packet_md_rel_path: str) -> str:
    lines = [
        f"# Writer Brief: {packet['chapter']}",
        "",
        f"- title: {packet['title']}",
        f"- status: {packet['status']}",
        f"- mode: {packet['mode']}",
        f"- target_path: `{packet['target_path']}`",
        f"- word_guidance: {packet.get('word_guidance', '')}",
        f"- local_skill: `{packet.get('local_skill_path', '')}`",
        f"- debug_packet_md: `{debug_packet_md_rel_path}`",
        f"- polish_required: {packet.get('polish_required', False)}",
        "",
        "## 开写步骤",
        "",
        "1. 先阅读本 brief，确认章节目标、小节结构、资产合同与写作约束。",
        "2. 再核对 thesis outline；若目录已变化，先重新执行 `prepare-outline`、`prepare-writing` 与 `prepare-chapter`。",
        "3. 默认只消费工作区中的材料包、文献包、代码证据包与本 brief，不重新回源项目仓库。",
        "4. 如需排查证据来源、匹配逻辑或字段级诊断信息，再回看 debug packet。",
        f"5. 按本 brief 直接写入或修订 `{packet['target_path']}`，随后按状态机执行 drafted / polished / reviewed。",
        "",
        "## 大纲同步",
        "",
        f"- status: {packet.get('outline_sync', {}).get('status', 'unknown')}",
        f"- outline_generated_at: {packet.get('outline_sync', {}).get('outline_generated_at', '')}",
        f"- brief_generated_at: {packet.get('generated_at', '')}",
        f"- outline_signature: {packet.get('outline_sync', {}).get('outline_signature', '')}",
        f"- warning: {packet.get('outline_sync', {}).get('warning', '') or 'none'}",
        "",
        "## 核心结构",
        "",
    ]
    lines.extend([f"- {item}" for item in packet.get("output_contract", {}).get("required_subsections", [])] or ["- none"])
    lines.extend(
        [
            "",
            "## 必需资产",
            "",
        ]
    )
    lines.extend(
        [
            f"- [{asset['asset_type']}] {asset['title']} -> {asset.get('section', '')}"
            for asset in packet.get("output_contract", {}).get("required_assets", [])
        ]
        or ["- none"]
    )
    screenshot_entries = [
        item for item in packet.get("asset_to_section_map", []) if item.get("workspace_image_path")
    ]
    if screenshot_entries:
        lines.extend(
            [
                "",
                "## 页面截图落点",
                "",
            ]
        )
        lines.extend(
            [
                f"- {item['title']} -> {item['target_section']} | source=`{item.get('source_path', '') or '-'}`"
                f" | workspace=`{item.get('workspace_image_path', '')}`"
                f" | selection_group=`{item.get('selection_group', '') or '-'}`"
                for item in screenshot_entries
            ]
        )
    lines.extend(
        [
            "",
            "## 必需输出标记",
            "",
        ]
    )
    lines.extend([f"- {marker}" for marker in packet.get("required_output_markers", [])] or ["- none"])
    lines.extend(
        [
            "",
            "## 结构化表格规范",
            "",
        ]
    )
    for table_spec in packet.get("table_specs", []):
        lines.extend(_render_table_spec_for_brief(table_spec))
    if not packet.get("table_specs"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## 输入文件",
            "",
        ]
    )
    for label in [
        "thesis_outline_md",
        "material_pack_json",
        "literature_pack_json",
        "reference_registry_json",
        "research_index_json",
        "research_dir",
        "code_evidence_pack_json",
        "code_snippets_dir",
        "code_screenshots_dir",
        "target_chapter",
    ]:
        value = packet.get("input_files", {}).get(label, "")
        if value:
            lines.append(f"- {label}: `{value}`")
    lines.extend(
        [
            "",
            "## 材料摘要",
            "",
            f"- chapter_material_scope: {', '.join(packet.get('chapter_material_scope', [])) or 'none'}",
            "",
        ]
    )
    for section_name, section in packet.get("material_sections", {}).items():
        lines.append(f"### {section_name}")
        lines.extend([f"- {item}" for item in section.get("summary", [])[:5]] or ["- no summary"])
        asset_counts = section.get("assets", {})
        counts = [f"{bucket}={len(asset_counts.get(bucket, []))}" for bucket in ASSET_BUCKET_ORDER if asset_counts.get(bucket)]
        if counts:
            lines.append(f"- asset_counts: {', '.join(counts)}")
        lines.append("")
    if packet.get("module_implementation_contract"):
        lines.extend(["## 第5章代码证据", ""])
        for module in packet.get("module_implementation_contract", []):
            lines.append(f"- {module['module_label']}")
            lines.append(f"  - parent_section: {module['parent_section']}")
            if module.get("code_screenshot_section"):
                lines.append(f"  - code_screenshot_section: {module['code_screenshot_section']}")
            for subfunction in module.get("subfunctions", []):
                lines.append(f"  - subfunction: {subfunction['section']}")
                lines.append(f"    - backend_evidence_ids: {_brief_entry_ids(subfunction.get('backend_entries', []))}")
                lines.append(f"    - frontend_evidence_ids: {_brief_entry_ids(subfunction.get('frontend_entries', []))}")
            if module.get("code_screenshot_section"):
                lines.append(f"  - screenshot_evidence_ids: {_brief_entry_ids(module.get('code_screenshots', []))}")
        lines.append("")
    lines.extend(
        [
            "## 写作约束",
            "",
        ]
    )
    lines.extend([f"- {rule}" for rule in _brief_style_rules(packet["chapter"], packet.get("research_contract", {}))])
    lines.extend(
        [
            "",
            "## 推荐参考文献",
            "",
        ]
    )
    lines.extend(
        [f"- [{ref['id']}] {ref['title']} ({ref['year']})" for ref in packet.get("recommended_references", [])]
        or ["- none"]
    )
    lines.extend(
        [
            "",
            "## 校验提醒",
            "",
            f"- validation_status: {packet.get('validation', {}).get('status', 'unknown')}",
        ]
    )
    lines.extend([f"- issue: {issue}" for issue in packet.get("validation", {}).get("issues", [])] or ["- issue: none"])
    lines.append("")
    return "\n".join(lines)


def _render_chapter_packet_md(packet: dict[str, Any]) -> str:
    lines = [
        f"# Chapter Packet: {packet['chapter']}",
        "",
        f"- schema_version: {packet.get('schema_version', 'unknown')}",
        f"- generated_at: {packet.get('generated_at', '')}",
        f"- packet_kind: {packet.get('packet_kind', 'unknown')}",
        f"- title: {packet['title']}",
        f"- mode: {packet['mode']}",
        f"- structure_source: {packet['structure_source']}",
        f"- target_path: `{packet['target_path']}`",
        f"- word_guidance: {packet['word_guidance']}",
        f"- local_skill: `{packet['local_skill_path']}`",
        f"- polish_required: {packet['polish_required']}",
        "",
        "## Execution Steps",
        "",
    ]
    lines.extend([f"{idx}. {step}" for idx, step in enumerate(packet["execution_steps"], start=1)])
    lines.extend(
        [
            "",
            "## Outline Sync",
            "",
            f"- status: {packet.get('outline_sync', {}).get('status', 'unknown')}",
            f"- outline_generated_at: {packet.get('outline_sync', {}).get('outline_generated_at', '')}",
            f"- packet_generated_at: {packet.get('outline_sync', {}).get('packet_generated_at', '')}",
            f"- outline_signature: {packet.get('outline_sync', {}).get('outline_signature', '')}",
            f"- warning: {packet.get('outline_sync', {}).get('warning', '') or 'none'}",
            f"- outline_required_subsections: {len(packet.get('outline_snapshot', {}).get('required_subsections', []))}",
            "",
            "## Input Files",
            "",
        ]
    )
    lines.extend([f"- {key}: `{value}`" for key, value in packet["input_files"].items()])
    lines.extend(
        [
            "",
            "## Output Contract",
            "",
            f"- title: `{packet['output_contract']['title']}`",
            f"- target_path: `{packet['output_contract']['target_path']}`",
            f"- structure_source: `{packet['output_contract']['structure_source']}`",
            f"- must_preserve_structure: `{packet['output_contract']['must_preserve_structure']}`",
            f"- must_use_reference_registry: `{packet['output_contract']['must_use_reference_registry']}`",
            f"- must_use_research_sidecar: `{packet['output_contract']['must_use_research_sidecar']}`",
            f"- research_recommended: `{packet['output_contract']['research_recommended']}`",
            f"- required_subsections: {', '.join(packet['output_contract']['required_subsections']) or 'none'}",
            f"- required_table_types: {', '.join(packet['output_contract']['required_table_types']) or 'none'}",
            f"- required_appendix_items: {', '.join(packet['output_contract']['required_appendix_items']) or 'none'}",
            f"- placeholder_policy: `{packet['output_contract']['placeholder_policy'].get('mode', 'optional')}`",
        ]
    )
    if packet["output_contract"].get("module_implementation_policy"):
        lines.append(f"- module_implementation_policy: {packet['output_contract']['module_implementation_policy']}")
    if packet["output_contract"]["required_assets"]:
        lines.extend(
            [
                "- required_assets:",
                *[
                    f"  - [{asset['asset_type']}] {asset['title']} -> {asset.get('section', '')}"
                    for asset in packet["output_contract"]["required_assets"]
                ],
            ]
        )
    if packet["output_contract"]["manual_allowed_markers"]:
        lines.append(f"- manual_allowed_markers: {', '.join(packet['output_contract']['manual_allowed_markers'])}")
    lines.extend(
        [
            "",
            "## Finalize Contract",
            "",
        ]
    )
    lines.extend([f"- {key}: `{value}`" for key, value in packet["finalize_after_write"].items()])
    lines.extend(
        [
            "",
            "## Research Contract",
            "",
            f"- must_use_research_sidecar: `{packet['research_contract']['must_use_research_sidecar']}`",
            f"- research_recommended: `{packet['research_contract']['research_recommended']}`",
        ]
    )
    lines.extend(
        [
            "",
            "## Section Outline",
            "",
            f"- chapter_material_scope: {', '.join(packet['chapter_material_scope']) or 'none'}",
        ]
    )
    lines.extend(
        [
            *(
                [
                    f"- L{item['depth']}: {item['title']} | materials: {', '.join(item['material_sections']) or 'inherit'}"
                    for item in packet["section_outline"]
                ]
                or ["- none"]
            ),
            "",
            "## Material Sections",
            "",
        ]
    )
    for section_name, section in packet["material_sections"].items():
        lines.append(f"### {section_name}")
        lines.extend([f"- {item}" for item in section.get("summary", [])[:5]] or ["- no summary"])
        lines.append("")
        asset_counts = section.get("assets", {})
        for bucket in ASSET_BUCKET_ORDER:
            count = len(asset_counts.get(bucket, []))
            if count:
                lines.append(f"- assets[{bucket}]: {count}")
        lines.append("")
    lines.extend(
        [
            "## Chapter Assets",
            "",
            f"- required_output_markers: {', '.join(packet['required_output_markers']) or 'none'}",
            f"- validation_status: {packet['validation']['status']}",
        ]
    )
    lines.extend([f"- issue: {issue}" for issue in packet["validation"].get("issues", [])] or ["- issue: none"])
    lines.append("")
    lines.extend(
        [
            "### Asset To Section Map",
            "",
            *(
                [
                    f"- [{item['asset_type']}] {item['title']} -> {item['target_section']} | required={item['required']} | evidence={item['evidence_level']}"
                    f" | source={item.get('source_path', '') or '-'}"
                    f" | workspace={item.get('workspace_image_path', '') or '-'}"
                    f" | selection_group={item.get('selection_group', '') or '-'}"
                    for item in packet["asset_to_section_map"]
                ]
                or ["- none"]
            ),
            "",
            "### Staged Page Screenshots",
            "",
        ]
    )
    lines.extend(
        [
            f"- {item.get('title', '') or '-'} | source={item.get('source_path', '') or '-'}"
            f" | workspace={item.get('workspace_path', '') or '-'}"
            f" | selection_group={item.get('selection_group', '') or '-'}"
            f" | name_source={item.get('name_source', '') or '-'}"
            f" | status={item.get('status', '') or '-'}"
            for item in packet.get("staged_page_screenshots", [])
        ]
        or ["- none"]
    )
    lines.extend(
        [
            "",
            "### Table Specs",
            "",
        ]
    )
    for table_spec in packet["table_specs"]:
        lines.append(f"- {table_spec['title']} | kind={table_spec['kind']} | source={table_spec['source_path'] or '-'}")
        lines.append(f"  - headers: {', '.join(table_spec['headers']) or 'none'}")
        lines.append(f"  - rows: {len(table_spec['rows'])}")
    if not packet["table_specs"]:
        lines.append("- none")
    lines.extend(
        [
            "",
            "### Appendix Contract",
            "",
            f"- required_titles: {', '.join(packet['appendix_contract']['required_titles']) or 'none'}",
            f"- selected_titles: {', '.join(packet['appendix_contract']['selected_titles']) or 'none'}",
            f"- placeholder_policy: {packet['appendix_contract']['placeholder_policy'].get('mode', 'optional')}",
            "",
        ]
    )
    lines.extend(
        [
            "### Code Evidence Contract",
            "",
            f"- required_code_evidence_count: {len(packet.get('required_code_evidence', []))}",
            f"- required_code_screenshot_count: {packet.get('required_code_screenshot_count', 0)}",
        ]
    )
    for item in packet.get("required_code_evidence", []):
        lines.append(f"- {item['module_label']} | {item['side']} -> {item['section']} | min_count={item['min_count']}")
    if not packet.get("required_code_evidence"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "### Code Evidence To Section Map",
            "",
        ]
    )
    for item in packet.get("code_evidence_to_section_map", []):
        lines.append(
            f"- [{item['side']}] {item['entry_id']} -> {item['target_section']} | render_as={item['render_as']} | source={item['source_path']}"
        )
    if not packet.get("code_evidence_to_section_map"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "### Module Implementation Contract",
            "",
        ]
    )
    for module in packet.get("module_implementation_contract", []):
        lines.append(f"- {module['module_label']}")
        lines.append(f"  - parent_section: {module['parent_section']}")
        if module.get("code_screenshot_section"):
            lines.append(f"  - code_screenshot_section: {module['code_screenshot_section']}")
        for subfunction in module.get("subfunctions", []):
            lines.append(f"  - subfunction: {subfunction['section']}")
            lines.append(
                f"    - backend_entries: {', '.join(entry['source_path'] for entry in subfunction.get('backend_entries', [])) or 'none'}"
            )
            lines.append(
                f"    - frontend_entries: {', '.join(entry['source_path'] for entry in subfunction.get('frontend_entries', [])) or 'none'}"
            )
        lines.append(
            f"  - backend_entries: {', '.join(entry['source_path'] for entry in module['backend_entries']) or 'none'}"
        )
        lines.append(
            f"  - frontend_entries: {', '.join(entry['source_path'] for entry in module['frontend_entries']) or 'none'}"
        )
        if module.get("code_screenshot_section"):
            lines.append(
                f"  - code_screenshots: {', '.join(entry['screenshot_path'] for entry in module['code_screenshots']) or 'none'}"
            )
    if not packet.get("module_implementation_contract"):
        lines.append("- none")
    lines.append("")
    lines.extend(["## Recommended References", ""])
    for ref in packet["recommended_references"]:
        lines.append(f"- [{ref['id']}] {ref['title']} ({ref['year']})")
    if not packet["recommended_references"]:
        lines.append("- no recommended references")
    lines.extend(
        [
            "",
            "## Raw Draft Prompt",
            "",
            packet["raw_prompt"],
            "",
            "## Polish Prompt",
            "",
            packet["polish_prompt"],
            "",
        ]
    )
    return "\n".join(lines)


def _render_chapter_start_md(packet: dict[str, Any], brief_rel_path: str, debug_packet_rel_path: str) -> str:
    required_subsections = packet.get("output_contract", {}).get("required_subsections", [])
    lines = [
        f"# Start Chapter: {packet['chapter']}",
        "",
        f"- title: {packet['title']}",
        f"- status: {packet['status']}",
        f"- mode: {packet['mode']}",
        f"- target_path: `{packet['target_path']}`",
        f"- word_guidance: {packet.get('word_guidance', '')}",
        f"- local_skill: `{packet.get('local_skill_path', '')}`",
        f"- writer_brief: `{brief_rel_path}`",
        f"- debug_packet_md: `{debug_packet_rel_path}`",
        "",
        "## 开写步骤",
        "",
        "1. 先阅读 writer brief，确认必须保留的小节结构、资产合同、表格规范与写作约束。",
        "2. 先确认论文目录已经锁定；如果大纲、小节层级或章节顺序发生变化，先执行 `prepare-outline` 与 `prepare-writing`，再重新生成 chapter start brief。",
        "3. 开写前先阅读下方输入文件；除非 brief 或 debug packet 明确要求，否则不要重新回源仓库摘材料。",
        "4. 只有在需要排查证据来源、字段映射或规则命中原因时，才回看 debug packet。",
        f"5. 按 writer brief 合同直接写入或修订 `{packet['target_path']}`。",
        f"6. raw draft 完成后执行 `python3 workflow_bundle/tools/cli.py finalize-chapter --config <workspace.json> --chapter {packet['chapter']} --status drafted`。",
        "7. 按本地润色 skill 完成 polish 后进入 `polished`；人工确认后再进入 `reviewed`。",
        "",
        "## 执行约束",
        "",
        "- 目录先于正文：章节写作必须服从已锁定的大纲，不得一边写正文一边私自改目录。",
        "- 引用按首次出现编号：不要手动追求固定编号，统一由工作流归一化。",
        "- 单句尽量单引：避免同一句连续出现多个引用编号。",
        "- 文献尽量单次主用：同一文献如非必要不要在同章反复引用；重复使用会进入 citation audit。",
        "",
        "## 大纲同步",
        "",
        f"- status: {packet.get('outline_sync', {}).get('status', 'unknown')}",
        f"- outline_generated_at: {packet.get('outline_sync', {}).get('outline_generated_at', '')}",
        f"- packet_generated_at: {packet.get('outline_sync', {}).get('packet_generated_at', '')}",
        f"- outline_signature: {packet.get('outline_sync', {}).get('outline_signature', '')}",
        f"- warning: {packet.get('outline_sync', {}).get('warning', '') or 'none'}",
        "",
        "## 必需结构",
        "",
    ]
    lines.extend([f"- {item}" for item in required_subsections] or ["- no fixed subsections"])
    lines.extend(
        [
            "",
            "## 必需输出标记",
            "",
        ]
    )
    lines.extend([f"- {marker}" for marker in packet.get("required_output_markers", [])] or ["- none"])
    lines.extend(
        [
            "",
            "## 输入文件",
            "",
        ]
    )
    for label, path in packet.get("input_files", {}).items():
        lines.append(f"- {label}: `{path}`")
    lines.extend(
        [
            "",
            "## 章节材料范围",
            "",
            f"- chapter_material_scope: {', '.join(packet.get('chapter_material_scope', [])) or 'none'}",
            "",
            "## 代码证据",
            "",
            f"- required_code_evidence_count: {len(packet.get('required_code_evidence', []))}",
            f"- required_code_screenshot_count: {packet.get('required_code_screenshot_count', 0)}",
        ]
    )
    for module in packet.get("module_implementation_contract", []):
        lines.append(f"- {module['module_label']}")
        lines.append(f"  - parent_section: {module['parent_section']}")
        if module.get("code_screenshot_section"):
            lines.append(f"  - code_screenshot_section: {module['code_screenshot_section']}")
        for subfunction in module.get("subfunctions", []):
            lines.append(f"  - subfunction: {subfunction['section']}")
            lines.append(
                f"    - backend_entries: {', '.join(entry['source_path'] for entry in subfunction.get('backend_entries', [])) or 'none'}"
            )
            lines.append(
                f"    - frontend_entries: {', '.join(entry['source_path'] for entry in subfunction.get('frontend_entries', [])) or 'none'}"
            )
        lines.append(
            f"  - backend_entries: {', '.join(entry['source_path'] for entry in module.get('backend_entries', [])) or 'none'}"
        )
        lines.append(
            f"  - frontend_entries: {', '.join(entry['source_path'] for entry in module.get('frontend_entries', [])) or 'none'}"
        )
        if module.get("code_screenshot_section"):
            lines.append(
                f"  - code_screenshots: {', '.join(entry['screenshot_path'] for entry in module.get('code_screenshots', [])) or 'none'}"
            )
    if not packet.get("module_implementation_contract"):
        lines.append("- no chapter-specific code evidence")
    lines.extend(
        [
            "",
            "## 校验快照",
            "",
            f"- status: {packet.get('validation', {}).get('status', 'unknown')}",
        ]
    )
    lines.extend([f"- issue: {issue}" for issue in packet.get("validation", {}).get("issues", [])] or ["- issue: none"])
    lines.append("")
    return "\n".join(lines)


def run_prepare_chapter(config_path: Path, chapter: str) -> dict[str, Path]:
    ctx = load_workspace_context(config_path)
    workspace_root = ctx["workspace_root"]
    config = ctx["config"]
    manifest = ctx["manifest"]
    writing_paths = writing_output_paths(config, workspace_root)
    material_paths = material_output_paths(config, workspace_root)
    queue = read_json(writing_paths["chapter_queue_json"])
    thesis_outline = read_json(writing_paths["thesis_outline_json"])
    material_pack = read_json(material_paths["material_pack_json"])
    code_pack = _load_code_evidence_pack(config, workspace_root)
    project_profile = _load_or_build_project_profile(manifest, material_pack, writing_paths)
    registry = read_json(writing_paths["reference_registry_json"]) if writing_paths["reference_registry_json"].exists() else {"entries": []}

    chapter_name = _normalize_chapter_name(chapter)
    chapter_map = _chapter_title_map(project_profile)
    if chapter_name not in chapter_map:
        raise FileNotFoundError(f"unknown chapter: {chapter_name}")

    queue_entry = next((entry for entry in queue["chapters"] if entry["chapter"] == chapter_name), None)
    if queue_entry is None:
        raise FileNotFoundError(f"chapter not found in queue: {chapter_name}")
    _validate_prepare_mode(queue_entry, chapter_name)

    packet = _chapter_packet(
        chapter_name,
        chapter_map[chapter_name],
        queue_entry,
        thesis_outline,
        material_pack,
        code_pack,
        registry,
        project_profile,
        _relative_to_workspace(writing_paths["local_skill_path"], workspace_root),
        queue_entry["target_path"],
        _relative_to_workspace(writing_paths["project_profile_json"], workspace_root),
        _relative_to_workspace(material_paths["code_evidence_pack_json"], workspace_root),
        _relative_to_workspace(material_paths["code_snippets_dir"], workspace_root),
        _relative_to_workspace(material_paths["code_screenshots_dir"], workspace_root),
        _relative_to_workspace(writing_paths["thesis_outline_json"], workspace_root),
        _relative_to_workspace(writing_paths["thesis_outline_md"], workspace_root),
        _relative_to_workspace(writing_paths["research_index_json"], workspace_root),
        _relative_to_workspace(writing_paths["research_index_md"], workspace_root),
        _relative_to_workspace(writing_paths["research_dir"], workspace_root),
        _relative_to_workspace(writing_paths["research_skill_path"], workspace_root),
        _relative_to_workspace(writing_paths["paper_reader_skill_path"], workspace_root),
    )
    packet["staged_page_screenshots"] = stage_chapter5_test_screenshots(
        workspace_root,
        Path(manifest["project_root"]).resolve(),
        packet.get("chapter_assets", []),
    )
    packet_json_path = workspace_root / queue_entry["packet_json"]
    packet_md_path = workspace_root / queue_entry["packet_md"]
    brief_md_path = workspace_root / queue_entry["brief_md"]
    write_json(packet_json_path, packet)
    write_text(packet_md_path, _render_chapter_packet_md(packet))
    write_text(brief_md_path, _render_chapter_brief_md(packet, queue_entry["packet_md"]))

    if queue_entry["status"] == "pending":
        queue_entry["status"] = "prepared"
        queue_entry["prepared_at"] = _now_iso()
    queue_entry["packet_generated_at"] = packet.get("generated_at", "")
    queue_entry["brief_generated_at"] = packet.get("generated_at", "")
    queue_entry["packet_kind"] = packet.get("packet_kind", "")
    queue_entry["packet_outline_generated_at"] = packet.get("outline_sync", {}).get("outline_generated_at", "")
    queue_entry["packet_outline_signature"] = packet.get("outline_sync", {}).get("outline_signature", "")
    queue_entry["packet_outline_status"] = packet.get("outline_sync", {}).get("status", "")
    write_json(writing_paths["chapter_queue_json"], queue)
    return {"packet_json": packet_json_path, "packet_md": packet_md_path, "brief_md": brief_md_path}


def run_start_chapter(config_path: Path, chapter: str) -> dict[str, Path]:
    prepared = run_prepare_chapter(config_path, chapter)
    ctx = load_workspace_context(config_path)
    workspace_root = ctx["workspace_root"]
    packet = read_json(prepared["packet_json"])
    start_md_path = prepared["packet_md"].with_name(f"{prepared['packet_md'].stem}.start.md")
    write_text(
        start_md_path,
        _render_chapter_start_md(
            packet,
            _relative_to_workspace(prepared["brief_md"], workspace_root),
            _relative_to_workspace(prepared["packet_md"], workspace_root),
        ),
    )
    target_path = workspace_root / packet["target_path"]
    return {
        "packet_json": prepared["packet_json"],
        "packet_md": prepared["packet_md"],
        "brief_md": prepared["brief_md"],
        "start_md": start_md_path,
        "target_chapter": target_path,
    }


def _format_references_md(registry: dict[str, Any]) -> str:
    used_entries = [entry for entry in registry.get("entries", []) if entry.get("used_by")]
    used_entries.sort(key=lambda item: item["id"])
    lines = ["# 参考文献", ""]
    if not used_entries:
        lines.append("[1] 待补正式参考文献。")
        return "\n".join(lines) + "\n"
    lines.extend(_render_reference_text(entry) for entry in used_entries)
    return "\n".join(lines) + "\n"


def _collect_placeholders(text: str) -> list[str]:
    found = []
    for marker in PLACEHOLDER_MARKERS:
        if marker in text:
            found.append(marker)
    return found


def _strip_markdown_for_diagnostics(text: str) -> str:
    stripped = re.sub(r"```.*?```", "", text, flags=re.S)
    stripped = re.sub(r"<!--.*?-->", "", stripped, flags=re.S)
    stripped = re.sub(r"!\[[^\]]*]\([^)]+\)", "", stripped)
    return stripped


def _extract_heading_section(text: str, heading_title: str) -> str:
    pattern = re.compile(
        rf"^##+\s+{re.escape(heading_title)}\s*$([\s\S]*?)(?=^##+\s+|\Z)",
        flags=re.M,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _first_body_paragraph(text: str) -> str:
    cleaned_text = _strip_markdown_for_diagnostics(text)
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", cleaned_text) if item.strip()]
    for paragraph in paragraphs:
        if paragraph.startswith("#"):
            continue
        if re.match(r"^图\d+\.\d+", paragraph) or re.match(r"^表\d+\.\d+", paragraph):
            continue
        return paragraph.replace("\n", " ").strip()
    return ""


def _extract_citation_sequence(text: str) -> list[int]:
    return [int(num) for num in re.findall(r"\[(\d+)\]", text)]


def _citation_diagnostics(sequence: list[int], text: str = "") -> dict[str, Any]:
    counts: dict[int, int] = {}
    first_appearance: list[int] = []
    seen: set[int] = set()
    order_warnings: list[str] = []
    max_first = 0
    for num in sequence:
        counts[num] = counts.get(num, 0) + 1
        if num in seen:
            continue
        if first_appearance and num < max_first:
            order_warnings.append(f"[{num}] 首次出现时编号小于前面已出现的文献编号")
        first_appearance.append(num)
        seen.add(num)
        max_first = max(max_first, num)
    reuse_warnings = [f"[{num}] 在同一章节中重复使用 {count} 次" for num, count in counts.items() if count > 1]
    sentence_warnings: list[str] = []
    if text:
        cleaned_text = _strip_markdown_for_diagnostics(text)
        sentences = [item.strip() for item in re.split(r"(?<=[。！？!?；;])\s*", cleaned_text) if item.strip()]
        for sentence in sentences:
            sentence_ids: list[int] = []
            for num in re.findall(r"\[(\d+)\]", sentence):
                citation_id = int(num)
                if citation_id not in sentence_ids:
                    sentence_ids.append(citation_id)
            if len(sentence_ids) > 1:
                excerpt = sentence.replace("\n", " ")
                if len(excerpt) > 80:
                    excerpt = excerpt[:77] + "..."
                sentence_warnings.append(
                    f"同一句出现多个引用 {', '.join(f'[{num}]' for num in sentence_ids)}：{excerpt}"
                )
    return {
        "sequence": sequence,
        "first_appearance": first_appearance,
        "order_ok": not order_warnings,
        "order_warnings": order_warnings,
        "reuse_warnings": reuse_warnings,
        "sentence_warnings": sentence_warnings,
    }


def _style_diagnostics(text: str) -> list[str]:
    cleaned_text = _strip_markdown_for_diagnostics(text)
    warnings: list[str] = []
    for phrase in STYLE_AVOID_PHRASES:
        if phrase in cleaned_text:
            if phrase == "本文":
                warnings.append("检测到“本文”，正文宜优先改为“本研究”“本系统”或“全文”")
            elif phrase == "本项目":
                warnings.append("检测到“本项目”，正文宜优先改为“本研究”或“本系统”")
            elif phrase == "证据路径":
                warnings.append("检测到“证据路径”，论文正文或表格不宜使用仓库证据路径式表达")
            else:
                warnings.append(f"检测到“{phrase}”，建议改为直接陈述设计或实现结论")
    for phrase in sorted(set(re.findall(r"从[^。；，,\n]{0,20}看", cleaned_text))):
        if phrase not in STYLE_AVOID_PHRASES:
            warnings.append(f"检测到“{phrase}”，建议改为直接陈述设计或实现结论")
    for phrase in sorted(
        set(re.findall(r"(?:根据|依据|基于)[^。；，,\n]{0,80}(?:文档|报告|说明)", cleaned_text))
    ):
        warnings.append(f"检测到“{phrase}”，建议改为直接陈述设计、实现或测试结论")
    for phrase in sorted(
        set(re.findall(r"(?:主要来自|来自)[^。；\n]{0,80}(?:文档|报告|说明)", cleaned_text))
    ):
        warnings.append(f"检测到“{phrase}”，建议改为直接陈述设计、实现或测试结论")
    for phrase in MATERIAL_VOICE_PHRASES:
        if phrase in cleaned_text:
            warnings.append(f"检测到材料来源式表述“{phrase}”，建议改为直接陈述系统结论或验证结果")
    for inline_path in sorted(
        set(re.findall(r"`[^`\n]*(?:/|\.(?:sh|py|md|json|sql|vue|go|java|ts|js|tsx|jsx))[^\n`]*`", cleaned_text))
    ):
        warnings.append(f"检测到代码或路径式表述 {inline_path}，正文宜改为设计或实现结论描述")
    for cluster in sorted(set(re.findall(r"(?:\[\d+\]){2,}", cleaned_text))):
        warnings.append(f"检测到并列引用 {cluster}，建议拆分为独立句子并分别引用")
    for phrase in sorted(set(re.findall(r"表明[^。；\n]{0,60}说明", cleaned_text))):
        warnings.append(f"检测到链式结论表述“{phrase}”，建议改为更直接的学术化结论表达")
    return warnings


def _style_diagnostic_summary(chapter: str, text: str) -> dict[str, Any]:
    cleaned_text = _strip_markdown_for_diagnostics(text)
    preferred_subject_count = 0
    preferred_subject_count += cleaned_text.count("本文")
    preferred_subject_count += cleaned_text.count("本项目")

    source_narration_matches = set(
        re.findall(r"(?:根据|依据|基于)[^。；，,\n]{0,80}(?:文档|报告|说明)", cleaned_text)
    )
    source_narration_matches.update(
        re.findall(r"(?:主要来自|来自)[^。；\n]{0,80}(?:文档|报告|说明)", cleaned_text)
    )
    source_narration_count = len(source_narration_matches)

    repository_voice_matches = set()
    if "证据路径" in cleaned_text:
        repository_voice_matches.add("证据路径")
    for phrase in MATERIAL_VOICE_PHRASES:
        if phrase in cleaned_text:
            repository_voice_matches.add(phrase)
    repository_voice_matches.update(
        re.findall(r"`[^`\n]*(?:/|\.(?:sh|py|md|json|sql|vue|go|java|ts|js|tsx|jsx))[^\n`]*`", cleaned_text)
    )
    repository_voice_count = len(repository_voice_matches)

    weak_leadin_matches = set()
    for phrase in STYLE_AVOID_PHRASES:
        if phrase in {
            "本文",
            "本项目",
            "证据路径",
        }:
            continue
        if phrase in cleaned_text:
            weak_leadin_matches.add(phrase)
    weak_leadin_matches.update(re.findall(r"从[^。；，,\n]{0,20}看", cleaned_text))
    weak_leadin_count = len(weak_leadin_matches)

    opening_rhythm_warnings: list[str] = []
    first_paragraph = _first_body_paragraph(text)
    if first_paragraph:
        for pattern in OPENING_RECITAL_PATTERNS:
            if re.search(pattern, first_paragraph):
                opening_rhythm_warnings.append(
                    f"章节开头段落存在目录式引入“{first_paragraph[:40]}...”，建议改为直接进入研究问题或实现主题"
                )
                break

    summary_recap_warnings: list[str] = []
    summary_text = _extract_heading_section(text, "1.5 本章小结")
    if not summary_text:
        summary_text = _extract_heading_section(text, "5.7 本章小结")
    if not summary_text:
        summary_text = _extract_heading_section(text, "6.4 本章小结")
    if not summary_text:
        summary_text = _extract_heading_section(text, "7.3 本章小结")
    if summary_text:
        summary_excerpt = summary_text.replace("\n", " ").strip()
        for pattern in SUMMARY_RECAP_PATTERNS:
            if re.search(pattern, summary_excerpt):
                summary_recap_warnings.append(
                    f"本章小结存在目录复述倾向“{summary_excerpt[:50]}...”，建议改为研究结论式总结"
                )
                break

    warnings = _style_diagnostics(text)
    return {
        "warnings": warnings,
        "preferred_subject_warning_count": preferred_subject_count,
        "source_narration_warning_count": source_narration_count,
        "repository_voice_warning_count": repository_voice_count,
        "weak_leadin_warning_count": weak_leadin_count,
        "opening_rhythm_warning_count": len(opening_rhythm_warnings),
        "summary_recap_warning_count": len(summary_recap_warnings),
        "opening_rhythm_warnings": opening_rhythm_warnings,
        "summary_recap_warnings": summary_recap_warnings,
    }


def _workspace_citation_state(workspace_root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    build = config.get("build", {})
    input_dir = workspace_root / build.get("input_dir", "polished_v3")
    reference_file = build.get("reference_file", "REFERENCES.md")
    states: list[dict[str, Any]] = []
    for chapter in _final_chapter_order(config):
        if chapter == reference_file:
            continue
        chapter_path = input_dir / chapter
        text = read_text_safe(chapter_path) if chapter_path.exists() else ""
        sequence = _extract_citation_sequence(text)
        states.append(
            {
                "chapter": chapter,
                "path": chapter_path,
                "text": text,
                "diagnostics": _citation_diagnostics(sequence, text),
            }
        )
    return states


def _normalize_workspace_citations(
    workspace_root: Path,
    config: dict[str, Any],
    writing_paths: dict[str, Path],
    registry: dict[str, Any],
) -> dict[str, Any]:
    chapter_states = _workspace_citation_state(workspace_root, config)
    first_appearance: list[int] = []
    seen_ids: set[int] = set()
    for state in chapter_states:
        for num in state["diagnostics"]["sequence"]:
            if num not in seen_ids:
                seen_ids.add(num)
                first_appearance.append(num)

    entries_by_old_id = {int(entry["id"]): dict(entry) for entry in registry.get("entries", [])}
    used_ids = [old_id for old_id in first_appearance if old_id in entries_by_old_id]
    unused_ids = [old_id for old_id in sorted(entries_by_old_id) if old_id not in used_ids]

    id_map: dict[int, int] = {}
    normalized_entries: list[dict[str, Any]] = []
    for old_id in used_ids + unused_ids:
        entry = dict(entries_by_old_id[old_id])
        new_id = len(normalized_entries) + 1
        id_map[old_id] = new_id
        entry["id"] = new_id
        entry["used_by"] = []
        normalized_entries.append(entry)

    rewritten_chapters: list[str] = []
    citation_pattern = re.compile(r"\[(\d+)\]")
    for state in chapter_states:
        updated_text = citation_pattern.sub(lambda match: f"[{id_map.get(int(match.group(1)), int(match.group(1)))}]", state["text"])
        if updated_text != state["text"]:
            write_text(state["path"], updated_text)
            rewritten_chapters.append(state["chapter"])

    normalized_registry = {
        "style": registry.get("style", "numeric"),
        "generated_at": _now_iso(),
        "entries": normalized_entries,
    }
    post_states = _workspace_citation_state(workspace_root, config)
    for state in post_states:
        for num in sorted(set(state["diagnostics"]["sequence"])):
            entry = next((item for item in normalized_registry["entries"] if item["id"] == num), None)
            if entry is not None:
                entry.setdefault("used_by", []).append(state["chapter"])

    build = config.get("build", {})
    references_path = workspace_root / build.get("input_dir", "polished_v3") / build.get("reference_file", "REFERENCES.md")
    write_json(writing_paths["reference_registry_json"], normalized_registry)
    write_text(references_path, _format_references_md(normalized_registry))

    report_lines = [
        "# Citation Audit",
        "",
        f"- generated_at: {normalized_registry['generated_at']}",
        f"- numbering_rule: first appearance across thesis",
        f"- rewritten_chapters: {', '.join(rewritten_chapters) if rewritten_chapters else 'none'}",
        "",
        "## First Appearance Order",
        "",
        "- pending",
        "",
        "## Chapter Diagnostics",
        "",
    ]
    seen_report_ids: set[int] = set()
    first_order_report: list[int] = []
    for state in post_states:
        for num in state["diagnostics"]["sequence"]:
            if num not in seen_report_ids:
                seen_report_ids.add(num)
                first_order_report.append(num)
    report_lines[8] = "- " + (", ".join(f"[{num}]" for num in first_order_report) if first_order_report else "none")
    for state in post_states:
        diagnostics = state["diagnostics"]
        report_lines.extend(
            [
                f"### {state['chapter']}",
                "",
                f"- citation_sequence: {', '.join(f'[{num}]' for num in diagnostics['sequence']) if diagnostics['sequence'] else 'none'}",
                f"- first_appearance: {', '.join(f'[{num}]' for num in diagnostics['first_appearance']) if diagnostics['first_appearance'] else 'none'}",
                f"- citation_order_ok: {'yes' if diagnostics['order_ok'] else 'no'}",
                "",
                "#### Order Warnings",
                "",
                *([f"- {item}" for item in diagnostics["order_warnings"]] or ["- none"]),
                "",
                "#### Reuse Warnings",
                "",
                *([f"- {item}" for item in diagnostics["reuse_warnings"]] or ["- none"]),
                "",
                "#### Sentence Warnings",
                "",
                *([f"- {item}" for item in diagnostics["sentence_warnings"]] or ["- none"]),
                "",
            ]
        )
    write_text(writing_paths["citation_audit_md"], "\n".join(report_lines).rstrip() + "\n")
    return {
        "registry": normalized_registry,
        "references_md": references_path,
        "citation_audit_md": writing_paths["citation_audit_md"],
        "rewritten_chapters": rewritten_chapters,
    }


def run_normalize_citations(config_path: Path) -> dict[str, Path]:
    ctx = load_workspace_context(config_path)
    workspace_root = ctx["workspace_root"]
    writing_paths = writing_output_paths(ctx["config"], workspace_root)
    registry = read_json(writing_paths["reference_registry_json"])
    result = _normalize_workspace_citations(workspace_root, ctx["config"], writing_paths, registry)
    return {
        "reference_registry_json": writing_paths["reference_registry_json"],
        "references_md": result["references_md"],
        "citation_audit_md": result["citation_audit_md"],
    }


def run_finalize_chapter(config_path: Path, chapter: str, status: str = "polished") -> dict[str, Path]:
    ctx = load_workspace_context(config_path)
    workspace_root = ctx["workspace_root"]
    config = ctx["config"]
    build = config.get("build", {})
    writing_paths = writing_output_paths(config, workspace_root)
    queue = read_json(writing_paths["chapter_queue_json"])
    registry = read_json(writing_paths["reference_registry_json"])
    chapter_name = _normalize_chapter_name(chapter)

    queue_entry = next((entry for entry in queue["chapters"] if entry["chapter"] == chapter_name), None)
    if queue_entry is None:
        raise FileNotFoundError(f"chapter not found in queue: {chapter_name}")
    _validate_transition(queue_entry, status, chapter_name)

    chapter_path = workspace_root / build.get("input_dir", "polished_v3") / chapter_name
    thesis_outline = read_json(writing_paths["thesis_outline_json"]) if writing_paths["thesis_outline_json"].exists() else {"chapters": []}
    current_outline_snapshot = _chapter_outline_snapshot(thesis_outline, chapter_name, queue_entry.get("title", ""))
    packet_sync = _resolve_packet_outline_sync(
        workspace_root / queue_entry["packet_json"],
        current_outline_snapshot,
        thesis_outline.get("generated_at", ""),
    )
    if packet_sync["status"] in OUTLINE_SYNC_BLOCKING_STATUSES:
        raise RuntimeError(
            f"{chapter_name} packet outline sync is {packet_sync['status']}; "
            "rerun prepare-outline, prepare-writing, and prepare-chapter before finalize-chapter"
        )
    normalize_result = _normalize_workspace_citations(workspace_root, config, writing_paths, registry)
    text = read_text_safe(chapter_path) if chapter_path.exists() else ""
    diagnostics = _citation_diagnostics(_extract_citation_sequence(text), text)
    citation_ids = sorted(set(diagnostics["sequence"]))
    placeholders = _collect_placeholders(text)
    style_summary = _style_diagnostic_summary(chapter_name, text)
    style_warnings = style_summary["warnings"]

    review_path = workspace_root / queue_entry["review_md"]
    write_text(
        review_path,
        "\n".join(
            [
                f"# Review: {chapter_name}",
                "",
                f"- status: {status}",
                f"- citations_used: {', '.join(f'[{num}]' for num in citation_ids) if citation_ids else 'none'}",
                f"- citation_sequence: {', '.join(f'[{num}]' for num in diagnostics['sequence']) if diagnostics['sequence'] else 'none'}",
                f"- citation_order_ok: {'yes' if diagnostics['order_ok'] else 'no'}",
                f"- placeholder_count: {len(placeholders)}",
                f"- citation_audit_md: { _relative_to_workspace(writing_paths['citation_audit_md'], workspace_root) }",
                "",
                "## Citation Order Warnings",
                "",
                *([f"- {item}" for item in diagnostics["order_warnings"]] or ["- none"]),
                "",
                "## Citation Reuse Warnings",
                "",
                *([f"- {item}" for item in diagnostics["reuse_warnings"]] or ["- none"]),
                "",
                "## Citation Sentence Warnings",
                "",
                *([f"- {item}" for item in diagnostics["sentence_warnings"]] or ["- none"]),
                "",
                "## Outline Sync",
                "",
                f"- packet_kind: {packet_sync['packet_kind']}",
                f"- packet_outline_status: {packet_sync['status']}",
                f"- packet_generated_at: {packet_sync['packet_generated_at'] or 'none'}",
                f"- packet_outline_generated_at: {packet_sync['packet_outline_generated_at'] or 'none'}",
                f"- current_outline_generated_at: {packet_sync['current_outline_generated_at'] or 'none'}",
                f"- warning: {packet_sync['warning'] or 'none'}",
                "",
                "## Style Warnings",
                "",
                *([f"- {item}" for item in style_warnings] or ["- none"]),
                "",
                "## Style Summary",
                "",
                f"- preferred_subject_warning_count: {style_summary['preferred_subject_warning_count']}",
                f"- source_narration_warning_count: {style_summary['source_narration_warning_count']}",
                f"- repository_voice_warning_count: {style_summary['repository_voice_warning_count']}",
                f"- weak_leadin_warning_count: {style_summary['weak_leadin_warning_count']}",
                f"- opening_rhythm_warning_count: {style_summary['opening_rhythm_warning_count']}",
                f"- summary_recap_warning_count: {style_summary['summary_recap_warning_count']}",
                "",
                "## Opening Rhythm Warnings",
                "",
                *([f"- {item}" for item in style_summary["opening_rhythm_warnings"]] or ["- none"]),
                "",
                "## Summary Recap Warnings",
                "",
                *([f"- {item}" for item in style_summary["summary_recap_warnings"]] or ["- none"]),
                "",
                "## Placeholders",
                "",
                *([f"- {marker}" for marker in placeholders] or ["- none"]),
                "",
            ]
        )
        + "\n",
    )

    queue_entry["status"] = status
    queue_entry["finalized_at"] = _now_iso()
    queue_entry["citation_count"] = len(citation_ids)
    queue_entry["citation_order_ok"] = diagnostics["order_ok"]
    queue_entry["citation_order_warning_count"] = len(diagnostics["order_warnings"])
    queue_entry["citation_reuse_warning_count"] = len(diagnostics["reuse_warnings"])
    queue_entry["citation_sentence_warning_count"] = len(diagnostics["sentence_warnings"])
    queue_entry["placeholder_count"] = len(placeholders)
    queue_entry["style_issue_count"] = len(style_warnings)
    queue_entry["style_preferred_subject_warning_count"] = style_summary["preferred_subject_warning_count"]
    queue_entry["style_source_narration_warning_count"] = style_summary["source_narration_warning_count"]
    queue_entry["style_repository_voice_warning_count"] = style_summary["repository_voice_warning_count"]
    queue_entry["style_weak_leadin_warning_count"] = style_summary["weak_leadin_warning_count"]
    queue_entry["style_opening_rhythm_warning_count"] = style_summary["opening_rhythm_warning_count"]
    queue_entry["style_summary_recap_warning_count"] = style_summary["summary_recap_warning_count"]
    queue_entry["packet_generated_at"] = packet_sync["packet_generated_at"]
    queue_entry["packet_kind"] = packet_sync["packet_kind"]
    queue_entry["packet_outline_generated_at"] = packet_sync["packet_outline_generated_at"]
    queue_entry["packet_outline_signature"] = packet_sync["packet_outline_signature"]
    queue_entry["packet_outline_status"] = packet_sync["status"]
    write_json(writing_paths["chapter_queue_json"], queue)
    return {
        "review_md": review_path,
        "references_md": normalize_result["references_md"],
        "citation_audit_md": writing_paths["citation_audit_md"],
        "chapter_queue_json": writing_paths["chapter_queue_json"],
    }
