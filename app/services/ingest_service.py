from sqlalchemy.orm import Session

from app.ingestion.rss import fetch_all_feeds
from app.ingestion.cleaner import clean_article
from app.ingestion.chunker import chunk_text

from app.retrieval.embeddings import embed_documents
from app.retrieval.faiss_store import FAISSStore

from app.models import NewsChunk


def ingest_news(db: Session):

    articles = fetch_all_feeds()

    documents = []

    metadata = []

    for article in articles:

        cleaned = clean_article(
            article
        )

        chunks = chunk_text(
            cleaned["text"]
        )

        for chunk in chunks:

            documents.append(chunk)

            metadata.append({
                "title": cleaned["title"],
                "source": cleaned["source"],
                "url": cleaned["url"],
                "chunk_text": chunk
            })

    if not documents:

        return {
            "message": "No articles found",
            "chunks_added": 0
        }

    embeddings = embed_documents(
        documents
    )

    dimension = embeddings.shape[1]

    store = FAISSStore(
        dimension
    )

    start_id = store.count()

    store.add_embeddings(
        embeddings
    )

    for i, data in enumerate(metadata):

        faiss_id = start_id + i

        record = NewsChunk(
            title=data["title"],
            source=data["source"],
            url=data["url"],
            chunk_text=data["chunk_text"],
            faiss_id=faiss_id
        )

        db.add(record)

    db.commit()

    return {
        "message": "Ingestion completed",
        "articles": len(articles),
        "chunks_added": len(documents)
    }