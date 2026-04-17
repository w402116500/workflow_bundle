from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any


THIS_ROOT = Path(__file__).resolve().parents[2]
if THIS_ROOT.name == "workflow_bundle":
    PRIMARY_WORKFLOW_ROOT = THIS_ROOT
else:
    PRIMARY_WORKFLOW_ROOT = THIS_ROOT / "workflow_bundle" if (THIS_ROOT / "workflow_bundle").exists() else THIS_ROOT

BUNDLE_VERSION_FILE = PRIMARY_WORKFLOW_ROOT / "VERSION"
SEMVER_TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def read_bundle_version() -> str:
    if not BUNDLE_VERSION_FILE.exists():
        return "0.0.0-dev"
    value = BUNDLE_VERSION_FILE.read_text(encoding="utf-8").strip()
    return value or "0.0.0-dev"


def bundle_version_tag(version: str | None = None) -> str:
    resolved = (version or read_bundle_version()).strip()
    if resolved.startswith("v"):
        return resolved
    return f"v{resolved}"


def _run_git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", "-C", str(PRIMARY_WORKFLOW_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return (completed.stdout or "").strip()


def _latest_semver_tag() -> str:
    raw = _run_git(["tag", "--sort=-v:refname"])
    if not raw:
        return ""
    for line in raw.splitlines():
        tag = line.strip()
        if SEMVER_TAG_PATTERN.match(tag):
            return tag
    return ""


def bundle_version_info() -> dict[str, Any]:
    version = read_bundle_version()
    commit_full = _run_git(["rev-parse", "HEAD"])
    commit_short = _run_git(["rev-parse", "--short", "HEAD"])
    dirty = bool(_run_git(["status", "--short"]))
    latest_tag = _latest_semver_tag()
    return {
        "version": version,
        "tag": bundle_version_tag(version),
        "version_file": str(BUNDLE_VERSION_FILE),
        "is_prerelease": "-" in version,
        "git_commit": commit_short,
        "git_commit_full": commit_full,
        "git_dirty": dirty,
        "latest_semver_tag": latest_tag,
    }


def bundle_version_line(include_commit: bool = True) -> str:
    info = bundle_version_info()
    line = f"workflow_bundle {info['version']}"
    if include_commit and info.get("git_commit"):
        line += f" ({info['git_commit']}"
        if info.get("git_dirty"):
            line += ", dirty"
        line += ")"
    return line
