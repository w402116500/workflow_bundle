from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

import win32com.client


wdAlignParagraphCenter = 1
wdLineSpaceSingle = 0
wdLineSpaceExactly = 4
wdFindContinue = 1
wdActiveEndPageNumber = 3
wdColorAutomatic = 0xFF000000
wdColorBlack = 0
wdUnderlineNone = 0


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


def _format_inline_shapes(doc):
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
                cap_para.Range.ParagraphFormat.LineSpacing = 23
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
    parser.add_argument("--figlog", default="")
    parser.add_argument("--figlog_out", default="")
    args = parser.parse_args(argv)

    in_path = Path(args.input_docx).resolve()
    out_path = Path(args.output_docx).resolve()
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
        _format_inline_shapes(doc)

        try:
            doc.Fields.Update()
        except Exception:
            pass

        if args.figlog and args.figlog_out:
            _update_figure_log(doc, Path(args.figlog).resolve(), Path(args.figlog_out).resolve())

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
