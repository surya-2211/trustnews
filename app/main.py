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

from app.schemas.retrieval import (
    RetrievalRequest,
    RetrievalResponse
)

from app.retrieval.retrieval_pipeline import (
    RetrievalPipeline
)

# Create database tables
Base.metadata.create_all(bind=engine)

retrieval_pipeline = RetrievalPipeline()

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

@app.post(
    "/generate-article",
    response_model=GeneratedArticleResponse
)
def generate_article_endpoint(
    request: GenerateArticleRequest,
    db: Session = Depends(get_db)
):

    try:

        # =====================================================
        # 1. RETRIEVE + RERANK EVIDENCE
        # =====================================================

        retrieval_result = retrieval_pipeline.run(

            db=db,

            query=request.query,

            top_k=request.top_k
        )


        # =====================================================
        # 2. CHECK EVIDENCE
        # =====================================================

        evidence = retrieval_result.get(
            "results",
            []
        )


        context = retrieval_result.get(
            "context",
            ""
        )


        if not evidence:

            raise HTTPException(

                status_code=404,

                detail=(
                    "No relevant evidence was found "
                    "for the requested query."
                )
            )


        # =====================================================
        # 3. GENERATE ARTICLE
        # =====================================================

        article = generate_article(

            query=request.query,

            results=evidence,

            context=context
        )


        # =====================================================
        # 4. BUILD HTML
        # =====================================================

        html = build_article_html(

            query=request.query,

            article=article,

            sources=evidence
        )


        # =====================================================
        # 5. SAVE HTML
        # =====================================================

        file_path = save_article_html(

            query=request.query,

            html=html
        )


        filename = (

            file_path
            .replace("\\", "/")
            .split("/")[-1]
        )


        # =====================================================
        # 6. RETURN RESPONSE
        # =====================================================

        return {

            "title": article.get(
                "title",
                "TrustNews Article"
            ),

            "query": request.query,

            "normalized_query":
                retrieval_result.get(
                    "normalized_query",
                    request.query
                ),

            "html_file":
                f"/generated_articles/{filename}",

            "sources": evidence
        }


    except HTTPException:

        raise


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc)
        )


@app.post(
    "/retrieve",
    response_model=RetrievalResponse
)
def retrieve(
    request: RetrievalRequest,
    db: Session = Depends(get_db)
):

    try:

        result = retrieval_pipeline.run(
            db=db,
            query=request.query,
            top_k=request.top_k
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )