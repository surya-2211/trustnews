import os
from pathlib import Path

import faiss
import numpy as np

from app.database import SessionLocal
from app.models import NewsChunk
from app.retrieval.embeddings import embed_documents


# Always use the project root
BASE_DIR = Path(__file__).resolve().parent

INDEX_PATH = BASE_DIR / "data" / "faiss" / "news.index"


def rebuild_faiss():

    db = SessionLocal()

    try:
        # Get all database records in FAISS ID order
        rows = (
            db.query(NewsChunk)
            .order_by(NewsChunk.faiss_id)
            .all()
        )

        if not rows:
            print("No news chunks found in PostgreSQL.")
            return

        # -------------------------------------------------
        # Verify IDs
        # -------------------------------------------------
        ids = [row.faiss_id for row in rows]

        expected_ids = list(range(len(rows)))

        if ids != expected_ids:
            raise RuntimeError(
                f"FAISS IDs are not contiguous.\n"
                f"Found: {ids}\n"
                f"Expected: {expected_ids}"
            )

        # -------------------------------------------------
        # Get text
        # -------------------------------------------------
        texts = [
            row.chunk_text
            for row in rows
        ]

        print(f"Re-embedding {len(texts)} chunks...")

        # -------------------------------------------------
        # Generate BGE embeddings
        # -------------------------------------------------
        embeddings = np.asarray(
            embed_documents(texts),
            dtype="float32"
        )

        print("Embedding shape:", embeddings.shape)

        # -------------------------------------------------
        # Create fresh FAISS index
        # -------------------------------------------------
        dimension = embeddings.shape[1]

        index = faiss.IndexFlatIP(dimension)

        index.add(embeddings)

        # -------------------------------------------------
        # Save
        # -------------------------------------------------
        INDEX_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        print("Saving FAISS index to:")
        print(INDEX_PATH)

        faiss.write_index(
            index,
            str(INDEX_PATH)
        )

        # -------------------------------------------------
        # VERIFY SAVED INDEX
        # -------------------------------------------------
        saved_index = faiss.read_index(
            str(INDEX_PATH)
        )

        print("--------------------------------")
        print("FAISS rebuild completed")
        print("Index path      :", INDEX_PATH)
        print("PostgreSQL rows :", len(rows))
        print("Embeddings shape:", embeddings.shape)
        print("FAISS vectors   :", index.ntotal)
        print("Saved vectors   :", saved_index.ntotal)
        print("Dimension       :", dimension)
        print("--------------------------------")

    finally:
        db.close()


if __name__ == "__main__":
    rebuild_faiss()