
import chromadb
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)

# Load the same embedding model used in ingest.py
embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Connect to the existing vector database
client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="tn_government_schemes",
    embedding_function=embedding_function
)


def search_schemes(question: str, top_k: int = 3):
    """Retrieve relevant scheme documents from ChromaDB."""

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=min(top_k, collection.count())
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    ids = results.get("ids", [[]])[0]

    retrieved = []

    for index, document in enumerate(documents):
        metadata = metadatas[index] if metadatas else None
        metadata = metadata or {}

        retrieved.append({
            "text": document,
            "source": metadata.get(
                "source",
                ids[index] if index < len(ids) else "unknown"
            )
        })

    return retrieved


