from typing import Any


def extract_relevant_evidence(
    inquiry: str,
    evidence: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    usable = [
        item
        for item in evidence
        if isinstance(item, dict)
        and isinstance(item.get("content"), str)
        and item["content"].strip()
    ]
    if not usable:
        return []

    from app.retrieval.reranker import rerank_results

    return rerank_results(
        inquiry,
        usable,
        top_k=top_k,
    )
