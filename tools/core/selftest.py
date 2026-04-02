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

from core.build_final_thesis_docx import resolve_output_docx_path
from core.project_common import load_workspace_context, read_json, write_json
from core.runtime_state import ACTIVE_WORKSPACE_POINTER_PATH


THIS_ROOT = Path(__file__).resolve().parents[2]
if THIS_ROOT.name == "workflow_bundle":
    PRIMARY_WORKFLOW_ROOT = THIS_ROOT
else:
    PRIMARY_WORKFLOW_ROOT = THIS_ROOT / "workflow_bundle"

FIXTURE_PROJECT_ROOT = PRIMARY_WORKFLOW_ROOT / "workflow" / "fixtures" / "fabric_trace_demo"
SELFTEST_DOCX_NAME = "selftest_release.docx"
CHAPTER5_BRIEF_EXPECTED = [
    "代码截图仅作为实现证据插图使用，不编号，不写“图5.x”题注，也不单独形成图题段落。",
    "若使用代码截图，必须紧跟在对应的后端或前端代码块之后插入，不能单独生成“关键代码截图”小节。",
]
CHAPTER5_PACKET_EXPECTED = [
    "Code screenshots in chapter 5 are inline implementation evidence only; do not assign figure numbers, `图5.x` captions, or separate caption paragraphs to them.",
    "If code screenshots are used, insert them immediately after the matching backend or frontend code block inside that same subfunction; do not create a standalone `关键代码截图` subsection.",
]
CHAPTER6_BRIEF_EXPECTED = [
    "第 6 章按样稿式测试章节来写，不写成压缩版测试总结。",
    "6.1 环境配置、6.2 功能测试、6.3 非功能测试均应优先保留真实表格。",
]
CHAPTER6_PACKET_EXPECTED = [
    "For chapter 6, follow the sample-like testing chapter pattern rather than a compressed summary style.",
    "Section 6.2 must keep one dedicated function-test subsection per core module, and each subsection must contain its required table as an actual markdown table before the explanatory paragraph.",
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


def _inspect_docx_xml(docx_path: Path) -> str:
    with zipfile.ZipFile(docx_path) as zf:
        return zf.read("word/document.xml").decode("utf-8", errors="replace")


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

        chapter5_path = ctx["workspace_root"] / ctx["config"].get("build", {}).get("input_dir", "polished_v3") / "05-系统实现.md"
        chapter5_text = chapter5_path.read_text(encoding="utf-8") if chapter5_path.exists() else ""
        docx_xml = _inspect_docx_xml(docx_path)
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
