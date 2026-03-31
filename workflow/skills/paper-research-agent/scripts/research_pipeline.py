#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from research_sidecar import build_research_index, run_research_sidecar  # type: ignore  # noqa: E402
except Exception:
    def _resolve_tools_dir() -> Path:
        current = Path(__file__).resolve()
        for candidate in [current.parent, *current.parents]:
            tools_dir = candidate / "tools"
            if (tools_dir / "core" / "research_sidecar.py").exists():
                return tools_dir
        raise RuntimeError("cannot locate repo tools directory for research pipeline")

    TOOLS_DIR = _resolve_tools_dir()
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from core.research_sidecar import build_research_index, run_research_sidecar  # type: ignore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Paper Research Agent sidecar pipeline.")
    parser.add_argument("--query", action="append", required=True, help="Research query. Repeat to provide multiple queries.")
    parser.add_argument("--max-papers", type=int, default=10)
    parser.add_argument("--output", required=True, help="Research sidecar output directory")
    parser.add_argument("--reader-script-rel", default="workflow/skills/paper-reader/scripts/read_paper.py")
    parser.add_argument("--standards-rel", default="workflow/skills/paper-research-agent/references/analysis_standards.md")
    args = parser.parse_args()

    research_dir = Path(args.output).resolve()
    summary = run_research_sidecar(
        queries=args.query,
        research_dir=research_dir,
        max_papers=args.max_papers,
        reader_script_rel=args.reader_script_rel,
        standards_rel=args.standards_rel,
    )
    build_research_index(
        summary=summary,
        research_dir=research_dir,
        research_index_json=research_dir / "_research_index.json",
        research_index_md=research_dir / "_research_index.md",
    )
    print(f"status: {summary['status']}")
    print(f"papers_found: {summary['papers_found']}")
    print(f"papers_downloaded: {summary['papers_downloaded']}")
    print(f"analysis_count: {summary['analysis_count']}")
    return 0 if summary["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
