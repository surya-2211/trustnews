from typing import Dict


def process_query(query: str) -> Dict:
    """
    Normalize and prepare the user's query
    before retrieval.
    """

    if not query:
        raise ValueError("Query cannot be empty.")

    query = query.strip()

    if len(query) < 3:
        raise ValueError("Query is too short.")

    normalized_query = " ".join(query.split())

    return {
        "original_query": query,
        "normalized_query": normalized_query
    }