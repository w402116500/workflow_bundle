from __future__ import annotations

import argparse
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from core.project_common import load_workspace_context, read_text_safe
except ImportError:  # pragma: no cover - fallback for direct script execution
    from project_common import load_workspace_context, read_text_safe
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{WORD_NS}}}"
W_VAL = f"{W}val"
W_FLD_CHAR_TYPE = f"{W}fldCharType"
REF_FIELD_RE = re.compile(r"(^| )REF (ref_\d+)($| )")


def _read_document_xml(docx_path: Path) -> str:
    with zipfile.ZipFile(docx_path) as z:
        return z.read("word/document.xml").decode("utf-8", errors="replace")


CODE_IMAGE_NAME_RE = re.compile(
    r"^(?:codeblock_.+|\d{2}-[a-z0-9-]+-(?:backend|frontend)-\d{2}-.+)\.(?:png|jpg|jpeg)$",
    re.IGNORECASE,
)
FIGURE_MARKER_RE = re.compile(r"<!--\s*figure:(\d+\.\d+)\s*-->")
FIGURE_CAPTION_RE = re.compile(r"^图(?P<num>\d+\.\d+)\s+(?P<title>.+?)\s*$")


def _count_toc_fields(document_xml: str) -> int:
    return len(re.findall(r'TOC\s+\\o\s+"1-3".*?\\h.*?\\z.*?\\u', document_xml))


def _count_page_fields(parts: list[str]) -> int:
    return sum(len(re.findall(r"\bPAGE\b", xml)) for xml in parts)


def _inspect_code_media_paragraphs(document_xml: str) -> dict[str, object]:
    paragraphs = re.findall(r"<w:p\b.*?</w:p>", document_xml, flags=re.DOTALL)
    code_image_paragraphs = 0
    violations: list[dict[str, object]] = []
    for paragraph_xml in paragraphs:
        image_names = [
            name
            for name in re.findall(r'name="([^"]+\.(?:png|jpg|jpeg))"', paragraph_xml, flags=re.IGNORECASE)
            if CODE_IMAGE_NAME_RE.match(name)
        ]
        if not image_names:
            continue
        code_image_paragraphs += 1
        is_single_spacing = 'w:lineRule="auto"' in paragraph_xml and 'w:line="240"' in paragraph_xml
        if is_single_spacing:
            continue
        violations.append(
            {
                "image_names": image_names[:3],
                "reason": "code/media paragraph is not using single-spacing media formatting",
            }
        )
    return {
        "code_media_paragraphs": code_image_paragraphs,
        "code_media_single_spacing_violations": len(violations),
        "code_media_violation_examples": violations[:10],
    }


def _collect_expected_figure_captions(config_path: Path | None) -> list[dict[str, str]]:
    if config_path is None:
        return []
    context = load_workspace_context(config_path)
    config = context["config"]
    workspace_root = context["workspace_root"]
    build = config.get("build", {}) or {}
    input_dir = workspace_root / build.get("input_dir", "polished_v3")
    chapter_order = list(build.get("chapter_order", []) or [])
    captions: list[dict[str, str]] = []
    seen: set[str] = set()
    for chapter_name in chapter_order:
        if not str(chapter_name).endswith(".md"):
            continue
        chapter_path = input_dir / str(chapter_name)
        if not chapter_path.exists():
            continue
        lines = read_text_safe(chapter_path).splitlines()
        for index, line in enumerate(lines):
            marker = FIGURE_MARKER_RE.search(line.strip())
            if not marker:
                continue
            figure_no = marker.group(1)
            caption = ""
            for back_index in range(index - 1, -1, -1):
                prev = lines[back_index].strip()
                if not prev:
                    continue
                match = FIGURE_CAPTION_RE.match(prev)
                if match and match.group("num") == figure_no:
                    caption = prev
                break
            if caption and caption not in seen:
                seen.add(caption)
                captions.append({"figure_no": figure_no, "caption": caption, "chapter": str(chapter_name)})
    return captions


