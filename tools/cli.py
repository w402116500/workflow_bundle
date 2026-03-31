from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from core.build_final_thesis_docx import main as build_main, resolve_output_docx_path
from core.code_evidence import run_extract_code
from core.extract import run_extract
from core.figure_assets import run_prepare_figures
from core.intake import run_intake
from core.postprocess_paths import resolve_postprocess_paths
from core.release_summary import run_write_build_summary, run_write_finalization_summary, run_write_release_summary
from core.runtime_state import (
    ACTIVE_WORKSPACE_POINTER_PATH,
    acquire_workspace_lock,
    append_workspace_execution_log,
    build_workspace_snapshot,
    build_resume_lines,
    get_workspace_lock_status,
    read_active_workspace_pointer,
    release_workspace_lock,
    refresh_workspace_handoff,
    resolve_default_config_path,
    set_active_workspace,
    sync_workspace_workflow_assets,
)
from core.scaffold import run_scaffold
from core.verify_citation_links import verify_citation_links
from core.workspace_checks import run_workspace_check
from core.writing import (
    run_finalize_chapter,
    run_literature,
    run_normalize_citations,
    run_prepare_chapter,
    run_prepare_outline,
    run_prepare_writing,
    run_start_chapter,
)


def _resolve_config_arg(config: Path | None) -> Path:
    return resolve_default_config_path(config)


def _resolve_verify_target(target: str | None) -> Path:
    if not target:
        return resolve_output_docx_path(_resolve_config_arg(None))

    path = Path(target)
    if path.suffix.lower() == ".json":
        return resolve_output_docx_path(_resolve_config_arg(path))
    return path


def _resolve_postprocess_targets(args: argparse.Namespace) -> tuple[Path | None, Path, Path, str, str]:
    config_path: Path | None = None
    if args.config or (not args.input_docx and not args.output_docx):
        config_path = _resolve_config_arg(args.config)
        paths = resolve_postprocess_paths(config_path)
        input_docx = Path(args.input_docx) if args.input_docx else paths["input_docx"]
        output_docx = Path(args.output_docx) if args.output_docx else paths["output_docx"]
        figlog = args.figlog or str(paths["input_figure_log"])
        figlog_out = args.figlog_out or str(paths["output_figure_log"])
        return config_path, input_docx, output_docx, figlog, figlog_out

    if not args.input_docx or not args.output_docx:
        raise ValueError("postprocess requires either --config or both input_docx and output_docx")
    return None, Path(args.input_docx), Path(args.output_docx), args.figlog, args.figlog_out


def _example_base_dir() -> Path:
    local_examples = Path(__file__).resolve().parent / "examples" / "health_record"
    if local_examples.exists():
        return local_examples

    repo_root = Path(__file__).resolve().parents[1]
    if repo_root.name == "workflow_bundle":
        fallback = repo_root.parent / "tools" / "examples" / "health_record"
        if fallback.exists():
            return fallback
    raise FileNotFoundError("bundled example assets are unavailable in this checkout")


def _run_example(example: str, command: str) -> int:
    if example != "health_record":
        print(f"unsupported example: {example}", file=sys.stderr)
        return 2

    base_dir = _example_base_dir()

    if command == "generate-diagrams":
        sys.path.insert(0, str(base_dir.parent.parent))
        from examples.health_record.generate_thesis_diagrams import main as generate_diagrams_main

        generate_diagrams_main()
        return 0

    if command == "generate-skeleton":
        script_path = base_dir / "generate_thesis_skeleton.js"
        completed = subprocess.run(["node", str(script_path)], cwd=script_path.parent, check=False)
        return completed.returncode

    print(f"unsupported example command: {command}", file=sys.stderr)
    return 2


def _coerce_detail_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [str(item) if isinstance(item, Path) else item for item in value[:8]]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if isinstance(item, (str, int, float, bool)) or item is None:
                result[key] = item
            elif isinstance(item, Path):
                result[key] = str(item)
        return result
    return value


