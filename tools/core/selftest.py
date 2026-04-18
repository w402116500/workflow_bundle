from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image

from core.bundle_version import bundle_version_info
from core.build_final_thesis_docx import resolve_output_docx_path
from core.figure_assets import _build_generic_er_dsl
from core.project_common import load_workspace_context, read_json, write_json
from core.runtime_state import ACTIVE_WORKSPACE_POINTER_PATH


THIS_ROOT = Path(__file__).resolve().parents[2]
if THIS_ROOT.name == "workflow_bundle":
    PRIMARY_WORKFLOW_ROOT = THIS_ROOT
else:
    PRIMARY_WORKFLOW_ROOT = THIS_ROOT / "workflow_bundle" if (THIS_ROOT / "workflow_bundle").exists() else THIS_ROOT

FIXTURE_PROJECT_ROOT = PRIMARY_WORKFLOW_ROOT / "workflow" / "fixtures" / "fabric_trace_demo"
SELFTEST_DOCX_NAME = "selftest_release.docx"
CHAPTER5_BRIEF_EXPECTED = [
    "代码截图仅作为可选实现证据插图使用，不编号，不写“图5.x”题注，也不单独形成图题段落。",
    "若使用代码截图，只能作为可选实现证据，并且必须紧跟在对应的后端或前端代码块之后插入，不能单独生成“关键代码截图”小节。",
]
CHAPTER5_PACKET_EXPECTED = [
    "Code screenshots in chapter 5 are optional inline implementation evidence only; do not assign figure numbers, `图5.x` captions, or separate caption paragraphs to them.",
    "If code screenshots are used, treat them as optional evidence only, insert them immediately after the matching backend or frontend code block inside that same subfunction, and do not create a standalone `关键代码截图` subsection.",
]
CHAPTER6_BRIEF_EXPECTED = [
    "第 6 章按样稿式测试章节来写，不写成压缩版测试总结。",
    "6.1 环境配置、6.2 功能测试、6.3 非功能测试均应优先保留真实表格。",
]
CHAPTER6_PACKET_EXPECTED = [
    "For chapter 6, follow the sample-like testing chapter pattern rather than a compressed summary style.",
    "Section 6.2 must keep one dedicated function-test subsection per core module, and each subsection must contain its required table as an actual markdown table before the explanatory paragraph.",
]
SELFTEST_ER_DSL = """实体甲(_实体甲编号_, 实体甲名称)\n实体乙(_实体乙编号_, 实体乙名称)\n\n实体甲 --- 1 --- < 关联 > --- N --- 实体乙\n"""
SELFTEST_GENERIC_ER_TABLE_DETAILS = [
    {
        "table": "device",
        "columns": [
            {"name": "device_id", "is_primary": True},
            {"name": "device_name", "is_primary": False},
        ],
    },
    {
        "table": "alert",
        "columns": [
            {"name": "alert_id", "is_primary": True},
            {"name": "device_id", "is_primary": False},
        ],
    },
    {
        "table": "work_order",
        "columns": [
            {"name": "order_id", "is_primary": True},
            {"name": "device_id", "is_primary": False},
            {"name": "source_alert_id", "is_primary": False},
        ],
    },
    {
        "table": "part_replacement",
        "columns": [
            {"name": "record_id", "is_primary": True},
            {"name": "order_id", "is_primary": False},
            {"name": "device_id", "is_primary": False},
        ],
    },
    {
        "table": "monitor_record",
        "columns": [
            {"name": "record_id", "is_primary": True},
            {"name": "device_id", "is_primary": False},
        ],
    },
]


class SelftestFailure(RuntimeError):
    pass


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _slugify_name(text: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z]+", "-", text).strip("-").lower()
    return slug or "selftest"


def _tail_lines(text: str, limit: int = 20) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-limit:]


def _run_command(command: list[str], log_basename: str, logs_dir: Path) -> tuple[dict[str, Any], str, str]:
    logs_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = logs_dir / f"{log_basename}.stdout.log"
    stderr_path = logs_dir / f"{log_basename}.stderr.log"
    started = time.monotonic()
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    duration = round(time.monotonic() - started, 3)
    stdout_text = completed.stdout or ""
    stderr_text = completed.stderr or ""
    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")
    result = {
        "command": command,
        "returncode": int(completed.returncode),
        "duration_seconds": duration,
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "stdout_tail": _tail_lines(stdout_text),
        "stderr_tail": _tail_lines(stderr_text),
    }
    return result, stdout_text, stderr_text


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SelftestFailure(message)


def _assert_contains(text: str, expected: str, label: str) -> dict[str, Any]:
    ok = expected in text
    return {
        "label": label,
        "ok": ok,
        "expected": expected,
    }


def _figure_no_slug(text: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z]+", "-", str(text)).strip("-").lower()
    return slug or "figure"


def _default_er_output_name(figure_no: str) -> str:
    return f"generated/fig{_figure_no_slug(figure_no)}-er-diagram.png"


def _default_plantuml_output_name(figure_no: str) -> str:
    return f"generated/fig{_figure_no_slug(figure_no)}-plantuml.png"


def _enabled_er_specs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = config.get("er_figure_specs") or {}
    if not isinstance(raw, dict):
        return {}
    enabled: dict[str, dict[str, Any]] = {}
    for raw_figure_no, raw_spec in raw.items():
        figure_no = str(raw_figure_no).strip()
        if not figure_no or not isinstance(raw_spec, dict) or raw_spec.get("enabled", True) is False:
            continue
        enabled[figure_no] = raw_spec
    return enabled


def _enabled_plantuml_specs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = config.get("plantuml_figure_specs") or {}
    if not isinstance(raw, dict):
        return {}
    enabled: dict[str, dict[str, Any]] = {}
    for raw_figure_no, raw_spec in raw.items():
        figure_no = str(raw_figure_no).strip()
        if not figure_no or not isinstance(raw_spec, dict) or raw_spec.get("enabled", True) is False:
            continue
        enabled[figure_no] = raw_spec
    return enabled


def _inspect_docx_xml(docx_path: Path) -> str:
    with zipfile.ZipFile(docx_path) as zf:
        return zf.read("word/document.xml").decode("utf-8", errors="replace")


def _extract_docx_image_extents_cm(docx_xml: str) -> list[tuple[float, float]]:
    matches = re.findall(r'<wp:extent cx="(\d+)" cy="(\d+)"', docx_xml)
    return [(int(cx) / 360000.0, int(cy) / 360000.0) for cx, cy in matches]


def _bundle_cli_path() -> Path:
    return PRIMARY_WORKFLOW_ROOT / "tools" / "cli.py"


def _load_active_workspace_pointer() -> tuple[bool, bytes]:
    if ACTIVE_WORKSPACE_POINTER_PATH.exists():
        return True, ACTIVE_WORKSPACE_POINTER_PATH.read_bytes()
    return False, b""


def _restore_active_workspace_pointer(existed: bool, content: bytes) -> None:
    ACTIVE_WORKSPACE_POINTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    if existed:
        ACTIVE_WORKSPACE_POINTER_PATH.write_bytes(content)
        return
    if ACTIVE_WORKSPACE_POINTER_PATH.exists():
        ACTIVE_WORKSPACE_POINTER_PATH.unlink()


