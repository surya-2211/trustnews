import faiss
import os
import numpy as np

from dotenv import load_dotenv

load_dotenv()

INDEX_PATH = os.getenv(
    "FAISS_INDEX_PATH",
    "data/faiss/news.index"
)

os.makedirs(
    os.path.dirname(INDEX_PATH),
    exist_ok=True
)


class FAISSStore:

    def __init__(self, dimension):

        self.dimension = dimension

        self.index = None

        self.load_or_create()


    def load_or_create(self):

        if os.path.exists(INDEX_PATH):

            self.index = faiss.read_index(
                INDEX_PATH
            )

        else:

            self.index = faiss.IndexFlatIP(
                self.dimension
            )


    def add_embeddings(self, embeddings):

        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        self.index.add(
            embeddings
        )

        faiss.write_index(
            self.index,
            INDEX_PATH
        )


    def search(
        self,
        query_embedding,
        top_k=5
    ):

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32"
        )

        scores, indices = self.index.search(
            query_embedding,
            top_k
        )

        return scores[0], indices[0]


    def count(self):

        return self.index.ntotal