def inspect_citation_links(docx_path: Path, config_path: Path | None = None) -> dict[str, object]:
    docx_path = docx_path.resolve()
    if not docx_path.exists():
        return {
            "docx_path": str(docx_path),
            "ref_fields": 0,
            "bookmarks": 0,
            "anchors_missing_bookmarks": 0,
            "missing": [],
            "toc_fields": 0,
            "page_fields": 0,
            "update_fields_enabled": False,
            "code_media_paragraphs": 0,
            "code_media_single_spacing_violations": 0,
            "code_media_violation_examples": [],
            "expected_figure_captions": 0,
            "missing_figure_captions": [],
            "status": 2,
            "error": f"not found: {docx_path}",
        }

    with zipfile.ZipFile(docx_path) as z:
        document_xml = z.read("word/document.xml").decode("utf-8", errors="replace")
        settings_xml = z.read("word/settings.xml").decode("utf-8", errors="replace") if "word/settings.xml" in z.namelist() else ""
        footer_parts = [
            z.read(name).decode("utf-8", errors="replace")
            for name in z.namelist()
            if name.startswith("word/footer") and name.endswith(".xml")
        ]

    ref_fields = set(re.findall(r" REF (ref_\d+)\b", document_xml))
    bookmarks = set(re.findall(r'w:name="(ref_\d+)"', document_xml))
    missing = sorted(ref_fields - bookmarks)
    toc_fields = _count_toc_fields(document_xml)
    page_fields = _count_page_fields(footer_parts)
    update_fields_enabled = "w:updateFields" in settings_xml
    code_media_check = _inspect_code_media_paragraphs(document_xml)
    expected_figure_captions = _collect_expected_figure_captions(config_path)
    missing_figure_captions = [item["caption"] for item in expected_figure_captions if item["caption"] not in document_xml]
    failed = (
        bool(missing)
        or toc_fields < 1
        or page_fields < 1
        or not update_fields_enabled
        or int(code_media_check["code_media_single_spacing_violations"]) > 0
        or bool(missing_figure_captions)
    )
    return {
        "docx_path": str(docx_path),
        "ref_fields": len(ref_fields),
        "bookmarks": len(bookmarks),
        "anchors_missing_bookmarks": len(missing),
        "missing": missing,
        "toc_fields": toc_fields,
        "page_fields": page_fields,
        "update_fields_enabled": update_fields_enabled,
        **code_media_check,
        "expected_figure_captions": len(expected_figure_captions),
        "missing_figure_captions": missing_figure_captions,
        "status": 1 if failed else 0,
        "error": "",
    }


def verify_citation_links(docx_path: Path, config_path: Path | None = None) -> int:
    result = inspect_citation_links(docx_path, config_path)
def _run_has_superscript(run_el: ET.Element) -> bool:
    rpr = run_el.find(f"{W}rPr")
    if rpr is None:
        return False
    vert = rpr.find(f"{W}vertAlign")
    return vert is not None and vert.get(W_VAL) == "superscript"


