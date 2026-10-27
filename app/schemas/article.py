from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# =========================================================
# ARTICLE SOURCE
# =========================================================

class ArticleSource(BaseModel):

    title: str

    source: str

    url: str

    content: str

    published_at: Optional[datetime] = None

    faiss_id: Optional[int] = None

    dense_score: Optional[float] = None

    keyword_score: Optional[float] = None

    retrieval_score: Optional[float] = None

    rerank_score: Optional[float] = None


# =========================================================
# GENERATE ARTICLE REQUEST
# =========================================================

class GenerateArticleRequest(BaseModel):

    query: str

    top_k: int = 10


# =========================================================
# GENERATED ARTICLE RESPONSE
# =========================================================

class GeneratedArticleResponse(BaseModel):

    title: str

    query: str

    normalized_query: str

    html_file: str

    sources: List[ArticleSource]