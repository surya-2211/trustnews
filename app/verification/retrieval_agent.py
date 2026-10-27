from typing import Any


class RetrievalAgent:
    def __init__(self, retrieval_pipeline: Any, top_k: int = 10):
        self.retrieval_pipeline = retrieval_pipeline
        self.top_k = top_k

    def retrieve(self, db: Any, query: str) -> list[dict[str, Any]]:
        result = self.retrieval_pipeline.run(
            db=db,
            query=query,
            top_k=self.top_k,
        )
        results = result.get("results", [])
        if not isinstance(results, list):
            raise RuntimeError("Retrieval pipeline returned malformed results.")
        return [
            item
            for item in results
            if isinstance(item, dict)
        ]