def inspect_citation_superscripts(docx_path: Path) -> dict[str, object]:
    docx_path = docx_path.resolve()
    if not docx_path.exists():
        return {
            "docx_path": str(docx_path),
            "ref_result_fields": 0,
            "missing_result_count": 0,
            "non_superscript_count": 0,
            "non_superscript_fields": [],
            "status": 2,
            "error": f"not found: {docx_path}",
        }

    xml = _read_document_xml(docx_path)
    root = ET.fromstring(xml)
    fields: list[dict[str, object]] = []

    for paragraph_index, paragraph_el in enumerate(root.iterfind(f".//{W}p")):
        paragraph_text = "".join(node.text or "" for node in paragraph_el.iterfind(f".//{W}t"))
        active_field: dict[str, object] | None = None
        for run_el in paragraph_el.iterfind(f".//{W}r"):

            fld_chars = run_el.findall(f"{W}fldChar")
            fld_type = next((node.get(W_FLD_CHAR_TYPE) for node in fld_chars if node.get(W_FLD_CHAR_TYPE)), "")
            if fld_type == "begin":
                active_field = {
                    "paragraph_index": paragraph_index,
                    "paragraph_text": paragraph_text[:160],
                    "code_parts": [],
                    "ref_id": "",
                    "capture_result": False,
                    "result_runs": [],
                }
                continue

            if active_field is None:
                continue

            instr_text_nodes = run_el.findall(f"{W}instrText")
            if instr_text_nodes:
                active_field["code_parts"].extend(node.text or "" for node in instr_text_nodes)

            if fld_type == "separate":
                code_text = " ".join("".join(str(part) for part in active_field["code_parts"]).split())
                match = REF_FIELD_RE.search(code_text)
                active_field["ref_id"] = match.group(2) if match else ""
                active_field["capture_result"] = bool(match)
                continue

            if bool(active_field.get("capture_result")):
                text_nodes = run_el.findall(f"{W}t")
                if text_nodes:
                    run_text = "".join(node.text or "" for node in text_nodes)
                    if run_text:
                        active_field["result_runs"].append(
                            {
                                "text": run_text,
                                "superscript": _run_has_superscript(run_el),
                            }
                        )

            if fld_type == "end":
                if bool(active_field.get("capture_result")):
                    result_runs = list(active_field.get("result_runs") or [])
                    result_text = "".join(str(item.get("text") or "") for item in result_runs)
                    text_runs = [item for item in result_runs if str(item.get("text") or "").strip()]
                    missing_result = not text_runs
                    non_sup_runs = [str(item.get("text") or "") for item in text_runs if item.get("superscript") is not True]
                    fields.append(
                        {
                            "ref_id": str(active_field.get("ref_id") or ""),
                            "paragraph_index": int(active_field.get("paragraph_index", -1) or -1),
                            "paragraph_text": str(active_field.get("paragraph_text") or ""),
                            "result_text": result_text,
                            "missing_result": missing_result,
                            "superscript_ok": (not missing_result) and not non_sup_runs,
                            "non_superscript_runs": non_sup_runs,
                        }
                    )
                active_field = None

    missing_result_fields = [field for field in fields if bool(field.get("missing_result"))]
    non_superscript_fields = [field for field in fields if not bool(field.get("superscript_ok"))]
    return {
        "docx_path": str(docx_path),
        "ref_result_fields": len(fields),
        "missing_result_count": len(missing_result_fields),
        "non_superscript_count": len(non_superscript_fields),
        "non_superscript_fields": non_superscript_fields[:20],
        "status": 1 if missing_result_fields or non_superscript_fields else 0,
        "error": "",
    }


def compare_citation_superscripts(base_docx_path: Path, final_docx_path: Path) -> dict[str, object]:
    base = inspect_citation_superscripts(base_docx_path)
    final = inspect_citation_superscripts(final_docx_path)
    if base["status"] == 2 or final["status"] == 2:
        return {
            "base_docx_path": str(base_docx_path.resolve()),
            "final_docx_path": str(final_docx_path.resolve()),
            "ok": False,
            "status": 2,
            "error": "; ".join(
                [msg for msg in (str(base.get("error") or ""), str(final.get("error") or "")) if msg]
            ),
        }

    ok = (
        int(base.get("ref_result_fields", -1)) == int(final.get("ref_result_fields", -2))
        and int(base.get("missing_result_count", -1)) == 0
        and int(final.get("missing_result_count", -1)) == 0
        and int(base.get("non_superscript_count", -1)) == 0
        and int(final.get("non_superscript_count", -1)) == 0
    )
    return {
        "base_docx_path": str(base_docx_path.resolve()),
        "final_docx_path": str(final_docx_path.resolve()),
        "base_ref_result_fields": int(base.get("ref_result_fields", 0)),
        "final_ref_result_fields": int(final.get("ref_result_fields", 0)),
        "base_missing_result_count": int(base.get("missing_result_count", 0)),
        "final_missing_result_count": int(final.get("missing_result_count", 0)),
        "base_non_superscript_count": int(base.get("non_superscript_count", 0)),
        "final_non_superscript_count": int(final.get("non_superscript_count", 0)),
        "ok": ok,
        "status": 0 if ok else 1,
        "error": "",
    }


