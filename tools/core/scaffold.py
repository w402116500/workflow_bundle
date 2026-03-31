from __future__ import annotations

from pathlib import Path
from typing import Any

from core.chapter_profile import build_project_profile, render_project_profile_md
from core.project_common import (
    CHAIN_LABELS,
    CHAPTER_BLUEPRINT,
    load_workspace_context,
    material_output_paths,
    read_json,
    write_json,
    write_text,
    writing_output_paths,
)


def _should_initialize_chapter(path: Path) -> bool:
    if not path.exists():
        return True
    if not path.is_file():
        return False
    return not path.read_text(encoding="utf-8").strip()


def _build_summary_hint(section_names: list[str], material_pack: dict[str, Any]) -> list[str]:
    hints: list[str] = []
    for section_name in section_names:
        section = material_pack["sections"].get(section_name, {})
        for item in section.get("summary", [])[:2]:
            hints.append(item)
    return hints


def _render_section_tree(
    filename: str,
    sections: list[dict[str, Any]],
    default_material_sections: list[str],
    literature_plan_rel: str,
    level: int = 2,
) -> list[str]:
    lines: list[str] = []
    for section in sections:
        material_sections = section.get("material_sections") or default_material_sections
        lines.extend(
            [
                f"{'#' * level} {section['title']}",
                "",
                f"- 材料来源：{', '.join(material_sections) if material_sections else 'none'}",
                "- 待补：将材料包中的 summary 与 evidence 转换为论文叙述，并保留证据可追溯性。",
            ]
        )
        if filename == "01-绪论.md" and "研究现状" in section["title"]:
            lines.append(f"- 待补：结合 `{literature_plan_rel}` 与 reference registry 补充研究现状。")
        lines.append("")
        lines.extend(_render_section_tree(filename, section.get("children", []), default_material_sections, literature_plan_rel, level + 1))
    return lines


def _render_chapter(filename: str, chapter_info: dict[str, Any], material_pack: dict[str, Any], literature_plan_rel: str) -> str:
    chain_label = CHAIN_LABELS.get(material_pack["metadata"]["chain_platform"], material_pack["metadata"]["chain_platform"])
    if filename == "00-摘要.md":
        return "（根据材料包补充中文摘要正文）\n\n关键词：" + chain_label + "；区块链；系统设计；系统实现；论文工作流\n"
    if filename == "00-Abstract.md":
        return "(Fill the English abstract based on the material pack.)\n\nKey words: blockchain; thesis workflow; system design; system implementation\n"
    if filename == "REFERENCES.md":
        return "[1] 待根据 docs/tasks/literature_plan.md 与 reference registry 补充正式参考文献。\n"

    title = chapter_info["title"]
    material_sections = chapter_info.get("material_sections", [])
    hints = _build_summary_hint(material_sections, material_pack)
    lines = [
        f"# {title}",
        "",
        "> 本文件由 scaffold 自动生成，用于承接后续章节写作。",
        f"> 章节结构来源：{chapter_info.get('structure_source', 'static')}",
        f"> 材料映射：{', '.join(material_sections) if material_sections else 'none'}",
    ]
    required_assets = chapter_info.get("required_assets", [])
    if required_assets:
        lines.append(f"> 必需资产：{', '.join(asset['title'] for asset in required_assets)}")
        lines.append(f"> 占位策略：{chapter_info.get('placeholder_policy', {}).get('mode', 'optional')}")
    if filename == "01-绪论.md":
        lines.append(f"> 文献任务：优先补齐 `{literature_plan_rel}` 与 reference registry。")
    lines.extend(["", "写作提示："])
    lines.extend([f"- {hint}" for hint in hints] or ["- 结合 material_pack.json 中对应 section 的 summary 与 evidence 补写正文。"])
    lines.append("")
    lines.extend(_render_section_tree(filename, chapter_info.get("sections", []), material_sections, literature_plan_rel))
    return "\n".join(lines) + "\n"


def _render_literature_plan(title: str, chain_platform: str) -> str:
    chain_label = CHAIN_LABELS.get(chain_platform, chain_platform)
    return "\n".join(
        [
            "# Literature Plan",
            "",
            "## Search Keywords",
            "",
            f"- 中文：{title}",
            f"- 中文：{chain_label} 系统设计 与 实现",
            f"- 中文：{chain_label} 区块链 应用",
            f"- English: {chain_label} system design and implementation",
            f"- English: {chain_label} blockchain application",
            "",
            "## Tasks",
            "",
            "- 收集近 5 年相关论文与应用案例。",
            "- 区分系统设计类、访问控制类、数据存证类、审计追溯类文献。",
            "- 形成研究现状对比表，补入 01-绪论.md。",
            "- 将筛选后的正式参考文献补入 REFERENCES.md。",
            "",
        ]
    )


def run_scaffold(config_path: Path) -> dict[str, Any]:
    ctx = load_workspace_context(config_path)
    workspace_root = ctx["workspace_root"]
    config = ctx["config"]
    manifest = ctx["manifest"]
    material_paths = material_output_paths(config, workspace_root)
    writing_paths = writing_output_paths(config, workspace_root)
    material_pack = read_json(material_paths["material_pack_json"])

    project_profile = build_project_profile(manifest, material_pack)
    write_json(writing_paths["project_profile_json"], project_profile)
    write_text(writing_paths["project_profile_md"], render_project_profile_md(project_profile))

    polished_dir = workspace_root / config.get("build", {}).get("input_dir", "polished_v3")
    polished_dir.mkdir(parents=True, exist_ok=True)
    literature_plan_rel = material_paths["literature_plan_md"].relative_to(workspace_root)
    chapter_profile = project_profile.get("chapter_profile", {})
    initialized_chapters: list[str] = []
    skipped_existing_chapters: list[str] = []

    for filename, title, _ in CHAPTER_BLUEPRINT:
        chapter_info = chapter_profile.get(
            filename,
            {
                "title": title,
                "sections": [],
                "material_sections": [],
                "structure_source": "static-fallback",
            },
        )
        chapter_path = polished_dir / filename
        if _should_initialize_chapter(chapter_path):
            write_text(chapter_path, _render_chapter(filename, chapter_info, material_pack, str(literature_plan_rel)))
            initialized_chapters.append(filename)
        else:
            skipped_existing_chapters.append(filename)

    write_text(material_paths["literature_plan_md"], _render_literature_plan(manifest["title"], manifest["chain_platform"]))
    return {
        "polished_dir": polished_dir,
        "literature_plan": material_paths["literature_plan_md"],
        "project_profile_json": writing_paths["project_profile_json"],
        "project_profile_md": writing_paths["project_profile_md"],
        "initialized_chapters": initialized_chapters,
        "skipped_existing_chapters": skipped_existing_chapters,
    }
