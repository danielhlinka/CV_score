import os
import pdfplumber
from docx import Document

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

def extract_text(file_path: str) -> str:
    """Extract raw text from a PDF or DOCX file."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF or DOCX.")
    if ext == ".pdf":
        return _extract_from_pdf(file_path)
    elif ext == ".docx":
        return _extract_from_docx(file_path)

def _extract_from_pdf(file_path: str) -> str:
    text_parts = []
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
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    if not paragraphs:
        raise ValueError("Could not extract any text from DOCX.")
    return "\n".join(paragraphs)

def validate_text(text: str, min_chars: int = 200) -> bool:
    """Sanity check — is there enough text to work with?"""
    return len(text.strip()) >= min_chars