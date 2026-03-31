from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from core.build_final_thesis_docx import DEFAULT_CHAPTER_ORDER, DEFAULT_KEYWORDS_CN, DEFAULT_KEYWORDS_EN


CHAIN_LABELS = {
    "fisco": "FISCO BCOS",
    "fabric": "Hyperledger Fabric",
}

MATERIAL_PACK_SCHEMA_VERSION = 8
PROJECT_PROFILE_SCHEMA_VERSION = 14
CHAPTER_PACKET_SCHEMA_VERSION = 12
CODE_EVIDENCE_SCHEMA_VERSION = 1

ASSET_BUCKET_ORDER = [
    "figures",
    "tables",
    "appendix_items",
    "code_artifacts",
    "test_artifacts",
]

MATERIAL_SECTION_ORDER = [
    "project_objective",
    "architecture",
    "roles_permissions",
    "business_flows",
    "api_interfaces",
    "database_design",
    "blockchain_design",
    "deployment_runtime",
    "demo_test_evidence",
    "risks_conflicts_missing",
]

WRITING_ORDER = [
    "02-系统开发工具及技术介绍.md",
    "03-需求分析.md",
    "04-系统设计.md",
    "05-系统实现.md",
    "06-系统测试.md",
    "01-绪论.md",
    "07-结论与展望.md",
    "00-摘要.md",
    "00-Abstract.md",
    "08-致谢.md",
    "REFERENCES.md",
]

# Macro-level fixed chapter framework only.
# Detailed subsection trees must come from docs/writing/project_profile.json.
CHAPTER_BLUEPRINT = [
    ("00-摘要.md", "摘要", []),
    ("00-Abstract.md", "Abstract", []),
    ("01-绪论.md", "1 绪论", []),
    ("02-系统开发工具及技术介绍.md", "2 系统开发工具及技术介绍", []),
    ("03-需求分析.md", "3 需求分析", []),
    ("04-系统设计.md", "4 系统设计", []),
    ("05-系统实现.md", "5 系统实现", []),
    ("06-系统测试.md", "6 系统测试", []),
    ("07-结论与展望.md", "7 结论与展望", []),
    ("08-致谢.md", "8 致谢", []),
    ("REFERENCES.md", "参考文献", []),
]


def slugify_name(text: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z]+", "-", text).strip("-").lower()
    return slug or "thesis-workspace"


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f".{path.name}.tmp-{os.getpid()}"
    tmp_path.write_text(content, encoding="utf-8", newline="\n")
    tmp_path.replace(path)


def write_json(path: Path, data: Any) -> None:
    _atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    _atomic_write_text(path, content)


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def make_relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path.resolve())


