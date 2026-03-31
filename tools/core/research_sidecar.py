from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import requests

from core.project_common import write_json, write_text


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_FALLBACK_URL = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _base_arxiv_id(arxiv_id: str) -> str:
    return arxiv_id.split("v")[0]


def _safe_name(text: str, limit: int = 80) -> str:
    normalized = re.sub(r"[^\w\s-]+", "", text, flags=re.UNICODE)
    normalized = re.sub(r"\s+", "_", normalized).strip("_")
    return (normalized or "paper")[:limit]


def _reader_deps_status() -> dict[str, bool]:
    status: dict[str, bool] = {}
    for module_name, import_name in [("pdfplumber", "pdfplumber"), ("pymupdf", "fitz"), ("Pillow", "PIL")]:
        try:
            __import__(import_name)
            status[module_name] = True
        except Exception:
            status[module_name] = False
    return status


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "thesis-workflow/1.0 (academic writing tooling; contact: local-workspace)",
            "Accept": "application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        }
    )
    return session


def _search_arxiv(query: str, max_results: int = 10, timeout: int = 30) -> list[dict[str, Any]]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    errors: list[str] = []
    session = _session()
    response = None
    for base_url in [ARXIV_API_URL, ARXIV_FALLBACK_URL]:
        for attempt in range(3):
            try:
                response = session.get(base_url, params=params, timeout=timeout)
                if response.status_code == 429:
                    wait_seconds = 5 * (attempt + 1)
                    errors.append(f"{base_url} returned 429, retrying in {wait_seconds}s")
                    time.sleep(wait_seconds)
                    continue
                response.raise_for_status()
                root = ET.fromstring(response.text)
                break
            except Exception as exc:
                errors.append(f"{base_url} attempt {attempt + 1} failed: {exc}")
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
        else:
            continue
        break
    if response is None or "root" not in locals():
        raise RuntimeError("; ".join(errors) if errors else "arxiv query failed")

    papers: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        entry_id = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
        title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip()
        published = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
        authors = [(author.findtext("atom:name", default="", namespaces=ATOM_NS) or "").strip() for author in entry.findall("atom:author", ATOM_NS)]
        categories = [item.attrib.get("term", "") for item in entry.findall("atom:category", ATOM_NS)]
        pdf_url = ""
        for link in entry.findall("atom:link", ATOM_NS):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href", "")
                break
        arxiv_id = entry_id.rsplit("/", 1)[-1] if entry_id else ""
        papers.append(
            {
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": [author for author in authors if author],
                "summary": re.sub(r"\s+", " ", summary),
                "published": published,
                "pdf_url": pdf_url,
                "url": entry_id,
                "categories": [item for item in categories if item],
                "source_query": query,
            }
        )
    return papers


