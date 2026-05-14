from __future__ import annotations

from pathlib import Path

import pdfplumber
from docx import Document

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def extract_text(file_path: str) -> str:
    """Extract raw text from a PDF or DOCX file."""
    extension = Path(file_path).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension}. Use PDF or DOCX.")
    if extension == ".pdf":
        return _extract_from_pdf(file_path)
    return _extract_from_docx(file_path)


def _extract_from_pdf(file_path: str) -> str:
    text_parts: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    if not text_parts:
        raise ValueError("Could not extract any text from PDF. File may be scanned/image-based.")
    return "\n".join(text_parts)


def _extract_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    parts: list[str] = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)

    for table in doc.tables:
        for row in table.rows:
            row_text = " — ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                parts.append(row_text)

    return "\n".join(parts)
