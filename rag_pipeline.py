
import os

import chromadb
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=api_key)

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768

db = chromadb.PersistentClient(path="./chroma_db")

collection = db.get_or_create_collection(
    name="tn_government_schemes_gemini",
    metadata={"hnsw:space": "cosine"}
)


def get_embedding(text: str) -> list[float]:
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config={
            "output_dimensionality": EMBEDDING_DIMENSIONS
        }
    )

    if not response.embeddings:
        raise RuntimeError("Gemini returned no embedding.")

    return response.embeddings[0].values


def search_schemes(question: str, top_k: int = 3) -> list[dict]:
    total = collection.count()

    if total == 0:
        return []

    query_vector = get_embedding(question)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, total)
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    ids = results.get("ids", [[]])[0]

    retrieved = []

    for index, document in enumerate(documents):
        metadata = (
            metadatas[index]
            if index < len(metadatas) and metadatas[index]
            else {}
        )

        source = metadata.get(
            "source",
            ids[index] if index < len(ids) else "unknown"
        )

        retrieved.append({
            "text": document,
            "source": source
        })

    return retrieved
