
import json
import chromadb
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)

with open("scheme_data.json", "r", encoding="utf-8") as file:
    data = json.load(file)

content = data["content"].strip()

if not content:
    raise ValueError("No scheme content found in JSON")

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="tn_government_schemes",
    embedding_function=embedding_function
)

collection.upsert(
    ids=["tnrd_scheme_page"],
    documents=[content],
    metadatas=[{
        "source": data["source"],
        "department": data["department"],
        "state": data["state"]
    }]
)

print("Scheme data stored successfully!")
print("Total documents:", collection.count())
