import os

import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


load_dotenv()


MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-base-en-v1.5"
)


model = SentenceTransformer(
    MODEL_NAME
)


def embed_documents(texts):

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    return np.asarray(
        embeddings,
        dtype="float32"
    )


def embed_query(query):

    embedding = model.encode(
        [query],
        normalize_embeddings=True,
        show_progress_bar=False
    )

    return np.asarray(
        embedding,
        dtype="float32"
    )