def verify_citation_links(docx_path: Path, config_path: Path | None = None) -> int:
    result = inspect_citation_links(docx_path, config_path)
    superscript_audit = inspect_citation_superscripts(docx_path)
    if result["status"] == 2:
        print(str(result["error"]), file=sys.stderr)
        return 2
    if superscript_audit["status"] == 2:
        print(str(superscript_audit["error"]), file=sys.stderr)
        return 2

    print(f"docx: {result['docx_path']}")
    print(f"ref fields: {result['ref_fields']}")
    print(f"bookmarks: {result['bookmarks']}")
    print(f"anchors missing bookmarks: {result['anchors_missing_bookmarks']}")
    print(f"toc fields: {result['toc_fields']}")
    print(f"page fields: {result['page_fields']}")
    print(f"update fields enabled: {result['update_fields_enabled']}")
    print(f"code/media paragraphs: {result['code_media_paragraphs']}")
    print(f"code/media single-spacing violations: {result['code_media_single_spacing_violations']}")
    print(f"expected figure captions: {result['expected_figure_captions']}")
    print(f"missing figure captions: {len(result['missing_figure_captions'])}")
    print(f"citation ref result fields: {superscript_audit['ref_result_fields']}")
    print(f"citation missing result count: {superscript_audit['missing_result_count']}")
    print(f"citation non-superscript count: {superscript_audit['non_superscript_count']}")
    missing = list(result["missing"])
    if missing:
        print("missing (first 30):")
        for x in missing[:30]:
            print(f"  - {x}")
        return 1

    if int(result["toc_fields"]) < 1:
        print("missing TOC field in document.xml", file=sys.stderr)
        return 1
    if int(result["page_fields"]) < 1:
        print("missing PAGE field in footer XML", file=sys.stderr)
        return 1
    if not bool(result["update_fields_enabled"]):
        print("missing w:updateFields in settings.xml", file=sys.stderr)
        return 1
    if int(result["code_media_single_spacing_violations"]) > 0:
        print("code/media paragraph spacing violations (first 10):", file=sys.stderr)
        for item in list(result["code_media_violation_examples"])[:10]:
            names = ", ".join(item.get("image_names", []))
            print(f"  - {names}: {item.get('reason', '')}", file=sys.stderr)
        return 1
    if list(result["missing_figure_captions"]):
        print("missing figure captions in DOCX:", file=sys.stderr)
        for caption in list(result["missing_figure_captions"])[:20]:
            print(f"  - {caption}", file=sys.stderr)
    if superscript_audit["missing_result_count"] or superscript_audit["non_superscript_count"]:
        print("citation superscript issues (first 20):")
        for field in list(superscript_audit["non_superscript_fields"])[:20]:
            print(
                "  - "
                f"{field.get('ref_id', '')} "
                f"paragraph={field.get('paragraph_index', -1)} "
                f"result={field.get('result_text', '')!r} "
                f"non_superscript_runs={field.get('non_superscript_runs', [])}"
            )
        return 1

    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify that citation REF fields have matching bookmarks.")
    parser.add_argument("docx_path", type=Path, help="Path to the generated DOCX file.")
    parser.add_argument("--config", type=Path, default=None, help="Optional workspace config for figure/caption verification.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return verify_citation_links(args.docx_path, args.config)


if __name__ == '__main__':
    raise SystemExit(main())