def _run_fixture_stage(out_root: Path) -> dict[str, Any]:
    logs_dir = out_root / "logs" / "fixture"
    fixture_workspace = out_root / "fixture_workspace"
    cli_path = _bundle_cli_path()
    stage: dict[str, Any] = {
        "name": "fixture",
        "project_root": str(FIXTURE_PROJECT_ROOT),
        "workspace_root": str(fixture_workspace),
        "config_path": str(fixture_workspace / "workflow" / "configs" / "workspace.json"),
        "commands": [],
        "assertions": [],
        "status": 0,
        "error": "",
    }

    try:
        _require(FIXTURE_PROJECT_ROOT.exists(), f"fixture project not found: {FIXTURE_PROJECT_ROOT}")

        smoke_cmd = [
            sys.executable,
            str(cli_path),
            "smoke-intake",
            "--project-root",
            str(FIXTURE_PROJECT_ROOT),
            "--title",
            "Workflow Bundle Selftest Fixture",
            "--out",
            str(fixture_workspace),
            "--chain",
            "fabric",
            "--min-refs",
            "1",
            "--max-refs",
            "1",
            "--skip-research-sidecar",
        ]
        smoke_result, _, _ = _run_command(smoke_cmd, "01-smoke-intake", logs_dir)
        stage["commands"].append(smoke_result)
        _require(smoke_result["returncode"] == 0, "smoke-intake failed for bundled fixture")

        config_path = Path(stage["config_path"])
        _require(config_path.exists(), f"fixture workspace config missing: {config_path}")
        material_pack_path = fixture_workspace / "docs" / "materials" / "material_pack.json"
        _require(material_pack_path.exists(), f"fixture material pack missing: {material_pack_path}")

        material_pack = read_json(material_pack_path)
        role_tables = (
            material_pack.get("sections", {})
            .get("roles_permissions", {})
            .get("assets", {})
            .get("tables", [])
        )
        role_table = next((item for item in role_tables if item.get("kind") == "role-matrix"), {})
        _require(role_table, "fixture role-matrix asset missing after smoke-intake")
        role_headers = role_table.get("table_headers") or []
        role_rows = role_table.get("table_rows") or []
        file_leak_pattern = re.compile(r"(?i)\b[\w.-]+\.(?:md|txt|docx|sql|json|vue|go|java|ts|js)\b|derived-from-pages-or-docs")
        for label, ok, actual in (
            ("fixture_role_matrix_headers", role_headers == ["角色", "主要职责", "权限边界"], role_headers),
            ("fixture_role_matrix_rows_present", len(role_rows) > 0, len(role_rows)),
            (
                "fixture_role_matrix_no_file_leaks",
                not any(file_leak_pattern.search(str(cell or "")) for row in role_rows for cell in row),
                role_rows,
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture role-matrix workflow regression detected")

        for idx, chapter in enumerate(("05-系统实现.md", "06-系统测试.md"), start=2):
            command = [
                sys.executable,
                str(cli_path),
                "prepare-chapter",
                "--config",
                str(config_path),
                "--chapter",
                chapter,
            ]
            result, _, _ = _run_command(command, f"{idx:02d}-prepare-{_slugify_name(chapter)}", logs_dir)
            stage["commands"].append(result)
            _require(result["returncode"] == 0, f"prepare-chapter failed for {chapter}")

        check_cmd = [sys.executable, str(cli_path), "check-workspace", "--config", str(config_path)]
        check_result, _, _ = _run_command(check_cmd, "04-check-workspace", logs_dir)
        stage["commands"].append(check_result)
        _require(check_result["returncode"] == 0, "fixture check-workspace did not pass")

        fixture_er_source = fixture_workspace / "docs" / "figure_specs" / "selftest-er.dbdia"
        fixture_er_source.parent.mkdir(parents=True, exist_ok=True)
        fixture_er_source.write_text(SELFTEST_ER_DSL, encoding="utf-8")
        fixture_config = read_json(config_path)
        fixture_plantuml_source = fixture_workspace / "docs" / "figure_specs" / "selftest-usecase.puml"
        fixture_plantuml_source.write_text(
            "\n".join(
                [
                    "@startuml",
                    "!pragma layout smetana",
                    "left to right direction",
                    "skinparam monochrome true",
                    "skinparam shadowing false",
                    "skinparam backgroundColor white",
                    "skinparam defaultFontName \"Noto Sans CJK SC\"",
                    "skinparam packageStyle rectangle",
                    "actor 平台管理员 as Admin",
                    "actor 审计员 as Auditor",
                    "rectangle 自测试系统 {",
                    "  usecase \"账号治理\" as UC1",
                    "  usecase \"审计核验\" as UC2",
                    "}",
                    "Admin --> UC1",
                    "Auditor --> UC2",
                    "@enduml",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        fixture_config["er_figure_specs"] = {
            "4.2": {
                "caption": "图4.2 自测试通用E-R图",
                "source_path": "docs/figure_specs/selftest-er.dbdia",
                "enabled": True,
            }
        }
        fixture_config["plantuml_figure_specs"] = {
            "3.2": {
                "caption": "图3.2 自测试 PlantUML 用例图",
                "source_path": "docs/figure_specs/selftest-usecase.puml",
                "output_name": "generated/fig3-2-selftest-usecase.png",
                "enabled": True,
                "override_builtin": True,
            }
        }
        write_json(config_path, fixture_config)

        prepare_figures_cmd = [sys.executable, str(cli_path), "prepare-figures", "--config", str(config_path)]
        prepare_figures_result, _, _ = _run_command(prepare_figures_cmd, "05-prepare-figures", logs_dir)
        stage["commands"].append(prepare_figures_result)
        _require(prepare_figures_result["returncode"] == 0, "fixture prepare-figures failed for generic er selftest")

        generic_er_dsl = _build_generic_er_dsl(SELFTEST_GENERIC_ER_TABLE_DETAILS, [])
        generic_relation_names = re.findall(r"<\s*([^>]+)\s*>", generic_er_dsl)
        for label, ok, actual in (
            ("fixture_generic_er_multi_relation_present", len(generic_relation_names) >= 4, generic_relation_names),
            (
                "fixture_generic_er_multi_relation_unique",
                len(generic_relation_names) == len(set(generic_relation_names)),
                generic_relation_names,
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture generic er fallback emitted duplicate relationship identifiers")

        refreshed_fixture_config = read_json(config_path)
        figure_cfg = (refreshed_fixture_config.get("figure_map") or {}).get("4.2", {})
        assertion = {
            "label": "fixture_generic_er_renderer",
            "ok": str(figure_cfg.get("renderer") or "") == "dbdia-er",
            "actual": str(figure_cfg.get("renderer") or ""),
        }
        stage["assertions"].append(assertion)
        _require(assertion["ok"], "fixture generic er spec did not render with dbdia-er")

        generated_er_path = fixture_workspace / str(figure_cfg.get("path") or "")
        assertion = {
            "label": "fixture_generic_er_output_exists",
            "ok": generated_er_path.exists(),
            "path": str(generated_er_path),
        }
        stage["assertions"].append(assertion)
        _require(assertion["ok"], f"fixture generic er output missing: {generated_er_path}")

        stale_placeholder_size = (64, 64)
        Image.new("RGB", stale_placeholder_size, (255, 255, 255)).save(generated_er_path)
        stale_renderer_cfg = read_json(config_path)
        stale_renderer_map = dict(stale_renderer_cfg.get("figure_map") or {})
        stale_renderer_entry = dict(stale_renderer_map.get("4.2") or {})
        stale_renderer_entry["spec_hash"] = "legacy-stale-er-output"
        stale_renderer_map["4.2"] = stale_renderer_entry
        stale_renderer_cfg["figure_map"] = stale_renderer_map
        write_json(config_path, stale_renderer_cfg)

        rerender_er_cmd = [sys.executable, str(cli_path), "prepare-figures", "--config", str(config_path)]
        rerender_er_result, rerender_er_stdout, _ = _run_command(
            rerender_er_cmd,
            "05a-prepare-figures-er-rerender-negative-adopt",
            logs_dir,
        )
        stage["commands"].append(rerender_er_result)
        _require(rerender_er_result["returncode"] == 0, "fixture prepare-figures failed during dbdia-er rerender regression")

        with Image.open(generated_er_path) as rerendered_image:
            rerendered_size = rerendered_image.size
        for label, ok, actual in (
            ("fixture_generic_er_rerender_status", "4.2 [rendered]" in rerender_er_stdout, rerender_er_stdout),
            ("fixture_generic_er_rerender_not_placeholder", rerendered_size != stale_placeholder_size, rerendered_size),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture dbdia-er stale output regression did not force rerender as expected")

        generated_src_dir = fixture_workspace / "docs" / "images" / "generated_src"
        stem = Path(_default_er_output_name("4.2")).stem
        for filename in (f"{stem}.dbdia", f"{stem}.dot", f"{stem}.svg"):
            path = generated_src_dir / filename
            assertion = {
                "label": f"fixture_generic_er_sidecar:{filename}",
                "ok": path.exists(),
                "path": str(path),
            }
            stage["assertions"].append(assertion)
            _require(assertion["ok"], f"fixture generic er sidecar missing: {path}")

        refreshed_fixture_config = read_json(config_path)
        plantuml_cfg = (refreshed_fixture_config.get("figure_map") or {}).get("3.2", {})
        assertion = {
            "label": "fixture_plantuml_renderer",
            "ok": str(plantuml_cfg.get("renderer") or "") == "plantuml",
            "actual": str(plantuml_cfg.get("renderer") or ""),
        }
        stage["assertions"].append(assertion)
        _require(assertion["ok"], "fixture plantuml figure did not render with plantuml renderer")

        generated_plantuml_path = fixture_workspace / str(plantuml_cfg.get("path") or "")
        assertion = {
            "label": "fixture_plantuml_output_exists",
            "ok": generated_plantuml_path.exists(),
            "path": str(generated_plantuml_path),
        }
        stage["assertions"].append(assertion)
        _require(assertion["ok"], f"fixture plantuml output missing: {generated_plantuml_path}")

        plantuml_stem = Path(
            str((fixture_config.get("plantuml_figure_specs") or {}).get("3.2", {}).get("output_name") or _default_plantuml_output_name("3.2"))
        ).stem
        for filename in (f"{plantuml_stem}.puml", f"{plantuml_stem}.svg"):
            path = generated_src_dir / filename
            assertion = {
                "label": f"fixture_plantuml_sidecar:{filename}",
                "ok": path.exists(),
                "path": str(path),
            }
            stage["assertions"].append(assertion)
            _require(assertion["ok"], f"fixture plantuml sidecar missing: {path}")

        chapter4_path = fixture_workspace / "polished_v3" / "04-系统设计.md"
        chapter5_path = fixture_workspace / "polished_v3" / "05-系统实现.md"
        _require(chapter4_path.exists(), f"fixture chapter 4 missing: {chapter4_path}")
        _require(chapter5_path.exists(), f"fixture chapter 5 missing: {chapter5_path}")

        chapter4_text = chapter4_path.read_text(encoding="utf-8")
        chapter5_text = chapter5_path.read_text(encoding="utf-8")
        for label, ok, actual in (
            ("fixture_scaffold_marker_4_2", "<!-- figure:4.2 -->" in chapter4_text, "<!-- figure:4.2 -->" in chapter4_text),
            ("fixture_scaffold_marker_5_1", "<!-- figure:5.1 -->" in chapter5_text, "<!-- figure:5.1 -->" in chapter5_text),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture scaffold did not emit required figure markers")

        chapter4_negative_text = chapter4_text.replace("<!-- figure:4.2 -->", "", 1)
        chapter4_path.write_text(chapter4_negative_text, encoding="utf-8")

        negative_check_cmd = [sys.executable, str(cli_path), "check-workspace", "--config", str(config_path)]
        negative_check_result, negative_check_stdout, _ = _run_command(
            negative_check_cmd,
            "06-check-workspace-figure-blocking-negative",
            logs_dir,
        )
        stage["commands"].append(negative_check_result)
        blocking_text_present = "Blocking figure integration issues:" in negative_check_stdout
        blocking_figure_present = "图4.2" in negative_check_stdout
        for label, ok, actual in (
            ("fixture_figure_blocking_negative_status", negative_check_result["returncode"] != 0, negative_check_result["returncode"]),
            ("fixture_figure_blocking_negative_section", blocking_text_present, blocking_text_present),
            ("fixture_figure_blocking_negative_figure_no", blocking_figure_present, blocking_figure_present),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture figure integration blocking regression did not trigger as expected")

        chapter4_text = chapter4_path.read_text(encoding="utf-8")
        chapter5_text = chapter5_path.read_text(encoding="utf-8")
        chapter4_markers = ["<!-- figure:4.2 -->", "<!-- figure:4.3 -->", "<!-- figure:4.4 -->", "<!-- figure:4.5 -->"]
        chapter5_markers = ["<!-- figure:5.1 -->"]
        if not all(marker in chapter4_text for marker in chapter4_markers):
            chapter4_appendix = "\n\n" + "\n".join(marker for marker in chapter4_markers if marker not in chapter4_text) + "\n"
            chapter4_path.write_text(chapter4_text.rstrip() + chapter4_appendix, encoding="utf-8")
        if not all(marker in chapter5_text for marker in chapter5_markers):
            chapter5_appendix = "\n\n" + "\n".join(marker for marker in chapter5_markers if marker not in chapter5_text) + "\n"
            chapter5_path.write_text(chapter5_text.rstrip() + chapter5_appendix, encoding="utf-8")

        positive_check_cmd = [sys.executable, str(cli_path), "check-workspace", "--config", str(config_path)]
        positive_check_result, positive_check_stdout, _ = _run_command(
            positive_check_cmd,
            "07-check-workspace-figure-blocking-positive",
            logs_dir,
        )
        stage["commands"].append(positive_check_result)
        for label, ok, actual in (
            ("fixture_figure_blocking_positive_status", positive_check_result["returncode"] == 0, positive_check_result["returncode"]),
            (
                "fixture_figure_blocking_positive_none",
                "Blocking figure integration issues:\n  - none" in positive_check_stdout,
                "Blocking figure integration issues:\n  - none" in positive_check_stdout,
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture figure integration blocking regression did not clear after marker insertion")

        missing_asset_cfg = read_json(config_path)
        missing_asset_figure_cfg = dict((missing_asset_cfg.get("figure_map") or {}).get("4.2") or {})
        missing_asset_figure_map = dict(missing_asset_cfg.get("figure_map") or {})
        missing_asset_figure_map.pop("4.2", None)
        missing_asset_cfg["figure_map"] = missing_asset_figure_map
        write_json(config_path, missing_asset_cfg)

        missing_asset_check_cmd = [sys.executable, str(cli_path), "check-workspace", "--config", str(config_path)]
        missing_asset_check_result, missing_asset_check_stdout, _ = _run_command(
            missing_asset_check_cmd,
            "07a-check-workspace-figure-mapped-asset-missing-negative",
            logs_dir,
        )
        stage["commands"].append(missing_asset_check_result)
        for label, ok, actual in (
            ("fixture_figure_asset_missing_negative_status", missing_asset_check_result["returncode"] != 0, missing_asset_check_result["returncode"]),
            ("fixture_figure_asset_missing_negative_figure_no", "图4.2" in missing_asset_check_stdout, "图4.2" in missing_asset_check_stdout),
            (
                "fixture_figure_asset_missing_negative_reason",
                "no mapped figure asset is present" in missing_asset_check_stdout,
                "no mapped figure asset is present" in missing_asset_check_stdout,
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture missing mapped figure asset regression did not trigger as expected")

        restored_missing_asset_cfg = read_json(config_path)
        restored_missing_asset_figure_map = dict(restored_missing_asset_cfg.get("figure_map") or {})
        restored_missing_asset_figure_map["4.2"] = missing_asset_figure_cfg
        restored_missing_asset_cfg["figure_map"] = restored_missing_asset_figure_map
        write_json(config_path, restored_missing_asset_cfg)

        restored_missing_asset_check_cmd = [sys.executable, str(cli_path), "check-workspace", "--config", str(config_path)]
        restored_missing_asset_check_result, restored_missing_asset_check_stdout, _ = _run_command(
            restored_missing_asset_check_cmd,
            "07b-check-workspace-figure-mapped-asset-missing-restored",
            logs_dir,
        )
        stage["commands"].append(restored_missing_asset_check_result)
        for label, ok, actual in (
            ("fixture_figure_asset_missing_restored_status", restored_missing_asset_check_result["returncode"] == 0, restored_missing_asset_check_result["returncode"]),
            (
                "fixture_figure_asset_missing_restored_none",
                "Blocking figure integration issues:\n  - none" in restored_missing_asset_check_stdout,
                "Blocking figure integration issues:\n  - none" in restored_missing_asset_check_stdout,
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture missing mapped figure asset regression did not clear after restore")

        refreshed_after_positive = read_json(config_path)
        figure5_cfg = (refreshed_after_positive.get("figure_map") or {}).get("5.1", {})
        mapped_figure5_path = fixture_workspace / str(figure5_cfg.get("path") or "")
        _require(mapped_figure5_path.exists(), f"fixture mapped chapter 5 figure missing: {mapped_figure5_path}")

        stale_chapter5_image = fixture_workspace / "docs" / "images" / "stale-function-structure.png"
        stale_chapter5_image.parent.mkdir(parents=True, exist_ok=True)
        stale_chapter5_image.write_bytes(mapped_figure5_path.read_bytes())

        chapter5_stale_text = chapter5_path.read_text(encoding="utf-8").replace("<!-- figure:5.1 -->", "")
        stale_ref_line = "![图5.1 系统功能结构图](../docs/images/stale-function-structure.png)"
        if "![图5.1 系统功能结构图]" in chapter5_stale_text:
            chapter5_stale_text = re.sub(
                r"!\[图5\.1 系统功能结构图\]\([^)]+\)",
                stale_ref_line,
                chapter5_stale_text,
                count=1,
            )
        else:
            chapter5_stale_text = chapter5_stale_text.replace(
                "图5.1 系统功能结构图",
                f"图5.1 系统功能结构图\n\n{stale_ref_line}",
                1,
            )
        chapter5_path.write_text(chapter5_stale_text.rstrip() + "\n", encoding="utf-8")

        stale_check_cmd = [sys.executable, str(cli_path), "check-workspace", "--config", str(config_path)]
        stale_check_result, stale_check_stdout, _ = _run_command(
            stale_check_cmd,
            "08-check-workspace-figure-blocking-stale-markdown",
            logs_dir,
        )
        stage["commands"].append(stale_check_result)
        for label, ok, actual in (
            ("fixture_figure_blocking_stale_markdown_status", stale_check_result["returncode"] != 0, stale_check_result["returncode"]),
            ("fixture_figure_blocking_stale_markdown_figure_no", "图5.1" in stale_check_stdout, "图5.1" in stale_check_stdout),
            (
                "fixture_figure_blocking_stale_markdown_reason",
                "instead of the mapped asset" in stale_check_stdout,
                "instead of the mapped asset" in stale_check_stdout,
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture stale markdown image regression did not trigger as expected")

        chapter5_restored_text = re.sub(
            r"!\[图5\.1 系统功能结构图\]\([^)]+\)",
            "<!-- figure:5.1 -->",
            chapter5_stale_text,
            count=1,
        )
        chapter5_path.write_text(chapter5_restored_text.rstrip() + "\n", encoding="utf-8")

        restored_check_cmd = [sys.executable, str(cli_path), "check-workspace", "--config", str(config_path)]
        restored_check_result, restored_check_stdout, _ = _run_command(
            restored_check_cmd,
            "09-check-workspace-figure-blocking-stale-markdown-restored",
            logs_dir,
        )
        stage["commands"].append(restored_check_result)
        for label, ok, actual in (
            ("fixture_figure_blocking_stale_markdown_restored_status", restored_check_result["returncode"] == 0, restored_check_result["returncode"]),
            (
                "fixture_figure_blocking_stale_markdown_restored_none",
                "Blocking figure integration issues:\n  - none" in restored_check_stdout,
                "Blocking figure integration issues:\n  - none" in restored_check_stdout,
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture stale markdown image regression did not clear after restoring marker")

        packet_json_path = fixture_workspace / "docs" / "writing" / "chapter_packets" / "05-系统实现.json"
        packet_payload = read_json(packet_json_path)
        expected_page_screenshot_paths = [
            str(item.get("workspace_image_path") or "").strip()
            for item in packet_payload.get("asset_to_section_map", [])
            if item.get("asset_type") == "figures" and item.get("required") and str(item.get("workspace_image_path") or "").strip()
        ]
        unique_expected_page_screenshot_paths = []
        for rel in expected_page_screenshot_paths:
            if rel and rel not in unique_expected_page_screenshot_paths:
                unique_expected_page_screenshot_paths.append(rel)
        if len(unique_expected_page_screenshot_paths) >= 2:
            expected_rel = unique_expected_page_screenshot_paths[0]
            wrong_rel = unique_expected_page_screenshot_paths[1]
            chapter5_page_text = chapter5_path.read_text(encoding="utf-8")
            current_rel = ""
            expected_resolved = str((fixture_workspace / expected_rel).resolve())
            for match in re.finditer(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)", chapter5_page_text):
                rel = str(match.group("path") or "").strip().split()[0] if str(match.group("path") or "").strip() else ""
                if not rel:
                    continue
                if str((chapter5_path.parent / rel).resolve()) == expected_resolved:
                    current_rel = rel
                    break
            _require(current_rel, f"fixture chapter 5 missing expected page screenshot ref for {expected_rel}")

            wrong_markdown_rel = f"../{wrong_rel}"
            chapter5_stale_page_text = chapter5_page_text.replace(current_rel, wrong_markdown_rel, 1)
            chapter5_path.write_text(chapter5_stale_page_text, encoding="utf-8")

            stale_page_check_cmd = [sys.executable, str(cli_path), "check-workspace", "--config", str(config_path)]
            stale_page_check_result, stale_page_check_stdout, _ = _run_command(
                stale_page_check_cmd,
                "10-check-workspace-page-screenshot-blocking-negative",
                logs_dir,
            )
            stage["commands"].append(stale_page_check_result)
            for label, ok, actual in (
                ("fixture_page_screenshot_blocking_negative_status", stale_page_check_result["returncode"] != 0, stale_page_check_result["returncode"]),
                (
                    "fixture_page_screenshot_blocking_negative_section",
                    "Blocking chapter 5 page screenshot issues:" in stale_page_check_stdout,
                    "Blocking chapter 5 page screenshot issues:" in stale_page_check_stdout,
                ),
                (
                    "fixture_page_screenshot_blocking_negative_reason",
                    "assigned to another section" in stale_page_check_stdout or "missing required page screenshot" in stale_page_check_stdout,
                    stale_page_check_stdout,
                ),
            ):
                assertion = {"label": label, "ok": ok, "actual": actual}
                stage["assertions"].append(assertion)
                _require(assertion["ok"], "fixture chapter 5 page screenshot regression did not trigger as expected")

            chapter5_path.write_text(chapter5_page_text, encoding="utf-8")

            restored_page_check_cmd = [sys.executable, str(cli_path), "check-workspace", "--config", str(config_path)]
            restored_page_check_result, restored_page_check_stdout, _ = _run_command(
                restored_page_check_cmd,
                "11-check-workspace-page-screenshot-blocking-restored",
                logs_dir,
            )
            stage["commands"].append(restored_page_check_result)
            for label, ok, actual in (
                ("fixture_page_screenshot_blocking_restored_status", restored_page_check_result["returncode"] == 0, restored_page_check_result["returncode"]),
                (
                    "fixture_page_screenshot_blocking_restored_none",
                    "Blocking chapter 5 page screenshot issues:\n  - none" in restored_page_check_stdout,
                    "Blocking chapter 5 page screenshot issues:\n  - none" in restored_page_check_stdout,
                ),
            ):
                assertion = {"label": label, "ok": ok, "actual": actual}
                stage["assertions"].append(assertion)
                _require(assertion["ok"], "fixture chapter 5 page screenshot regression did not clear after restore")

        fixture_ai_config = read_json(config_path)
        fixture_ai_image_generation = dict(fixture_ai_config.get("image_generation") or {})
        fixture_ai_image_generation["enabled"] = True
        fixture_ai_image_generation["provider"] = "zetatechs-gemini"
        fixture_ai_config["image_generation"] = fixture_ai_image_generation
        fixture_ai_config["reference_extraction"] = {
            "enabled": True,
            "provider": "zetatechs-gemini",
            "base_url": "https://api.zetatechs.com",
            "api_key_env": "NEWAPI_API_KEY",
            "default_model": "gemini-3.1-flash-image-preview",
            "timeout_sec": 180,
            "output_dir": "docs/images/reference_guides",
        }
        fixture_guide_markdown = fixture_workspace / "docs" / "reference_inputs" / "fixture-use-case-guide.md"
        fixture_guide_markdown.parent.mkdir(parents=True, exist_ok=True)
        fixture_guide_markdown.write_text(
            "\n".join(
                [
                    "# 传统 UML 用例图要点",
                    "",
                    "- 参与者使用小人。",
                    "- 用例使用椭圆。",
                    "- 系统边界使用矩形框，参与者在外、用例在内。",
                    "- 普通关联线用于角色和用例之间的关系。",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        fixture_guide_image = fixture_workspace / "docs" / "reference_inputs" / "fixture-use-case-example.png"
        Image.new("RGB", (240, 160), (255, 255, 255)).save(fixture_guide_image)
        fixture_structure_markdown = fixture_workspace / "docs" / "reference_inputs" / "fixture-structure-guide.md"
        fixture_structure_markdown.write_text(
            "\n".join(
                [
                    "# 传统系统功能结构图要点",
                    "",
                    "- 顶层系统名称居中置顶。",
                    "- 一级模块横向展开。",
                    "- 二级子功能在对应模块下纵向展开。",
                    "- 使用矩形框和清晰的正交连接线。",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        fixture_ai_config["reference_guide_specs"] = {
            "fixture-use-case-guide": {
                "enabled": True,
                "guide_type": "use_case",
                "description": "自测试用：传统 UML 用例图规范抽取。",
                "sources": [
                    {
                        "kind": "markdown",
                        "path": str(fixture_guide_markdown.relative_to(fixture_workspace)),
                        "role": "text-spec",
                    },
                    {
                        "kind": "image",
                        "path": str(fixture_guide_image.relative_to(fixture_workspace)),
                        "role": "symbol-style",
                        "note": "仅用于测试图像来源被正确登记。",
                    },
                ],
                "extract_focus": ["符号规范", "布局规范", "关系规范", "禁止项"],
            },
            "fixture-structure-guide": {
                "enabled": True,
                "guide_type": "function_structure",
                "description": "自测试用：传统系统功能结构图规范抽取。",
                "sources": [
                    {
                        "kind": "markdown",
                        "path": str(fixture_structure_markdown.relative_to(fixture_workspace)),
                        "role": "text-spec",
                    },
                    {
                        "kind": "image",
                        "path": str(mapped_figure5_path.relative_to(fixture_workspace)),
                        "role": "layout-style",
                        "note": "仅用于测试 function_structure guide 能读取已冻结样图。",
                    },
                ],
                "extract_focus": ["树状层级", "模块框样式", "正交连线", "禁止项"],
            }
        }
        fixture_ai_config["ai_figure_specs"] = {
            "5.1": {
                "caption": "图5.1 系统功能结构图",
                "chapter": "05-系统实现.md",
                "intent": "展示系统名称、一级功能模块及代表性子功能之间的树状结构关系，整体保持论文技术图风格。",
                "diagram_type": "function_structure",
                "style_notes": "参考图仅用于继承树状布局、模块分组与白底黑线风格；重新清理图内文字，不保留任何旧标题、边缘装饰或英文字样。",
                "enabled": True,
                "override_builtin": True,
                "reference_guides": ["missing-structure-guide"],
                "reference_images": [
                    {
                        "path": str(mapped_figure5_path.relative_to(fixture_workspace)),
                        "role": "layout-reference",
                        "note": "仅参考当前 5.1 的树状层级、模块分组和线框布局，不要求复刻原图像素。",
                    }
                ],
            }
        }
        write_json(config_path, fixture_ai_config)

        guide_prepare_cmd = [
            sys.executable,
            str(cli_path),
            "prepare-reference-guides",
            "--config",
            str(config_path),
            "--guide",
            "fixture-use-case-guide",
            "--dry-run",
        ]
        guide_prepare_result, _, _ = _run_command(
            guide_prepare_cmd,
            "10-prepare-reference-guides-dry-run",
            logs_dir,
        )
        stage["commands"].append(guide_prepare_result)
        _require(guide_prepare_result["returncode"] == 0, "fixture prepare-reference-guides --dry-run failed")

        guide_summary_path = fixture_workspace / "word_output" / "reference_guide_prepare_summary.json"
        guide_manifest_path = fixture_workspace / "docs" / "images" / "reference_guides" / "manifest.json"
        for path in (guide_summary_path, guide_manifest_path):
            assertion = {"label": f"fixture_reference_guide_artifact:{path.name}", "ok": path.exists(), "path": str(path)}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], f"fixture reference guide artifact missing: {path}")

        guide_summary = read_json(guide_summary_path)
        guide_prepared = list(guide_summary.get("prepared_guides") or [])
        guide_manifest = read_json(guide_manifest_path)
        guide_manifest_entry = ((guide_manifest.get("guides") or {}).get("fixture-use-case-guide") or {})
        for label, ok, actual in (
            ("fixture_reference_guide_dry_run_status", len(guide_prepared) == 1, len(guide_prepared)),
            (
                "fixture_reference_guide_manifest_markdown_source",
                ((guide_manifest_entry.get("sources") or [{}])[0].get("kind") == "markdown"),
                ((guide_manifest_entry.get("sources") or [{}])[0].get("kind")),
            ),
            (
                "fixture_reference_guide_manifest_image_source",
                any(str(item.get("kind") or "") == "image" for item in (guide_manifest_entry.get("sources") or [])),
                guide_manifest_entry.get("sources") or [],
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture reference guide dry-run regression failed")

        structure_guide_prepare_cmd = [
            sys.executable,
            str(cli_path),
            "prepare-reference-guides",
            "--config",
            str(config_path),
            "--guide",
            "fixture-structure-guide",
            "--dry-run",
        ]
        structure_guide_prepare_result, _, _ = _run_command(
            structure_guide_prepare_cmd,
            "10b-prepare-reference-guides-dry-run-function-structure",
            logs_dir,
        )
        stage["commands"].append(structure_guide_prepare_result)
        _require(
            structure_guide_prepare_result["returncode"] == 0,
            "fixture prepare-reference-guides --dry-run failed for function_structure guide",
        )

        guide_summary = read_json(guide_summary_path)
        guide_prepared = list(guide_summary.get("prepared_guides") or [])
        guide_manifest = read_json(guide_manifest_path)
        structure_manifest_entry = ((guide_manifest.get("guides") or {}).get("fixture-structure-guide") or {})
        for label, ok, actual in (
            ("fixture_structure_guide_dry_run_status", len(guide_prepared) == 1, len(guide_prepared)),
            (
                "fixture_structure_guide_manifest_type",
                str(structure_manifest_entry.get("guide_type") or "") == "function_structure",
                structure_manifest_entry.get("guide_type"),
            ),
            (
                "fixture_structure_guide_manifest_image_source",
                any(str(item.get("kind") or "") == "image" for item in (structure_manifest_entry.get("sources") or [])),
                structure_manifest_entry.get("sources") or [],
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture function_structure guide regression failed")

        ai_missing_guide_cmd = [
            sys.executable,
            str(cli_path),
            "prepare-ai-figures",
            "--config",
            str(config_path),
            "--fig",
            "5.1",
            "--dry-run",
        ]
        ai_missing_guide_result, _, ai_missing_guide_stderr = _run_command(
            ai_missing_guide_cmd,
            "11-prepare-ai-figures-dry-run-missing-guide",
            logs_dir,
        )
        stage["commands"].append(ai_missing_guide_result)
        for label, ok, actual in (
            ("fixture_ai_missing_guide_status", ai_missing_guide_result["returncode"] != 0, ai_missing_guide_result["returncode"]),
            (
                "fixture_ai_missing_guide_reason",
                "missing-structure-guide" in ai_missing_guide_stderr,
                ai_missing_guide_stderr,
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture AI missing-guide regression did not trigger as expected")

        reference_guides_dir = fixture_workspace / "docs" / "images" / "reference_guides"
        reference_guides_dir.mkdir(parents=True, exist_ok=True)
        manual_guide_name = "fixture-manual-structure"
        manual_guide_json = reference_guides_dir / f"{manual_guide_name}.json"
        write_json(
            manual_guide_json,
            {
                "schema_version": 1,
                "guide_name": manual_guide_name,
                "guide_type": "function_structure",
                "description": "自测试手工 guide",
                "summary": "树状功能结构图应采用白底黑线、顶层居中、子模块分层展开的传统论文版式。",
                "symbol_rules": ["所有模块使用矩形框。"],
                "layout_rules": ["顶层系统名称置顶，一级模块横向展开，二级模块在对应一级模块下纵向展开。"],
                "relationship_rules": ["使用清晰的正交或垂直连接线表达层级。"],
                "text_rules": ["图内文字应简洁统一。"],
                "forbidden_rules": ["不要渐变、不要海报式装饰、不要图内重复图题。"],
                "common_failure_modes": ["不要把树状图画成流程图。"],
                "prompt_fragments": {
                    "must": ["白底黑线", "树状层级清晰"],
                    "avoid": ["不要装饰性图标"],
                    "layout": ["顶层居中，一级横向，二级纵向"],
                    "style": ["传统论文技术图风格"],
                    "text": ["中文标签精炼统一"],
                },
                "spec_hash": "fixture-manual-guide",
            },
        )

        fixture_ai_config = read_json(config_path)
        fixture_ai_config["ai_figure_specs"]["5.1"]["reference_guides"] = [manual_guide_name]
        write_json(config_path, fixture_ai_config)

        ai_prepare_cmd = [
            sys.executable,
            str(cli_path),
            "prepare-ai-figures",
            "--config",
            str(config_path),
            "--fig",
            "5.1",
            "--dry-run",
        ]
        ai_prepare_result, _, _ = _run_command(
            ai_prepare_cmd,
            "12-prepare-ai-figures-dry-run-reference-guide",
            logs_dir,
        )
        stage["commands"].append(ai_prepare_result)
        _require(ai_prepare_result["returncode"] == 0, "fixture prepare-ai-figures --dry-run failed for reference-guide workflow")

        ai_summary_path = fixture_workspace / "word_output" / "ai_figure_prepare_summary.json"
        ai_prompt_manifest_path = fixture_workspace / "docs" / "images" / "generated_ai" / "prompt_manifest.json"
        for path in (ai_summary_path, ai_prompt_manifest_path):
            assertion = {"label": f"fixture_ai_artifact:{path.name}", "ok": path.exists(), "path": str(path)}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], f"fixture AI figure artifact missing: {path}")

        ai_summary = read_json(ai_summary_path)
        ai_prepared = list(ai_summary.get("prepared_figures") or [])
        ai_manifest = read_json(ai_prompt_manifest_path)
        ai_manifest_entry = ((ai_manifest.get("figures") or {}).get("5.1") or {})
        expected_reference_rel = str(mapped_figure5_path.relative_to(fixture_workspace))
        for label, ok, actual in (
            ("fixture_ai_prepare_dry_run_status", len(ai_prepared) == 1, len(ai_prepared)),
            (
                "fixture_ai_prepare_reference_path",
                ((ai_manifest_entry.get("reference_images") or [{}])[0].get("path") == expected_reference_rel),
                ((ai_manifest_entry.get("reference_images") or [{}])[0].get("path")),
            ),
            (
                "fixture_ai_prepare_reference_guide_name",
                ((ai_manifest_entry.get("reference_guides") or [{}])[0].get("guide_name") == manual_guide_name),
                ((ai_manifest_entry.get("reference_guides") or [{}])[0].get("guide_name")),
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture AI reference-guide prompt manifest regression failed")

        ai_preflight_cmd = [sys.executable, str(cli_path), "release-preflight", "--config", str(config_path)]
        ai_preflight_result, ai_preflight_stdout, _ = _run_command(
            ai_preflight_cmd,
            "13-release-preflight-ai-override-missing-image",
            logs_dir,
        )
        stage["commands"].append(ai_preflight_result)
        for label, ok, actual in (
            ("fixture_ai_preflight_missing_status", ai_preflight_result["returncode"] != 0, ai_preflight_result["returncode"]),
            (
                "fixture_ai_preflight_missing_section",
                "Blocking AI figure override issues:" in ai_preflight_stdout,
                "Blocking AI figure override issues:" in ai_preflight_stdout,
            ),
            (
                "fixture_ai_preflight_missing_figure_no",
                "5.1" in ai_preflight_stdout,
                "5.1" in ai_preflight_stdout,
            ),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture AI override blocking regression did not trigger as expected")

        brief_dir = fixture_workspace / "docs" / "writing" / "chapter_briefs"
        packet_dir = fixture_workspace / "docs" / "writing" / "chapter_packets"
        chapter_queue_path = fixture_workspace / "docs" / "writing" / "chapter_queue.json"
        brief5 = brief_dir / "05-系统实现.md"
        brief6 = brief_dir / "06-系统测试.md"
        packet5 = packet_dir / "05-系统实现.md"
        packet6 = packet_dir / "06-系统测试.md"

        for path in (brief5, brief6, packet5, packet6, chapter_queue_path):
            stage["assertions"].append({"label": f"exists:{path.name}", "ok": path.exists(), "path": str(path)})
            _require(path.exists(), f"expected fixture artifact missing: {path}")

        brief5_text = brief5.read_text(encoding="utf-8")
        brief6_text = brief6.read_text(encoding="utf-8")
        packet5_text = packet5.read_text(encoding="utf-8")
        packet6_text = packet6.read_text(encoding="utf-8")

        for expected in CHAPTER5_BRIEF_EXPECTED:
            assertion = _assert_contains(brief5_text, expected, f"brief5:{expected}")
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture Chapter 5 brief is missing code screenshot constraints")
        for expected in CHAPTER5_PACKET_EXPECTED:
            assertion = _assert_contains(packet5_text, expected, f"packet5:{expected}")
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture Chapter 5 packet is missing inline code screenshot rules")
        for expected in CHAPTER6_BRIEF_EXPECTED:
            assertion = _assert_contains(brief6_text, expected, f"brief6:{expected}")
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture Chapter 6 brief is missing test-evidence constraints")
        for expected in CHAPTER6_PACKET_EXPECTED:
            assertion = _assert_contains(packet6_text, expected, f"packet6:{expected}")
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "fixture Chapter 6 packet is missing testing chapter rules")

        queue = read_json(chapter_queue_path)
        entries = {entry.get("chapter"): entry for entry in queue.get("chapters", [])}
        for chapter in ("05-系统实现.md", "06-系统测试.md"):
            entry = entries.get(chapter) or {}
            packet_status = str(entry.get("packet_outline_status") or "")
            assertion = {
                "label": f"chapter_queue:{chapter}:packet_outline_status",
                "ok": packet_status == "current",
                "actual": packet_status,
            }
            stage["assertions"].append(assertion)
            _require(assertion["ok"], f"{chapter} packet_outline_status is not current in fixture workspace")

    except SelftestFailure as exc:
        stage["status"] = 1
        stage["error"] = str(exc)

    return stage


def _run_workspace_stage(config_path: Path, out_root: Path) -> dict[str, Any]:
    logs_dir = out_root / "logs" / "workspace"
    cli_path = _bundle_cli_path()
    stage: dict[str, Any] = {
        "name": "workspace",
        "config_path": str(config_path),
        "commands": [],
        "assertions": [],
        "status": 0,
        "error": "",
        "docx_path": "",
    }

    try:
        _require(config_path.exists(), f"workspace config not found: {config_path}")

        resume_cmd = [sys.executable, str(cli_path), "resume", "--config", str(config_path), "--json"]
        resume_result, resume_stdout, _ = _run_command(resume_cmd, "01-resume", logs_dir)
        stage["commands"].append(resume_result)
        _require(resume_result["returncode"] == 0, "resume failed for workspace selftest")
        resume_payload = json.loads(resume_stdout)

        signature_status = str(resume_payload.get("bundle", {}).get("signature_status") or "")
        lock_status = str(resume_payload.get("lock", {}).get("state") or "")
        stage["assertions"].append(
            {
                "label": "workspace_signature_status",
                "ok": signature_status == "current",
                "actual": signature_status,
            }
        )
        _require(
            signature_status == "current",
            f"workspace is drifted; run `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config {config_path}` first",
        )
        stage["assertions"].append({"label": "workspace_lock_status", "ok": lock_status == "unlocked", "actual": lock_status})
        _require(
            lock_status == "unlocked",
            f"workspace lock is {lock_status}; inspect with `python3 workflow_bundle/tools/cli.py lock-status --config {config_path}` before selftest",
        )

        preflight_cmd = [sys.executable, str(cli_path), "release-preflight", "--config", str(config_path)]
        preflight_result, _, _ = _run_command(preflight_cmd, "02-release-preflight", logs_dir)
        stage["commands"].append(preflight_result)
        _require(preflight_result["returncode"] == 0, "release-preflight failed for workspace selftest")

        build_cmd = [
            sys.executable,
            str(cli_path),
            "release-build",
            "--config",
            str(config_path),
            "--output-name",
            SELFTEST_DOCX_NAME,
        ]
        build_result, _, _ = _run_command(build_cmd, "03-release-build", logs_dir)
        stage["commands"].append(build_result)
        _require(build_result["returncode"] == 0, "release-build failed for workspace selftest")

        verify_cmd = [
            sys.executable,
            str(cli_path),
            "release-verify",
            "--config",
            str(config_path),
            "--output-name",
            SELFTEST_DOCX_NAME,
        ]
        verify_result, _, _ = _run_command(verify_cmd, "04-release-verify", logs_dir)
        stage["commands"].append(verify_result)
        _require(verify_result["returncode"] == 0, "release-verify failed for workspace selftest")

        ctx = load_workspace_context(config_path)
        output_dir = ctx["workspace_root"] / ctx["config"].get("build", {}).get("output_dir", "word_output")
        build_summary_path = output_dir / "build_summary.json"
        release_summary_path = output_dir / "release_summary.json"
        figure_prepare_summary_path = output_dir / "figure_prepare_summary.json"
        docx_path = resolve_output_docx_path(config_path, SELFTEST_DOCX_NAME)
        stage["docx_path"] = str(docx_path)

        for path in (docx_path, build_summary_path, release_summary_path, figure_prepare_summary_path):
            assertion = {"label": f"exists:{path.name}", "ok": path.exists(), "path": str(path)}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], f"expected workspace release artifact missing: {path}")

        release_summary = read_json(release_summary_path)
        citation_verify = release_summary.get("citation_verify", {})
        anchors_missing = int(citation_verify.get("anchors_missing_bookmarks", -1))
        ref_fields = int(citation_verify.get("ref_fields", -1))
        bookmarks = int(citation_verify.get("bookmarks", -1))
        for label, ok, actual in (
            ("anchors_missing_bookmarks", anchors_missing == 0, anchors_missing),
            ("citation_ref_fields_present", ref_fields >= 0, ref_fields),
            ("citation_bookmarks_present", bookmarks >= 0, bookmarks),
            ("citation_ref_bookmark_match", ref_fields == bookmarks, f"{ref_fields} vs {bookmarks}"),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], f"workspace release summary failed assertion: {label}={actual}")

        enabled_er_specs = _enabled_er_specs(ctx["config"])
        enabled_plantuml_specs = _enabled_plantuml_specs(ctx["config"])
        generated_src_dir = ctx["workspace_root"] / "docs" / "images" / "generated_src"
        for figure_no, er_spec in enabled_er_specs.items():
            figure_cfg = (ctx["config"].get("figure_map") or {}).get(figure_no, {})
            assertion = {
                "label": f"workspace_er_renderer:{figure_no}",
                "ok": str(figure_cfg.get("renderer") or "") == "dbdia-er",
                "actual": str(figure_cfg.get("renderer") or ""),
            }
            stage["assertions"].append(assertion)
            _require(assertion["ok"], f"workspace er figure {figure_no} renderer mismatch: expected dbdia-er")

            output_name = str(er_spec.get("output_name") or "").strip() or _default_er_output_name(figure_no)
            stem = Path(output_name).stem
            for filename in (f"{stem}.dbdia", f"{stem}.dot", f"{stem}.svg"):
                path = generated_src_dir / filename
                assertion = {
                    "label": f"workspace_er_sidecar:{figure_no}:{filename}",
                    "ok": path.exists(),
                    "path": str(path),
                }
                stage["assertions"].append(assertion)
                _require(assertion["ok"], f"workspace er sidecar missing for figure {figure_no}: {path}")

        for figure_no, plantuml_spec in enabled_plantuml_specs.items():
            figure_cfg = (ctx["config"].get("figure_map") or {}).get(figure_no, {})
            assertion = {
                "label": f"workspace_plantuml_renderer:{figure_no}",
                "ok": str(figure_cfg.get("renderer") or "") == "plantuml",
                "actual": str(figure_cfg.get("renderer") or ""),
            }
            stage["assertions"].append(assertion)
            _require(assertion["ok"], f"workspace plantuml figure {figure_no} renderer mismatch: expected plantuml")

            output_name = str(plantuml_spec.get("output_name") or "").strip() or _default_plantuml_output_name(figure_no)
            stem = Path(output_name).stem
            for filename in (f"{stem}.puml", f"{stem}.svg"):
                path = generated_src_dir / filename
                assertion = {
                    "label": f"workspace_plantuml_sidecar:{figure_no}:{filename}",
                    "ok": path.exists(),
                    "path": str(path),
                }
                stage["assertions"].append(assertion)
                _require(assertion["ok"], f"workspace plantuml sidecar missing for figure {figure_no}: {path}")

        chapter5_path = ctx["workspace_root"] / ctx["config"].get("build", {}).get("input_dir", "polished_v3") / "05-系统实现.md"
        chapter5_text = chapter5_path.read_text(encoding="utf-8") if chapter5_path.exists() else ""
        chapter5_image_entries: list[dict[str, str]] = []
        for match in re.finditer(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)", chapter5_text):
            rel = str(match.group("path") or "").strip().split()[0] if str(match.group("path") or "").strip() else ""
            if rel:
                chapter5_image_entries.append({"alt": str(match.group("alt") or "").strip(), "path": rel})
        chapter5_image_refs = [entry["path"] for entry in chapter5_image_entries]
        chapter5_missing_images = [
            rel for rel in chapter5_image_refs if not (chapter5_path.parent / rel).resolve().exists()
        ]
        assertion = {
            "label": "chapter5_markdown_image_refs_exist",
            "ok": not chapter5_missing_images,
            "missing": chapter5_missing_images,
        }
        stage["assertions"].append(assertion)
        _require(assertion["ok"], f"chapter 5 contains broken markdown image refs: {chapter5_missing_images}")
        chapter5_page_screenshot_refs = [rel for rel in chapter5_image_refs if "docs/images/chapter5/" in rel]
        project_profile_path = ctx["workspace_root"] / "docs" / "writing" / "project_profile.json"
        required_page_screenshots = 0
        chapter5_packet_paths: list[str] = []
        chapter5_resolved_image_map = {
            str((chapter5_path.parent / rel).resolve()): rel
            for rel in chapter5_image_refs
        }
        packet_json_path = ctx["workspace_root"] / "docs" / "writing" / "chapter_packets" / "05-系统实现.json"
        if packet_json_path.exists():
            packet_payload = read_json(packet_json_path)
            for item in packet_payload.get("asset_to_section_map", []):
                if item.get("asset_type") != "figures" or not item.get("required"):
                    continue
                workspace_image_path = str(item.get("workspace_image_path", "") or "").strip()
                if not workspace_image_path:
                    continue
                chapter5_packet_paths.append(workspace_image_path)
        if chapter5_packet_paths:
            required_page_screenshots = len(chapter5_packet_paths)
        elif project_profile_path.exists():
            project_profile = read_json(project_profile_path)
            for asset in project_profile.get("chapter_profile", {}).get("05-系统实现.md", {}).get("required_assets", []):
                if asset.get("asset_type") != "figures" or asset.get("kind") != "test-screenshot":
                    continue
                required_page_screenshots += int(asset.get("min_count", 1) or 1)
        if required_page_screenshots > 0:
            if chapter5_packet_paths:
                required_paths = sorted(set(chapter5_packet_paths))
                chapter5_page_screenshot_refs = []
                matched_required_paths: list[str] = []
                for rel in required_paths:
                    resolved = str((ctx["workspace_root"] / rel).resolve())
                    matched = chapter5_resolved_image_map.get(resolved, "")
                    if matched:
                        chapter5_page_screenshot_refs.append(matched)
                        matched_required_paths.append(rel)
                missing_required_paths = [rel for rel in required_paths if rel not in matched_required_paths]
                screenshots_ok = not missing_required_paths
            else:
                chapter5_page_screenshot_refs = [rel for rel in chapter5_image_refs if "docs/images/chapter5/" in rel]
                missing_required_paths = []
                screenshots_ok = len(chapter5_page_screenshot_refs) >= required_page_screenshots
            assertion = {
                "label": "chapter5_page_screenshot_refs",
                "ok": screenshots_ok,
                "actual": len(chapter5_page_screenshot_refs),
                "expected_min": required_page_screenshots,
                "matched_refs": chapter5_page_screenshot_refs,
                "expected_refs": chapter5_packet_paths,
                "missing_expected_refs": missing_required_paths,
            }
            stage["assertions"].append(assertion)
            _require(
                assertion["ok"],
                f"chapter 5 page screenshots missing or mismatched: expected={chapter5_packet_paths} missing={missing_required_paths}",
            )
        docx_xml = _inspect_docx_xml(docx_path)
        image_extents_cm = _extract_docx_image_extents_cm(docx_xml)
        max_image_height_cm = max((height for _, height in image_extents_cm), default=0.0)
        max_image_width_cm = max((width for width, _ in image_extents_cm), default=0.0)
        for label, ok, actual in (
            ("docx_max_image_height_cm", max_image_height_cm <= 21.0, round(max_image_height_cm, 2)),
            ("docx_max_image_width_cm", max_image_width_cm <= 16.0, round(max_image_width_cm, 2)),
        ):
            assertion = {"label": label, "ok": ok, "actual": actual}
            stage["assertions"].append(assertion)
            _require(assertion["ok"], f"workspace DOCX image layout overflow detected: {label}={actual}")
        if "docs/materials/code_screenshots/" in chapter5_text:
            assertion = {
                "label": "code_screenshot_caption_removed",
                "ok": "关键代码截图" not in docx_xml,
            }
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "exported DOCX still contains code screenshot caption paragraphs")
        if "<!-- figure:5.1 -->" in chapter5_text:
            assertion = {
                "label": "normal_figure_caption_preserved",
                "ok": "图5.1" in docx_xml,
            }
            stage["assertions"].append(assertion)
            _require(assertion["ok"], "exported DOCX lost the normal numbered figure caption for figure 5.1")

        lock_cmd = [sys.executable, str(cli_path), "lock-status", "--config", str(config_path), "--json"]
        lock_result, lock_stdout, _ = _run_command(lock_cmd, "05-lock-status", logs_dir)
        stage["commands"].append(lock_result)
        _require(lock_result["returncode"] == 0, "lock-status failed after workspace selftest")
        lock_payload = json.loads(lock_stdout)
        assertion = {"label": "workspace_lock_released", "ok": str(lock_payload.get("state") or "") == "unlocked"}
        stage["assertions"].append(assertion)
        _require(assertion["ok"], "workspace lock was not released after selftest release commands")

    except SelftestFailure as exc:
        stage["status"] = 1
        stage["error"] = str(exc)

    return stage


def run_selftest(workspace_config: Path | None = None, out_root: Path | None = None) -> dict[str, Any]:
    created_out_root = Path(out_root).resolve() if out_root else Path(tempfile.mkdtemp(prefix="workflow_bundle_selftest_")).resolve()
    created_out_root.mkdir(parents=True, exist_ok=True)
    pointer_existed, pointer_content = _load_active_workspace_pointer()

    summary: dict[str, Any] = {
        "generated_at": _now_iso(),
        "bundle": bundle_version_info(),
        "bundle_root": str(PRIMARY_WORKFLOW_ROOT),
        "out_root": str(created_out_root),
        "summary_json": str(created_out_root / "selftest_summary.json"),
        "status": 0,
        "fixture": {},
        "workspace": {},
        "error": "",
    }

    try:
        fixture_stage = _run_fixture_stage(created_out_root)
        summary["fixture"] = fixture_stage
        if fixture_stage["status"] != 0:
            raise SelftestFailure(fixture_stage["error"] or "fixture selftest failed")

        if workspace_config:
            workspace_stage = _run_workspace_stage(Path(workspace_config).resolve(), created_out_root)
            summary["workspace"] = workspace_stage
            if workspace_stage["status"] != 0:
                raise SelftestFailure(workspace_stage["error"] or "workspace selftest failed")

    except SelftestFailure as exc:
        summary["status"] = 1
        summary["error"] = str(exc)
    finally:
        _restore_active_workspace_pointer(pointer_existed, pointer_content)
        write_json(Path(summary["summary_json"]), summary)

    return summary
