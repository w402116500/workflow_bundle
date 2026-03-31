#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


def _load_optional_modules() -> tuple[Any, Any]:
    pdfplumber = None
    fitz = None
    try:
        import pdfplumber as _pdfplumber  # type: ignore

        pdfplumber = _pdfplumber
    except Exception:
        pdfplumber = None
    try:
        import fitz as _fitz  # type: ignore

        fitz = _fitz
    except Exception:
        fitz = None
    return pdfplumber, fitz


PDFPLUMBER, FITZ = _load_optional_modules()


def _require_text_reader() -> None:
    if PDFPLUMBER is None and FITZ is None:
        print("missing dependencies: need `pdfplumber` or `pymupdf` to read PDFs", file=sys.stderr)
        raise SystemExit(1)


def _extract_text(pdf_path: Path) -> str:
    if PDFPLUMBER is not None:
        chunks: list[str] = []
        with PDFPLUMBER.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                chunks.append(page.extract_text() or "")
        return "\n\n".join(chunks)
    if FITZ is not None:
        doc = FITZ.open(str(pdf_path))
        try:
            return "\n\n".join(page.get_text("text") for page in doc)
        finally:
            doc.close()
    return ""


def _extract_metadata(pdf_path: Path) -> dict[str, Any]:
    if FITZ is None:
        return {"source_file": str(pdf_path)}
    doc = FITZ.open(str(pdf_path))
    try:
        metadata = doc.metadata or {}
        metadata["page_count"] = doc.page_count
        metadata["source_file"] = str(pdf_path)
        return metadata
    finally:
        doc.close()


def _split_sections(text: str) -> dict[str, str]:
    pattern = re.compile(r"(?m)^(abstract|introduction|related work|background|method|methods|approach|experiment|experiments|results|discussion|conclusion|conclusions|references)\s*$", re.IGNORECASE)
    matches = list(pattern.finditer(text))
    if not matches:
        return {"01_Full_Text": text}

    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        key = f"{idx + 1:02d}_{re.sub(r'[^A-Za-z0-9]+', '_', title).strip('_') or 'Section'}"
        sections[key] = text[start:end].strip()
    return sections


def _extract_tables(pdf_path: Path, output_dir: Path) -> int:
    if PDFPLUMBER is None:
        return 0
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    with PDFPLUMBER.open(str(pdf_path)) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            try:
                tables = page.extract_tables() or []
            except Exception:
                tables = []
            for table_idx, table in enumerate(tables, start=1):
                csv_path = output_dir / f"table_{page_idx}_{table_idx}.csv"
                with csv_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.writer(handle)
                    for row in table:
                        writer.writerow(row or [])
                count += 1
    return count


def _extract_images(pdf_path: Path, output_dir: Path) -> int:
    if FITZ is None:
        return 0
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    doc = FITZ.open(str(pdf_path))
    try:
        for page_idx, page in enumerate(doc, start=1):
            for image_idx, image in enumerate(page.get_images(full=True), start=1):
                xref = image[0]
                image_data = doc.extract_image(xref)
                ext = image_data.get("ext", "png")
                img_path = output_dir / f"fig_{page_idx}_{image_idx}.{ext}"
                img_path.write_bytes(image_data["image"])
                count += 1
    finally:
        doc.close()
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Read a paper PDF and extract text/sections/tables/images.")
    parser.add_argument("pdf_path")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--text", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--images", action="store_true")
    parser.add_argument("--tables", action="store_true")
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else pdf_path.with_suffix("")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.text or args.full or (not args.images and not args.tables):
        _require_text_reader()
        text = _extract_text(pdf_path)
        (output_dir / "paper.txt").write_text(text, encoding="utf-8")
        (output_dir / "metadata.json").write_text(json.dumps(_extract_metadata(pdf_path), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        sections_dir = output_dir / "sections"
        sections_dir.mkdir(parents=True, exist_ok=True)
        for name, content in _split_sections(text).items():
            (sections_dir / f"{name}.txt").write_text(content + "\n", encoding="utf-8")

    if args.tables or args.full:
        _extract_tables(pdf_path, output_dir / "tables")

    if args.images or args.full:
        _extract_images(pdf_path, output_dir / "figures")

    print(f"output_dir: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
