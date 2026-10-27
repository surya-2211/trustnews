from app.models import NewsChunk


# ============================================================
# FETCH CHUNKS
# ============================================================

def fetch_chunks(
    db,
    ranked_results
):
    """
    Fetch complete document/chunk information from the
    database using FAISS IDs.

    The returned objects contain both retrieval scores
    and reranker scores.
    """

    ids = [
        result["faiss_id"]
        for result in ranked_results
        if "faiss_id" in result
    ]

    if not ids:
        return []

    rows = (
        db.query(NewsChunk)
        .filter(
            NewsChunk.faiss_id.in_(ids)
        )
        .all()
    )

    # --------------------------------------------------------
    # Map database rows by FAISS ID
    # --------------------------------------------------------

    row_map = {
        row.faiss_id: row
        for row in rows
    }

    output = []

    # --------------------------------------------------------
    # Preserve reranker ordering
    # --------------------------------------------------------

    for result in ranked_results:

        faiss_id = result.get(
            "faiss_id"
        )

        row = row_map.get(
            faiss_id
        )

        if row is None:
            continue

        output.append({

            # -----------------------------------------------
            # Database information
            # -----------------------------------------------

            "id":
                row.id,

            "faiss_id":
                row.faiss_id,

            "title":
                getattr(
                    row,
                    "title",
                    ""
                ),

            "source":
                getattr(
                    row,
                    "source",
                    ""
                ),

            "url":
                getattr(
                    row,
                    "url",
                    ""
                ),

            "published_at":
                getattr(
                    row,
                    "published_at",
                    None
                ),

            "content":
                row.chunk_text,

            # -----------------------------------------------
            # Retrieval scores
            # -----------------------------------------------

            "dense_score":
                float(
                    result.get(
                        "dense_score",
                        0.0
                    )
                ),

            "keyword_score":
                float(
                    result.get(
                        "keyword_score",
                        0.0
                    )
                ),

            "retrieval_score":
                float(
                    result.get(
                        "retrieval_score",
                        0.0
                    )
                ),

            # -----------------------------------------------
            # Reranker score
            # -----------------------------------------------

            "rerank_score":
                float(
                    result.get(
                        "rerank_score",
                        0.0
                    )
                )
        })

    return output


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(
    query: str,
    results: list,
    max_results: int = 8
):
    """
    Build the final context passed to the LLM.

    Results are assumed to already be ordered by reranker
    relevance.
    """

    selected = results[:max_results]

    context_parts = [

        "TRUSTNEWS RETRIEVAL CONTEXT",

        "=" * 40,

        "",

        "QUERY",

        query,

        "",

        f"TOTAL EVIDENCE: {len(selected)}",

        ""
    ]

    # ========================================================
    # ADD EVIDENCE
    # ========================================================

    for index, result in enumerate(
        selected,
        start=1
    ):

        content = str(
            result.get(
                "content",
                ""
            )
        ).strip()

        dense_score = float(
            result.get(
                "dense_score",
                0.0
            )
        )

        keyword_score = float(
            result.get(
                "keyword_score",
                0.0
            )
        )

        retrieval_score = float(
            result.get(
                "retrieval_score",
                0.0
            )
        )

        rerank_score = float(
            result.get(
                "rerank_score",
                0.0
            )
        )

        context_parts.extend([

            f"[EVIDENCE {index}]",

            "-" * 40,

            f"Title: {result.get('title', '')}",

            f"Source: {result.get('source', '')}",

            f"URL: {result.get('url', '')}",

            "",

            # -----------------------------------------------
            # Retrieval information
            # -----------------------------------------------

            f"Dense Score: {dense_score:.6f}",

            f"Keyword Score: {keyword_score:.6f}",

            f"Retrieval Score: {retrieval_score:.6f}",

            # -----------------------------------------------
            # Reranker information
            # -----------------------------------------------

            f"Rerank Score: {rerank_score:.6f}",

            "",

            "CONTENT:",

            content,

            "",

            f"[END EVIDENCE {index}]",

            ""
        ])

    return "\n".join(
        context_parts
    )