
import sys
from pathlib import Path

import chromadb
from pypdf import PdfReader
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)

PDF_DIR = Path("scheme_pdfs")
DB_DIR = "./chroma_db"
COLLECTION_NAME = "tn_government_schemes"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path=DB_DIR)

collection = client.get_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function
)


def split_text(text):
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def main():
    PDF_DIR.mkdir(exist_ok=True)

    pdf_files = list(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDFs found!")
        print("Place official scheme PDFs inside:", PDF_DIR.resolve())
        return

    total_chunks = 0

    for pdf_path in pdf_files:
        print(f"\nReading: {pdf_path.name}")

        try:
            reader = PdfReader(str(pdf_path))
            full_text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            ).strip()

            if not full_text:
                print("No extractable text. This PDF may be scanned.")
                continue

            chunks = split_text(full_text)

            for index, chunk in enumerate(chunks):
                doc_id = (
                    f"pdf_{pdf_path.stem}_chunk_{index}"
                )

                collection.upsert(
                    ids=[doc_id],
                    documents=[chunk],
                    metadatas=[{
                        "source": pdf_path.name,
                        "page_type": "pdf",
                        "chunk_index": index
                    }]
                )

            total_chunks += len(chunks)
            print(f"Stored {len(chunks)} chunks.")

        except Exception as error:
            print(f"Failed to process {pdf_path.name}: {error}")

    print("\nPDF ingestion completed!")
    print("New chunks processed:", total_chunks)
    print("Total collection documents:", collection.count())


if __name__ == "__main__":
    main()
