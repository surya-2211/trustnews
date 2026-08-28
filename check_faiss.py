from app.retrieval.faiss_store import FAISSStore

store = FAISSStore(768)

print("FAISS vector count:", store.count())