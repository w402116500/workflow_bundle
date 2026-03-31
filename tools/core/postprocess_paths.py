from __future__ import annotations

from pathlib import Path

from core.build_final_thesis_docx import resolve_output_docx_path
from core.project_common import load_workspace_context


def _resolve_workspace_member(workspace_root: Path, raw_path: str | None, fallback_name: str) -> Path:
    path = Path(raw_path or fallback_name)
    if path.is_absolute():
        return path
    return workspace_root / path


def _resolve_output_member(base_dir: Path, raw_path: str | None, fallback_name: str) -> Path:
    path = Path(raw_path or fallback_name)
    if path.is_absolute():
        return path
    return base_dir / path


def resolve_postprocess_paths(config_path: Path) -> dict[str, Path]:
    ctx = load_workspace_context(config_path)
    config = ctx["config"]
    workspace_root = ctx["workspace_root"]
    build = config.get("build", {})
    postprocess = config.get("postprocess", {})

    output_dir = _resolve_workspace_member(workspace_root, build.get("output_dir"), "word_output")
    input_docx = resolve_output_docx_path(ctx["config_path"])
    input_figure_log = _resolve_output_member(output_dir, build.get("figure_log"), "figure_insert_log.csv")

    final_dir = _resolve_workspace_member(workspace_root, postprocess.get("final_dir"), "final")
    default_output_name = f"{input_docx.stem}_windows_final{input_docx.suffix}"
    default_figure_log_name = "figure_insert_log_final.csv"
    output_docx = _resolve_output_member(final_dir, postprocess.get("output_docx"), default_output_name)
    output_figure_log = _resolve_output_member(final_dir, postprocess.get("figure_log"), default_figure_log_name)
    final_summary_json = _resolve_output_member(final_dir, postprocess.get("summary_json"), "final_summary.json")
    final_runs_dir = _resolve_output_member(final_dir, postprocess.get("summary_runs_dir"), "final_runs")

    return {
        "workspace_root": workspace_root,
        "output_dir": output_dir,
        "input_docx": input_docx,
        "input_figure_log": input_figure_log,
        "final_dir": final_dir,
        "output_docx": output_docx,
        "output_figure_log": output_figure_log,
        "final_summary_json": final_summary_json,
        "final_runs_dir": final_runs_dir,
    }
