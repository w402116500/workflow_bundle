from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from core.project_common import CHAIN_LABELS, build_workspace_config, make_relative, read_text_safe, slugify_name, write_json, write_text
from core.runtime_state import append_workspace_execution_log, refresh_workspace_handoff, set_active_workspace, sync_workspace_workflow_assets


TEXT_SUFFIXES = {".md", ".txt", ".java", ".go", ".sol", ".js", ".ts", ".tsx", ".json", ".yaml", ".yml", ".sh", ".properties", ".xml", ".sql"}
IGNORED_PARTS = {"node_modules", ".git", "__pycache__", "word_output"}


def _read_small_text(path: Path) -> str:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return ""
    try:
        if path.stat().st_size > 256_000:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _is_ignored(path: Path, project_root: Path) -> bool:
    try:
        rel = path.relative_to(project_root)
    except Exception:
        return False
    if any(part in IGNORED_PARTS for part in rel.parts):
        return True
    if any(part.startswith("unpacked_") for part in rel.parts):
        return True
    rel_str = str(rel).replace("\\", "/")
    if rel_str.startswith("workflow/fixtures/"):
        return True
    return False


def _score_chain_platform(project_root: Path) -> tuple[dict[str, int], list[str]]:
    scores = {"fisco": 0, "fabric": 0}
    reasons: list[str] = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if _is_ignored(path, project_root):
            continue
        text = _read_small_text(path)
        rel = path.relative_to(project_root)
        rel_str = str(rel).lower()

        if path.suffix.lower() == ".sol":
            scores["fisco"] += 4
            reasons.append(f"FISCO indicator: Solidity contract {rel}")
        if "fisco bcos" in text.lower() or "web3sdk" in text.lower() or "org.fisco" in text.lower():
            scores["fisco"] += 3
            reasons.append(f"FISCO indicator in {rel}")

        if "hyperledger fabric" in text.lower() or "fabric-samples" in text.lower():
            scores["fabric"] += 3
            reasons.append(f"Fabric indicator in {rel}")
        if "contractapi" in text.lower() or "peer chaincode" in text.lower() or "orderer" in text.lower():
            scores["fabric"] += 3
            reasons.append(f"Fabric indicator in {rel}")
        if "chaincode" in rel_str or rel.name.lower() == "network.sh":
            scores["fabric"] += 2
            reasons.append(f"Fabric path indicator: {rel}")
    return scores, reasons


def detect_chain_platform(project_root: Path, requested: str) -> tuple[str, str, list[str]]:
    if requested in {"fisco", "fabric"}:
        return requested, "explicit", [f"chain platform fixed by user: {requested}"]

    scores, reasons = _score_chain_platform(project_root)
    platform = "fisco" if scores["fisco"] >= scores["fabric"] else "fabric"
    confidence = "high" if abs(scores["fisco"] - scores["fabric"]) >= 3 else "medium"
    if scores["fisco"] == 0 and scores["fabric"] == 0:
        platform = "fisco"
        confidence = "low"
        reasons.append("no strong chain indicator found; defaulted to fisco")
    return platform, confidence, reasons


def _find_candidate_dirs(project_root: Path, names: list[str]) -> list[Path]:
    found: list[Path] = []
    for path in project_root.rglob("*"):
        if _is_ignored(path, project_root):
            continue
        if path.is_dir() and path.name.lower() in names:
            found.append(path)
    return sorted(found, key=lambda p: (len(p.parts), str(p)))


