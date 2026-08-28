from sqlalchemy.orm import Session

from app.retrieval.embeddings import embed_query
from app.retrieval.faiss_store import FAISSStore
from app.models import NewsChunk


def search_news(
    db: Session,
    query: str,
    top_k: int = 5
):

    query_embedding = embed_query(
        query
    )

    dimension = query_embedding.shape[1]

    store = FAISSStore(
        dimension
    )

    scores, ids = store.search(
        query_embedding,
        top_k
    )

    results = []

    for score, faiss_id in zip(
        scores,
        ids
    ):

        if faiss_id == -1:
            continue

        chunk = db.query(
            NewsChunk
        ).filter(
            NewsChunk.faiss_id == int(
                faiss_id
            )
        ).first()

        if chunk:

            results.append({
                "score": float(score),
                "title": chunk.title,
                "source": chunk.source,
                "url": chunk.url,
                "content": chunk.chunk_text
            })

    return results