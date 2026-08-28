from app.retrieval.embeddings import embed_documents
from app.retrieval.faiss_store import FAISSStore


documents = [
    "NASA announced a new space exploration mission.",
    "Scientists discovered a new exoplanet using advanced telescopes.",
    "Researchers developed a new artificial intelligence model.",
    "Space agencies are preparing for future lunar missions."
]


print("Generating embeddings...")

embeddings = embed_documents(documents)

print(
    "Embedding shape:",
    embeddings.shape
)


dimension = embeddings.shape[1]

print(
    "Embedding dimension:",
    dimension
)


store = FAISSStore(dimension)

print(
    "Existing vectors:",
    store.count()
)


store.add_embeddings(embeddings)

print(
    "Vectors after insertion:",
    store.count()
)