def _find_first_matching_file(project_root: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(path for path in project_root.rglob(pattern) if not _is_ignored(path, project_root))
        if matches:
            return matches[0]
    return None


def detect_source_paths(project_root: Path, chain_platform: str) -> dict[str, str]:
    frontend = None
    backend = None
    chain_path = None

    for candidate in _find_candidate_dirs(project_root, ["frontend", "web", "ui", "client"]):
        if list(candidate.rglob("*.vue")) or list(candidate.rglob("*.tsx")) or (candidate / "package.json").exists():
            frontend = candidate
            break

    for candidate in _find_candidate_dirs(project_root, ["backend", "server", "api"]):
        if list(candidate.rglob("*Controller.java")) or list(candidate.rglob("*.go")) or list(candidate.rglob("*.js")):
            backend = candidate
            break

    if chain_platform == "fisco":
        for candidate in _find_candidate_dirs(project_root, ["contracts", "contract"]):
            if list(candidate.rglob("*.sol")):
                chain_path = candidate
                break
        if chain_path is None:
            sol_file = _find_first_matching_file(project_root, ["*.sol"])
            chain_path = sol_file.parent if sol_file else None
    else:
        for candidate in _find_candidate_dirs(project_root, ["chaincode", "chaincodes"]):
            if list(candidate.rglob("*.go")) or list(candidate.rglob("*.js")):
                chain_path = candidate
                break
        if chain_path is None:
            go_file = _find_first_matching_file(project_root, ["*chaincode*.go", "*.go"])
            if go_file and "contractapi" in _read_small_text(go_file).lower():
                chain_path = go_file.parent

    database = _find_first_matching_file(project_root, ["init.sql", "schema.sql", "*.sql"])
    ops_doc = project_root / "README.md" if (project_root / "README.md").exists() else _find_first_matching_file(
        project_root,
        [
            "network.sh",
            "docker-compose.yml",
            "docker-compose.yaml",
            "project-start.sh",
            "*部署说明*.md",
            "*启动脚本说明*.md",
        ],
    )
    overview_docs = sorted((project_root / "docs").glob("*.md")) if (project_root / "docs").exists() else []
    if not overview_docs:
        overview_docs = sorted(
            path
            for path in project_root.glob("*.md")
            if path.name not in {"AGENTS.md", "README.md"} and "测试" not in path.name
        )

    source_paths = {
        "frontend": make_relative(frontend, project_root) if frontend else "",
        "backend": make_relative(backend, project_root) if backend else "",
        "database": make_relative(database, project_root) if database else "",
        "contracts": "",
        "chaincode": "",
        "ops_docs": make_relative(ops_doc, project_root) if ops_doc else "",
        "overview_docs": "docs" if overview_docs else (make_relative(project_root / "README.md", project_root) if (project_root / "README.md").exists() else ""),
    }
    if chain_platform == "fisco":
        source_paths["contracts"] = make_relative(chain_path, project_root) if chain_path else ""
    else:
        source_paths["chaincode"] = make_relative(chain_path, project_root) if chain_path else ""
    return source_paths


def detect_document_paths(project_root: Path) -> dict[str, list[str]]:
    docs: list[Path] = []
    if (project_root / "docs").exists():
        docs.extend(sorted((project_root / "docs").rglob("*.md")))
    if (project_root / "README.md").exists():
        docs.append(project_root / "README.md")
    docs.extend(
        sorted(
            path
            for path in project_root.glob("*.md")
            if path.name not in {"AGENTS.md", "README.md"}
        )
    )

    rel_docs = list(dict.fromkeys(make_relative(path, project_root) for path in docs))
    requirements = [p for p in rel_docs if re.search(r"requirement|需求|任务书|功能模块|规划", p, re.IGNORECASE)]
    design = [p for p in rel_docs if re.search(r"design|架构|计划|方案|设计|接口|数据库|链码|部署说明|启动脚本说明|总体项目文档", p, re.IGNORECASE)]
    references = [p for p in rel_docs if re.search(r"reference|文献|研究现状", p, re.IGNORECASE)]
    writing_rules = [p for p in rel_docs if re.search(r"writing|论文|guide|规范|任务书", p, re.IGNORECASE)]

    if not requirements and rel_docs:
        requirements = rel_docs[:1]
    if not design and len(rel_docs) > 1:
        design = rel_docs[1:3]

    return {
        "requirements": requirements,
        "design": design,
        "references": references,
        "writing_rules": writing_rules,
    }


def detect_stack(project_root: Path, source_paths: dict[str, str], chain_platform: str) -> dict[str, str]:
    frontend_framework = "unknown"
    backend_framework = "unknown"
    database_kind = "unknown"
    chain_sdk = CHAIN_LABELS[chain_platform]

    frontend_dir = project_root / source_paths["frontend"] if source_paths.get("frontend") else None
    if frontend_dir and frontend_dir.exists():
        if list(frontend_dir.rglob("*.vue")):
            frontend_framework = "vue"
        elif list(frontend_dir.rglob("*.tsx")) or list(frontend_dir.rglob("*.jsx")):
            frontend_framework = "react"

    backend_dir = project_root / source_paths["backend"] if source_paths.get("backend") else None
    if backend_dir and backend_dir.exists():
        go_text = "\n".join(_read_small_text(p) for p in backend_dir.rglob("*.go"))
        java_text = "\n".join(_read_small_text(p) for p in backend_dir.rglob("*.java"))
        if "@springbootapplication" in java_text.lower() or "@restcontroller" in java_text.lower():
            backend_framework = "spring-boot"
        elif "github.com/gin-gonic/gin" in go_text.lower() or "gin.default()" in go_text.lower() or "gin.new()" in go_text.lower():
            backend_framework = "gin"
        elif "express(" in java_text.lower():
            backend_framework = "express"

    database_file = project_root / source_paths["database"] if source_paths.get("database") else None
    if database_file and database_file.exists():
        sql_text = _read_small_text(database_file).lower()
        if "innodb" in sql_text or "mysql" in sql_text:
            database_kind = "mysql"
        elif "postgres" in sql_text:
            database_kind = "postgresql"
        else:
            database_kind = "sql"

    if chain_platform == "fisco":
        chain_sdk = "fisco-java-sdk" if backend_dir and "fisco" in "\n".join(_read_small_text(p) for p in backend_dir.rglob("*.java")).lower() else "fisco-bcos"
    else:
        chain_sdk = "fabric-contract-api" if source_paths.get("chaincode") else "hyperledger-fabric"

    return {
        "frontend_framework": frontend_framework,
        "backend_framework": backend_framework,
        "database_kind": database_kind,
        "chain_sdk": chain_sdk,
    }


def _collect_missing_inputs(source_paths: dict[str, str], document_paths: dict[str, list[str]], chain_platform: str) -> list[str]:
    missing: list[str] = []
    required_sources = ["frontend", "backend", "database", "ops_docs"]
    required_sources.append("contracts" if chain_platform == "fisco" else "chaincode")
    for key in required_sources:
        if not source_paths.get(key):
            missing.append(f"missing source path: {key}")
    for key in ["requirements", "design"]:
        if not document_paths.get(key):
            missing.append(f"missing document category: {key}")
    return missing


def _render_intake_report(title: str, project_root: Path, workspace_root: Path, chain_platform: str, confidence: str, reasons: list[str], source_paths: dict[str, str], doc_paths: dict[str, list[str]], stack: dict[str, str], missing: list[str]) -> str:
    lines = [
        f"# Intake Report",
        "",
        f"- title: {title}",
        f"- project_root: {project_root}",
        f"- workspace_root: {workspace_root}",
        f"- chain_platform: {chain_platform}",
        f"- detection_confidence: {confidence}",
        "",
        "## Detection Reasons",
    ]
    lines.extend([f"- {reason}" for reason in reasons] or ["- no detection reason captured"])
    lines.extend(["", "## Source Paths"])
    lines.extend([f"- {key}: `{value or 'MISSING'}`" for key, value in source_paths.items()])
    lines.extend(["", "## Document Paths"])
    for key, values in doc_paths.items():
        lines.append(f"- {key}:")
        if values:
            lines.extend([f"  - `{value}`" for value in values])
        else:
            lines.append("  - `MISSING`")
    lines.extend(["", "## Detected Stack"])
    lines.extend([f"- {key}: `{value}`" for key, value in stack.items()])
    lines.extend(["", "## Missing Inputs"])
    lines.extend([f"- {item}" for item in missing] or ["- none"])
    return "\n".join(lines) + "\n"
def run_intake(project_root: Path, title: str, out_dir: Path, discipline: str | None = None, chain: str = "auto") -> dict[str, Any]:
    project_root = project_root.resolve()
    workspace_root = out_dir.resolve()
    chain_platform, confidence, reasons = detect_chain_platform(project_root, chain)
    source_paths = detect_source_paths(project_root, chain_platform)
    document_paths = detect_document_paths(project_root)
    stack = detect_stack(project_root, source_paths, chain_platform)
    missing_inputs = _collect_missing_inputs(source_paths, document_paths, chain_platform)

    workspace_root.mkdir(parents=True, exist_ok=True)
    for rel in [
        "workflow/configs",
        "workflow/skills/academic-paper-crafter",
        "workflow/skills/thesis-workflow-resume",
        "workflow/skills/thesis-workflow-orchestrator",
        "workflow/skills/paper-research-agent",
        "workflow/skills/paper-reader",
        "docs/materials",
        "docs/workflow",
        "docs/tasks",
        "docs/writing/chapter_packets",
        "docs/writing/chapter_briefs",
        "docs/writing/review",
        "docs/writing/research",
        "docs/images",
        "polished_v3",
        "word_output",
    ]:
        (workspace_root / rel).mkdir(parents=True, exist_ok=True)

    manifest = {
        "project_id": slugify_name(title),
        "title": title,
        "discipline": discipline or "计算机类",
        "project_type": "blockchain-fullstack",
        "project_root": str(project_root),
        "chain_platform": chain_platform,
        "detection_confidence": confidence,
        "source_of_truth": {
            "thesis": "polished_v3",
            "evidence_docs": "docs/materials",
            "evidence_code": str(project_root),
            "generated_output": "word_output",
        },
        "source_paths": source_paths,
        "document_paths": document_paths,
        "detected_stack": stack,
        "missing_inputs": missing_inputs,
    }
    config = build_workspace_config(project_root, title, workspace_root, chain_platform, discipline)

    manifest_path = workspace_root / "workflow" / "configs" / "project_manifest.json"
    config_path = workspace_root / "workflow" / "configs" / "workspace.json"
    report_path = workspace_root / "docs" / "materials" / "intake_report.md"
    write_json(manifest_path, manifest)
    write_json(config_path, config)
    sync_result = sync_workspace_workflow_assets(config_path)
    write_text(
        report_path,
        _render_intake_report(title, project_root, workspace_root, chain_platform, confidence, reasons, source_paths, document_paths, stack, missing_inputs),
    )
    set_active_workspace(config_path)
    refresh_workspace_handoff(config_path, trigger="intake", command="intake")
    append_workspace_execution_log(
        config_path,
        "intake",
        {
            "workspace_root": str(workspace_root),
            "project_root": str(project_root),
            "title": title,
            "chain_platform": chain_platform,
            "workflow_assets_state_json": sync_result["workflow_assets_state_json"],
            "bundle_signature": sync_result["bundle_signature"],
        },
    )

    return {
        "workspace_root": workspace_root,
        "config_path": config_path,
        "manifest_path": manifest_path,
        "report_path": report_path,
        "chain_platform": chain_platform,
    }