def _record_workspace_state(config_path: Path | None, command: str, details: dict[str, Any] | None = None, log: bool = True) -> dict[str, str]:
    handoff = refresh_workspace_handoff(config_path, trigger="cli", command=command)
    if log:
        merged: dict[str, Any] = dict(details or {})
        merged.update(handoff)
        append_workspace_execution_log(config_path, command, {key: _coerce_detail_value(value) for key, value in merged.items()})
    return handoff


def _log_readonly_command(config_path: Path | None, command: str, details: dict[str, Any] | None = None) -> None:
    append_workspace_execution_log(config_path, command, {key: _coerce_detail_value(value) for key, value in (details or {}).items()})


def _run_with_workspace_lock(
    config_path: Path | None,
    command: str,
    action: Callable[[], Any],
) -> Any:
    acquire_workspace_lock(config_path, command)
    try:
        return action()
    finally:
        release_workspace_lock(config_path, command)


def _workflow_scripts_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "workflow" / "scripts"


def _run_bundle_sync_check() -> int:
    script_path = _workflow_scripts_dir() / "check_bundle_sync.sh"
    completed = subprocess.run(["bash", str(script_path)], check=False)
    return int(completed.returncode)


def _resolve_release_config_input(config_option: Path | None, config_arg: str | None) -> Path:
    if config_option and config_arg:
        option_path = _resolve_config_arg(config_option)
        arg_path = _resolve_config_arg(Path(config_arg))
        if option_path != arg_path:
            raise ValueError(f"release command received conflicting config paths: {option_path} != {arg_path}")
        return option_path
    if config_option:
        return _resolve_config_arg(config_option)
    if config_arg:
        return _resolve_config_arg(Path(config_arg))
    return _resolve_config_arg(None)


def _run_workspace_check_command(config_path: Path, command_name: str) -> int:
    result = run_workspace_check(config_path)
    snapshot = build_workspace_snapshot(config_path, trigger=command_name, command=command_name, persist_signature=False)
    _log_readonly_command(
        config_path,
        command_name,
        {
            "status": result["status"],
            "workflow_signature_status": snapshot["bundle"]["signature_status"],
            "lock_status": snapshot["lock"]["state"],
        },
    )
    for line in result["lines"]:
        print(line)
    return int(result["status"])


def _run_release_preflight_command(config_path: Path, command_name: str) -> int:
    sync_status = _run_bundle_sync_check()
    if sync_status != 0:
        return sync_status
    return _run_workspace_check_command(config_path, command_name)


def _build_release_build_args(config_path: Path, output_name: str | None = None) -> list[str]:
    build_args: list[str] = ["--config", str(config_path)]
    if output_name:
        build_args.extend(["--output-name", output_name])
    return build_args


def _print_prepare_figures_result(result: dict[str, Any]) -> None:
    print(f"config_path: {result['config_path']}")
    print(f"diagram_dir: {result['diagram_dir']}")
    print(f"generated_figures: {len(result['generated_figures'])}")
    for item in result["generated_figures"]:
        print(f"{item['figure_no']} [{item.get('status', 'rendered')}]: {item['path']}")


