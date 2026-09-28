import faiss
from pathlib import Path
import numpy as np


# Always use the same project-root path
BASE_DIR = Path(__file__).resolve().parent

INDEX_PATH = BASE_DIR / "data" / "faiss" / "news.index"

print("Index path:", INDEX_PATH)
print("File exists:", INDEX_PATH.exists())

if not INDEX_PATH.exists():
    raise FileNotFoundError(
        f"FAISS index not found: {INDEX_PATH}"
    )

index = faiss.read_index(str(INDEX_PATH))

print("\nFAISS information")
print("------------------")
print("Total vectors:", index.ntotal)
print("Vector dimensions:", index.d)
print("Index type:", type(index).__name__)

# Extract embeddings
embeddings = index.reconstruct_n(
    0,
    index.ntotal
)

# Save actual numbers
OUTPUT_PATH = BASE_DIR / "embeddings.txt"

np.savetxt(
    OUTPUT_PATH,
    embeddings,
    fmt="%.8f"
)

print("\nEmbedding information")
print("---------------------")
print("Rows:", embeddings.shape[0])
print("Columns:", embeddings.shape[1])
print("File:", OUTPUT_PATH)