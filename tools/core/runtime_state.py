from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from core.project_common import (
    WRITING_ORDER,
    load_workspace_context,
    material_output_paths,
    read_json,
    read_text_safe,
    workflow_state_paths,
    write_json,
    write_text,
    writing_output_paths,
)


THIS_ROOT = Path(__file__).resolve().parents[2]
if THIS_ROOT.name == "workflow_bundle":
    REPO_ROOT = THIS_ROOT.parent
    PRIMARY_WORKFLOW_ROOT = THIS_ROOT
else:
    REPO_ROOT = THIS_ROOT
    PRIMARY_WORKFLOW_ROOT = REPO_ROOT / "workflow_bundle" if (REPO_ROOT / "workflow_bundle").exists() else REPO_ROOT

ACTIVE_WORKSPACE_POINTER_PATH = PRIMARY_WORKFLOW_ROOT / "workflow" / "configs" / "active_workspace.json"
LOCK_TTL_HOURS = 2
MANAGED_WORKFLOW_DOCS = [
    "05-draft-polished-alignment.md",
    "06-ai-prompt-guide.md",
    "07-current-project-execution-checklist.md",
    "08-dual-platform-release.md",
    "CHAPTER_EXECUTION.md",
    "MIGRATION.md",
    "THESIS_WORKFLOW.md",
    "WORKSPACE_SPEC.md",
    "references/command-map.md",
]
MANAGED_WORKFLOW_SKILLS = [
    "academic-paper-crafter",
    "thesis-workflow-resume",
    "thesis-workflow-orchestrator",
    "paper-research-agent",
    "paper-reader",
]


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _resolve_input_path(raw_path: str | None, root: Path, fallback: str) -> Path:
    path = Path(raw_path or fallback)
    if path.is_absolute():
        return path
    return root / path


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _path_stat(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "modified_at": "",
            "size_bytes": 0,
        }
    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
        "size_bytes": stat.st_size,
    }


def _bundle_cli_path() -> Path:
    return PRIMARY_WORKFLOW_ROOT / "tools" / "cli.py"


def _render_workspace_workflow_readme(ctx: dict[str, Any]) -> str:
    cli_path = _bundle_cli_path()
    config_path = ctx["config_path"]
    lines = [
        "# Thesis Workspace Workflow",
        "",
        f"- title: {ctx['config'].get('metadata', {}).get('title') or ctx['manifest'].get('title', '')}",
        f"- workspace_root: `{ctx['workspace_root']}`",
        f"- workspace_config: `{config_path}`",
        f"- bundle_root: `{PRIMARY_WORKFLOW_ROOT}`",
        "",
        "Cold-start commands:",
        f"- `python3 {cli_path} resume --config {config_path}`",
        f"- `python3 {cli_path} sync-workflow-assets --config {config_path}`",
        f"- `python3 {cli_path} lock-status --config {config_path}`",
        "",
        "Recommended release commands:",
        f"- `python3 {cli_path} release-preflight --config {config_path}`",
        f"- `python3 {cli_path} release-build --config {config_path}`",
        f"- `python3 {cli_path} release-verify --config {config_path}`",
        "",
        "Source of truth:",
        "- thesis: `polished_v3/`",
        "- workflow state: `docs/workflow/` and `docs/writing/`",
        "- generated artifacts: `word_output/` and `final/`",
        "",
        "Managed local workflow assets:",
        "- `workflow/README.md`",
        "- `workflow/06-ai-prompt-guide.md`",
        "- `workflow/*.md` execution docs",
        "- `workflow/references/command-map.md`",
        "- `workflow/skills/*`",
        "",
        "When `workflow_signature_status` is `drifted`, sync the local workflow assets before trusting old workspace docs or skills.",
        "",
    ]
    return "\n".join(lines)


def _managed_workflow_doc_targets(workspace_root: Path) -> list[Path]:
    return [workspace_root / "workflow" / relative for relative in MANAGED_WORKFLOW_DOCS]


def _managed_workflow_skill_targets(workspace_root: Path) -> list[Path]:
    return [workspace_root / "workflow" / "skills" / name for name in MANAGED_WORKFLOW_SKILLS]


