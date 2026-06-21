import pytest
import os
from services.parser.extractor import extract_text

SAMPLE_PDF = "/Users/namansinha/Downloads/Anisha/POLITY_MCQs_with_Solutions_PART_1.pdf"

def test_extract_returns_list_of_tuples():
    result = extract_text(SAMPLE_PDF)
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(page_num, int) and isinstance(text, str)
               for page_num, text in result)

def test_extract_page_numbers_are_sequential():
    result = extract_text(SAMPLE_PDF)
    page_nums = [p for p, _ in result]
    assert page_nums == list(range(1, len(result) + 1))

def test_extract_content_not_empty():
    result = extract_text(SAMPLE_PDF)
    non_empty = [text for _, text in result if text.strip()]
    assert len(non_empty) > 0

def test_extract_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        extract_text("/nonexistent/path/file.pdf")
