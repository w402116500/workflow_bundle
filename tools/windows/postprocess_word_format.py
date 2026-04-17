from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import win32com.client
from core.document_format import resolve_document_format


wdAlignParagraphCenter = 1
wdLineSpaceSingle = 0
wdLineSpaceExactly = 4
wdFindContinue = 1
wdActiveEndPageNumber = 3
wdColorAutomatic = 0xFF000000
wdColorBlack = 0
wdUnderlineNone = 0
wdHeaderFooterPrimary = 1
wdCollapseEnd = 0
wdFieldPage = 33
wdFieldNumPages = 26


def _load_document_format(config_path: Path | None) -> dict[str, object]:
    if config_path is None or not config_path.exists():
        return resolve_document_format({})
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return resolve_document_format(config)


def _find_paragraph_by_text(doc, text: str):
    for p in doc.Paragraphs:
        if p.Range.Text.strip() == text:
            return p
    return None


def _insert_toc_at_paragraph(doc, paragraph):
    rng = paragraph.Range
    rng.Text = ""
    doc.TablesOfContents.Add(
        Range=rng,
        UseHeadingStyles=True,
        UpperHeadingLevel=1,
        LowerHeadingLevel=3,
        IncludePageNumbers=True,
        RightAlignPageNumbers=True,
        UseHyperlinks=True,
    )


def _format_inline_shapes(doc, document_format: dict[str, object]):
    captions = dict(document_format.get("captions", {}))
    figure_caption = dict(captions.get("figure", {}))
    caption_line_spacing = float(figure_caption.get("line_spacing_pt", 23.0))
    for ishape in doc.InlineShapes:
        try:
            para = ishape.Range.Paragraphs(1)
            pf = para.Range.ParagraphFormat
            pf.Alignment = wdAlignParagraphCenter
            pf.LineSpacingRule = wdLineSpaceSingle
            pf.SpaceBefore = 12
            pf.SpaceAfter = 12
            cap_para = para.Next()
            if cap_para is not None:
                cap_para.Range.ParagraphFormat.Alignment = wdAlignParagraphCenter
                cap_para.Range.ParagraphFormat.LineSpacingRule = wdLineSpaceExactly
                cap_para.Range.ParagraphFormat.LineSpacing = caption_line_spacing
        except Exception:
            continue


def _set_no_compress_images(app):
    try:
        app.Options.DoNotCompressPicturesInFile = True
    except Exception:
        pass


def _set_styles_black(doc):
    targets = {
        "Normal",
        "Heading 1",
        "Heading 2",
        "Heading 3",
        "Hyperlink",
        "FollowedHyperlink",
        "Caption",
    }
    for i in range(1, 10):
        targets.add(f"TOC {i}")

    for name in targets:
        try:
            st = doc.Styles(name)
            st.Font.Color = wdColorBlack
            if name in {"Hyperlink", "FollowedHyperlink"}:
                st.Font.Underline = wdUnderlineNone
        except Exception:
            continue


def _set_hyperlinks_black(doc):
    try:
        for hl in doc.Hyperlinks:
            try:
                hl.Range.Font.Color = wdColorBlack
                hl.Range.Font.Underline = wdUnderlineNone
            except Exception:
                continue
    except Exception:
        pass


def _restore_reference_field_superscripts(doc):
    try:
        for field in doc.Fields:
            try:
                code_text = " ".join(str(field.Code.Text or "").split())
                if " REF ref_" not in f" {code_text} ":
                    continue
                result_range = field.Result
                result_range.Font.Superscript = True
                result_range.Font.Color = wdColorBlack
                result_range.Font.Underline = wdUnderlineNone
            except Exception:
                continue
    except Exception:
        pass


def _verify_reference_field_superscripts(doc) -> list[str]:
    failures: list[str] = []
    try:
        for field in doc.Fields:
            try:
                code_text = " ".join(str(field.Code.Text or "").split())
                match = re.search(r"(^| )REF (ref_\d+)($| )", code_text)
                if not match:
                    continue
                result_range = field.Result
                result_text = str(result_range.Text or "").strip()
                if not result_text:
                    failures.append(f"{match.group(2)}:<empty>")
                    continue
                if not bool(result_range.Font.Superscript):
                    failures.append(f"{match.group(2)}:{result_text}")
            except Exception:
                continue
    except Exception:
        pass
    return failures