def sync_workspace_workflow_assets(config_path: Path | None = None) -> dict[str, Any]:
    resolved_config = resolve_default_config_path(config_path)
    ctx = load_workspace_context(resolved_config)
    workspace_root = ctx["workspace_root"]
    state_paths = workflow_state_paths(ctx["config"], workspace_root)
    workflow_root = workspace_root / "workflow"
    workflow_root.mkdir(parents=True, exist_ok=True)

    synced_items: list[str] = []

    readme_path = workflow_root / "README.md"
    write_text(readme_path, _render_workspace_workflow_readme(ctx))
    synced_items.append(str(readme_path.relative_to(workspace_root)))

    source_workflow_root = PRIMARY_WORKFLOW_ROOT / "workflow"
    for relative in MANAGED_WORKFLOW_DOCS:
        source_path = source_workflow_root / relative
        target_path = workflow_root / relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        write_text(target_path, read_text_safe(source_path))
        synced_items.append(str(target_path.relative_to(workspace_root)))

    for skill_name in MANAGED_WORKFLOW_SKILLS:
        source_dir = source_workflow_root / "skills" / skill_name
        target_dir = workflow_root / "skills" / skill_name
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(source_dir, target_dir)
        synced_items.append(str(target_dir.relative_to(workspace_root)))

    bundle_signature = compute_bundle_signature()
    state_payload = {
        "synced_at": _now_iso(),
        "bundle_signature": bundle_signature,
        "source_bundle_root": str(PRIMARY_WORKFLOW_ROOT),
        "synced_items": synced_items,
    }
    write_json(state_paths["workflow_assets_state_json"], state_payload)

    return {
        "config_path": str(resolved_config),
        "workspace_root": str(workspace_root),
        "workflow_readme": str(readme_path),
        "workflow_assets_state_json": str(state_paths["workflow_assets_state_json"]),
        "bundle_signature": bundle_signature,
        "synced_at": state_payload["synced_at"],
        "synced_items": synced_items,
        "synced_doc_count": len(MANAGED_WORKFLOW_DOCS) + 1,
        "synced_skill_count": len(MANAGED_WORKFLOW_SKILLS),
    }


def compute_bundle_signature() -> str:
    hasher = hashlib.sha1()
    scan_roots = [
        PRIMARY_WORKFLOW_ROOT / "workflow",
        PRIMARY_WORKFLOW_ROOT / "tools",
        PRIMARY_WORKFLOW_ROOT / "paper-research-agent",
        PRIMARY_WORKFLOW_ROOT / "paper-reader",
    ]
    for root in scan_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            relative = path.relative_to(PRIMARY_WORKFLOW_ROOT)
            stat = path.stat()
            hasher.update(str(relative).encode("utf-8"))
            hasher.update(str(stat.st_size).encode("utf-8"))
            hasher.update(str(int(stat.st_mtime)).encode("utf-8"))
    return hasher.hexdigest()[:12]


def resolve_default_config_path(config_path: Path | None = None) -> Path:
    if config_path:
        return Path(config_path).resolve()

    if not ACTIVE_WORKSPACE_POINTER_PATH.exists():
        raise FileNotFoundError(
            "No active workspace configured. Run `python3 workflow_bundle/tools/cli.py set-active-workspace --config <workspace.json>` first."
        )

    pointer = read_json(ACTIVE_WORKSPACE_POINTER_PATH)
    raw_path = str(pointer.get("config_path") or "").strip()
    if not raw_path:
        raise FileNotFoundError(
            f"Active workspace pointer is invalid: {ACTIVE_WORKSPACE_POINTER_PATH}"
        )

    resolved = Path(raw_path)
    if not resolved.is_absolute():
        resolved = (REPO_ROOT / resolved).resolve()

    if not resolved.exists():
        raise FileNotFoundError(
            f"Active workspace config does not exist: {resolved}"
        )
    return resolved


def read_active_workspace_pointer() -> dict[str, Any]:
    if not ACTIVE_WORKSPACE_POINTER_PATH.exists():
        return {}
    return read_json(ACTIVE_WORKSPACE_POINTER_PATH)


def set_active_workspace(config_path: Path) -> dict[str, str]:
    resolved_config = resolve_default_config_path(config_path)
    ctx = load_workspace_context(resolved_config)
    payload = {
        "updated_at": _now_iso(),
        "config_path": str(ctx["config_path"]),
        "workspace_root": str(ctx["workspace_root"]),
        "title": ctx["config"].get("metadata", {}).get("title") or ctx["manifest"].get("title", ""),
        "chain_platform": ctx["config"].get("metadata", {}).get("chain_platform") or ctx["manifest"].get("chain_platform", ""),
        "workspace_name": ctx["config"].get("workspace_name", ""),
    }
    write_json(ACTIVE_WORKSPACE_POINTER_PATH, payload)
    return {
        "active_workspace_json": str(ACTIVE_WORKSPACE_POINTER_PATH),
        "config_path": str(ctx["config_path"]),
        "workspace_root": str(ctx["workspace_root"]),
    }


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return read_json(path)


def _signature_status(recorded_signature: str, current_signature: str) -> str:
    return "current" if recorded_signature and recorded_signature == current_signature else "drifted"