def load_workspace_context(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = read_json(config_path)
    workspace_root = (config_path.parent / config.get("workspace_root", "../..")).resolve()
    manifest_path = (workspace_root / config.get("project_manifest", "workflow/configs/project_manifest.json")).resolve()
    manifest = read_json(manifest_path)
    return {
        "config_path": config_path,
        "config": config,
        "workspace_root": workspace_root,
        "manifest_path": manifest_path,
        "manifest": manifest,
    }


def build_workspace_config(project_root: Path, title: str, workspace_root: Path, chain_platform: str, discipline: str | None) -> dict[str, Any]:
    chain_label = CHAIN_LABELS[chain_platform]
    return {
        "workspace_name": slugify_name(title),
        "workspace_root": "../..",
        "project_manifest": "workflow/configs/project_manifest.json",
        "materials": {
            "material_pack_json": "docs/materials/material_pack.json",
            "material_pack_md": "docs/materials/material_pack.md",
            "code_evidence_pack_json": "docs/materials/code_evidence_pack.json",
            "code_evidence_pack_md": "docs/materials/code_evidence_pack.md",
            "code_snippets_dir": "docs/materials/code_snippets",
            "code_screenshots_dir": "docs/materials/code_screenshots",
            "source_inventory_md": "docs/materials/source_inventory.md",
            "missing_items_md": "docs/materials/missing_items.md",
            "intake_report_md": "docs/materials/intake_report.md",
        },
        "tasks": {
            "literature_plan_md": "docs/tasks/literature_plan.md",
        },
        "workflow_state": {
            "handoff_json": "docs/workflow/handoff.json",
            "handoff_md": "docs/workflow/handoff.md",
            "execution_log_md": "docs/workflow/execution_log.md",
            "workspace_lock_json": "docs/workflow/workspace.lock.json",
            "workflow_assets_state_json": "docs/workflow/workflow_assets_state.json",
        },
        "writing": {
            "project_profile_json": "docs/writing/project_profile.json",
            "project_profile_md": "docs/writing/project_profile.md",
            "thesis_outline_json": "docs/writing/thesis_outline.json",
            "thesis_outline_md": "docs/writing/thesis_outline.md",
            "literature_pack_json": "docs/writing/literature_pack.json",
            "literature_pack_md": "docs/writing/literature_pack.md",
            "reference_registry_json": "docs/writing/reference_registry.json",
            "citation_audit_md": "docs/writing/citation_audit.md",
            "research_dir": "docs/writing/research",
            "research_index_json": "docs/writing/research_index.json",
            "research_index_md": "docs/writing/research_index.md",
            "chapter_queue_json": "docs/writing/chapter_queue.json",
            "chapter_packets_dir": "docs/writing/chapter_packets",
            "chapter_briefs_dir": "docs/writing/chapter_briefs",
            "review_dir": "docs/writing/review",
            "local_skill_path": "workflow/skills/academic-paper-crafter/SKILL.md",
            "resume_skill_path": "workflow/skills/thesis-workflow-resume/SKILL.md",
            "orchestrator_skill_path": "workflow/skills/thesis-workflow-orchestrator/SKILL.md",
            "research_skill_path": "workflow/skills/paper-research-agent/SKILL.md",
            "paper_reader_skill_path": "workflow/skills/paper-reader/SKILL.md",
        },
        "scaffold": {
            "chapter_template_profile": "blockchain-fullstack",
        },
        "build": {
            "input_dir": "polished_v3",
            "diagram_dir": "docs/images",
            "output_dir": "word_output",
            "output_docx": f"{slugify_name(title)}.docx",
            "figure_log": "figure_insert_log.csv",
            "processed_image_dir": "processed_images",
            "reference_file": "REFERENCES.md",
            "abstract_cn_file": "00-摘要.md",
            "abstract_en_file": "00-Abstract.md",
            "chapter_order": list(DEFAULT_CHAPTER_ORDER),
        },
        "postprocess": {
            "final_dir": "final",
            "output_docx": f"{slugify_name(title)}_windows_final.docx",
            "figure_log": "figure_insert_log_final.csv",
        },
        "defaults": {
            "keywords_cn": DEFAULT_KEYWORDS_CN if chain_platform == "fisco" else f"{chain_label}；区块链；系统设计；系统实现；论文工作流",
            "keywords_en": DEFAULT_KEYWORDS_EN if chain_platform == "fisco" else f"{chain_label}; blockchain; system design; system implementation; thesis workflow",
        },
        "figure_map": {},
        "metadata": {
            "project_root": str(project_root.resolve()),
            "title": title,
            "discipline": discipline or "计算机类",
            "chain_platform": chain_platform,
        },
    }


def material_output_paths(config: dict[str, Any], workspace_root: Path) -> dict[str, Path]:
    materials = config.get("materials", {})
    tasks = config.get("tasks", {})
    return {
        "material_pack_json": workspace_root / materials.get("material_pack_json", "docs/materials/material_pack.json"),
        "material_pack_md": workspace_root / materials.get("material_pack_md", "docs/materials/material_pack.md"),
        "code_evidence_pack_json": workspace_root / materials.get("code_evidence_pack_json", "docs/materials/code_evidence_pack.json"),
        "code_evidence_pack_md": workspace_root / materials.get("code_evidence_pack_md", "docs/materials/code_evidence_pack.md"),
        "code_snippets_dir": workspace_root / materials.get("code_snippets_dir", "docs/materials/code_snippets"),
        "code_screenshots_dir": workspace_root / materials.get("code_screenshots_dir", "docs/materials/code_screenshots"),
        "source_inventory_md": workspace_root / materials.get("source_inventory_md", "docs/materials/source_inventory.md"),
        "missing_items_md": workspace_root / materials.get("missing_items_md", "docs/materials/missing_items.md"),
        "intake_report_md": workspace_root / materials.get("intake_report_md", "docs/materials/intake_report.md"),
        "literature_plan_md": workspace_root / tasks.get("literature_plan_md", "docs/tasks/literature_plan.md"),
    }


def workflow_state_paths(config: dict[str, Any], workspace_root: Path) -> dict[str, Path]:
    workflow_state = config.get("workflow_state", {})
    return {
        "handoff_json": workspace_root / workflow_state.get("handoff_json", "docs/workflow/handoff.json"),
        "handoff_md": workspace_root / workflow_state.get("handoff_md", "docs/workflow/handoff.md"),
        "execution_log_md": workspace_root / workflow_state.get("execution_log_md", "docs/workflow/execution_log.md"),
        "workspace_lock_json": workspace_root / workflow_state.get("workspace_lock_json", "docs/workflow/workspace.lock.json"),
        "workflow_assets_state_json": workspace_root / workflow_state.get("workflow_assets_state_json", "docs/workflow/workflow_assets_state.json"),
    }


def writing_output_paths(config: dict[str, Any], workspace_root: Path) -> dict[str, Path]:
    writing = config.get("writing", {})
    return {
        "project_profile_json": workspace_root / writing.get("project_profile_json", "docs/writing/project_profile.json"),
        "project_profile_md": workspace_root / writing.get("project_profile_md", "docs/writing/project_profile.md"),
        "thesis_outline_json": workspace_root / writing.get("thesis_outline_json", "docs/writing/thesis_outline.json"),
        "thesis_outline_md": workspace_root / writing.get("thesis_outline_md", "docs/writing/thesis_outline.md"),
        "literature_pack_json": workspace_root / writing.get("literature_pack_json", "docs/writing/literature_pack.json"),
        "literature_pack_md": workspace_root / writing.get("literature_pack_md", "docs/writing/literature_pack.md"),
        "reference_registry_json": workspace_root / writing.get("reference_registry_json", "docs/writing/reference_registry.json"),
        "citation_audit_md": workspace_root / writing.get("citation_audit_md", "docs/writing/citation_audit.md"),
        "research_dir": workspace_root / writing.get("research_dir", "docs/writing/research"),
        "research_index_json": workspace_root / writing.get("research_index_json", "docs/writing/research_index.json"),
        "research_index_md": workspace_root / writing.get("research_index_md", "docs/writing/research_index.md"),
        "chapter_queue_json": workspace_root / writing.get("chapter_queue_json", "docs/writing/chapter_queue.json"),
        "chapter_packets_dir": workspace_root / writing.get("chapter_packets_dir", "docs/writing/chapter_packets"),
        "chapter_briefs_dir": workspace_root / writing.get("chapter_briefs_dir", "docs/writing/chapter_briefs"),
        "review_dir": workspace_root / writing.get("review_dir", "docs/writing/review"),
        "local_skill_path": workspace_root / writing.get("local_skill_path", "workflow/skills/academic-paper-crafter/SKILL.md"),
        "resume_skill_path": workspace_root / writing.get("resume_skill_path", "workflow/skills/thesis-workflow-resume/SKILL.md"),
        "orchestrator_skill_path": workspace_root / writing.get("orchestrator_skill_path", "workflow/skills/thesis-workflow-orchestrator/SKILL.md"),
        "research_skill_path": workspace_root / writing.get("research_skill_path", "workflow/skills/paper-research-agent/SKILL.md"),
        "paper_reader_skill_path": workspace_root / writing.get("paper_reader_skill_path", "workflow/skills/paper-reader/SKILL.md"),
    }