def _apply_header_footer(doc, document_format: dict[str, object]):
    header_footer = dict(document_format.get("header_footer", {}))
    if not header_footer.get("enabled"):
        return

    header_text = str(header_footer.get("header_text", "") or "").strip()
    header_font_cn = str(header_footer.get("header_font_cn", "SimSun"))
    header_font_en = str(header_footer.get("header_font_en", "Times New Roman"))
    header_size = float(header_footer.get("header_size_pt", 10.5))
    footer_size = float(header_footer.get("footer_size_pt", 10.5))
    body = dict(document_format.get("body", {}))
    line_spacing = float(body.get("line_spacing_pt", 20.0))

    for index in range(1, doc.Sections.Count + 1):
        section = doc.Sections(index)

        header = section.Headers(wdHeaderFooterPrimary)
        try:
            header.LinkToPrevious = False
        except Exception:
            pass
        header_range = header.Range
        header_range.Text = header_text
        header_range.ParagraphFormat.Alignment = wdAlignParagraphCenter
        header_range.ParagraphFormat.LineSpacingRule = wdLineSpaceExactly
        header_range.ParagraphFormat.LineSpacing = line_spacing
        header_range.Font.NameFarEast = header_font_cn
        header_range.Font.Name = header_font_en
        header_range.Font.Size = header_size
        header_range.Font.Bold = False
        header_range.Font.Color = wdColorBlack

        footer = section.Footers(wdHeaderFooterPrimary)
        try:
            footer.LinkToPrevious = False
        except Exception:
            pass
        footer_range = footer.Range
        footer_range.Text = ""
        footer_range.ParagraphFormat.Alignment = wdAlignParagraphCenter
        footer_range.ParagraphFormat.LineSpacingRule = wdLineSpaceExactly
        footer_range.ParagraphFormat.LineSpacing = line_spacing
        footer_range.Font.NameFarEast = "SimSun"
        footer_range.Font.Name = "Times New Roman"
        footer_range.Font.Size = footer_size
        footer_range.Font.Bold = False
        footer_range.Font.Color = wdColorBlack
        footer_range.InsertAfter("第")
        footer_range.Collapse(wdCollapseEnd)
        doc.Fields.Add(Range=footer_range, Type=wdFieldPage)
        footer_range = footer.Range
        footer_range.Collapse(wdCollapseEnd)
        footer_range.InsertAfter("页 共")
        footer_range.Collapse(wdCollapseEnd)
        doc.Fields.Add(Range=footer_range, Type=wdFieldNumPages)
        footer_range = footer.Range
        footer_range.Collapse(wdCollapseEnd)
        footer_range.InsertAfter("页")


def _update_figure_log(doc, input_csv: Path, output_csv: Path):
    if not input_csv.exists():
        return
    rows = []
    with input_csv.open("r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for r in reader:
            rows.append(r)

    caption2page = {}
    for ishape in doc.InlineShapes:
        try:
            para = ishape.Range.Paragraphs(1)
            cap_para = para.Next()
            if cap_para is None:
                continue
            cap_text = cap_para.Range.Text.strip()
            if not cap_text.startswith("图"):
                continue
            page = cap_para.Range.Information(wdActiveEndPageNumber)
            caption2page[cap_text] = int(page)
        except Exception:
            continue

    for r in rows:
        cap = (r.get("figure_caption") or "").strip()
        if cap in caption2page:
            r["inserted_page"] = str(caption2page[cap])

    with output_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["figure_caption", "source_path", "processed_path", "inserted_page"])
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "figure_caption": r.get("figure_caption", ""),
                    "source_path": r.get("source_path", ""),
                    "processed_path": r.get("processed_path", ""),
                    "inserted_page": r.get("inserted_page", ""),
                }
            )


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input_docx")
    parser.add_argument("output_docx")
    parser.add_argument("--config", default="")
    parser.add_argument("--figlog", default="")
    parser.add_argument("--figlog_out", default="")
    args = parser.parse_args(argv)

    in_path = Path(args.input_docx).resolve()
    out_path = Path(args.output_docx).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    document_format = _load_document_format(config_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(in_path, out_path)

    app = win32com.client.DispatchEx("Word.Application")
    app.Visible = False
    app.DisplayAlerts = 0

    doc = None
    try:
        _set_no_compress_images(app)
        doc = app.Documents.Open(
            str(out_path),
            ReadOnly=False,
            AddToRecentFiles=False,
            ConfirmConversions=False,
            Revert=False,
            OpenAndRepair=True,
        )

        toc_placeholder = "（请在 Word 中插入“目录”，并更新域以生成目录。）"
        p = _find_paragraph_by_text(doc, toc_placeholder)
        if p is not None:
            _insert_toc_at_paragraph(doc, p)

        _set_styles_black(doc)
        _set_hyperlinks_black(doc)
        _format_inline_shapes(doc, document_format)
        _apply_header_footer(doc, document_format)

        try:
            doc.Fields.Update()
        except Exception:
            pass

        try:
            for idx in range(1, doc.TablesOfContents.Count + 1):
                doc.TablesOfContents(idx).Update()
        except Exception:
            pass

        _restore_reference_field_superscripts(doc)

        if args.figlog and args.figlog_out:
            _update_figure_log(doc, Path(args.figlog).resolve(), Path(args.figlog_out).resolve())

        failures = _verify_reference_field_superscripts(doc)
        if failures:
            raise RuntimeError(f"citation superscript audit failed: {', '.join(failures[:10])}")

        doc.Save()
    finally:
        if doc is not None:
            try:
                doc.Close(SaveChanges=False)
            except Exception:
                pass
        try:
            app.Quit()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
