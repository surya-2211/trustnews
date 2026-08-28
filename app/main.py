from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import (
    Base,
    engine,
    get_db
)

from app.schemas import QueryRequest

from app.services.ingest_service import (
    ingest_news
)

from app.services.query_service import (
    search_news
)


Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title="TrustNews API",
    version="1.0.0"
)


@app.get("/")
def root():

    return {
        "message": "TrustNews API is running"
    }


@app.post("/ingest")
def ingest(
    db: Session = Depends(get_db)
):

    return ingest_news(db)


@app.post("/search")
def search(
    request: QueryRequest,
    db: Session = Depends(get_db)
):

    results = search_news(
        db,
        request.query,
        request.top_k
    )

    return {
        "query": request.query,
        "results": results
    }