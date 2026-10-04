from app.retrieval.query_expansion import expand_query

query = "NASA astronaut mission"

result = expand_query(query)

print("\nOriginal query:")
print(query)

print("\nExpanded queries:")
for i, item in enumerate(result, start=1):
    print(f"{i}. {item}")