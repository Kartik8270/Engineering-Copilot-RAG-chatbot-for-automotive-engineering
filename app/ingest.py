"""PDF -> cleaned, section-aware chunks with page/section/table metadata."""
import re
from pathlib import Path

import pdfplumber
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import CHUNK_OVERLAP, CHUNK_SIZE

HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Z][^\n]{2,80})$")
DOC_ID = re.compile(r"\b[A-Z]{1,4}-\d{2,4}\b")


def _table_text(rows) -> str:
    clean = [[(c or "").replace("\n", " ").strip() for c in r] for r in rows if r and any(r)]
    return "\n".join(" | ".join(r) for r in clean)


def ingest_pdf(path: Path) -> tuple[list[Document], dict]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    m = DOC_ID.search(path.stem)
    doc_id = m.group(0) if m else path.stem
    segments = []  # (section, page, kind, text)
    section = "0"

    with pdfplumber.open(path) as pdf:
        meta = pdf.metadata or {}
        n_pages = len(pdf.pages)
        for pno, page in enumerate(pdf.pages, start=1):
            tables = page.find_tables()
            body = page
            for t in tables:
                body = body.outside_bbox(t.bbox)  # avoid duplicating table text
            buf = []
            for line in (body.extract_text() or "").splitlines():
                h = HEADING.match(line.strip())
                if h:
                    if buf:
                        segments.append((section, pno, "text", "\n".join(buf)))
                        buf = []
                    section = h.group(1)
                buf.append(line)
            if buf:
                segments.append((section, pno, "text", "\n".join(buf)))
            for t in tables:
                txt = _table_text(t.extract())
                if txt:
                    segments.append((section, pno, "table", txt))

    chunks = []
    for section, pno, kind, text in segments:
        if not text.strip():
            continue
        for piece in splitter.split_text(text):
            chunks.append(Document(
                page_content=piece,
                metadata={"source": path.name, "doc_id": doc_id, "page": pno,
                          "section": section, "type": kind},
            ))
    info = {"source": path.name, "doc_id": doc_id, "pages": n_pages, "chunks": len(chunks),
            "title": meta.get("Title") or "", "author": meta.get("Author") or ""}
    return chunks, info
