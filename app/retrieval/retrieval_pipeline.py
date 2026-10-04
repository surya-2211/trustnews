from app.retrieval.query_processor import (
    process_query
)

from app.retrieval.query_expansion import (
    expand_query
)

from app.retrieval.hybrid_retriever import (
    HybridRetriever
)

from app.retrieval.reranker import (
    rerank_results
)

from app.retrieval.context_builder import (
    fetch_chunks,
    build_context
)


class RetrievalPipeline:

    def __init__(self):

        self.retriever = HybridRetriever()

    def run(
        self,
        db,
        query: str,
        top_k: int = 10
    ):

        # ========================================================
        # 1. PROCESS QUERY
        # ========================================================

        processed = process_query(
            query
        )

        normalized_query = (
            processed[
                "normalized_query"
            ]
        )

        # ========================================================
        # 2. EXPAND QUERY
        # ========================================================

        expanded_queries = (
            expand_query(
                normalized_query
            )
        )

        # ========================================================
        # 3. HYBRID RETRIEVAL
        # ========================================================

        candidates = self.retriever.search(
            db,
            expanded_queries,
            top_k
        )

        # ========================================================
        # 4. FETCH DOCUMENT CONTENT
        # ========================================================

        candidate_documents = fetch_chunks(
            db,
            candidates
        )

        # ========================================================
        # 5. RERANK DOCUMENTS
        # ========================================================

        ranked = rerank_results(
            normalized_query,
            candidate_documents,
            top_k
        )

        # ranked already contains complete evidence
        MIN_RERANK_SCORE = 0.05

        evidence = [
            item
            for item in ranked
            if item.get("rerank_score", 0.0) >= MIN_RERANK_SCORE
        ][:top_k]

        # ========================================================
        # 6. BUILD CONTEXT
        # ========================================================

        context = build_context(
            normalized_query,
            evidence,
            max_results=8
        )

        # ========================================================
        # DEBUG
        # ========================================================

        print("\n========== RETRIEVAL DEBUG ==========")

        print(
            "Query:",
            query
        )

        print(
            "Normalized query:",
            normalized_query
        )

        print("\nExpanded queries:")

        for q in expanded_queries:
            print(
                "  -",
                q
            )

        print(
            "\nCandidate count:",
            len(candidates)
        )

        print("\nCandidates:")

        for candidate in candidates:
            print(
                candidate
            )

        print(
            "\nCandidate documents:",
            len(candidate_documents)
        )

        print("\nReranked results:")

        for item in ranked:

            print(
                item.get("title"),
                "| rerank:",
                item.get("rerank_score"),
                "| retrieval:",
                item.get("retrieval_score")
            )

        print(
            "\nFinal evidence count:",
            len(evidence)
        )

        print(
            "======================================\n"
        )

        # ========================================================
        # RETURN
        # ========================================================

        return {

            "query":
                query,

            "normalized_query":
                normalized_query,

            "expanded_queries":
                expanded_queries,

            "candidate_count":
                len(candidates),

            "results":
                evidence,

            "context":
                context
        }