def workflow_signature_status(config_path: Path | None = None) -> dict[str, Any]:
    resolved_config = resolve_default_config_path(config_path)
    ctx = load_workspace_context(resolved_config)
    state_paths = workflow_state_paths(ctx["config"], ctx["workspace_root"])
    workflow_assets_state = _read_optional_json(state_paths["workflow_assets_state_json"])
    recorded_signature = str(workflow_assets_state.get("bundle_signature", "") or "")
    current_signature = compute_bundle_signature()
    synced_items = [str(item) for item in workflow_assets_state.get("synced_items", []) if str(item).strip()]
    missing_items = [item for item in synced_items if not (ctx["workspace_root"] / item).exists()]
    status = _signature_status(recorded_signature, current_signature)
    if missing_items:
        status = "drifted"
    return {
        "status": status,
        "current_signature": current_signature,
        "recorded_signature": recorded_signature,
        "assets_state_path": str(state_paths["workflow_assets_state_json"]),
        "synced_at": str(workflow_assets_state.get("synced_at", "") or ""),
        "missing_items": missing_items,
    }


def _read_lock_record(lock_path: Path) -> dict[str, Any]:
    if not lock_path.exists():
        return {}
    return read_json(lock_path)


def get_workspace_lock_status(config_path: Path | None = None) -> dict[str, Any]:
    resolved_config = resolve_default_config_path(config_path)
    ctx = load_workspace_context(resolved_config)
    state_paths = workflow_state_paths(ctx["config"], ctx["workspace_root"])
    lock_path = state_paths["workspace_lock_json"]
    record = _read_lock_record(lock_path)
    now = datetime.now().astimezone()
    expires_at = _parse_iso(str(record.get("expires_at") or ""))
    state = "unlocked"
    if record:
        state = "expired" if expires_at and expires_at < now else "active"
    holder = ""
    if record:
        holder = f"{record.get('owner', 'unknown')}@{record.get('hostname', 'unknown')} pid={record.get('pid', 'unknown')}"
    return {
        "state": state,
        "path": str(lock_path),
        "owner": str(record.get("owner", "") or ""),
        "hostname": str(record.get("hostname", "") or ""),
        "pid": int(record.get("pid", 0) or 0),
        "command": str(record.get("command", "") or ""),
        "created_at": str(record.get("created_at", "") or ""),
        "expires_at": str(record.get("expires_at", "") or ""),
        "holder": holder,
        "record": record,
    }


def acquire_workspace_lock(config_path: Path | None, command: str, owner: str | None = None, ttl_hours: int = LOCK_TTL_HOURS) -> dict[str, Any]:
    resolved_config = resolve_default_config_path(config_path)
    ctx = load_workspace_context(resolved_config)
    state_paths = workflow_state_paths(ctx["config"], ctx["workspace_root"])
    current_status = get_workspace_lock_status(resolved_config)
    current_record = current_status.get("record", {})
    current_pid = os.getpid()
    current_host = socket.gethostname()

    if current_status["state"] == "active":
        same_process = current_status["pid"] == current_pid and current_status["hostname"] == current_host
        if not same_process:
            append_workspace_execution_log(
                resolved_config,
                "lock-conflict",
                {
                    "attempted_command": command,
                    "lock_state": current_status["state"],
                    "lock_holder": current_status["holder"],
                    "lock_path": current_status["path"],
                },
            )
            raise RuntimeError(
                f"workspace is locked by {current_status['holder']} for `{current_record.get('command', '')}`; "
                f"use `python3 workflow_bundle/tools/cli.py lock-status --config {resolved_config}` to inspect or "
                f"`python3 workflow_bundle/tools/cli.py clear-lock --config {resolved_config} --force` after confirming it is stale."
            )

    now = datetime.now().astimezone()
    payload = {
        "owner": owner or os.environ.get("USER", "unknown"),
        "hostname": current_host,
        "pid": current_pid,
        "command": command,
        "created_at": now.isoformat(timespec="seconds"),
        "expires_at": now.replace(microsecond=0).isoformat(timespec="seconds"),
    }
    expires_at = now.timestamp() + ttl_hours * 3600
    payload["expires_at"] = datetime.fromtimestamp(expires_at, tz=now.tzinfo).isoformat(timespec="seconds")
    write_json(state_paths["workspace_lock_json"], payload)
    append_workspace_execution_log(
        resolved_config,
        "lock-acquired",
        {
            "command": command,
            "lock_path": str(state_paths["workspace_lock_json"]),
            "expires_at": payload["expires_at"],
        },
    )
    return {
        "lock_path": str(state_paths["workspace_lock_json"]),
        "state": "active",
        "holder": f"{payload['owner']}@{payload['hostname']} pid={payload['pid']}",
        "expires_at": payload["expires_at"],
    }


def release_workspace_lock(config_path: Path | None, command: str, force: bool = False) -> dict[str, Any]:
    resolved_config = resolve_default_config_path(config_path)
    ctx = load_workspace_context(resolved_config)
    state_paths = workflow_state_paths(ctx["config"], ctx["workspace_root"])
    lock_path = state_paths["workspace_lock_json"]
    current_status = get_workspace_lock_status(resolved_config)
    if current_status["state"] == "unlocked":
        return {"lock_path": str(lock_path), "state": "unlocked"}

    same_process = current_status["pid"] == os.getpid() and current_status["hostname"] == socket.gethostname()
    if current_status["state"] == "active" and not same_process and not force:
        raise RuntimeError(
            f"workspace lock is held by {current_status['holder']}; use --force only after confirming that lock is stale."
        )

    if lock_path.exists():
        lock_path.unlink()
    append_workspace_execution_log(
        resolved_config,
        "lock-released",
        {
            "command": command,
            "lock_path": str(lock_path),
            "release_mode": "force" if force else "normal",
        },
    )
    return {"lock_path": str(lock_path), "state": "unlocked"}


