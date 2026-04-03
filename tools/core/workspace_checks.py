from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from core.ai_image_generation import ai_override_blocking_entries
from core.project_common import load_workspace_context, read_json, writing_output_paths


PACKET_SYNC_BLOCKING_STATUSES = {"stale", "legacy", "missing"}


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
    }
