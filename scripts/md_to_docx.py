"""
Convert MAGISTERKA_SCALONA.md (or any markdown) to Word .docx.

Usage:
  python md_to_docx.py [input.md] [output.docx]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from data_paths import LEGACY

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


def set_run_font(run, name: str = "Times New Roman", size: int = 12, bold=False, italic=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def add_formatted_runs(paragraph, text: str, base_size: int = 12, base_bold: bool = False):
    """Parse **bold**, *italic*, `code` in inline text."""
    # Split keeping delimiters
    pattern = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")
    parts = pattern.split(text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) >= 4:
            run = paragraph.add_run(part[2:-2])
            set_run_font(run, size=base_size, bold=True)
        elif part.startswith("*") and part.endswith("*") and len(part) >= 2 and not part.startswith("**"):
            run = paragraph.add_run(part[1:-1])
            set_run_font(run, size=base_size, italic=True, bold=base_bold)
        elif part.startswith("`") and part.endswith("`") and len(part) >= 2:
            run = paragraph.add_run(part[1:-1])
            set_run_font(run, name="Consolas", size=max(9, base_size - 1))
        else:
            # strip remaining markdown links [text](url) -> text
            clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", part)
            clean = clean.replace("\\(", "(").replace("\\)", ")")
            run = paragraph.add_run(clean)
            set_run_font(run, size=base_size, bold=base_bold)


def is_table_separator(line: str) -> bool:
    s = line.strip()
    if not s.startswith("|"):
        return False
    # |---|:---:|---|
    core = s.strip("|").replace(" ", "")
    return bool(re.match(r"^:?-+:?(\|:?-+:?)*$", core))


def parse_table_row(line: str) -> list[str]:
    s = line.strip().strip("|")
    cells = [c.strip() for c in s.split("|")]
    return cells


def add_table(doc: Document, rows: list[list[str]]):
    if not rows:
        return
    ncols = max(len(r) for r in rows)
    # pad
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    table = doc.add_table(rows=len(rows), cols=ncols)
    table.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, cell_text in enumerate(row):
            cell = table.rows[i].cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            # clean cell markdown lightly
            clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", cell_text)
            clean = re.sub(r"`([^`]+)`", r"\1", clean)
            clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
            run = p.add_run(clean)
            set_run_font(run, size=9, bold=(i == 0))
    doc.add_paragraph()


def convert(md_path: Path, docx_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    # drop YAML front matter
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :].lstrip("\n")

    lines = text.splitlines()
    doc = Document()

    # Page setup
    section = doc.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    # Default style
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    pf = style.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(6)

    i = 0
    in_code = False
    code_buf: list[str] = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # fenced code
        if stripped.startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                p = doc.add_paragraph()
                run = p.add_run("\n".join(code_buf))
                set_run_font(run, name="Consolas", size=9)
                p.paragraph_format.left_indent = Cm(0.5)
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # empty
        if not stripped:
            i += 1
            continue

        # horizontal rule
        if stripped in ("---", "***", "___") or re.match(r"^-{3,}$", stripped):
            i += 1
            continue

        # headings
        hm = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if hm:
            level = len(hm.group(1))
            title = hm.group(2).strip()
            # Word heading levels 1-9; map # -> Heading 1
            style_name = f"Heading {min(level, 9)}"
            p = doc.add_paragraph(style=style_name)
            # clear default and add formatted
            if p.runs:
                p.runs[0].text = ""
            add_formatted_runs(p, title, base_size=14 if level == 1 else 12, base_bold=True)
            for run in p.runs:
                run.font.color.rgb = RGBColor(0, 0, 0)
            i += 1
            continue

        # table block
        if stripped.startswith("|") and i + 1 < len(lines) and is_table_separator(lines[i + 1]):
            rows = [parse_table_row(stripped)]
            i += 2  # skip separator
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not is_table_separator(lines[i]):
                    rows.append(parse_table_row(lines[i]))
                i += 1
            add_table(doc, rows)
            continue

        # bullet list
        if re.match(r"^[-*+]\s+", stripped):
            item = re.sub(r"^[-*+]\s+", "", stripped)
            p = doc.add_paragraph(style="List Bullet")
            add_formatted_runs(p, item, base_size=12)
            i += 1
            continue

        # numbered list
        if re.match(r"^\d+\.\s+", stripped):
            item = re.sub(r"^\d+\.\s+", "", stripped)
            p = doc.add_paragraph(style="List Number")
            add_formatted_runs(p, item, base_size=12)
            i += 1
            continue

        # blockquote
        if stripped.startswith(">"):
            q = re.sub(r"^>\s?", "", stripped)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1)
            add_formatted_runs(p, q, base_size=11, base_bold=False)
            for run in p.runs:
                run.italic = True
            i += 1
            continue

        # normal paragraph (may continue? keep simple line-by-line merge of non-empty until blank - already line based)
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0.75)
        add_formatted_runs(p, stripped, base_size=12)
        i += 1

    docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(docx_path))
    print(f"Zapisano: {docx_path}")
    print(f"Rozmiar: {docx_path.stat().st_size / 1024:.1f} KB")


def main():
    archive = LEGACY / "processed"
    default_in = archive / "MAGISTERKA_SCALONA.md"
    default_out = archive / "MAGISTERKA_SCALONA.docx"

    md = Path(sys.argv[1]) if len(sys.argv) > 1 else default_in
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else default_out
    if not md.exists():
        raise SystemExit(f"Brak pliku: {md}")
    convert(md, out)


if __name__ == "__main__":
    main()
