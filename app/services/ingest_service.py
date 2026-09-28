from sqlalchemy.orm import Session
from sqlalchemy import func

from app.ingestion.rss import fetch_all_feeds
from app.ingestion.cleaner import clean_article
from app.ingestion.chunker import chunk_text

from app.retrieval.embeddings import embed_documents
from app.retrieval.faiss_store import FAISSStore

from app.models import NewsChunk


def ingest_news(db: Session):
    # ---------------------------------------------------------
    # 1. Fetch RSS articles
    # ---------------------------------------------------------
    articles = fetch_all_feeds()

    if not articles:
        return {
            "message": "No articles found",
            "articles": 0,
            "chunks_added": 0
        }

    # ---------------------------------------------------------
    # 2. Get URLs already stored in PostgreSQL
    # ---------------------------------------------------------
    existing_urls = {
        url
        for url in db.query(NewsChunk.url).distinct().all()
        for url in url
        if url
    }

    # Remove duplicate articles from the RSS response itself
    unique_articles = {}
    for article in articles:
        url = article.get("url", "").strip()

        if url:
            unique_articles[url] = article

    # Only keep completely new articles
    new_articles = [
        article
        for url, article in unique_articles.items()
        if url not in existing_urls
    ]

    if not new_articles:
        return {
            "message": "No new articles found",
            "articles": len(articles),
            "new_articles": 0,
            "chunks_added": 0
        }

    # ---------------------------------------------------------
    # 3. Clean and chunk only NEW articles
    # ---------------------------------------------------------
    documents = []
    metadata = []

    for article in new_articles:
        cleaned = clean_article(article)

        chunks = chunk_text(cleaned["text"])

        for chunk_index, chunk in enumerate(chunks):

            if not chunk.strip():
                continue

            documents.append(chunk)

            metadata.append({
                "title": cleaned["title"],
                "source": cleaned["source"],
                "url": cleaned["url"],
                "chunk_text": chunk,
                "chunk_index": chunk_index,
            })

    if not documents:
        return {
            "message": "No new chunks created",
            "articles": len(articles),
            "new_articles": len(new_articles),
            "chunks_added": 0
        }

    # ---------------------------------------------------------
    # 4. Load FAISS
    # ---------------------------------------------------------
    embeddings = embed_documents(documents)

    dimension = embeddings.shape[1]

    store = FAISSStore(dimension)

    # ---------------------------------------------------------
    # 5. IMPORTANT: verify FAISS and PostgreSQL are aligned
    # ---------------------------------------------------------
    db_max_faiss_id = db.query(
        func.max(NewsChunk.faiss_id)
    ).scalar()

    expected_faiss_count = (
        0 if db_max_faiss_id is None
        else db_max_faiss_id + 1
    )

    if store.count() != expected_faiss_count:
        raise RuntimeError(
            "FAISS and PostgreSQL are out of sync. "
            f"FAISS vectors={store.count()}, "
            f"PostgreSQL expected={expected_faiss_count}. "
            "Rebuild the FAISS index before ingesting more news."
        )

    # ---------------------------------------------------------
    # 6. Assign FAISS IDs
    # ---------------------------------------------------------
    start_id = store.count()

    new_records = []

    for i, data in enumerate(metadata):

        faiss_id = start_id + i

        record = NewsChunk(
            title=data["title"],
            source=data["source"],
            url=data["url"],
            chunk_text=data["chunk_text"],
            faiss_id=faiss_id
        )

        new_records.append(record)

    # ---------------------------------------------------------
    # 7. Insert PostgreSQL records FIRST
    # ---------------------------------------------------------
    try:
        db.add_all(new_records)
        db.commit()

    except Exception:
        db.rollback()
        raise

    # ---------------------------------------------------------
    # 8. Only after DB succeeds, add vectors to FAISS
    # ---------------------------------------------------------
    try:
        store.add_embeddings(embeddings)

    except Exception:
        raise RuntimeError(
            "PostgreSQL was updated successfully, "
            "but FAISS failed to update. "
            "Rebuild the FAISS index from PostgreSQL."
        )

    # ---------------------------------------------------------
    # 9. Return result
    # ---------------------------------------------------------
    return {
        "message": "Ingestion completed",
        "articles": len(articles),
        "new_articles": len(new_articles),
        "chunks_added": len(documents),
        "faiss_total": store.count()
    }