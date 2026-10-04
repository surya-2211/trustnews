from app.retrieval.query_processor import process_query

queries = [
    "NASA astronaut mission",
    "  NASA   astronaut   mission  ",
    "NASA astronot mission",
    "What are the latest NASA astronaut missions?"
]

for query in queries:
    print("\nINPUT:")
    print(query)

    result = process_query(query)

    print("OUTPUT:")
    print(result)