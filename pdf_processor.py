
from pathlib import Path
from pypdf import PdfReader

DOCUMENTS_DIR = Path("documents")


def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


def process_pdfs():
    DOCUMENTS_DIR.mkdir(exist_ok=True)

    pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in the documents folder.")
        print("Add a government scheme PDF and run again.")
        return

    for pdf_path in pdf_files:
        try:
            text = extract_text_from_pdf(pdf_path)

            output_path = Path("data") / f"{pdf_path.stem}.txt"
            output_path.parent.mkdir(exist_ok=True)
            output_path.write_text(text, encoding="utf-8")

            print(f"Processed: {pdf_path.name}")
            print(f"Extracted characters: {len(text)}")
            print(f"Saved to: {output_path}")

        except Exception as error:
            print(f"Failed to process {pdf_path.name}: {error}")


if __name__ == "__main__":
    process_pdfs()
