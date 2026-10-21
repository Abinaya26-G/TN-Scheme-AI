
import os

import chromadb
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=api_key)

# Same embedding model and dimensions must be used in rag_pipeline.py.
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768

db = chromadb.PersistentClient(path="./chroma_db")
collection_name = "tn_government_schemes"

# Use a NEW collection because existing vectors were generated
# using all-MiniLM-L6-v2, which is incompatible with Gemini vectors.
collection = db.get_or_create_collection(
    name="tn_government_schemes_gemini",
    metadata={"hnsw:space": "cosine"}
)

schemes = [
    {
        "id": "official_pudhumai_penn",
        "text": """
        Scheme: Pudhumai Penn Scheme.
        Source: Tamil Nadu Government scheme information portal.
        Benefit: Rs. 1000 per month through DBT.
        Eligibility described in the source: girl students who
        studied Classes 6 to 12 continuously in Government schools
        or Government-aided Tamil-medium schools.
        Application: UMIS portal.
        Verify current eligibility and rules using the official
        source before giving advice.
        """,
        "source": "https://tils.tn.gov.in/schemes",
        "scheme_name": "Pudhumai Penn Scheme",
        "category": "education"
    },
    {
        "id": "official_tamil_pudhalvan",
        "text": """
        Scheme: Tamil Pudhalvan Scheme.
        Source: Tamil Nadu Government scheme information portal.
        Benefit: Rs. 1000 per month through DBT.
        Eligibility described in the source: boy students who
        studied Classes 6 to 12 continuously in Government schools
        or Government-aided Tamil-medium schools.
        Application: UMIS portal.
        Verify current eligibility and rules using the official
        source before giving advice.
        """,
        "source": "https://tils.tn.gov.in/schemes",
        "scheme_name": "Tamil Pudhalvan Scheme",
        "category": "education"
    },
    {
        "id": "official_social_security_pensions",
        "text": """
        Scheme category: Tamil Nadu Social Security Pension Schemes.
        Official source: Commissionerate of Revenue Administration
        and Disaster Management, Government of Tamil Nadu.
        Schemes include old-age pension, widow pension, differently
        abled pension, destitute widow pension and other assistance
        for vulnerable groups.
        Eligibility depends on the individual scheme.
        Verify current amounts and application procedures on the
        official government website.
        """,
        "source": "https://www.cra.tn.gov.in/about_schemes.php",
        "scheme_name": "Social Security Pension Schemes",
        "category": "social_welfare"
    },
    {
        "id": "official_disability_student_scholarship",
        "text": """
        Scheme: Scholarship for differently abled students.
        Official source: Tamil Nadu Commissionerate for Welfare
        of the Differently Abled.
        The source describes scholarship assistance for students
        from Class 9 onwards and higher education.
        Eligibility and marks requirements must be verified against
        the latest official scheme rules.
        Apply through the relevant District Differently Abled
        Welfare Officer as directed by the official source.
        """,
        "source": "https://scd.tn.gov.in/specialedu.php",
        "scheme_name": "Scholarship for Differently Abled Students",
        "category": "education"
    }
]


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


print("Generating Gemini embeddings and indexing schemes...")

for scheme in schemes:
    text = scheme["text"].strip()
    vector = get_embedding(text)

    collection.upsert(
        ids=[scheme["id"]],
        documents=[text],
        embeddings=[vector],
        metadatas=[{
            "source": scheme["source"],
            "scheme_name": scheme["scheme_name"],
            "category": scheme["category"],
            "data_type": "official_source_summary"
        }]
    )

print("Ingestion completed!")
print("Collection:", collection.name)
print("Total documents:", collection.count())

question = "What is the eligibility and monthly benefit of Pudhumai Penn?"
query_vector = get_embedding(question)

results = collection.query(
    query_embeddings=[query_vector],
    n_results=min(2, collection.count())
)

print("\nSemantic search test:")

for document, metadata in zip(
    results["documents"][0],
    results["metadatas"][0]
):
    print("\nScheme:", metadata.get("scheme_name"))
    print("Source:", metadata.get("source"))
    print("Retrieved text:", document[:300], "...")
