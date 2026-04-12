from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import Any

from core.ai_image_generation import ai_override_blocking_entries
from core.project_common import load_workspace_context, read_json, read_text_safe, writing_output_paths


PACKET_SYNC_BLOCKING_STATUSES = {"stale", "legacy", "missing"}
FIGURE_TITLE_RE = re.compile(r"^图(?P<figure_no>\d+\.\d+)\s*(?P<title>.*)$")
FIGURE_MARKER_RE = re.compile(r"<!--\s*figure:\s*(?P<figs>.+?)\s*-->")
FIGURE_PLACEHOLDER_RE = re.compile(r"^（配图占位，终稿插入图(?P<figs>.+?)）\s*$")
MARKDOWN_IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(?P<level>#+)\s+(?P<title>.+?)\s*$")


def _extract_figure_no(text: str) -> str:
    match = FIGURE_TITLE_RE.match(str(text or "").strip())
    return str(match.group("figure_no") if match else "").strip()


def _parse_figure_nos(raw: str) -> list[str]:
    return re.findall(r"\d+\.\d+", str(raw or ""))


def _resolve_workspace_member(workspace_root: Path, raw_path: str | None, fallback_name: str) -> Path:
    path = Path(raw_path or fallback_name)
    if path.is_absolute():
        return path
    return workspace_root / path


def _resolve_markdown_image_source(
    md_path: Path,
    rel_path: str,
    workspace_root: Path,
    diagram_dir: Path,
    output_dir: Path,
    processed_image_dir: Path,
) -> Path | None:
    candidate = (md_path.parent / rel_path).resolve()
    if candidate.exists():
        return candidate

    basename = Path(rel_path).name
    search_roots = [
        diagram_dir,
        workspace_root / "images",
        workspace_root / "docs",
        output_dir / "processed_images",
        processed_image_dir,
    ]

    for root in search_roots:
        direct = root / basename
        if direct.exists():
            return direct

    for root in search_roots:
        if not root.exists():
            continue
        matches = list(root.rglob(basename))
        if matches:
            return matches[0]
    return None


def _same_file(path_a: Path, path_b: Path) -> bool:
    try:
        if path_a.exists() and path_b.exists():
            return path_a.samefile(path_b)
    except Exception:
        pass
    try:
        return path_a.resolve() == path_b.resolve()
    except Exception:
        return False


def _same_file_or_bytes(path_a: Path, path_b: Path) -> bool:
    if _same_file(path_a, path_b):
        return True
    try:
        return path_a.exists() and path_b.exists() and path_a.read_bytes() == path_b.read_bytes()
    except Exception:
        return False


def _markdown_section_ranges(chapter_text: str) -> dict[str, tuple[int, int]]:
    lines = chapter_text.splitlines()
    headings: list[dict[str, Any]] = []
    for index, raw_line in enumerate(lines, start=1):
        match = HEADING_RE.match(raw_line.strip())
        if not match:
            continue
        headings.append(
            {
                "line": index,
                "level": len(match.group("level")),
                "title": str(match.group("title") or "").strip(),
            }
        )

    ranges: dict[str, tuple[int, int]] = {}
    for idx, heading in enumerate(headings):
        end_line = len(lines)
        for candidate in headings[idx + 1 :]:
            if int(candidate["level"]) <= int(heading["level"]):
                end_line = int(candidate["line"]) - 1
                break
        ranges[str(heading["title"])] = (int(heading["line"]), end_line)
    return ranges


def _chapter_markdown_image_entries(
    chapter_path: Path,
    chapter_text: str,
    workspace_root: Path,
    diagram_dir: Path,
    output_dir: Path,
    processed_image_dir: Path,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line_no, raw_line in enumerate(chapter_text.splitlines(), start=1):
        for match in MARKDOWN_IMAGE_RE.finditer(raw_line):
            rel_path = str(match.group("path") or "").strip()
            if not rel_path:
                continue
            resolved = _resolve_markdown_image_source(
                chapter_path,
                rel_path,
                workspace_root,
                diagram_dir,
                output_dir,
                processed_image_dir,
            )
            entries.append(
                {
                    "line_no": line_no,
                    "alt": str(match.group("alt") or "").strip(),
                    "rel_path": rel_path,
                    "resolved_path": str(resolved) if resolved else "",
                }
            )
    return entries


def _is_chapter5_page_screenshot_ref(rel_path: str) -> bool:
    normalized = str(rel_path or "").replace("\\", "/").strip().lower()
    if not normalized or "docs/materials/code_screenshots/" in normalized:
        return False
    basename = Path(normalized).name
    if "docs/images/chapter5/" in normalized:
        return True
    return basename.startswith("ch5-") and "/docs/images/" in normalized


def _chapter_has_required_figure_reference(
    chapter_path: Path,
    chapter_text: str,
    figure_no: str,
    expected_source_path: Path,
    workspace_root: Path,
    diagram_dir: Path,
    output_dir: Path,
    processed_image_dir: Path,
) -> tuple[bool, str, str, str]:
    lines = chapter_text.splitlines()
    caption_prefix = f"图{figure_no}"
    valid_reference_kind = ""
    mismatched_reference_path = ""
    mismatched_reference_kind = ""

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        marker = FIGURE_MARKER_RE.match(line) or FIGURE_PLACEHOLDER_RE.match(line)
        if marker and figure_no in _parse_figure_nos(marker.group("figs")):
            if not valid_reference_kind:
                valid_reference_kind = "marker"
            continue

        image_match = MARKDOWN_IMAGE_RE.search(line)
        if not image_match:
            continue

        match_kind = ""
        rel_path = image_match.group("path").strip()
        alt = image_match.group("alt").strip()
        if caption_prefix in alt:
            match_kind = "markdown-image-alt"

        if not match_kind:
            for back_index in range(index - 1, -1, -1):
                previous = lines[back_index].strip()
                if not previous:
                    continue
                if previous.startswith(caption_prefix):
                    match_kind = "markdown-image-after-caption"
                break

        if not match_kind:
            continue

        resolved = _resolve_markdown_image_source(
            chapter_path,
            rel_path,
            workspace_root,
            diagram_dir,
            output_dir,
            processed_image_dir,
        )
        if resolved is None:
            mismatched_reference_path = rel_path
            mismatched_reference_kind = f"{match_kind}-unresolved"
            continue

        if _same_file(resolved, expected_source_path):
            if not valid_reference_kind:
                valid_reference_kind = match_kind
            continue

        mismatched_reference_path = str(resolved)
        mismatched_reference_kind = match_kind

    if mismatched_reference_path:
        return False, valid_reference_kind, mismatched_reference_path, mismatched_reference_kind
    return bool(valid_reference_kind), valid_reference_kind, "", ""


def _figure_integration_blocking_entries(
    config: dict[str, Any],
    workspace_root: Path,
    writing_paths: dict[str, Path],
) -> list[dict[str, str]]:
    project_profile_path = writing_paths["project_profile_json"]
    if not project_profile_path.exists():
        return []

    project_profile = read_json(project_profile_path)
    chapter_profile = project_profile.get("chapter_profile", {})
    build = config.get("build", {}) or {}
    input_dir = workspace_root / build.get("input_dir", "polished_v3")
    diagram_dir = _resolve_workspace_member(workspace_root, build.get("diagram_dir"), "docs/images")
    output_dir = _resolve_workspace_member(workspace_root, build.get("output_dir"), "word_output")
    processed_image_dir = _resolve_workspace_member(
        output_dir,
        build.get("processed_image_dir"),
        "processed_images",
    )
    raw_figure_map = config.get("figure_map") or {}

    blocking_entries: list[dict[str, str]] = []

    for chapter_name, chapter_info in chapter_profile.items():
        required_assets = chapter_info.get("required_assets", [])
        if not required_assets:
            continue

        chapter_path = input_dir / str(chapter_name)
        chapter_text = read_text_safe(chapter_path) if chapter_path.exists() else ""

        for asset in required_assets:
            if str(asset.get("asset_type", "")) != "figures":
                continue

            title = str(asset.get("title") or asset.get("marker") or "").strip()
            figure_no = _extract_figure_no(title)
            if not figure_no:
                continue

            figure_cfg = raw_figure_map.get(figure_no)
            if not isinstance(figure_cfg, dict):
                blocking_entries.append(
                    {
                        "chapter": str(chapter_name),
                        "figure_no": figure_no,
                        "title": title,
                        "section": str(asset.get("section") or ""),
                        "figure_path": "",
                        "reference_kind": "",
                        "mismatched_reference_path": "",
                        "mismatched_reference_kind": "",
                        "issue_type": "missing-mapped-figure-asset",
                    }
                )
                continue

            raw_path = str(figure_cfg.get("path") or "").strip()
            if not raw_path:
                blocking_entries.append(
                    {
                        "chapter": str(chapter_name),
                        "figure_no": figure_no,
                        "title": title,
                        "section": str(asset.get("section") or ""),
                        "figure_path": "",
                        "reference_kind": "",
                        "mismatched_reference_path": "",
                        "mismatched_reference_kind": "",
                        "issue_type": "missing-mapped-figure-asset",
                    }
                )
                continue

            source_path = _resolve_workspace_member(workspace_root, raw_path, raw_path)
            if not source_path.exists():
                blocking_entries.append(
                    {
                        "chapter": str(chapter_name),
                        "figure_no": figure_no,
                        "title": title,
                        "section": str(asset.get("section") or ""),
                        "figure_path": str(source_path),
                        "reference_kind": "",
                        "mismatched_reference_path": "",
                        "mismatched_reference_kind": "",
                        "issue_type": "mapped-figure-asset-missing-on-disk",
                    }
                )
                continue

            has_reference, reference_kind, mismatched_reference_path, mismatched_reference_kind = _chapter_has_required_figure_reference(
                chapter_path,
                chapter_text,
                figure_no,
                source_path,
                workspace_root,
                diagram_dir,
                output_dir,
                processed_image_dir,
            )
            if has_reference:
                continue

            blocking_entries.append(
                {
                    "chapter": str(chapter_name),
                    "figure_no": figure_no,
                    "title": title,
                    "section": str(asset.get("section") or ""),
                    "figure_path": str(source_path),
                    "reference_kind": reference_kind,
                    "mismatched_reference_path": mismatched_reference_path,
                    "mismatched_reference_kind": mismatched_reference_kind,
                    "issue_type": "missing-figure-reference" if not mismatched_reference_path else "mismatched-figure-reference",
                }
            )

    return blocking_entries


def _chapter5_page_screenshot_blocking_entries(
    config: dict[str, Any],
    workspace_root: Path,
    writing_paths: dict[str, Path],
) -> list[dict[str, str]]:
    packet_json_path = writing_paths["chapter_packets_dir"] / "05-系统实现.json"
    chapter_path = workspace_root / (config.get("build", {}) or {}).get("input_dir", "polished_v3") / "05-系统实现.md"
    if not packet_json_path.exists() or not chapter_path.exists():
        return []

    packet_payload = read_json(packet_json_path)
    required_items = [
        item
        for item in packet_payload.get("asset_to_section_map", [])
        if item.get("asset_type") == "figures" and item.get("required") and str(item.get("workspace_image_path") or "").strip()
    ]
    if not required_items:
        return []

    build = config.get("build", {}) or {}
    diagram_dir = _resolve_workspace_member(workspace_root, build.get("diagram_dir"), "docs/images")
    output_dir = _resolve_workspace_member(workspace_root, build.get("output_dir"), "word_output")
    processed_image_dir = _resolve_workspace_member(output_dir, build.get("processed_image_dir"), "processed_images")
    chapter_text = read_text_safe(chapter_path)
    section_ranges = _markdown_section_ranges(chapter_text)
    image_entries = _chapter_markdown_image_entries(
        chapter_path,
        chapter_text,
        workspace_root,
        diagram_dir,
        output_dir,
        processed_image_dir,
    )
    page_image_entries = [entry for entry in image_entries if _is_chapter5_page_screenshot_ref(str(entry.get("rel_path") or ""))]

    entries_by_section: dict[str, list[dict[str, Any]]] = {}
    for entry in page_image_entries:
        line_no = int(entry.get("line_no", 0) or 0)
        matched_section = ""
        matched_start_line = -1
        for section, (start_line, end_line) in section_ranges.items():
            if start_line <= line_no <= end_line:
                if start_line >= matched_start_line:
                    matched_section = section
                    matched_start_line = start_line
        if matched_section:
            entries_by_section.setdefault(matched_section, []).append(entry)

    expected_by_section: dict[str, list[dict[str, Any]]] = {}
    expected_path_to_section: dict[str, str] = {}
    for item in required_items:
        section = str(item.get("target_section") or "").strip()
        workspace_image_path = str(item.get("workspace_image_path") or "").strip()
        if not section or not workspace_image_path:
            continue
        expected_entry = {
            "title": str(item.get("title") or "").strip(),
            "workspace_image_path": workspace_image_path,
            "expected_path": str((workspace_root / workspace_image_path).resolve()),
        }
        expected_by_section.setdefault(section, []).append(expected_entry)
        expected_path_to_section[expected_entry["expected_path"]] = section

    blocking_entries: list[dict[str, str]] = []

    for section, expected_entries in expected_by_section.items():
        section_images = entries_by_section.get(section, [])
        if section not in section_ranges:
            blocking_entries.append(
                {
                    "chapter": "05-系统实现.md",
                    "section": section,
                    "issue_type": "missing-section-heading",
                    "title": "",
                    "expected_path": "",
                    "actual_path": "",
                    "message": f"required page screenshot section heading not found: {section}",
                }
            )
            continue

        used_image_indexes: set[int] = set()
        for expected in expected_entries:
            matched_index = -1
            expected_path = Path(expected["expected_path"])
            for idx, image in enumerate(section_images):
                if idx in used_image_indexes:
                    continue
                resolved_path = str(image.get("resolved_path") or "").strip()
                if not resolved_path:
                    continue
                if _same_file_or_bytes(Path(resolved_path), expected_path):
                    matched_index = idx
                    break
            if matched_index >= 0:
                used_image_indexes.add(matched_index)
            else:
                blocking_entries.append(
                    {
                        "chapter": "05-系统实现.md",
                        "section": section,
                        "issue_type": "missing-required-page-screenshot",
                        "title": str(expected.get("title") or ""),
                        "expected_path": str(expected.get("workspace_image_path") or ""),
                        "actual_path": "",
                        "message": f"required page screenshot missing in section {section}: {expected.get('workspace_image_path', '')}",
                    }
                )

        for idx, image in enumerate(section_images):
            resolved_path = str(image.get("resolved_path") or "").strip()
            rel_path = str(image.get("rel_path") or "").strip()
            alt = str(image.get("alt") or "").strip()
            if not resolved_path:
                continue
            matched_expected_path = ""
            matched_expected_section = ""
            for expected_path, expected_section in expected_path_to_section.items():
                if _same_file_or_bytes(Path(resolved_path), Path(expected_path)):
                    matched_expected_path = expected_path
                    matched_expected_section = expected_section
                    break
            if matched_expected_section and matched_expected_section != section:
                blocking_entries.append(
                    {
                        "chapter": "05-系统实现.md",
                        "section": section,
                        "issue_type": "cross-section-page-screenshot",
                        "title": alt,
                        "expected_path": str(Path(matched_expected_path).relative_to(workspace_root)) if matched_expected_path else "",
                        "actual_path": rel_path,
                        "message": f"page screenshot {rel_path} is assigned to {matched_expected_section} but is used in {section}",
                    }
                )
            elif (
                not matched_expected_section
                and ("representative" in rel_path.lower() or "代表性页面截图" in alt)
            ):
                blocking_entries.append(
                    {
                        "chapter": "05-系统实现.md",
                        "section": section,
                        "issue_type": "stale-representative-page-screenshot",
                        "title": alt,
                        "expected_path": "",
                        "actual_path": rel_path,
                        "message": f"stale representative page screenshot remains in {section}: {rel_path}",
                    }
                )

    return blocking_entries


def _status_line(ok: bool, label: str, value: str) -> str:
    return f"[{'PASS' if ok else 'WARN'}] {label}: {value}"


def _summarize_counter(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return ", ".join(f"{key}={counter[key]}" for key in sorted(counter))


def run_workspace_check(config_path: Path) -> dict[str, Any]:
    from core.runtime_state import get_workspace_lock_status, workflow_signature_status

    ctx = load_workspace_context(config_path)
    cfg_path = ctx["config_path"]
    config = ctx["config"]
    workspace_root = ctx["workspace_root"]
    build = config.get("build", {})
    writing_paths = writing_output_paths(config, workspace_root)

    checks = {
        "config": cfg_path,
        "workspace_root": workspace_root,
        "input_dir": workspace_root / build.get("input_dir", "polished_v3"),
        "diagram_dir": workspace_root / build.get("diagram_dir", "docs/images"),
        "output_dir": workspace_root / build.get("output_dir", "word_output"),
        "project_manifest": ctx["manifest_path"],
        "chapter_queue_json": writing_paths["chapter_queue_json"],
        "orchestrator_skill": writing_paths["orchestrator_skill_path"],
        "resume_skill": writing_paths["resume_skill_path"],
    }
    signature = workflow_signature_status(cfg_path)
    lock_status = get_workspace_lock_status(cfg_path)

    lines: list[str] = []
    status = 0
    for label, path in checks.items():
        exists = path.exists()
        lines.append(_status_line(exists, label, str(path)))
        if label in {"config", "workspace_root", "input_dir", "chapter_queue_json"} and not exists:
            status = 1

    packet_status_counter: Counter[str] = Counter()
    packet_kind_counter: Counter[str] = Counter()
    blocking_entries: list[dict[str, str]] = []
    style_warning_entries: list[dict[str, Any]] = []
    placeholder_entries: list[dict[str, Any]] = []
    style_subject_entries: list[dict[str, Any]] = []
    style_source_entries: list[dict[str, Any]] = []
    style_repository_entries: list[dict[str, Any]] = []
    style_leadin_entries: list[dict[str, Any]] = []
    style_opening_entries: list[dict[str, Any]] = []
    style_summary_entries: list[dict[str, Any]] = []
    citation_order_entries: list[dict[str, Any]] = []
    citation_reuse_entries: list[dict[str, Any]] = []
    citation_sentence_entries: list[dict[str, Any]] = []
    ai_figure_blocking_entries = ai_override_blocking_entries(cfg_path)
    figure_integration_blocking_entries = _figure_integration_blocking_entries(config, workspace_root, writing_paths)
    chapter5_page_screenshot_blocking_entries = _chapter5_page_screenshot_blocking_entries(config, workspace_root, writing_paths)

    if checks["chapter_queue_json"].exists():
        queue = read_json(checks["chapter_queue_json"])
        for entry in queue.get("chapters", []):
            chapter = str(entry.get("chapter", ""))
            if chapter == build.get("reference_file", "REFERENCES.md"):
                continue
            packet_status = str(entry.get("packet_outline_status") or "missing")
            packet_kind = str(entry.get("packet_kind") or "missing")
            packet_status_counter[packet_status] += 1
            packet_kind_counter[packet_kind] += 1
            if packet_status in PACKET_SYNC_BLOCKING_STATUSES:
                blocking_entries.append(
                    {
                        "chapter": chapter,
                        "packet_outline_status": packet_status,
                        "packet_kind": packet_kind,
                    }
                )
            style_issue_count = int(entry.get("style_issue_count", 0) or 0)
            placeholder_count = int(entry.get("placeholder_count", 0) or 0)
            style_preferred_subject_warning_count = int(entry.get("style_preferred_subject_warning_count", 0) or 0)
            style_source_narration_warning_count = int(entry.get("style_source_narration_warning_count", 0) or 0)
            style_repository_voice_warning_count = int(entry.get("style_repository_voice_warning_count", 0) or 0)
            style_weak_leadin_warning_count = int(entry.get("style_weak_leadin_warning_count", 0) or 0)
            style_opening_rhythm_warning_count = int(entry.get("style_opening_rhythm_warning_count", 0) or 0)
            style_summary_recap_warning_count = int(entry.get("style_summary_recap_warning_count", 0) or 0)
            citation_order_ok = entry.get("citation_order_ok")
            citation_order_warning_count = int(entry.get("citation_order_warning_count", 0) or 0)
            citation_reuse_warning_count = int(entry.get("citation_reuse_warning_count", 0) or 0)
            citation_sentence_warning_count = int(entry.get("citation_sentence_warning_count", 0) or 0)
            if style_issue_count > 0:
                style_warning_entries.append({"chapter": chapter, "style_issue_count": style_issue_count})
            if placeholder_count > 0:
                placeholder_entries.append({"chapter": chapter, "placeholder_count": placeholder_count})
            if style_preferred_subject_warning_count > 0:
                style_subject_entries.append(
                    {"chapter": chapter, "style_preferred_subject_warning_count": style_preferred_subject_warning_count}
                )
            if style_source_narration_warning_count > 0:
                style_source_entries.append(
                    {"chapter": chapter, "style_source_narration_warning_count": style_source_narration_warning_count}
                )
            if style_repository_voice_warning_count > 0:
                style_repository_entries.append(
                    {"chapter": chapter, "style_repository_voice_warning_count": style_repository_voice_warning_count}
                )
            if style_weak_leadin_warning_count > 0:
                style_leadin_entries.append(
                    {"chapter": chapter, "style_weak_leadin_warning_count": style_weak_leadin_warning_count}
                )
            if style_opening_rhythm_warning_count > 0:
                style_opening_entries.append(
                    {"chapter": chapter, "style_opening_rhythm_warning_count": style_opening_rhythm_warning_count}
                )
            if style_summary_recap_warning_count > 0:
                style_summary_entries.append(
                    {"chapter": chapter, "style_summary_recap_warning_count": style_summary_recap_warning_count}
                )
            if citation_order_ok is False or citation_order_warning_count > 0:
                citation_order_entries.append(
                    {"chapter": chapter, "citation_order_warning_count": citation_order_warning_count}
                )
            if citation_reuse_warning_count > 0:
                citation_reuse_entries.append(
                    {"chapter": chapter, "citation_reuse_warning_count": citation_reuse_warning_count}
                )
            if citation_sentence_warning_count > 0:
                citation_sentence_entries.append(
                    {"chapter": chapter, "citation_sentence_warning_count": citation_sentence_warning_count}
                )

    lines.extend(
        [
            "",
            "Source of truth:",
            f"  thesis: {checks['input_dir']}",
            f"  generated: {checks['output_dir']}",
            "",
            "Workflow runtime:",
            f"  workflow_signature_status: {signature['status']}",
            f"  current_bundle_signature: {signature['current_signature']}",
            f"  recorded_bundle_signature: {signature['recorded_signature'] or 'none'}",
            f"  workflow_assets_state: {signature['assets_state_path']}",
            f"  workflow_assets_synced_at: {signature['synced_at'] or 'unknown'}",
            f"  lock_status: {lock_status['state']}",
            f"  lock_holder: {lock_status['holder'] or 'none'}",
            f"  orchestrator_skill: {checks['orchestrator_skill']}",
            f"  resume_skill: {checks['resume_skill']}",
            "",
            "Packet sync summary:",
            f"  packet_outline_status: {_summarize_counter(packet_status_counter)}",
            f"  packet_kind: {_summarize_counter(packet_kind_counter)}",
        ]
    )

    if blocking_entries:
        status = 1
        lines.extend(["", "Blocking packet sync issues:"])
        for entry in blocking_entries:
            lines.append(
                f"  - {entry['chapter']}: packet_outline_status={entry['packet_outline_status']}, packet_kind={entry['packet_kind']}"
            )
    else:
        lines.extend(["", "Blocking packet sync issues:", "  - none"])

    if ai_figure_blocking_entries:
        status = 1
        lines.extend(["", "Blocking AI figure override issues:"])
        for entry in ai_figure_blocking_entries:
            lines.append(f"  - 图{entry['figure_no']}: missing prepared asset at {entry['expected_path']}")
    else:
        lines.extend(["", "Blocking AI figure override issues:", "  - none"])

    if figure_integration_blocking_entries:
        status = 1
        lines.extend(["", "Blocking figure integration issues:"])
        for entry in figure_integration_blocking_entries:
            section = f", section={entry['section']}" if entry.get("section") else ""
            mismatch_path = str(entry.get("mismatched_reference_path") or "").strip()
            mismatch_kind = str(entry.get("mismatched_reference_kind") or "").strip()
            issue_type = str(entry.get("issue_type") or "").strip()
            if issue_type == "missing-mapped-figure-asset":
                lines.append(
                    f"  - {entry['chapter']}: 图{entry['figure_no']} ({entry['title']}) is required but no mapped figure asset is present{section}"
                )
            elif issue_type == "mapped-figure-asset-missing-on-disk":
                lines.append(
                    f"  - {entry['chapter']}: 图{entry['figure_no']} ({entry['title']}) maps to a missing file{section}; figure_path={entry['figure_path']}"
                )
            elif mismatch_path:
                if mismatch_kind.endswith("-unresolved"):
                    lines.append(
                        f"  - {entry['chapter']}: 图{entry['figure_no']} ({entry['title']}) has markdown image reference {mismatch_path} but it does not resolve to the mapped asset{section}; figure_path={entry['figure_path']}"
                    )
                else:
                    lines.append(
                        f"  - {entry['chapter']}: 图{entry['figure_no']} ({entry['title']}) uses markdown image {mismatch_path} instead of the mapped asset{section}; figure_path={entry['figure_path']}"
                    )
            else:
                lines.append(
                    f"  - {entry['chapter']}: 图{entry['figure_no']} ({entry['title']}) has mapped asset but no figure marker or markdown image reference{section}; figure_path={entry['figure_path']}"
                )
    else:
        lines.extend(["", "Blocking figure integration issues:", "  - none"])

    if chapter5_page_screenshot_blocking_entries:
        status = 1
        lines.extend(["", "Blocking chapter 5 page screenshot issues:"])
        for entry in chapter5_page_screenshot_blocking_entries:
            issue_type = str(entry.get("issue_type") or "").strip()
            if issue_type == "missing-required-page-screenshot":
                lines.append(
                    f"  - {entry['chapter']}: section={entry['section']} missing required page screenshot {entry['expected_path']}"
                )
            elif issue_type == "cross-section-page-screenshot":
                lines.append(
                    f"  - {entry['chapter']}: section={entry['section']} uses page screenshot {entry['actual_path']} assigned to another section (expected asset: {entry['expected_path']})"
                )
            elif issue_type == "stale-representative-page-screenshot":
                lines.append(
                    f"  - {entry['chapter']}: section={entry['section']} still contains stale representative screenshot {entry['actual_path']}"
                )
            else:
                lines.append(f"  - {entry['chapter']}: {entry.get('message', 'chapter 5 page screenshot mismatch')}")
    else:
        lines.extend(["", "Blocking chapter 5 page screenshot issues:", "  - none"])

    lines.extend(["", "Review warning summary:"])
    if style_warning_entries:
        lines.append("  style_issue_count:")
        for entry in style_warning_entries:
            lines.append(f"    - {entry['chapter']}: {entry['style_issue_count']}")
    else:
        lines.append("  style_issue_count: none")
    if placeholder_entries:
        lines.append("  placeholder_count:")
        for entry in placeholder_entries:
            lines.append(f"    - {entry['chapter']}: {entry['placeholder_count']}")
    else:
        lines.append("  placeholder_count: none")
    if style_subject_entries:
        lines.append("  style_preferred_subject_warning_count:")
        for entry in style_subject_entries:
            lines.append(f"    - {entry['chapter']}: {entry['style_preferred_subject_warning_count']}")
    else:
        lines.append("  style_preferred_subject_warning_count: none")
    if style_source_entries:
        lines.append("  style_source_narration_warning_count:")
        for entry in style_source_entries:
            lines.append(f"    - {entry['chapter']}: {entry['style_source_narration_warning_count']}")
    else:
        lines.append("  style_source_narration_warning_count: none")
    if style_repository_entries:
        lines.append("  style_repository_voice_warning_count:")
        for entry in style_repository_entries:
            lines.append(f"    - {entry['chapter']}: {entry['style_repository_voice_warning_count']}")
    else:
        lines.append("  style_repository_voice_warning_count: none")
    if style_leadin_entries:
        lines.append("  style_weak_leadin_warning_count:")
        for entry in style_leadin_entries:
            lines.append(f"    - {entry['chapter']}: {entry['style_weak_leadin_warning_count']}")
    else:
        lines.append("  style_weak_leadin_warning_count: none")
    if style_opening_entries:
        lines.append("  style_opening_rhythm_warning_count:")
        for entry in style_opening_entries:
            lines.append(f"    - {entry['chapter']}: {entry['style_opening_rhythm_warning_count']}")
    else:
        lines.append("  style_opening_rhythm_warning_count: none")
    if style_summary_entries:
        lines.append("  style_summary_recap_warning_count:")
        for entry in style_summary_entries:
            lines.append(f"    - {entry['chapter']}: {entry['style_summary_recap_warning_count']}")
    else:
        lines.append("  style_summary_recap_warning_count: none")
    if citation_order_entries:
        lines.append("  citation_order_warning_count:")
        for entry in citation_order_entries:
            lines.append(f"    - {entry['chapter']}: {entry['citation_order_warning_count']}")
    else:
        lines.append("  citation_order_warning_count: none")
    if citation_reuse_entries:
        lines.append("  citation_reuse_warning_count:")
        for entry in citation_reuse_entries:
            lines.append(f"    - {entry['chapter']}: {entry['citation_reuse_warning_count']}")
    else:
        lines.append("  citation_reuse_warning_count: none")
    if citation_sentence_entries:
        lines.append("  citation_sentence_warning_count:")
        for entry in citation_sentence_entries:
            lines.append(f"    - {entry['chapter']}: {entry['citation_sentence_warning_count']}")
    else:
        lines.append("  citation_sentence_warning_count: none")

    return {
        "status": status,
        "lines": lines,
        "blocking_entries": blocking_entries,
        "workflow_signature_status": signature["status"],
        "workflow_assets_state_path": signature["assets_state_path"],
        "workflow_assets_synced_at": signature["synced_at"],
        "lock_status": lock_status["state"],
        "packet_status_counter": dict(packet_status_counter),
        "packet_kind_counter": dict(packet_kind_counter),
        "style_warning_entries": style_warning_entries,
        "placeholder_entries": placeholder_entries,
        "style_subject_entries": style_subject_entries,
        "style_source_entries": style_source_entries,
        "style_repository_entries": style_repository_entries,
        "style_leadin_entries": style_leadin_entries,
        "style_opening_entries": style_opening_entries,
        "style_summary_entries": style_summary_entries,
        "citation_order_entries": citation_order_entries,
        "citation_reuse_entries": citation_reuse_entries,
        "citation_sentence_entries": citation_sentence_entries,
        "ai_figure_blocking_entries": ai_figure_blocking_entries,
        "figure_integration_blocking_entries": figure_integration_blocking_entries,
        "chapter5_page_screenshot_blocking_entries": chapter5_page_screenshot_blocking_entries,
    }