def _download_pdfs(papers: list[dict[str, Any]], papers_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    downloaded: list[dict[str, Any]] = []
    papers_dir.mkdir(parents=True, exist_ok=True)
    session = _session()
    for paper in papers:
        pdf_url = paper.get("pdf_url", "")
        if not pdf_url:
            errors.append(f"{paper.get('arxiv_id', 'unknown')}: missing pdf url")
            continue
        filename = f"{_safe_name(paper.get('title', 'paper'))}-{paper.get('arxiv_id', 'unknown')}.pdf"
        pdf_path = papers_dir / filename
        if pdf_path.exists():
            paper["pdf_path"] = str(pdf_path)
            downloaded.append(paper)
            continue
        last_error = None
        for attempt in range(3):
            try:
                response = session.get(pdf_url, timeout=60)
                if response.status_code == 429:
                    time.sleep(5 * (attempt + 1))
                    continue
                response.raise_for_status()
                pdf_path.write_bytes(response.content)
                paper["pdf_path"] = str(pdf_path)
                downloaded.append(paper)
                time.sleep(2)
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                time.sleep(2 * (attempt + 1))
        if last_error is not None:
            errors.append(f"{paper.get('arxiv_id', 'unknown')}: pdf download failed: {last_error}")
    return downloaded, errors


def _analysis_output_path(analysis_dir: Path, paper: dict[str, Any]) -> Path:
    return analysis_dir / f"{_safe_name(paper.get('title', 'paper'))}-{paper.get('arxiv_id', 'unknown')}_analysis.md"


def _generate_agent_task(
    paper: dict[str, Any],
    output_md: Path,
    reader_script_rel: str,
    standards_rel: str,
) -> str:
    pdf_path = paper.get("pdf_path", "")
    extracted_dir = output_md.parent.parent / "extracted" / output_md.stem
    return f"""【Paper Research Agent - Deep Analysis Task】

📄 Paper Information:
- Title: {paper.get('title', '')}
- ArXiv ID: {paper.get('arxiv_id', '')}
- PDF Path: {pdf_path}
- Output Report: {output_md}
- Analysis Standard: {standards_rel}

Step 1: Read `{standards_rel}`.
Step 2: Use paper reader to extract the full paper:
```bash
python3 {reader_script_rel} "{pdf_path}" --full --output-dir "{extracted_dir}"
```
Step 3: Based on the extracted sections/tables/figures, write a 6-section analysis report to `{output_md}`.

Strict rules:
- Read the full paper rather than only the abstract.
- Use exact data from extracted tables when available.
- Do not fabricate citations, numbers, conclusions, or missing sections.
- Mark uncertain information explicitly.
"""


def _write_agent_tasks(
    downloaded_papers: list[dict[str, Any]],
    research_dir: Path,
    reader_script_rel: str,
    standards_rel: str,
) -> list[dict[str, Any]]:
    task_dir = research_dir / "agent_tasks"
    analysis_dir = research_dir / "analysis"
    task_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    tasks: list[dict[str, Any]] = []
    for idx, paper in enumerate(downloaded_papers, start=1):
        output_md = _analysis_output_path(analysis_dir, paper)
        task = _generate_agent_task(paper, output_md, reader_script_rel, standards_rel)
        task_path = task_dir / f"task_{paper.get('arxiv_id', idx)}.txt"
        write_text(task_path, task)
        tasks.append(
            {
                "id": idx,
                "paper": paper,
                "task_file": str(task_path),
                "output_report": str(output_md),
                "task": task,
            }
        )
    write_json(research_dir / "_agent_tasks.json", tasks)
    return tasks


def _summarize_papers(research_dir: Path, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    analysis_dir = research_dir / "analysis"
    items: list[dict[str, Any]] = []
    for paper in papers:
        analysis_path = _analysis_output_path(analysis_dir, paper)
        published = paper.get("published", "")
        year = 0
        if published[:4].isdigit():
            year = int(published[:4])
        items.append(
            {
                "arxiv_id": paper.get("arxiv_id", ""),
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "year": year,
                "published": published,
                "summary": paper.get("summary", ""),
                "url": paper.get("url", ""),
                "pdf_url": paper.get("pdf_url", ""),
                "pdf_path": paper.get("pdf_path", ""),
                "analysis_path": str(analysis_path),
                "analysis_exists": analysis_path.exists(),
                "source_query": paper.get("source_query", ""),
            }
        )
    return items


def render_research_index_md(index: dict[str, Any]) -> str:
    lines = [
        "# Research Index",
        "",
        f"- generated_at: {index['generated_at']}",
        f"- status: {index['status']}",
        f"- papers_found: {index['papers_found']}",
        f"- papers_downloaded: {index['papers_downloaded']}",
        f"- analysis_count: {index['analysis_count']}",
        f"- task_count: {index['task_count']}",
        "",
        "## Queries",
        "",
    ]
    lines.extend([f"- {query}" for query in index.get("queries_used", [])] or ["- none"])
    lines.extend(["", "## Reader Dependencies", ""])
    for name, ok in index.get("reader_dependencies", {}).items():
        lines.append(f"- {name}: {'ok' if ok else 'missing'}")
    lines.extend(["", "## Errors", ""])
    lines.extend([f"- {error}" for error in index.get("errors", [])] or ["- none"])
    lines.extend(["", "## Papers", "", "| id | year | title | downloaded | analyzed | source_query |", "|---|---:|---|---|---|---|"])
    for item in index.get("papers", []):
        lines.append(
            f"| {item['arxiv_id'] or '-'} | {item['year'] or '-'} | {item['title']} | {'yes' if item['pdf_path'] else 'no'} | {'yes' if item['analysis_exists'] else 'no'} | {item['source_query']} |"
        )
    if not index.get("papers"):
        lines.append("| - | - | no papers | - | - | - |")
    return "\n".join(lines) + "\n"


def run_research_sidecar(
    queries: list[str],
    research_dir: Path,
    max_papers: int,
    reader_script_rel: str,
    standards_rel: str,
) -> dict[str, Any]:
    research_dir.mkdir(parents=True, exist_ok=True)
    papers_dir = research_dir / "papers"
    analysis_dir = research_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    query_attempts: list[dict[str, Any]] = []
    errors: list[str] = []
    dedup: dict[str, dict[str, Any]] = {}

    for query in queries[:3]:
        try:
            results = _search_arxiv(query, max_results=max_papers * 2)
            query_attempts.append({"query": query, "count": len(results)})
            for paper in results:
                base_id = _base_arxiv_id(paper.get("arxiv_id", ""))
                if base_id and base_id not in dedup:
                    dedup[base_id] = paper
                if len(dedup) >= max_papers:
                    break
        except Exception as exc:
            query_attempts.append({"query": query, "count": 0, "error": str(exc)})
            errors.append(f"query `{query}` failed: {exc}")
        if len(dedup) >= max_papers:
            break

    papers = list(dedup.values())[:max_papers]
    downloaded: list[dict[str, Any]] = []
    if papers:
        downloaded, download_errors = _download_pdfs(papers, papers_dir)
        errors.extend(download_errors)

    tasks = _write_agent_tasks(downloaded, research_dir, reader_script_rel, standards_rel) if downloaded else []
    analysis_count = len(list(analysis_dir.glob("*_analysis.md")))
    if analysis_count > 0:
        status = "analyses_present"
    elif papers:
        status = "prepared"
    else:
        status = "failed"

    summary_papers = _summarize_papers(research_dir, papers)
    summary = {
        "generated_at": _now_iso(),
        "status": status,
        "queries_used": [item["query"] for item in query_attempts],
        "query_attempts": query_attempts,
        "papers_found": len(papers),
        "papers_downloaded": len(downloaded),
        "analysis_count": analysis_count,
        "task_count": len(tasks),
        "reader_dependencies": _reader_deps_status(),
        "errors": errors,
        "papers": summary_papers,
    }
    write_json(research_dir / "_research_summary.json", summary)
    return summary


def build_research_index(
    summary: dict[str, Any],
    research_dir: Path,
    research_index_json: Path,
    research_index_md: Path,
) -> dict[str, Any]:
    index = {
        "generated_at": _now_iso(),
        "status": summary.get("status", "failed"),
        "research_dir": str(research_dir),
        "queries_used": summary.get("queries_used", []),
        "papers_found": summary.get("papers_found", 0),
        "papers_downloaded": summary.get("papers_downloaded", 0),
        "analysis_count": summary.get("analysis_count", 0),
        "task_count": summary.get("task_count", 0),
        "reader_dependencies": summary.get("reader_dependencies", {}),
        "errors": summary.get("errors", []),
        "papers": summary.get("papers", []),
    }
    write_json(research_index_json, index)
    write_text(research_index_md, render_research_index_md(index))
    return index


def build_registry_fallback_index(
    registry_entries: list[dict[str, Any]],
    research_dir: Path,
    research_index_json: Path,
    research_index_md: Path,
    base_errors: list[str],
) -> dict[str, Any]:
    papers: list[dict[str, Any]] = []
    for entry in registry_entries[:10]:
        papers.append(
            {
                "arxiv_id": "",
                "title": entry.get("title", ""),
                "authors": entry.get("authors", []),
                "year": entry.get("year", 0),
                "published": str(entry.get("year", "")),
                "summary": entry.get("abstract_excerpt", ""),
                "url": entry.get("url", "") or (f"https://doi.org/{entry['doi']}" if entry.get("doi") else ""),
                "pdf_url": "",
                "pdf_path": "",
                "analysis_path": "",
                "analysis_exists": False,
                "source_query": entry.get("source_query", ""),
                "source": entry.get("source", "crossref"),
                "fallback_from_registry": True,
            }
        )
    fallback_payload = {
        "generated_at": _now_iso(),
        "source": "reference_registry",
        "papers": papers,
    }
    write_json(research_dir / "_registry_fallback.json", fallback_payload)
    index = {
        "generated_at": _now_iso(),
        "status": "metadata_only",
        "research_dir": str(research_dir),
        "queries_used": [],
        "papers_found": len(papers),
        "papers_downloaded": 0,
        "analysis_count": 0,
        "task_count": 0,
        "reader_dependencies": _reader_deps_status(),
        "errors": list(base_errors) + ["research sidecar fell back to reference registry metadata"],
        "papers": papers,
    }
    write_json(research_index_json, index)
    write_text(research_index_md, render_research_index_md(index))
    return index


def research_papers_to_registry_entries(papers: list[dict[str, Any]], extract_theme_keywords: Any) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for paper in papers:
        text_for_theme = " ".join([paper.get("title", ""), paper.get("summary", "")])
        published = paper.get("published", "")
        year = int(published[:4]) if published[:4].isdigit() else 0
        entries.append(
            {
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "year": year,
                "venue": "arXiv",
                "doi": "",
                "url": paper.get("url") or paper.get("pdf_url", ""),
                "type": "preprint",
                "themes": sorted(extract_theme_keywords(text_for_theme)),
                "abstract_excerpt": paper.get("summary", "")[:600],
                "source_query": paper.get("source_query", ""),
                "source": "arxiv",
            }
        )
    return entries
