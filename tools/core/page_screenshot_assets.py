from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any


_CHAPTER5_SELECTION_GROUP_FILENAME_MAP = {
    "identity-registration": "fig5-4-register-login.png",
    "identity-dashboard": "fig5-2-admin-dashboard.png",
    "identity-permission": "fig5-2-3-user-permission.png",
    "identity-role-default": "fig5-2-3-user-permission.png",
    "identity-route-guard": "fig5-3-forbidden-page.png",
    "identity-route-menu": "fig5-2-3-user-permission.png",
    "batch-main-flow": "fig5-5-batch-management.png",
    "record-process-flow": "fig5-6-process-records.png",
    "record-inspection-flow": "fig5-7-inspection-report.png",
    "record-logistics-flow": "fig5-8-logistics-records.png",
    "record-route-trace": "fig5-4-3-stage-progress.png",
    "trace-invalid": "fig5-5-2-trace-code-control.png",
    "trace-success": "fig5-9-public-trace.png",
    "trace-flow": "fig5-9-public-trace.png",
    "trace-route-query": "fig5-9-public-trace.png",
}

_CHAPTER5_SECTION_FILENAME_MAP = {
    "5.2.1 注册登录与会话建立实现": "fig5-4-register-login.png",
    "5.3.3 批次状态维护与全流程入口实现": "fig5-5-batch-management.png",
    "5.4.1 生产环节记录录入实现": "fig5-6-process-records.png",
    "5.5.3 公开追溯查询与结果展示实现": "fig5-9-public-trace.png",
}

_CHAPTER5_COMPAT_SOURCE_STEM_GROUP_MAP = {
    "register-five-fixed-accounts-clean": "identity-registration",
    "register-remaining-accounts": "identity-registration",
    "admin-dashboard-fixed-flow": "identity-dashboard",
    "role-admin-default": "identity-dashboard",
    "dealer-fixed-flow-forbidden": "identity-route-guard",
    "farmer-fixed-flow": "batch-main-flow",
    "processor-fixed-flow": "record-process-flow",
    "inspector-fixed-flow": "record-inspection-flow",
    "logistics-fixed-flow": "record-logistics-flow",
    "public-trace-success": "trace-success",
    "public-trace-fixed-flow": "trace-flow",
}


def _normalized_source_path(source_path: str) -> str:
    return source_path.replace("\\", "/").strip()


def _chapter5_source_file_info(asset: dict[str, Any]) -> tuple[str, str, str]:
    source_path = _normalized_source_path(str(asset.get("source_path", "") or ""))
    if ".runtime/test-artifacts/" not in source_path:
        return "", "", ""
    source = Path(source_path)
    stem = source.stem.lower()
    suffix = source.suffix.lower() or ".png"
    return source_path, stem, suffix


def _chapter5_section_candidates(asset: dict[str, Any]) -> list[str]:
    return [
        str(section).strip()
        for section in (asset.get("section_candidates") or [])
        if str(section).strip().startswith("5.")
    ]


def _chapter5_filename_from_selection_group(selection_group: str) -> str:
    return _CHAPTER5_SELECTION_GROUP_FILENAME_MAP.get(selection_group.strip().lower(), "")


def _chapter5_filename_from_section(section: str) -> str:
    if section in _CHAPTER5_SECTION_FILENAME_MAP:
        return _CHAPTER5_SECTION_FILENAME_MAP[section]
    if section == "5.2.3 用户管理与权限治理实现":
        return "fig5-2-3-user-permission.png"
    if section == "5.4.2 仓储物流等流转记录实现":
        return "fig5-4-2-record-circulation.png"
    if section == "5.5.2 溯源码管理与状态控制实现":
        return "fig5-5-2-trace-code-control.png"
    return ""


def _chapter5_workspace_target(asset: dict[str, Any]) -> tuple[str, str]:
    source_path, stem, suffix = _chapter5_source_file_info(asset)
    if not source_path:
        return "", ""

    selection_group = str(asset.get("selection_group", "") or "").strip().lower()
    filename = _chapter5_filename_from_selection_group(selection_group)
    if filename:
        return filename, "selection-group"

    for section in _chapter5_section_candidates(asset):
        filename = _chapter5_filename_from_section(section)
        if filename:
            return filename, "section-candidate"

    compat_group = _CHAPTER5_COMPAT_SOURCE_STEM_GROUP_MAP.get(stem, "")
    if compat_group:
        filename = _chapter5_filename_from_selection_group(compat_group)
        if filename:
            return filename, "legacy-source-stem"

    slug = re.sub(r"[^0-9a-z]+", "-", stem).strip("-") or "runtime-page"
    return f"{slug}{suffix}", "slug"


def chapter5_test_screenshot_workspace_relpath(asset: dict[str, Any]) -> str:
    if asset.get("asset_type") != "figures" or asset.get("kind") != "test-screenshot":
        return ""
    filename, _ = _chapter5_workspace_target(asset)
    if not filename:
        return ""
    return f"docs/images/chapter5/{filename}"


def _resolve_source_path(project_root: Path, asset: dict[str, Any]) -> Path | None:
    source_path = _normalized_source_path(str(asset.get("source_path", "") or ""))
    if not source_path:
        return None
    resolved = (project_root / source_path).resolve()
    return resolved if resolved.exists() else None


def stage_chapter5_test_screenshots(
    workspace_root: Path,
    project_root: Path,
    assets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    staged: list[dict[str, Any]] = []
    seen_targets: set[str] = set()

    for asset in assets:
        filename, name_source = _chapter5_workspace_target(asset)
        workspace_relpath = f"docs/images/chapter5/{filename}" if filename else ""
        if not workspace_relpath or workspace_relpath in seen_targets:
            continue
        seen_targets.add(workspace_relpath)

        source_path = _resolve_source_path(project_root, asset)
        target_path = (workspace_root / workspace_relpath).resolve()
        status = "missing-source"
        if source_path is not None:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if target_path.exists() and target_path.read_bytes() == source_path.read_bytes():
                status = "cached"
            else:
                status = "copied" if not target_path.exists() else "updated"
                shutil.copy2(source_path, target_path)

        staged.append(
            {
                "title": asset.get("title", ""),
                "source_path": str(source_path) if source_path else "",
                "workspace_path": workspace_relpath,
                "selection_group": str(asset.get("selection_group", "") or ""),
                "section_candidates": _chapter5_section_candidates(asset),
                "name_source": name_source,
                "status": status,
            }
        )

    return staged
