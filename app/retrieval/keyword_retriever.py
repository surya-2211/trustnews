from sqlalchemy import text
from sqlalchemy.orm import Session


def keyword_search(
    db: Session,
    query: str,
    top_k: int = 10
):

    sql = text("""
        SELECT
            id,
            faiss_id,
            chunk_text,

            ts_rank(
                to_tsvector(
                    'english',
                    COALESCE(chunk_text, '')
                ),
                plainto_tsquery(
                    'english',
                    :query
                )
            ) AS keyword_score

        FROM news_chunks

        WHERE
            to_tsvector(
                'english',
                COALESCE(chunk_text, '')
            )
            @@
            plainto_tsquery(
                'english',
                :query
            )

        ORDER BY keyword_score DESC

        LIMIT :top_k
    """)

    rows = db.execute(
        sql,
        {
            "query": query,
            "top_k": top_k
        }
    ).fetchall()

    return [
        {
            "id": row.id,

            "faiss_id": row.faiss_id,

            "chunk_text": row.chunk_text,

            "keyword_score": float(
                row.keyword_score
            )
        }

        for row in rows
    ]