def _latest_modified_at(paths: list[Path]) -> str:
    timestamps = [datetime.fromtimestamp(path.stat().st_mtime).astimezone() for path in paths if path.exists()]
    if not timestamps:
        return ""
    return max(timestamps).isoformat(timespec="seconds")


def _source_of_truth_paths(config: dict[str, Any], workspace_root: Path, writing_paths: dict[str, Path]) -> list[Path]:
    build = config.get("build", {})
    input_dir = _resolve_input_path(build.get("input_dir"), workspace_root, "polished_v3")
    chapter_order = list(build.get("chapter_order") or [])
    candidates = [writing_paths["chapter_queue_json"], writing_paths["citation_audit_md"]]
    for chapter in chapter_order:
        candidates.append(input_dir / chapter)
    return [path for path in candidates if path.exists()]


def _summary_paths(config: dict[str, Any], workspace_root: Path) -> dict[str, Path]:
    build = config.get("build", {})
    postprocess = config.get("postprocess", {})
    output_dir = _resolve_input_path(build.get("output_dir"), workspace_root, "word_output")
    final_dir = _resolve_input_path(postprocess.get("final_dir"), workspace_root, "final")
    return {
        "build_summary_json": output_dir / "build_summary.json",
        "release_summary_json": output_dir / "release_summary.json",
        "figure_prepare_summary_json": output_dir / "figure_prepare_summary.json",
        "final_summary_json": final_dir / "final_summary.json",
    }


def _chapter_status_summary(queue: dict[str, Any]) -> dict[str, Any]:
    chapters = queue.get("chapters", [])
    status_counter: Counter[str] = Counter()
    for entry in chapters:
        status_counter[str(entry.get("status") or "unknown")] += 1
    return {
        "total": len(chapters),
        "status_counter": dict(status_counter),
        "chapters": [
            {
                "chapter": entry.get("chapter", ""),
                "title": entry.get("title", ""),
                "status": entry.get("status", ""),
                "mode": entry.get("mode", ""),
                "packet_outline_status": entry.get("packet_outline_status", ""),
                "brief_md": entry.get("brief_md", ""),
                "target_path": entry.get("target_path", ""),
            }
            for entry in chapters
        ],
    }


def _next_chapter_action(queue: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    chapters_by_name = {str(entry.get("chapter")): entry for entry in queue.get("chapters", [])}

    if preflight.get("blocking_entries"):
        blocking = preflight["blocking_entries"][0]
        chapter = str(blocking.get("chapter", ""))
        return {
            "stage": "packet-sync-blocked",
            "reason": f"{chapter} packet_outline_status={blocking.get('packet_outline_status', 'unknown')}",
            "commands": [
                f"python3 workflow_bundle/tools/cli.py prepare-chapter --config {queue.get('config_path', '<workspace.json>')} --chapter {chapter}"
            ]
            if chapter
            else [f"python3 workflow_bundle/tools/cli.py prepare-writing --config {queue.get('config_path', '<workspace.json>')}"],
            "chapter": chapter,
        }

    for chapter_name in WRITING_ORDER:
        entry = chapters_by_name.get(chapter_name)
        if not entry:
            continue
        status = str(entry.get("status") or "")
        if status in {"reviewed", "managed"}:
            continue
        config_path = queue.get("config_path", "<workspace.json>")
        chapter = str(entry.get("chapter", ""))
        if status == "pending":
            return {
                "stage": "chapter-preparation",
                "reason": f"{chapter} is still pending",
                "commands": [
                    f"python3 workflow_bundle/tools/cli.py start-chapter --config {config_path} --chapter {chapter}"
                ],
                "chapter": chapter,
            }
        if status == "prepared":
            return {
                "stage": "chapter-drafting",
                "reason": f"{chapter} is prepared and waiting for draft",
                "commands": [
                    f"python3 workflow_bundle/tools/cli.py resume --config {config_path}",
                    f"python3 workflow_bundle/tools/cli.py finalize-chapter --config {config_path} --chapter {chapter} --status drafted",
                ],
                "chapter": chapter,
            }
        if status == "drafted":
            return {
                "stage": "chapter-polish",
                "reason": f"{chapter} needs academic-paper-crafter polish",
                "commands": [
                    f"python3 workflow_bundle/tools/cli.py finalize-chapter --config {config_path} --chapter {chapter} --status polished"
                ],
                "chapter": chapter,
            }
        if status == "polished":
            return {
                "stage": "chapter-review",
                "reason": f"{chapter} is polished and waiting for reviewed status",
                "commands": [
                    f"python3 workflow_bundle/tools/cli.py finalize-chapter --config {config_path} --chapter {chapter} --status reviewed"
                ],
                "chapter": chapter,
            }
        if status == "manual_pending":
            return {
                "stage": "manual-chapter",
                "reason": f"{chapter} must be completed manually",
                "commands": [
                    f"python3 workflow_bundle/tools/cli.py finalize-chapter --config {config_path} --chapter {chapter} --status reviewed"
                ],
                "chapter": chapter,
            }

    return {
        "stage": "chapters-reviewed",
        "reason": "all chapters are reviewed or managed",
        "commands": [],
        "chapter": "",
    }


def _release_action(config_path: Path, config: dict[str, Any], workspace_root: Path, writing_paths: dict[str, Path]) -> dict[str, Any]:
    paths = _summary_paths(config, workspace_root)
    release_summary = _read_optional_json(paths["release_summary_json"])
    final_summary = _read_optional_json(paths["final_summary_json"])
    latest_source_at = _latest_modified_at(_source_of_truth_paths(config, workspace_root, writing_paths))
    release_generated_at = release_summary.get("generated_at", "")
    release_dt = _parse_iso(release_generated_at)
    source_dt = _parse_iso(latest_source_at)
    release_fresh = bool(release_dt and source_dt and release_dt >= source_dt)

    if not release_summary or not release_fresh:
        return {
            "stage": "content-reviewed",
            "reason": "linux release artifact is missing or older than the latest source-of-truth files",
            "commands": [
                f"python3 workflow_bundle/tools/cli.py release-build --config {config_path}",
                f"python3 workflow_bundle/tools/cli.py release-verify --config {config_path}",
            ],
            "latest_source_at": latest_source_at,
            "release_generated_at": release_generated_at,
            "release_fresh": release_fresh,
        }

    if not final_summary:
        return {
            "stage": "linux-release-ready",
            "reason": "linux delivery artifact is current; windows finalization is optional and not yet completed",
            "commands": [],
            "latest_source_at": latest_source_at,
            "release_generated_at": release_generated_at,
            "release_fresh": release_fresh,
        }

    return {
        "stage": "windows-finalized",
        "reason": "linux release and windows finalization summaries both exist",
        "commands": [],
        "latest_source_at": latest_source_at,
        "release_generated_at": release_generated_at,
        "release_fresh": release_fresh,
    }


def _classify_phase(ctx: dict[str, Any], preflight: dict[str, Any], queue: dict[str, Any], writing_paths: dict[str, Path], material_paths: dict[str, Path]) -> dict[str, Any]:
    config_path = ctx["config_path"]
    workspace_root = ctx["workspace_root"]

    if not material_paths["code_evidence_pack_json"].exists():
        return {
            "phase": "workspace-initialized",
            "reason": "code evidence pack is missing",
            "commands": [f"python3 workflow_bundle/tools/cli.py extract-code --config {config_path}"],
            "files_to_read": [str(material_paths["intake_report_md"])],
        }

    if not material_paths["material_pack_json"].exists():
        return {
            "phase": "workspace-initialized",
            "reason": "material pack is missing",
            "commands": [f"python3 workflow_bundle/tools/cli.py extract --config {config_path}"],
            "files_to_read": [str(material_paths["intake_report_md"])],
        }

    if not writing_paths["project_profile_json"].exists():
        return {
            "phase": "materials-prepared",
            "reason": "project profile is missing",
            "commands": [f"python3 workflow_bundle/tools/cli.py scaffold --config {config_path}"],
            "files_to_read": [str(material_paths["material_pack_md"])],
        }

    if not writing_paths["literature_pack_json"].exists() or not writing_paths["reference_registry_json"].exists():
        return {
            "phase": "materials-prepared",
            "reason": "literature pack or reference registry is missing",
            "commands": [f"python3 workflow_bundle/tools/cli.py literature --config {config_path}"],
            "files_to_read": [str(writing_paths["project_profile_md"])],
        }

    if not writing_paths["thesis_outline_json"].exists():
        return {
            "phase": "materials-prepared",
            "reason": "thesis outline is missing",
            "commands": [f"python3 workflow_bundle/tools/cli.py prepare-outline --config {config_path}"],
            "files_to_read": [str(writing_paths["project_profile_md"])],
        }

    if not writing_paths["chapter_queue_json"].exists():
        return {
            "phase": "materials-prepared",
            "reason": "chapter queue is missing",
            "commands": [f"python3 workflow_bundle/tools/cli.py prepare-writing --config {config_path}"],
            "files_to_read": [str(writing_paths["thesis_outline_md"])],
        }

    chapter_action = _next_chapter_action(queue, preflight)
    if chapter_action["stage"] != "chapters-reviewed":
        nonterminal_entries = [
            entry
            for entry in queue.get("chapters", [])
            if str(entry.get("status") or "") not in {"reviewed", "managed"}
        ]
        reviewed_exists = any(str(entry.get("status") or "") == "reviewed" for entry in queue.get("chapters", []))
        started = reviewed_exists or any(str(entry.get("status") or "") != "pending" for entry in nonterminal_entries)
        files_to_read = [str(writing_paths["thesis_outline_md"]), str(writing_paths["chapter_queue_json"])]
        chapter_name = chapter_action.get("chapter", "")
        if chapter_name:
            entry = next((item for item in queue.get("chapters", []) if item.get("chapter") == chapter_name), {})
            brief_md = entry.get("brief_md")
            if brief_md:
                files_to_read.append(str(workspace_root / brief_md))
            if entry.get("literature_required") and writing_paths["research_index_md"].exists():
                files_to_read.append(str(writing_paths["research_index_md"]))
            if writing_paths["citation_audit_md"].exists():
                files_to_read.append(str(writing_paths["citation_audit_md"]))
        return {
            "phase": "chapter-in-progress" if started else "writing-prepared",
            "reason": chapter_action["reason"],
            "commands": chapter_action["commands"],
            "files_to_read": files_to_read,
            "chapter": chapter_name,
        }

    release_action = _release_action(config_path, ctx["config"], workspace_root, writing_paths)
    files_to_read = [str(writing_paths["chapter_queue_json"])]
    summary_paths = _summary_paths(ctx["config"], workspace_root)
    if summary_paths["build_summary_json"].exists():
        files_to_read.append(str(summary_paths["build_summary_json"]))
    if summary_paths["release_summary_json"].exists():
        files_to_read.append(str(summary_paths["release_summary_json"]))
    if summary_paths["final_summary_json"].exists():
        files_to_read.append(str(summary_paths["final_summary_json"]))
    return {
        "phase": release_action["stage"],
        "reason": release_action["reason"],
        "commands": release_action["commands"],
        "files_to_read": files_to_read,
    }


def _render_handoff_md(handoff: dict[str, Any]) -> str:
    lines = [
        "# Workflow Handoff",
        "",
        f"- generated_at: {handoff['generated_at']}",
        f"- workspace_title: {handoff['workspace']['title']}",
        f"- config_path: `{handoff['workspace']['config_path']}`",
        f"- workspace_root: `{handoff['workspace']['workspace_root']}`",
        f"- chain_platform: `{handoff['workspace']['chain_platform']}`",
        f"- active_workspace_match: `{handoff['active_workspace']['matches_current']}`",
        f"- bundle_signature: `{handoff['bundle']['signature']}`",
        f"- recorded_bundle_signature: `{handoff['bundle']['recorded_signature'] or 'none'}`",
        f"- workflow_signature_status: `{handoff['bundle']['signature_status']}`",
        f"- lock_status: `{handoff['lock']['state']}`",
        f"- phase: `{handoff['phase']['name']}`",
        f"- phase_reason: {handoff['phase']['reason']}",
        "",
        "## Next Commands",
        "",
    ]
    if handoff["next_commands"]:
        lines.extend([f"- `{command}`" for command in handoff["next_commands"]])
    else:
        lines.append("- none")
    lines.extend(["", "## Read First", ""])
    lines.extend([f"- `{path}`" for path in handoff["read_first"]] or ["- none"])
    lines.extend(
        [
            "",
            "## Skills",
            "",
            f"- orchestrator: `{handoff['skills']['orchestrator_skill_path']}`",
            f"- resume: `{handoff['skills']['resume_skill_path']}`",
            f"- local_polish: `{handoff['skills']['local_skill_path']}`",
            f"- research: `{handoff['skills']['research_skill_path']}`",
            f"- paper_reader: `{handoff['skills']['paper_reader_skill_path']}`",
            "",
            "## Source Of Truth",
            "",
            f"- thesis: `{handoff['source_of_truth']['thesis']}`",
            f"- materials: `{handoff['source_of_truth']['materials']}`",
            f"- writing_state: `{handoff['source_of_truth']['chapter_queue']}`",
            f"- workflow_assets_state: `{handoff['source_of_truth']['workflow_assets_state']}`",
            f"- linux_release: `{handoff['source_of_truth']['release_summary']}`",
            f"- windows_final: `{handoff['source_of_truth']['final_summary']}`",
            "",
            "## Runtime Status",
            "",
            f"- lock_path: `{handoff['lock']['path']}`",
            f"- lock_holder: `{handoff['lock']['holder'] or 'none'}`",
            f"- workflow_assets_synced_at: `{handoff['bundle']['synced_at'] or 'unknown'}`",
            f"- workflow_assets_state_path: `{handoff['bundle']['assets_state_path']}`",
            "",
            "## Chapter Status",
            "",
        ]
    )
    for key, value in sorted(handoff["chapter_status"]["status_counter"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Blocking Issues", ""])
    if handoff["blocking_issues"]:
        for entry in handoff["blocking_issues"]:
            lines.append(
                f"- {entry.get('chapter', '')}: packet_outline_status={entry.get('packet_outline_status', '')}, packet_kind={entry.get('packet_kind', '')}"
            )
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def build_workspace_snapshot(
    config_path: Path | None = None,
    trigger: str = "manual",
    command: str = "",
    persist_signature: bool = False,
) -> dict[str, Any]:
    resolved_config = resolve_default_config_path(config_path)
    ctx = load_workspace_context(resolved_config)
    config = ctx["config"]
    workspace_root = ctx["workspace_root"]
    state_paths = workflow_state_paths(config, workspace_root)
    writing_paths = writing_output_paths(config, workspace_root)
    material_paths = material_output_paths(config, workspace_root)
    summary_paths = _summary_paths(config, workspace_root)
    active_pointer = read_active_workspace_pointer()
    signature = workflow_signature_status(resolved_config)
    lock_status = get_workspace_lock_status(resolved_config)
    from core.workspace_checks import run_workspace_check

    preflight = run_workspace_check(resolved_config)
    queue = _read_optional_json(writing_paths["chapter_queue_json"])
    queue["config_path"] = str(resolved_config)
    phase = _classify_phase(ctx, preflight, queue, writing_paths, material_paths)
    source_input_dir = _resolve_input_path(config.get("build", {}).get("input_dir"), workspace_root, "polished_v3")
    next_commands = list(phase.get("commands", []))
    read_first = list(dict.fromkeys(phase.get("files_to_read", [])))
    if signature["status"] != "current":
        sync_command = f"python3 workflow_bundle/tools/cli.py sync-workflow-assets --config {resolved_config}"
        next_commands = [sync_command, *[command for command in next_commands if command != sync_command]]
        read_first = list(
            dict.fromkeys(
                [
                    str(workspace_root / "workflow" / "README.md"),
                    signature["assets_state_path"],
                    *read_first,
                ]
            )
        )
    return {
        "generated_at": _now_iso(),
        "trigger": trigger,
        "command": command,
        "workspace": {
            "config_path": str(resolved_config),
            "workspace_root": str(workspace_root),
            "workspace_name": config.get("workspace_name", ""),
            "title": config.get("metadata", {}).get("title") or ctx["manifest"].get("title", ""),
            "chain_platform": config.get("metadata", {}).get("chain_platform") or ctx["manifest"].get("chain_platform", ""),
            "project_root": config.get("metadata", {}).get("project_root") or ctx["manifest"].get("project_root", ""),
        },
        "active_workspace": {
            "pointer_path": str(ACTIVE_WORKSPACE_POINTER_PATH),
            "config_path": active_pointer.get("config_path", ""),
            "matches_current": active_pointer.get("config_path", "") == str(resolved_config),
        },
        "bundle": {
            "root": str(PRIMARY_WORKFLOW_ROOT),
            "signature": signature["current_signature"],
            "recorded_signature": signature["recorded_signature"],
            "signature_status": signature["status"],
            "assets_state_path": signature["assets_state_path"],
            "synced_at": signature["synced_at"],
            "missing_items": signature["missing_items"],
        },
        "lock": lock_status,
        "phase": {
            "name": phase["phase"],
            "reason": phase["reason"],
        },
        "next_commands": next_commands,
        "read_first": read_first,
        "skills": {
            "orchestrator_skill_path": str(writing_paths["orchestrator_skill_path"]),
            "resume_skill_path": str(writing_paths["resume_skill_path"]),
            "local_skill_path": str(writing_paths["local_skill_path"]),
            "research_skill_path": str(writing_paths["research_skill_path"]),
            "paper_reader_skill_path": str(writing_paths["paper_reader_skill_path"]),
        },
        "source_of_truth": {
            "thesis": str(source_input_dir),
            "materials": str(material_paths["material_pack_json"]),
            "chapter_queue": str(writing_paths["chapter_queue_json"]),
            "citation_audit": str(writing_paths["citation_audit_md"]),
            "workflow_assets_state": str(state_paths["workflow_assets_state_json"]),
            "handoff_json": str(state_paths["handoff_json"]),
            "handoff_md": str(state_paths["handoff_md"]),
            "release_summary": str(summary_paths["release_summary_json"]),
            "final_summary": str(summary_paths["final_summary_json"]),
        },
        "chapter_status": _chapter_status_summary(queue),
        "preflight": {
            "status": preflight["status"],
            "packet_status_counter": preflight["packet_status_counter"],
            "packet_kind_counter": preflight["packet_kind_counter"],
        },
        "blocking_issues": preflight.get("blocking_entries", []),
        "style_warnings": {
            "style": preflight.get("style_warning_entries", []),
            "placeholder": preflight.get("placeholder_entries", []),
            "citation_order": preflight.get("citation_order_entries", []),
            "citation_reuse": preflight.get("citation_reuse_entries", []),
            "citation_sentence": preflight.get("citation_sentence_entries", []),
        },
        "artifacts": {
            "build_summary": _path_stat(summary_paths["build_summary_json"]),
            "release_summary": _path_stat(summary_paths["release_summary_json"]),
            "final_summary": _path_stat(summary_paths["final_summary_json"]),
            "figure_prepare_summary": _path_stat(summary_paths["figure_prepare_summary_json"]),
        },
        "constraints": [
            "polished_v3 is the only thesis source of truth",
            "read chapter_briefs before chapter_packets",
            "sync workflow assets when workflow_signature_status is drifted",
            "do not continue chapter writing when packet_outline_status is stale/legacy/missing",
            "chapter 5 must consume code_evidence_pack, inline code snippets, and staged page screenshots when available",
            "drafted chapters must be polished with academic-paper-crafter before reviewed status",
        ],
    }


def refresh_workspace_handoff(config_path: Path | None = None, trigger: str = "manual", command: str = "") -> dict[str, str]:
    resolved_config = resolve_default_config_path(config_path)
    ctx = load_workspace_context(resolved_config)
    state_paths = workflow_state_paths(ctx["config"], ctx["workspace_root"])
    handoff = build_workspace_snapshot(resolved_config, trigger=trigger, command=command, persist_signature=True)
    write_json(state_paths["handoff_json"], handoff)
    write_text(state_paths["handoff_md"], _render_handoff_md(handoff))
    return {
        "config_path": str(resolved_config),
        "handoff_json": str(state_paths["handoff_json"]),
        "handoff_md": str(state_paths["handoff_md"]),
        "phase": handoff["phase"]["name"],
        "workflow_signature_status": handoff["bundle"]["signature_status"],
        "lock_status": handoff["lock"]["state"],
    }


def append_workspace_execution_log(config_path: Path | None, command: str, details: dict[str, Any] | None = None) -> dict[str, str]:
    resolved_config = resolve_default_config_path(config_path)
    ctx = load_workspace_context(resolved_config)
    state_paths = workflow_state_paths(ctx["config"], ctx["workspace_root"])
    log_path = state_paths["execution_log_md"]
    if log_path.exists():
        content = read_text_safe(log_path)
    else:
        content = "# Workspace Execution Log\n\n"

    lines = [
        f"## {_now_iso()}",
        "",
        f"- command: `{command}`",
        f"- config: `{resolved_config}`",
    ]
    if details:
        for key in sorted(details):
            value = details[key]
            if value is None or value == "" or value == [] or value == {}:
                continue
            if isinstance(value, (dict, list)):
                rendered = json.dumps(value, ensure_ascii=False)
            else:
                rendered = str(value)
            lines.append(f"- {key}: `{rendered}`")
    lines.extend(["", ""])
    write_text(log_path, content + "\n".join(lines))
    return {"execution_log_md": str(log_path)}


def build_resume_lines(config_path: Path | None = None) -> tuple[list[str], dict[str, Any]]:
    handoff = build_workspace_snapshot(config_path, trigger="resume", command="resume", persist_signature=False)
    lines = [
        f"active_workspace: {handoff['workspace']['title']}",
        f"config_path: {handoff['workspace']['config_path']}",
        f"workspace_root: {handoff['workspace']['workspace_root']}",
        f"phase: {handoff['phase']['name']}",
        f"phase_reason: {handoff['phase']['reason']}",
        f"orchestrator_skill_path: {handoff['skills']['orchestrator_skill_path']}",
        f"resume_skill_path: {handoff['skills']['resume_skill_path']}",
        f"workflow_signature_status: {handoff['bundle']['signature_status']}",
        f"lock_status: {handoff['lock']['state']}",
        f"handoff_json: {handoff['source_of_truth']['handoff_json']}",
        f"handoff_md: {handoff['source_of_truth']['handoff_md']}",
        "",
        "next_commands:",
    ]
    if handoff["next_commands"]:
        lines.extend([f"  - {command}" for command in handoff["next_commands"]])
    else:
        lines.append("  - none")
    lines.extend(["", "read_first:"])
    if handoff["read_first"]:
        lines.extend([f"  - {path}" for path in handoff["read_first"]])
    else:
        lines.append("  - none")
    lines.extend(["", "blocking_issues:"])
    if handoff["blocking_issues"]:
        for entry in handoff["blocking_issues"]:
            lines.append(
                f"  - {entry.get('chapter', '')}: packet_outline_status={entry.get('packet_outline_status', '')}, packet_kind={entry.get('packet_kind', '')}"
            )
    else:
        lines.append("  - none")
    if handoff["lock"]["state"] != "unlocked":
        lines.extend(["", "lock_detail:", f"  - holder: {handoff['lock']['holder'] or 'unknown'}", f"  - command: {handoff['lock']['command'] or 'unknown'}"])
    return lines, handoff
