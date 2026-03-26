import re
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from parser.unified_ir import (
    UnifiedDocument, Heading, Paragraph,
    Image, Table, TableCell, DocumentList, ListItem
)


# ── Heading detection ──────────────────────────────────────────────────────────
# PyMuPDF gives us font sizes — we use them to detect headings.
# Strategy: collect all font sizes on the page, the largest ones are headings.

def _detect_heading_level(font_size: float, size_map: dict) -> int:
    """Map a font size to a heading level (1–4) based on relative size."""
    sizes = sorted(size_map.keys(), reverse=True)
    for i, size in enumerate(sizes[:4]):
        if font_size >= size:
            return i + 1
    return 0  # not a heading


def _build_size_map(page) -> dict:
    """Collect all distinct font sizes on a page."""
    sizes = {}
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                size = round(span["size"])
                sizes[size] = sizes.get(size, 0) + 1
    return sizes


# ── PDF Parser ─────────────────────────────────────────────────────────────────

def parse_pdf(file_bytes: bytes, filename: str) -> UnifiedDocument:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    unified = UnifiedDocument(filename=filename, total_pages=len(doc))
    image_index = 0

    for page_num, page in enumerate(doc, start=1):
        size_map = _build_size_map(page)
        body_size = max(size_map, key=size_map.get) if size_map else 12

        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            # ── Text blocks ──
            if block["type"] == 0:
                lines_text = []
                max_font_size = 0

                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        line_text += span["text"]
                        if span["size"] > max_font_size:
                            max_font_size = span["size"]
                    lines_text.append(line_text.strip())

                full_text = " ".join(t for t in lines_text if t)
                if not full_text.strip():
                    continue

                # Decide: heading or paragraph?
                if max_font_size > body_size * 1.2:
                    level = _detect_heading_level(max_font_size, size_map)
                    unified.elements.append(Heading(
                        level=level if level > 0 else 1,
                        text=full_text,
                        page=page_num
                    ))
                else:
                    # Check if it looks like a list item
                    if re.match(r"^(\u2022|\u2013|\-|\*|\d+\.)\s", full_text):
                        unified.elements.append(DocumentList(
                            page=page_num,
                            items=[ListItem(text=full_text)]
                        ))
                    else:
                        unified.elements.append(Paragraph(
                            text=full_text,
                            page=page_num
                        ))

            # ── Image blocks ──
            elif block["type"] == 1:
                image_bytes = block.get("image")
                unified.elements.append(Image(
                    index=image_index,
                    page=page_num,
                    image_bytes=image_bytes
                ))
                image_index += 1

        # ── Tables (via PyMuPDF table detection) ──
        tables = page.find_tables()
        for table in tables:
            rows = []
            for row_idx, row in enumerate(table.extract()):
                cells = []
                for cell_text in row:
                    cells.append(TableCell(
                        text=str(cell_text) if cell_text else "",
                        is_header=(row_idx == 0)
                    ))
                rows.append(cells)
            if rows:
                unified.elements.append(Table(page=page_num, rows=rows))

    unified.compute_stats()
    doc.close()
    return unified


# ── DOCX Parser ────────────────────────────────────────────────────────────────

def parse_docx(file_bytes: bytes, filename: str) -> UnifiedDocument:
    import io
    doc = DocxDocument(io.BytesIO(file_bytes))
    unified = UnifiedDocument(filename=filename, total_pages=1)
    image_index = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        style = para.style.name.lower()

        # Headings
        if "heading" in style:
            try:
                level = int(style.split()[-1])
            except ValueError:
                level = 1
            unified.elements.append(Heading(level=level, text=text, page=1))

        # List items
        elif "list" in style:
            unified.elements.append(DocumentList(
                page=1,
                items=[ListItem(text=text)]
            ))

        # Normal paragraph
        else:
            unified.elements.append(Paragraph(text=text, page=1))

    # Tables
    for table in doc.tables:
        rows = []
        for row_idx, row in enumerate(table.rows):
            cells = [
                TableCell(
                    text=cell.text.strip(),
                    is_header=(row_idx == 0)
                )
                for cell in row.cells
            ]
            rows.append(cells)
        if rows:
            unified.elements.append(Table(page=1, rows=rows))

    # Images (inline shapes)
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            unified.elements.append(Image(
                index=image_index,
                page=1,
                image_bytes=rel.target_part.blob
            ))
            image_index += 1

    unified.compute_stats()
    return unified


# ── Main entry point ───────────────────────────────────────────────────────────

def parse_document(file_bytes: bytes, filename: str, content_type: str) -> UnifiedDocument:
    if content_type == "application/pdf":
        return parse_pdf(file_bytes, filename)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return parse_docx(file_bytes, filename)
    else:
        raise ValueError(f"Unsupported file type: {content_type}")