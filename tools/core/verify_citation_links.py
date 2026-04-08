from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

try:
    from core.project_common import load_workspace_context, read_text_safe
except ImportError:  # pragma: no cover - fallback for direct script execution
    from project_common import load_workspace_context, read_text_safe


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
    if result["status"] == 2:
        print(str(result["error"]), file=sys.stderr)
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
        return 1

    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify that citation REF fields have matching bookmarks.")
    parser.add_argument("docx_path", type=Path, help="Path to the generated DOCX file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return verify_citation_links(args.docx_path)


if __name__ == '__main__':
    raise SystemExit(main())
