from generation.article_generator import generate_article


results = [
    {
        "title": "NASA mission update",
        "source": "NASA",
        "content": (
            "NASA announced an update about its latest space "
            "mission and provided information about the mission's "
            "objectives."
        ),
        "url": "https://example.com/article",
        "score": 0.91
    },
    {
        "title": "Scientists discuss the mission",
        "source": "Science News",
        "content": (
            "Scientists discussed the scientific goals of the "
            "mission and the expected observations."
        ),
        "url": "https://example.com/science",
        "score": 0.87
    }
]


query = "What are the objectives of the latest NASA mission?"

article = generate_article(
    query,
    results
)

print("\nGENERATED ARTICLE\n")
print(article)