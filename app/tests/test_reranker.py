from app.retrieval.reranker import rerank_results

query = "NASA astronaut mission"

results = [
    {
        "title": "Artemis II Crew at NASA Marshall",
        "content": "The crew of NASA's Artemis II mission..."
    },
    {
        "title": "NASA Awards First Prize in LunaRecycle Challenge",
        "content": "NASA named a team from MIT..."
    }
]

ranked = rerank_results(
    query,
    results,
    top_k=2
)

for result in ranked:
    print("\nTitle:", result["title"])
    print("Rerank score:", result["rerank_score"])