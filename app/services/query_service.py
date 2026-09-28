from sqlalchemy.orm import Session

from app.retrieval.embeddings import embed_query
from app.retrieval.faiss_store import FAISSStore
from app.models import NewsChunk


def search_news(
    db: Session,
    query: str,
    top_k: int = 5
):

    # ---------------------------------------------------------
    # STEP 1: Convert user query into an embedding
    # ---------------------------------------------------------

    query_embedding = embed_query(query)

    dimension = query_embedding.shape[1]

    store = FAISSStore(dimension)

    total_vectors = store.count()

    # ---------------------------------------------------------
    # STEP 2: Search FAISS
    # ---------------------------------------------------------

    scores, indices = store.search(
        query_embedding,
        top_k
    )

    results = []

    # ---------------------------------------------------------
    # STEP 3: Convert FAISS IDs into PostgreSQL records
    # ---------------------------------------------------------

    for score, faiss_id in zip(scores, indices):

        # FAISS returns -1 when there is no result
        if faiss_id == -1:
            continue

        news = (
            db.query(NewsChunk)
            .filter(
                NewsChunk.faiss_id == int(faiss_id)
            )
            .first()
        )

        if news is None:
            continue

        results.append({

            "faiss_id": int(faiss_id),

            "score": float(score),

            "title": news.title,

            "source": news.source,

            "url": news.url,

            "content": news.chunk_text
        })

    # ---------------------------------------------------------
    # STEP 4: Return results + explanation
    # ---------------------------------------------------------

    return {

        "query": query,

        "top_k": top_k,

        "results": results,

        "retrieval_steps": [

            {
                "step": 1,
                "operation": "User query",
                "description": "The user entered a natural-language search query.",
                "value": query
            },

            {
                "step": 2,
                "operation": "Query embedding",
                "description": "The query was converted into a 768-dimensional vector using the BGE embedding model.",
                "embedding_dimension": dimension
            },

            {
                "step": 3,
                "operation": "FAISS vector search",
                "description": "FAISS compared the query vector against the stored news vectors using Inner Product similarity.",
                "total_vectors": total_vectors,
                "requested_results": top_k
            },

            {
                "step": 4,
                "operation": "Similarity calculation",
                "description": "Each candidate receives an Inner Product similarity score. Because embeddings are normalized, this corresponds to cosine similarity.",
                "formula": "similarity = query_vector · document_vector"
            },

            {
                "step": 5,
                "operation": "Ranking",
                "description": "Results are ranked from highest similarity score to lowest similarity score."
            },

            {
                "step": 6,
                "operation": "PostgreSQL lookup",
                "description": "The FAISS IDs of the top results are used to retrieve the corresponding news records from PostgreSQL."
            }

        ]
    }