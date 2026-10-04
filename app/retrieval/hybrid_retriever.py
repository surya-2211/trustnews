from typing import Dict, List

from app.retrieval.dense_retriever import (
    DenseRetriever
)

from app.retrieval.keyword_retriever import (
    keyword_search
)


class HybridRetriever:

    def __init__(self):

        self.dense_retriever = DenseRetriever()

        # ========================================================
        # WEIGHTS
        # ========================================================

        self.dense_weight = 0.5
        self.keyword_weight = 0.5

        # ========================================================
        # RELEVANCE THRESHOLDS
        # ========================================================

        # Tune these using validation queries.
        #
        # 0.50 is too permissive for the current dataset.
        #

        self.min_dense_score = 0.70

        # Actual PostgreSQL ts_rank score.
        self.min_keyword_score = 0.05

        # Minimum hybrid score.
        self.min_retrieval_score = 0.35

    # ============================================================
    # KEYWORD NORMALIZATION
    # ============================================================

    def normalize_keyword_scores(
        self,
        results: List[dict]
    ):

        positive_scores = [
            float(
                item.get(
                    "keyword_score",
                    0.0
                )
            )
            for item in results
            if float(
                item.get(
                    "keyword_score",
                    0.0
                )
            ) > 0.0
        ]

        if not positive_scores:

            for item in results:

                item[
                    "keyword_score_normalized"
                ] = 0.0

            return results

        minimum = min(
            positive_scores
        )

        maximum = max(
            positive_scores
        )

        for item in results:

            score = float(
                item.get(
                    "keyword_score",
                    0.0
                )
            )

            if score <= 0.0:

                normalized = 0.0

            elif maximum == minimum:

                normalized = 1.0

            else:

                normalized = (
                    score - minimum
                ) / (
                    maximum - minimum
                )

            item[
                "keyword_score_normalized"
            ] = normalized

        return results

    # ============================================================
    # CALCULATE SCORES
    # ============================================================

    def calculate_retrieval_scores(
        self,
        candidates: Dict[int, dict]
    ):

        results = list(
            candidates.values()
        )

        if not results:
            return []

        self.normalize_keyword_scores(
            results
        )

        for item in results:

            dense_score = float(
                item.get(
                    "dense_score",
                    0.0
                )
            )

            keyword_normalized = float(
                item.get(
                    "keyword_score_normalized",
                    0.0
                )
            )

            # Dense score comes from normalized
            # BGE embeddings + inner product.
            dense_normalized = max(
                0.0,
                min(
                    dense_score,
                    1.0
                )
            )

            item[
                "dense_score_normalized"
            ] = dense_normalized

            item[
                "retrieval_score"
            ] = (
                self.dense_weight
                * dense_normalized
                +
                self.keyword_weight
                * keyword_normalized
            )

            item[
                "dense_match"
            ] = (
                dense_score
                >= self.min_dense_score
            )

            item[
                "keyword_match"
            ] = (
                float(
                    item.get(
                        "keyword_score",
                        0.0
                    )
                )
                >= self.min_keyword_score
            )

        results.sort(
            key=lambda item: item[
                "retrieval_score"
            ],
            reverse=True
        )

        return results

    # ============================================================
    # SEARCH
    # ============================================================

    def search(
        self,
        db,
        queries: List[str],
        top_k: int = 10
    ):

        candidates: Dict[int, dict] = {}

        # ========================================================
        # RUN ALL QUERIES
        # ========================================================

        for query in queries:

            # ----------------------------------------------------
            # Dense
            # ----------------------------------------------------

            dense_results = (
                self.dense_retriever.search(
                    query,
                    top_k
                )
            )

            # ----------------------------------------------------
            # Keyword
            # ----------------------------------------------------

            keyword_results = (
                keyword_search(
                    db,
                    query,
                    top_k
                )
            )

            # ====================================================
            # MERGE DENSE
            # ====================================================

            for result in dense_results:

                faiss_id = int(
                    result["faiss_id"]
                )

                if faiss_id not in candidates:

                    candidates[faiss_id] = {

                        "faiss_id":
                            faiss_id,

                        "dense_score":
                            0.0,

                        "keyword_score":
                            0.0
                    }

                candidates[
                    faiss_id
                ][
                    "dense_score"
                ] = max(

                    candidates[
                        faiss_id
                    ][
                        "dense_score"
                    ],

                    float(
                        result.get(
                            "dense_score",
                            0.0
                        )
                    )
                )

            # ====================================================
            # MERGE KEYWORD
            # ====================================================

            for result in keyword_results:

                faiss_id = int(
                    result["faiss_id"]
                )

                if faiss_id not in candidates:

                    candidates[faiss_id] = {

                        "faiss_id":
                            faiss_id,

                        "dense_score":
                            0.0,

                        "keyword_score":
                            0.0
                    }

                candidates[
                    faiss_id
                ][
                    "keyword_score"
                ] = max(

                    candidates[
                        faiss_id
                    ][
                        "keyword_score"
                    ],

                    float(
                        result.get(
                            "keyword_score",
                            0.0
                        )
                    )
                )

        # ========================================================
        # CALCULATE SCORES
        # ========================================================

        ranked_candidates = (
            self.calculate_retrieval_scores(
                candidates
            )
        )

        # ========================================================
        # FILTER
        # ========================================================

        filtered_results = []

        for item in ranked_candidates:

            dense_score = float(
                item.get(
                    "dense_score",
                    0.0
                )
            )

            keyword_score = float(
                item.get(
                    "keyword_score",
                    0.0
                )
            )

            retrieval_score = float(
                item.get(
                    "retrieval_score",
                    0.0
                )
            )

            strong_dense = (
                dense_score
                >= self.min_dense_score
            )

            strong_keyword = (
                keyword_score
                >= self.min_keyword_score
            )

            strong_hybrid = (
                retrieval_score
                >= self.min_retrieval_score
            )

            # ----------------------------------------------------
            # Accept:
            #
            # Strong semantic match
            # OR
            # strong lexical match
            #
            # but final score must still pass threshold.
            # ----------------------------------------------------

            if (
                strong_hybrid
                and (
                    strong_dense
                    or strong_keyword
                )
            ):

                filtered_results.append(
                    item
                )

        return filtered_results[:top_k]