from sentence_transformers import CrossEncoder


# ============================================================
# MODEL
# ============================================================

RERANKER_MODEL = "BAAI/bge-reranker-base"

_reranker = None


# ============================================================
# LAZY LOAD
# ============================================================

def get_reranker():

    global _reranker

    if _reranker is None:

        print(
            f"Loading reranker model: {RERANKER_MODEL}"
        )

        _reranker = CrossEncoder(
            RERANKER_MODEL
        )

    return _reranker


# ============================================================
# RERANK
# ============================================================

def rerank_results(
    query,
    results,
    top_k=5
):
    """
    Re-rank retrieved documents using a CrossEncoder.

    IMPORTANT:
    Each result MUST contain either:

        content

    or:

        chunk_text

    and optionally:

        title

    before this function is called.

    The CrossEncoder compares:

        query <-> document

    directly, which gives a much better relevance
    estimate than dense similarity alone.
    """

    if not results:
        return []

    reranker = get_reranker()

    pairs = []

    # ========================================================
    # BUILD QUERY / DOCUMENT PAIRS
    # ========================================================

    for item in results:

        title = str(
            item.get(
                "title",
                ""
            )
        ).strip()

        content = str(
            item.get(
                "content",
                ""
            )
        ).strip()

        # Support chunk_text as fallback
        if not content:

            content = str(
                item.get(
                    "chunk_text",
                    ""
                )
            ).strip()

        # ----------------------------------------------------
        # Combine title + content
        # ----------------------------------------------------

        if title and content:

            document_text = (
                f"{title}\n\n{content}"
            )

        elif content:

            document_text = content

        else:

            document_text = title

        pairs.append(
            [
                query,
                document_text
            ]
        )

    # ========================================================
    # CROSS ENCODER
    # ========================================================

    scores = reranker.predict(
        pairs,
        show_progress_bar=False
    )

    # ========================================================
    # ATTACH SCORES
    # ========================================================

    ranked_results = []

    for item, score in zip(
        results,
        scores
    ):

        result = dict(item)

        result[
            "rerank_score"
        ] = float(score)

        ranked_results.append(
            result
        )

    # ========================================================
    # SORT BY CROSS-ENCODER SCORE
    # ========================================================

    ranked_results.sort(
        key=lambda item: item[
            "rerank_score"
        ],
        reverse=True
    )

    # ========================================================
    # RETURN TOP K
    # ========================================================

    return ranked_results[:top_k]