def _run_release_build_flow(config_path: Path, output_name: str | None, command_name: str) -> dict[str, Any]:
    def _action() -> dict[str, Any]:
        figure_result = run_prepare_figures(config_path)
        build_main(_build_release_build_args(config_path, output_name))
        return {
            "config_path": str(config_path),
            "diagram_dir": str(figure_result["diagram_dir"]),
            "generated_figures": figure_result["generated_figures"],
            "docx_path": resolve_output_docx_path(config_path, output_name),
            "output_name": output_name or "",
        }

    return _run_with_workspace_lock(config_path, command_name, _action)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified thesis tools CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build thesis DOCX from a workspace config.")
    build_parser.add_argument("--config", type=Path)
    build_parser.add_argument("--output-name")
    build_parser.add_argument("--print-output-path", action="store_true")

    intake_parser = subparsers.add_parser("intake", help="Generate a thesis workspace from a local project path.")
    intake_parser.add_argument("--project-root", type=Path, required=True)
    intake_parser.add_argument("--title", required=True)
    intake_parser.add_argument("--out", type=Path, required=True)
    intake_parser.add_argument("--discipline", default="计算机类")
    intake_parser.add_argument("--chain", choices=["auto", "fisco", "fabric"], default="auto")

    set_active_parser = subparsers.add_parser("set-active-workspace", help="Set the active workspace pointer used by no-argument workflow commands.")
    set_active_parser.add_argument("--config", type=Path, required=True)

    resolve_active_parser = subparsers.add_parser("resolve-active-workspace", help="Resolve the active workspace config path.")
    resolve_active_parser.add_argument("--print-path", action="store_true")

    refresh_handoff_parser = subparsers.add_parser("refresh-handoff", help="Refresh the workspace handoff artifacts.")
    refresh_handoff_parser.add_argument("--config", type=Path)

    resume_parser = subparsers.add_parser("resume", help="Summarize the current workspace state and recommended next step.")
    resume_parser.add_argument("--config", type=Path)
    resume_parser.add_argument("--json", action="store_true")

    lock_status_parser = subparsers.add_parser("lock-status", help="Inspect the workspace lock state.")
    lock_status_parser.add_argument("--config", type=Path)
    lock_status_parser.add_argument("--json", action="store_true")

    clear_lock_parser = subparsers.add_parser("clear-lock", help="Clear a workspace lock after confirming it is stale.")
    clear_lock_parser.add_argument("--config", type=Path)
    clear_lock_parser.add_argument("--force", action="store_true")

    sync_assets_parser = subparsers.add_parser("sync-workflow-assets", help="Sync workspace-local workflow docs and skills from the current bundle.")
    sync_assets_parser.add_argument("--config", type=Path)

    extract_parser = subparsers.add_parser("extract", help="Extract a structured material pack from a workspace config.")
    extract_parser.add_argument("--config", type=Path)

    extract_code_parser = subparsers.add_parser("extract-code", help="Extract code evidence snippets and white-background screenshots from a workspace config.")
    extract_code_parser.add_argument("--config", type=Path)

    prepare_figures_parser = subparsers.add_parser("prepare-figures", help="Generate project-specific figure assets and update figure_map for a workspace.")
    prepare_figures_parser.add_argument("--config", type=Path)

    scaffold_parser = subparsers.add_parser("scaffold", help="Generate chapter skeletons and literature tasks from a workspace config.")
    scaffold_parser.add_argument("--config", type=Path)

    literature_parser = subparsers.add_parser("literature", help="Generate literature pack and reference registry for a workspace.")
    literature_parser.add_argument("--config", type=Path)
    literature_parser.add_argument("--min-refs", type=int, default=15)
    literature_parser.add_argument("--max-refs", type=int, default=18)

    prepare_outline_parser = subparsers.add_parser("prepare-outline", help="Generate and lock the thesis outline before drafting.")
    prepare_outline_parser.add_argument("--config", type=Path)

    prepare_writing_parser = subparsers.add_parser("prepare-writing", help="Create chapter queue and writing asset skeletons.")
    prepare_writing_parser.add_argument("--config", type=Path)

    prepare_chapter_parser = subparsers.add_parser("prepare-chapter", help="Prepare a full writing packet for one chapter.")
    prepare_chapter_parser.add_argument("--config", type=Path)
    prepare_chapter_parser.add_argument("--chapter", required=True)

    start_chapter_parser = subparsers.add_parser("start-chapter", help="Prepare a chapter packet and generate a start brief for immediate drafting.")
    start_chapter_parser.add_argument("--config", type=Path)
    start_chapter_parser.add_argument("--chapter", required=True)

    finalize_chapter_parser = subparsers.add_parser("finalize-chapter", help="Finalize a drafted/polished chapter and update registry state.")
    finalize_chapter_parser.add_argument("--config", type=Path)
    finalize_chapter_parser.add_argument("--chapter", required=True)
    finalize_chapter_parser.add_argument("--status", choices=["drafted", "polished", "reviewed"], default="polished")

    normalize_citations_parser = subparsers.add_parser("normalize-citations", help="Renumber citations by first appearance and emit a citation audit report.")
    normalize_citations_parser.add_argument("--config", type=Path)

    workspace_check_parser = subparsers.add_parser("check-workspace", help="Check workspace readiness, packet sync state, and review warnings.")
    workspace_check_parser.add_argument("--config", type=Path)

    release_preflight_parser = subparsers.add_parser("release-preflight", help="Run release preflight including compat sync and workspace checks.")
    release_preflight_parser.add_argument("config_path", nargs="?")
    release_preflight_parser.add_argument("--config", dest="config_option", type=Path)

    release_build_parser = subparsers.add_parser("release-build", help="Run release preflight, refresh figures, build DOCX, and write build summary.")
    release_build_parser.add_argument("config_path", nargs="?")
    release_build_parser.add_argument("--config", dest="config_option", type=Path)
    release_build_parser.add_argument("--output-name")

    release_verify_parser = subparsers.add_parser("release-verify", help="Verify a built DOCX or run the full release verify chain from a workspace config.")
    release_verify_parser.add_argument("target", nargs="?")
    release_verify_parser.add_argument("--config", dest="config_option", type=Path)
    release_verify_parser.add_argument("--output-name")

    release_summary_parser = subparsers.add_parser("write-release-summary", help="Write a machine-readable release summary artifact for a workspace.")
    release_summary_parser.add_argument("--config", type=Path)
    release_summary_parser.add_argument("--docx", type=Path)

    build_summary_parser = subparsers.add_parser("write-build-summary", help="Write a machine-readable build summary artifact for a workspace.")
    build_summary_parser.add_argument("--config", type=Path)
    build_summary_parser.add_argument("--docx", type=Path)

    finalization_summary_parser = subparsers.add_parser("write-finalization-summary", help="Write a machine-readable Windows finalization summary artifact for a workspace.")
    finalization_summary_parser.add_argument("--config", type=Path)
    finalization_summary_parser.add_argument("--base-docx", type=Path)
    finalization_summary_parser.add_argument("--final-docx", type=Path)
    finalization_summary_parser.add_argument("--figure-log", type=Path)

    verify_parser = subparsers.add_parser("verify", help="Verify citation anchors in a DOCX or workspace config.")
    verify_parser.add_argument("target", nargs="?", help="DOCX path or workspace config JSON path.")

    postprocess_parser = subparsers.add_parser("postprocess", help="Run Windows Word post-processing.")
    postprocess_parser.add_argument("input_docx", nargs="?")
    postprocess_parser.add_argument("output_docx", nargs="?")
    postprocess_parser.add_argument("--config", type=Path)
    postprocess_parser.add_argument("--figlog", default="")
    postprocess_parser.add_argument("--figlog_out", default="")
    postprocess_parser.add_argument("--print-output-path", action="store_true")

    example_parser = subparsers.add_parser("example", help="Run bundled example-specific tooling.")
    example_subparsers = example_parser.add_subparsers(dest="example_command", required=True)

    example_diagrams = example_subparsers.add_parser("generate-diagrams", help="Generate bundled example diagrams.")
    example_diagrams.add_argument("--example", default="health_record")

    example_skeleton = example_subparsers.add_parser("generate-skeleton", help="Generate bundled example skeleton DOCX.")
    example_skeleton.add_argument("--example", default="health_record")

    smoke_intake_parser = subparsers.add_parser("smoke-intake", help="Run the bundled intake-to-writing-prep smoke sequence for a new workspace.")
    smoke_intake_parser.add_argument("--project-root", type=Path, required=True)
    smoke_intake_parser.add_argument("--title", required=True)
    smoke_intake_parser.add_argument("--out", type=Path, required=True)
    smoke_intake_parser.add_argument("--discipline", default="计算机类")
    smoke_intake_parser.add_argument("--chain", choices=["auto", "fisco", "fabric"], default="auto")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "build":
        config_path = _resolve_config_arg(args.config)
        build_args: list[str] = ["--config", str(config_path)]
        if args.output_name:
            build_args.extend(["--output-name", args.output_name])
        if args.print_output_path:
            build_args.append("--print-output-path")
        if args.print_output_path:
            build_main(build_args)
            return 0

        def _action() -> None:
            build_main(build_args)
            _record_workspace_state(
                config_path,
                "build",
                {
                    "output_docx": str(resolve_output_docx_path(config_path, args.output_name)),
                    "output_name": args.output_name or "",
                },
            )

        _run_with_workspace_lock(config_path, "build", _action)
        return 0

    if args.command == "intake":
        result = run_intake(args.project_root, args.title, args.out, args.discipline, args.chain)
        print(f"workspace_root: {result['workspace_root']}")
        print(f"config_path: {result['config_path']}")
        print(f"manifest_path: {result['manifest_path']}")
        print(f"chain_platform: {result['chain_platform']}")
        return 0

    if args.command == "set-active-workspace":
        result = set_active_workspace(args.config)
        handoff = refresh_workspace_handoff(args.config, trigger="set-active-workspace", command="set-active-workspace")
        append_workspace_execution_log(args.config, "set-active-workspace", {**result, **handoff})
        print(f"active_workspace_json: {result['active_workspace_json']}")
        print(f"config_path: {result['config_path']}")
        print(f"workspace_root: {result['workspace_root']}")
        print(f"handoff_json: {handoff['handoff_json']}")
        print(f"handoff_md: {handoff['handoff_md']}")
        return 0

    if args.command == "resolve-active-workspace":
        pointer = read_active_workspace_pointer()
        config_path = _resolve_config_arg(None)
        if args.print_path:
            print(config_path)
            return 0
        print(f"active_workspace_json: {ACTIVE_WORKSPACE_POINTER_PATH}")
        print(f"config_path: {config_path}")
        print(f"title: {pointer.get('title', '')}")
        print(f"workspace_root: {pointer.get('workspace_root', '')}")
        return 0

    if args.command == "refresh-handoff":
        config_path = _resolve_config_arg(args.config)
        result = refresh_workspace_handoff(config_path, trigger="refresh-handoff", command="refresh-handoff")
        append_workspace_execution_log(config_path, "refresh-handoff", result)
        print(f"config_path: {result['config_path']}")
        print(f"handoff_json: {result['handoff_json']}")
        print(f"handoff_md: {result['handoff_md']}")
        print(f"phase: {result['phase']}")
        print(f"workflow_signature_status: {result['workflow_signature_status']}")
        print(f"lock_status: {result['lock_status']}")
        return 0

    if args.command == "resume":
        config_path = _resolve_config_arg(args.config)
        lines, handoff = build_resume_lines(config_path)
        _log_readonly_command(
            config_path,
            "resume",
            {
                "phase": handoff["phase"]["name"],
                "next_commands": handoff["next_commands"],
                "workflow_signature_status": handoff["bundle"]["signature_status"],
                "lock_status": handoff["lock"]["state"],
            },
        )
        if args.json:
            print(json.dumps(handoff, ensure_ascii=False, indent=2))
        else:
            for line in lines:
                print(line)
        return 0

    if args.command == "lock-status":
        config_path = _resolve_config_arg(args.config)
        snapshot = build_workspace_snapshot(config_path, trigger="lock-status", command="lock-status", persist_signature=False)
        _log_readonly_command(
            config_path,
            "lock-status",
            {
                "lock_status": snapshot["lock"]["state"],
                "lock_holder": snapshot["lock"]["holder"],
                "workflow_signature_status": snapshot["bundle"]["signature_status"],
            },
        )
        if args.json:
            print(json.dumps(snapshot["lock"], ensure_ascii=False, indent=2))
            return 0
        print(f"config_path: {snapshot['workspace']['config_path']}")
        print(f"lock_status: {snapshot['lock']['state']}")
        print(f"lock_path: {snapshot['lock']['path']}")
        print(f"lock_holder: {snapshot['lock']['holder'] or 'none'}")
        print(f"lock_command: {snapshot['lock']['command'] or 'none'}")
        print(f"lock_created_at: {snapshot['lock']['created_at'] or 'none'}")
        print(f"lock_expires_at: {snapshot['lock']['expires_at'] or 'none'}")
        return 0

    if args.command == "clear-lock":
        config_path = _resolve_config_arg(args.config)
        result = release_workspace_lock(config_path, "clear-lock", force=args.force)
        _record_workspace_state(config_path, "clear-lock", {"force": args.force, **result})
        print(f"lock_path: {result['lock_path']}")
        print(f"lock_status: {result['state']}")
        return 0

    if args.command == "sync-workflow-assets":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "sync-workflow-assets",
            lambda: (
                lambda inner: (_record_workspace_state(config_path, "sync-workflow-assets", inner), inner)[1]
            )(sync_workspace_workflow_assets(config_path)),
        )
        print(f"workflow_readme: {result['workflow_readme']}")
        print(f"workflow_assets_state_json: {result['workflow_assets_state_json']}")
        print(f"bundle_signature: {result['bundle_signature']}")
        print(f"synced_at: {result['synced_at']}")
        print(f"synced_doc_count: {result['synced_doc_count']}")
        print(f"synced_skill_count: {result['synced_skill_count']}")
        return 0

    if args.command == "extract":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "extract",
            lambda: (lambda inner: (_record_workspace_state(config_path, "extract", inner), inner)[1])(run_extract(config_path)),
        )
        print(f"material_pack_json: {result['material_pack_json']}")
        print(f"material_pack_md: {result['material_pack_md']}")
        return 0

    if args.command == "extract-code":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "extract-code",
            lambda: (lambda inner: (_record_workspace_state(config_path, "extract-code", inner), inner)[1])(run_extract_code(config_path)),
        )
        print(f"code_evidence_pack_json: {result['code_evidence_pack_json']}")
        print(f"code_evidence_pack_md: {result['code_evidence_pack_md']}")
        print(f"code_snippets_dir: {result['code_snippets_dir']}")
        print(f"code_screenshots_dir: {result['code_screenshots_dir']}")
        return 0

    if args.command == "prepare-figures":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "prepare-figures",
            lambda: (
                lambda inner: (_record_workspace_state(config_path, "prepare-figures", {"generated_figures": len(inner["generated_figures"])}), inner)[1]
            )(run_prepare_figures(config_path)),
        )
        print(f"config_path: {result['config_path']}")
        print(f"diagram_dir: {result['diagram_dir']}")
        print(f"generated_figures: {len(result['generated_figures'])}")
        for item in result["generated_figures"]:
            print(f"{item['figure_no']} [{item.get('status', 'rendered')}]: {item['path']}")
        return 0

    if args.command == "scaffold":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "scaffold",
            lambda: (lambda inner: (_record_workspace_state(config_path, "scaffold", inner), inner)[1])(run_scaffold(config_path)),
        )
        print(f"polished_dir: {result['polished_dir']}")
        print(f"literature_plan: {result['literature_plan']}")
        print(f"initialized_chapters: {len(result.get('initialized_chapters', []))}")
        print(f"skipped_existing_chapters: {len(result.get('skipped_existing_chapters', []))}")
        return 0

    if args.command == "literature":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "literature",
            lambda: (lambda inner: (_record_workspace_state(config_path, "literature", inner), inner)[1])(run_literature(config_path, args.min_refs, args.max_refs)),
        )
        print(f"literature_pack_json: {result['literature_pack_json']}")
        print(f"literature_pack_md: {result['literature_pack_md']}")
        print(f"reference_registry_json: {result['reference_registry_json']}")
        print(f"research_index_json: {result['research_index_json']}")
        print(f"research_index_md: {result['research_index_md']}")
        return 0

    if args.command == "prepare-outline":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "prepare-outline",
            lambda: (lambda inner: (_record_workspace_state(config_path, "prepare-outline", inner), inner)[1])(run_prepare_outline(config_path)),
        )
        print(f"thesis_outline_json: {result['thesis_outline_json']}")
        print(f"thesis_outline_md: {result['thesis_outline_md']}")
        return 0

    if args.command == "prepare-writing":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "prepare-writing",
            lambda: (lambda inner: (_record_workspace_state(config_path, "prepare-writing", inner), inner)[1])(run_prepare_writing(config_path)),
        )
        print(f"chapter_queue_json: {result['chapter_queue_json']}")
        return 0

    if args.command == "prepare-chapter":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "prepare-chapter",
            lambda: (
                lambda inner: (_record_workspace_state(config_path, "prepare-chapter", {"chapter": args.chapter, **inner}), inner)[1]
            )(run_prepare_chapter(config_path, args.chapter)),
        )
        print(f"packet_json: {result['packet_json']}")
        print(f"packet_md: {result['packet_md']}")
        print(f"brief_md: {result['brief_md']}")
        return 0

    if args.command == "start-chapter":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "start-chapter",
            lambda: (
                lambda inner: (_record_workspace_state(config_path, "start-chapter", {"chapter": args.chapter, **inner}), inner)[1]
            )(run_start_chapter(config_path, args.chapter)),
        )
        print(f"packet_json: {result['packet_json']}")
        print(f"packet_md: {result['packet_md']}")
        print(f"brief_md: {result['brief_md']}")
        print(f"start_md: {result['start_md']}")
        print(f"target_chapter: {result['target_chapter']}")
        return 0

    if args.command == "finalize-chapter":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "finalize-chapter",
            lambda: (
                lambda inner: (
                    _record_workspace_state(config_path, "finalize-chapter", {"chapter": args.chapter, "status": args.status, **inner}),
                    inner,
                )[1]
            )(run_finalize_chapter(config_path, args.chapter, args.status)),
        )
        print(f"review_md: {result['review_md']}")
        print(f"references_md: {result['references_md']}")
        print(f"citation_audit_md: {result['citation_audit_md']}")
        print(f"chapter_queue_json: {result['chapter_queue_json']}")
        return 0

    if args.command == "normalize-citations":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "normalize-citations",
            lambda: (lambda inner: (_record_workspace_state(config_path, "normalize-citations", inner), inner)[1])(run_normalize_citations(config_path)),
        )
        print(f"reference_registry_json: {result['reference_registry_json']}")
        print(f"references_md: {result['references_md']}")
        print(f"citation_audit_md: {result['citation_audit_md']}")
        return 0

    if args.command == "check-workspace":
        config_path = _resolve_config_arg(args.config)
        return _run_workspace_check_command(config_path, "check-workspace")

    if args.command == "release-preflight":
        config_path = _resolve_release_config_input(args.config_option, args.config_path)
        return _run_release_preflight_command(config_path, "release-preflight")

    if args.command == "release-build":
        config_path = _resolve_release_config_input(args.config_option, args.config_path)
        preflight_status = _run_release_preflight_command(config_path, "release-build-preflight")
        if preflight_status != 0:
            return preflight_status
        result = _run_release_build_flow(config_path, args.output_name, "release-build")
        _print_prepare_figures_result(result)
        print(f"docx_path: {result['docx_path']}")
        summary = run_write_build_summary(config_path, result["docx_path"])
        _record_workspace_state(
            config_path,
            "release-build",
            {
                "docx_path": str(result["docx_path"]),
                "output_name": result["output_name"],
                "generated_figures": len(result["generated_figures"]),
                **summary,
            },
        )
        print(f"build_summary_json: {summary['build_summary_json']}")
        print(f"build_run_json: {summary['build_run_json']}")
        return 0

    if args.command == "release-verify":
        config_mode = bool(args.config_option) or not args.target or str(args.target).lower().endswith(".json")
        if config_mode:
            config_arg = None if args.config_option or not args.target or not str(args.target).lower().endswith(".json") else args.target
            config_path = _resolve_release_config_input(args.config_option, config_arg)
            preflight_status = _run_release_preflight_command(config_path, "release-verify-preflight")
            if preflight_status != 0:
                return preflight_status
            result = _run_release_build_flow(config_path, args.output_name, "release-verify")
            _print_prepare_figures_result(result)
            print(f"docx_path: {result['docx_path']}")
            verify_status = verify_citation_links(result["docx_path"])
            if verify_status != 0:
                _record_workspace_state(
                    config_path,
                    "release-verify",
                    {
                        "docx_path": str(result["docx_path"]),
                        "output_name": result["output_name"],
                        "generated_figures": len(result["generated_figures"]),
                        "verify_status": verify_status,
                    },
                )
                return verify_status
            summary = run_write_release_summary(config_path, result["docx_path"])
            _record_workspace_state(
                config_path,
                "release-verify",
                {
                    "docx_path": str(result["docx_path"]),
                    "output_name": result["output_name"],
                    "generated_figures": len(result["generated_figures"]),
                    **summary,
                },
            )
            print(f"release_summary_json: {summary['release_summary_json']}")
            print(f"release_run_json: {summary['release_run_json']}")
            return 0

        if args.output_name:
            print("--output-name is only supported when release-verify builds from a workspace config.", file=sys.stderr)
            return 2

        docx_path = Path(args.target)
        return verify_citation_links(docx_path)

    if args.command == "write-release-summary":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "write-release-summary",
            lambda: (
                lambda inner: (_record_workspace_state(config_path, "write-release-summary", inner), inner)[1]
            )(run_write_release_summary(config_path, args.docx)),
        )
        print(f"release_summary_json: {result['release_summary_json']}")
        print(f"release_run_json: {result['release_run_json']}")
        return 0

    if args.command == "write-build-summary":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "write-build-summary",
            lambda: (
                lambda inner: (_record_workspace_state(config_path, "write-build-summary", inner), inner)[1]
            )(run_write_build_summary(config_path, args.docx)),
        )
        print(f"build_summary_json: {result['build_summary_json']}")
        print(f"build_run_json: {result['build_run_json']}")
        return 0

    if args.command == "write-finalization-summary":
        config_path = _resolve_config_arg(args.config)
        result = _run_with_workspace_lock(
            config_path,
            "write-finalization-summary",
            lambda: (
                lambda inner: (_record_workspace_state(config_path, "write-finalization-summary", inner), inner)[1]
            )(run_write_finalization_summary(config_path, args.base_docx, args.final_docx, args.figure_log)),
        )
        print(f"final_summary_json: {result['final_summary_json']}")
        print(f"final_run_json: {result['final_run_json']}")
        return 0

    if args.command == "verify":
        return verify_citation_links(_resolve_verify_target(args.target))

    if args.command == "postprocess":
        try:
            config_path, input_docx, output_docx, figlog, figlog_out = _resolve_postprocess_targets(args)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2

        if args.print_output_path:
            print(output_docx)
            return 0

        try:
            from windows.postprocess_word_format import main as postprocess_main
        except ModuleNotFoundError as exc:
            print(f"windows-only dependency unavailable: {exc}", file=sys.stderr)
            return 1
        def _postprocess_action() -> tuple[int, dict[str, Any] | None]:
            exit_code = int(
                postprocess_main(
                    [
                        str(input_docx),
                        str(output_docx),
                        "--figlog",
                        figlog,
                        "--figlog_out",
                        figlog_out,
                    ]
                )
                or 0
            )
            summary: dict[str, Any] | None = None
            if exit_code == 0 and config_path:
                summary = run_write_finalization_summary(config_path, input_docx, output_docx, Path(figlog_out) if figlog_out else None)
                _record_workspace_state(config_path, "postprocess", summary)
            return exit_code, summary

        if config_path:
            result, summary = _run_with_workspace_lock(config_path, "postprocess", _postprocess_action)
        else:
            result, summary = _postprocess_action()
        if result == 0 and config_path and summary:
            print(f"final_summary_json: {summary['final_summary_json']}")
            print(f"final_run_json: {summary['final_run_json']}")
        return result

    if args.command == "example":
        return _run_example(args.example, args.example_command)

    if args.command == "smoke-intake":
        intake_result = run_intake(args.project_root, args.title, args.out, args.discipline, args.chain)
        config_path = Path(intake_result["config_path"])
        cli_path = Path(__file__).resolve()
        smoke_steps = [
            ["extract-code", "--config", str(config_path)],
            ["extract", "--config", str(config_path)],
            ["scaffold", "--config", str(config_path)],
            ["literature", "--config", str(config_path)],
            ["prepare-outline", "--config", str(config_path)],
            ["prepare-writing", "--config", str(config_path)],
            ["set-active-workspace", "--config", str(config_path)],
            ["resume", "--config", str(config_path)],
            ["check-workspace", "--config", str(config_path)],
        ]
        for subcmd in smoke_steps:
            completed = subprocess.run(
                [sys.executable, str(cli_path), *subcmd],
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.stdout:
                print(completed.stdout.rstrip())
            if completed.returncode != 0:
                if completed.stderr:
                    print(completed.stderr.rstrip(), file=sys.stderr)
                return completed.returncode
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
