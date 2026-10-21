
import json
import hashlib
import chromadb

from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)

INPUT_FILE = "collected_schemes.json"
DB_PATH = "./chroma_db"
COLLECTION_NAME = "tn_government_schemes"

CHUNK_SIZE = 1000
OVERLAP = 150
BATCH_SIZE = 32


def split_text(text):
    text = " ".join(text.split())
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()

        if len(chunk) >= 100:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - OVERLAP

    return chunks


with open(INPUT_FILE, "r", encoding="utf-8") as file:
    pages = json.load(file)

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path=DB_PATH)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function
)

records = []
seen_chunks = set()

for page in pages:
    content = page.get("content", "").strip()
    source = page.get("source", "")
    title = page.get("title", "Unknown page")

    if not content or not source:
        continue

    for index, chunk in enumerate(split_text(content)):
        # Avoid identical text chunks from repeated pages
        chunk_hash = hashlib.sha256(
            chunk.encode("utf-8")
        ).hexdigest()

        if chunk_hash in seen_chunks:
            continue

        seen_chunks.add(chunk_hash)

        record_id = hashlib.sha256(
            f"{source}|{index}|{chunk_hash}".encode("utf-8")
        ).hexdigest()

        records.append({
            "id": record_id,
            "text": chunk,
            "metadata": {
                "source": source,
                "title": title[:500],
                "state": "Tamil Nadu",
                "chunk_index": index
            }
        })

for start in range(0, len(records), BATCH_SIZE):
    batch = records[start:start + BATCH_SIZE]

    collection.upsert(
        ids=[item["id"] for item in batch],
        documents=[item["text"] for item in batch],
        metadatas=[item["metadata"] for item in batch]
    )

print("\nIngestion completed!")
print("Pages scanned:", len(pages))
print("Unique chunks prepared:", len(records))
print("Total documents in database:", collection.count())
