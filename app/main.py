from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, get_db
from app.schemas import QueryRequest
from app.services.ingest_service import ingest_news
from app.services.query_service import search_news
from app.schemas.article import (
    GenerateArticleRequest,
    GeneratedArticleResponse
)

from app.generation.article_generator import (
    generate_article
)

from app.generation.article_template import (
    build_article_html
)

from app.generation.html_exporter import (
    save_article_html
)

# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(
    title="TrustNews API",
    version="1.0.0"
)


# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


app.mount(
    "/generated_articles",
    StaticFiles(directory="generated_articles"),
    name="generated_articles"
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
    return search_news(
        db,
        request.query,
        request.top_k
    )

@app.post("/generate-article")
def generate_article_endpoint(
    request: GenerateArticleRequest
):

    try:

        article = generate_article(
            request.query,
            [
                result.model_dump()
                for result in request.results
            ]
        )

        html = build_article_html(
            query=request.query,
            article=article,
            sources=[
                result.model_dump()
                for result in request.results
            ]
        )

        file_path = save_article_html(
            query=request.query,
            html=html
        )

        filename = file_path.replace("\\", "/").split("/")[-1]

        return {
            "title": article.get(
                "title",
                "TrustNews Article"
            ),
            "query": request.query,

            "html_file": f"/generated_articles/{filename}",

            "sources": [
                result.model_dump()
                for result in request.results
            ]
        }
                

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )