from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from core.bundle_version import bundle_version_info
from core.build_final_thesis_docx import resolve_output_docx_path
from core.postprocess_paths import resolve_postprocess_paths
from core.project_common import load_workspace_context, read_json, write_json
from core.verify_citation_links import compare_citation_superscripts, inspect_citation_links, inspect_citation_superscripts
from core.workspace_checks import run_workspace_check


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _resolve_workspace_member(workspace_root: Path, raw_path: str | None, fallback_name: str) -> Path:
    path = Path(raw_path or fallback_name)
    if path.is_absolute():
        return path
    return workspace_root / path


def _summary_output_paths(config: dict[str, Any], workspace_root: Path) -> dict[str, Path]:
    build = config.get("build", {})
    output_dir = _resolve_workspace_member(workspace_root, build.get("output_dir"), "word_output")
    build_runs_dir = output_dir / "build_runs"
    release_runs_dir = output_dir / "release_runs"
    return {
        "output_dir": output_dir,
        "figure_prepare_summary_json": output_dir / "figure_prepare_summary.json",
        "build_summary_json": output_dir / "build_summary.json",
        "build_runs_dir": build_runs_dir,
        "release_summary_json": output_dir / "release_summary.json",
        "release_runs_dir": release_runs_dir,
    }


def _path_stat(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "size_bytes": 0,
            "modified_at": "",
        }
    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
    }


def _workspace_summary(ctx: dict[str, Any]) -> dict[str, str]:
    config = ctx["config"]
    return {
        "config_path": str(ctx["config_path"]),
        "workspace_root": str(ctx["workspace_root"]),
        "title": config.get("metadata", {}).get("title") or ctx["manifest"].get("title", ""),
        "chain_platform": config.get("metadata", {}).get("chain_platform") or ctx["manifest"].get("chain_platform", ""),
    }


def _preflight_summary(preflight: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": preflight["status"],
        "packet_status_counter": preflight["packet_status_counter"],
        "packet_kind_counter": preflight["packet_kind_counter"],
        "blocking_entries": preflight["blocking_entries"],
        "figure_integration_blocking_entries": preflight.get("figure_integration_blocking_entries", []),
        "chapter5_page_screenshot_blocking_entries": preflight.get("chapter5_page_screenshot_blocking_entries", []),
        "style_warning_entries": preflight["style_warning_entries"],
        "placeholder_entries": preflight["placeholder_entries"],
    }


def _load_figure_prepare_summary(summary_path: Path) -> dict[str, Any]:
    if not summary_path.exists():
        return {}
    return read_json(summary_path)


def _run_slug(generated_at: str) -> str:
    return generated_at.replace(":", "").replace("+", "_").replace("-", "")


def _build_common_summary(ctx: dict[str, Any], docx_path: Path, preflight: dict[str, Any], figure_prepare_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": _now_iso(),
        "bundle": bundle_version_info(),
        "workspace": _workspace_summary(ctx),
        "preflight": _preflight_summary(preflight),
        "figure_prepare": figure_prepare_summary,
        "docx": _path_stat(docx_path),
    }


def run_write_build_summary(config_path: Path, docx_path: Path | None = None) -> dict[str, str]:
    ctx = load_workspace_context(config_path)
    paths = _summary_output_paths(ctx["config"], ctx["workspace_root"])
    paths["output_dir"].mkdir(parents=True, exist_ok=True)
    paths["build_runs_dir"].mkdir(parents=True, exist_ok=True)

    resolved_docx_path = docx_path.resolve() if docx_path else resolve_output_docx_path(ctx["config_path"])
    preflight = run_workspace_check(ctx["config_path"])
    figure_prepare_summary = _load_figure_prepare_summary(paths["figure_prepare_summary_json"])

    summary = _build_common_summary(ctx, resolved_docx_path, preflight, figure_prepare_summary)
    summary["citation_superscript_audit"] = inspect_citation_superscripts(resolved_docx_path)
    summary["build"] = {
        "status": 0 if summary["docx"]["exists"] else 1,
        "artifact_type": "基础排版稿",
        "verified": summary["citation_superscript_audit"].get("status") == 0,
    }

    run_slug = _run_slug(summary["generated_at"])
    build_run_path = paths["build_runs_dir"] / f"build_summary_{run_slug}.json"
    write_json(paths["build_summary_json"], summary)
    write_json(build_run_path, summary)
    return {
        "build_summary_json": str(paths["build_summary_json"]),
        "build_run_json": str(build_run_path),
    }


def run_write_release_summary(config_path: Path, docx_path: Path | None = None) -> dict[str, str]:
    ctx = load_workspace_context(config_path)
    paths = _summary_output_paths(ctx["config"], ctx["workspace_root"])
    paths["output_dir"].mkdir(parents=True, exist_ok=True)
    paths["release_runs_dir"].mkdir(parents=True, exist_ok=True)

    resolved_docx_path = docx_path.resolve() if docx_path else resolve_output_docx_path(ctx["config_path"])
    preflight = run_workspace_check(ctx["config_path"])
    citation_check = inspect_citation_links(resolved_docx_path, ctx["config_path"])
    citation_superscript_audit = inspect_citation_superscripts(resolved_docx_path)
    figure_prepare_summary = _load_figure_prepare_summary(paths["figure_prepare_summary_json"])

    summary = _build_common_summary(ctx, resolved_docx_path, preflight, figure_prepare_summary)
    summary["citation_verify"] = citation_check
    summary["citation_superscript_audit"] = citation_superscript_audit
    summary["release_verify"] = {
        "verified": citation_check.get("status") == 0 and citation_superscript_audit.get("status") == 0,
    }

    run_slug = _run_slug(summary["generated_at"])
    release_run_path = paths["release_runs_dir"] / f"release_summary_{run_slug}.json"
    write_json(paths["release_summary_json"], summary)
    write_json(release_run_path, summary)
    return {
        "release_summary_json": str(paths["release_summary_json"]),
        "release_run_json": str(release_run_path),
    }


def run_write_finalization_summary(
    config_path: Path,
    base_docx_path: Path | None = None,
    final_docx_path: Path | None = None,
    figure_log_path: Path | None = None,
) -> dict[str, str]:
    ctx = load_workspace_context(config_path)
    postprocess_paths = resolve_postprocess_paths(ctx["config_path"])
    postprocess_paths["final_dir"].mkdir(parents=True, exist_ok=True)
    postprocess_paths["final_runs_dir"].mkdir(parents=True, exist_ok=True)

    resolved_base_docx_path = base_docx_path.resolve() if base_docx_path else resolve_output_docx_path(ctx["config_path"])
    resolved_final_docx_path = final_docx_path.resolve() if final_docx_path else postprocess_paths["output_docx"]
    resolved_figure_log_path = figure_log_path.resolve() if figure_log_path else postprocess_paths["output_figure_log"]
    preflight = run_workspace_check(ctx["config_path"])
    figure_prepare_summary = _load_figure_prepare_summary(_summary_output_paths(ctx["config"], ctx["workspace_root"])["figure_prepare_summary_json"])
    base_citation_superscript_audit = inspect_citation_superscripts(resolved_base_docx_path)
    final_citation_superscript_audit = inspect_citation_superscripts(resolved_final_docx_path)
    citation_superscript_compare = compare_citation_superscripts(resolved_base_docx_path, resolved_final_docx_path)

    summary = {
        "generated_at": _now_iso(),
        "bundle": bundle_version_info(),
        "workspace": _workspace_summary(ctx),
        "preflight": _preflight_summary(preflight),
        "figure_prepare": figure_prepare_summary,
        "base_docx": _path_stat(resolved_base_docx_path),
        "final_docx": _path_stat(resolved_final_docx_path),
        "base_citation_superscript_audit": base_citation_superscript_audit,
        "final_citation_superscript_audit": final_citation_superscript_audit,
        "citation_superscript_compare": citation_superscript_compare,
        "figure_log": {
            "input": _path_stat(postprocess_paths["input_figure_log"]),
            "output": _path_stat(resolved_figure_log_path),
        },
        "finalization": {
            "status": 0 if resolved_final_docx_path.exists() else 1,
            "artifact_type": "Windows终稿",
            "platform": "windows-word",
            "verified": citation_superscript_compare.get("ok") is True,
        },
    }

    run_slug = _run_slug(summary["generated_at"])
    final_run_path = postprocess_paths["final_runs_dir"] / f"final_summary_{run_slug}.json"
    write_json(postprocess_paths["final_summary_json"], summary)
    write_json(final_run_path, summary)
    return {
        "final_summary_json": str(postprocess_paths["final_summary_json"]),
        "final_run_json": str(final_run_path),
        "citation_superscript_compare_ok": "true" if citation_superscript_compare.get("ok") is True else "false",
        "final_citation_non_superscript_count": str(final_citation_superscript_audit.get("non_superscript_count", 0)),
    }
