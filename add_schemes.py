
import chromadb
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="tn_government_schemes",
    embedding_function=embedding_function
)

schemes = [
    {
        "id": "tn_scheme_mudhalvar_marundhagam",
        "name": "Mudhalvar Marundhagam",
        "category": "health",
        "source": "https://www.tn.gov.in/",
        "text": """
        Scheme: Mudhalvar Marundhagam.
        State: Tamil Nadu.
        Category: Public health and medicines.
        Consult the Tamil Nadu Government official website
        for current scheme details, locations and eligibility.
        """
    },
    {
        "id": "tn_scheme_amma_two_wheeler",
        "name": "Amma Two Wheeler Scheme",
        "category": "women_welfare",
        "source": "https://www.tn.gov.in/",
        "text": """
        Scheme: Amma Two Wheeler Scheme.
        State: Tamil Nadu.
        Category: Women welfare and mobility.
        Check the current status, eligibility and application
        availability through official Tamil Nadu sources.
        """
    }
]

for scheme in schemes:
    collection.upsert(
        ids=[scheme["id"]],
        documents=[scheme["text"]],
        metadatas=[{
            "scheme_name": scheme["name"],
            "category": scheme["category"],
            "source": scheme["source"],
            "state": "Tamil Nadu"
        }]
    )

print("Added sample scheme records.")
print("Total documents:", collection.count())
