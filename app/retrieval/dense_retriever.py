import os
import faiss
import numpy as np

from app.retrieval.embeddings import embed_query


INDEX_PATH = os.getenv(
    "FAISS_INDEX_PATH",
    "data/faiss/news.index"
)


class DenseRetriever:

    def __init__(self):

        if not os.path.exists(INDEX_PATH):
            raise FileNotFoundError(
                f"FAISS index not found: {INDEX_PATH}"
            )

        self.index = faiss.read_index(
            INDEX_PATH
        )

    def search(
        self,
        query: str,
        top_k: int = 10
    ):

        query_embedding = np.asarray(
            embed_query(query),
            dtype="float32"
        )

        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(
                1, -1
            )

        scores, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for score, index_id in zip(
            scores[0],
            indices[0]
        ):

            if index_id < 0:
                continue

            results.append({
                "faiss_id": int(index_id),
                "dense_score": float(score)
            })

        return results