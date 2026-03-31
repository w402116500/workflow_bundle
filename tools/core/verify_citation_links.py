from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path


def inspect_citation_links(docx_path: Path) -> dict[str, object]:
    docx_path = docx_path.resolve()
    if not docx_path.exists():
        return {
            "docx_path": str(docx_path),
            "ref_fields": 0,
            "bookmarks": 0,
            "anchors_missing_bookmarks": 0,
            "missing": [],
            "status": 2,
            "error": f"not found: {docx_path}",
        }

    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")

    ref_fields = set(re.findall(r" REF (ref_\d+)\b", xml))
    bookmarks = set(re.findall(r'w:name="(ref_\d+)"', xml))
    missing = sorted(ref_fields - bookmarks)
    return {
        "docx_path": str(docx_path),
        "ref_fields": len(ref_fields),
        "bookmarks": len(bookmarks),
        "anchors_missing_bookmarks": len(missing),
        "missing": missing,
        "status": 1 if missing else 0,
        "error": "",
    }


def verify_citation_links(docx_path: Path) -> int:
    result = inspect_citation_links(docx_path)
    if result["status"] == 2:
        print(str(result["error"]), file=sys.stderr)
        return 2

    print(f"docx: {result['docx_path']}")
    print(f"ref fields: {result['ref_fields']}")
    print(f"bookmarks: {result['bookmarks']}")
    print(f"anchors missing bookmarks: {result['anchors_missing_bookmarks']}")
    missing = list(result["missing"])
    if missing:
        print("missing (first 30):")
        for x in missing[:30]:
            print(f"  - {x}")
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
