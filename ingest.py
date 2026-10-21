
import chromadb
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)

print("Loading embedding model...")

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path="./chroma_db")

collection_name = "tn_government_schemes"

# Reuse the existing collection; do not delete existing data.
try:
    collection = client.get_collection(
        name=collection_name,
        embedding_function=embedding_function
    )
    print("Existing collection connected.")

except Exception as error:
    print("Could not connect to existing collection:", error)
    raise RuntimeError(
        "Check that rag_pipeline.py and ingest.py use "
        "the same ChromaDB collection and embedding model."
    ) from error


# Official-source summaries for retrieval.
# Verify current rules on the linked official websites.
schemes = [
    {
        "id": "official_pudhumai_penn",
        "text": """
        Scheme: Pudhumai Penn Scheme.
        Department information source: Tamil Nadu Government
        scheme information portal, TILS.
        Benefit: Rs. 1000 per month through DBT.
        Eligibility described on the source page:
        girl students who studied Classes 6 to 12 continuously
        in Government schools or Government-aided Tamil-medium
        schools.
        Application: online through the UMIS portal.
        Documents listed: school study certificate, community
        certificate, income certificate, bank passbook, Aadhaar
        card and admission proof.
        Confirm current eligibility and rules on the official page.
        """,
        "source": "https://tils.tn.gov.in/schemes",
        "scheme_name": "Pudhumai Penn Scheme",
        "category": "education"
    },
    {
        "id": "official_tamil_pudhalvan",
        "text": """
        Scheme: Tamil Pudhalvan Scheme.
        Department information source: Tamil Nadu Government
        scheme information portal, TILS.
        Benefit: Rs. 1000 per month through DBT.
        Eligibility described on the source page:
        boy students who studied Classes 6 to 12 continuously
        in Government schools or Government-aided Tamil-medium
        schools.
        Application: online through the UMIS portal.
        Documents listed: school study certificate, community
        certificate, income certificate, bank passbook, Aadhaar
        card and admission proof.
        Confirm current eligibility and rules on the official page.
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
        Schemes listed include old-age pension, widow pension,
        differently abled pension, destitute widow pension,
        deserted wives pension and assistance for certain
        vulnerable groups.
        Eligibility depends on the individual scheme.
        Consult the official source for current eligibility,
        pension amounts and application procedures.
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
        The source lists scholarship assistance for students
        from Class 9 onwards and for higher education.
        Eligibility described on the page includes studying
        in Government-recognised schools, colleges or training
        centres and obtaining at least 40 percent marks in the
        previous qualifying examination.
        Documents listed include an institution certificate,
        national identity card for differently abled persons
        and previous examination marks statement.
        Apply through the concerned District Differently Abled
        Welfare Officer. Verify current rules on the official page.
        """,
        "source": "https://scd.tn.gov.in/specialedu.php",
        "scheme_name": "Scholarship for Differently Abled Students",
        "category": "education"
    }
]

print("Indexing official-source summaries...")

for scheme in schemes:
    collection.upsert(
        ids=[scheme["id"]],
        documents=[scheme["text"].strip()],
        metadatas=[{
            "source": scheme["source"],
            "scheme_name": scheme["scheme_name"],
            "category": scheme["category"],
            "data_type": "official_source_summary"
        }]
    )

print("\nIngestion completed!")
print("Collection:", collection.name)
print("Total documents:", collection.count())

results = collection.query(
    query_texts=[
        "What is the eligibility and monthly benefit "
        "of Pudhumai Penn?"
    ],
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
