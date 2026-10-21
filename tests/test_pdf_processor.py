from pathlib import Path
from pypdf import PdfWriter

from pdf_processor import extract_text_from_pdf


def test_extract_text_from_pdf(tmp_path: Path):
    pdf_path = tmp_path / "sample.pdf"

    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)

    with pdf_path.open("wb") as file:
        writer.write(file)

    text = extract_text_from_pdf(pdf_path)

    assert isinstance(text, str)