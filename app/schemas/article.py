from pydantic import BaseModel
from typing import List, Optional


class ArticleSource(BaseModel):
    title: str
    source: str
    url: str
    content: str
    score: Optional[float] = None
    faiss_id: Optional[int] = None


class GenerateArticleRequest(BaseModel):
    query: str
    results: List[ArticleSource]


class GeneratedArticleResponse(BaseModel):
    title: str
    query: str
    html_file: str
    sources: List[ArticleSource]