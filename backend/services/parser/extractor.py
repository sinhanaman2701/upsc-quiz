import pdfplumber
import os


def extract_text(pdf_path: str) -> list[tuple[int, str]]:
    """
    Extract text from a PDF file, page by page.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of (page_number, text) tuples where page_number is 1-indexed

    Raises:
        FileNotFoundError: If the PDF file does not exist
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append((i, text))
    return pages
