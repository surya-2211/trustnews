from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class RetrievalRequest(BaseModel):

    query: str

    top_k: int = 10


class RetrievalResult(BaseModel):

    faiss_id: int

    title: str = ""

    source: str = ""

    url: str = ""

    published_at: Optional[datetime] = None

    content: str

    dense_score: float = 0.0

    keyword_score: float = 0.0

    retrieval_score: float = 0.0


class RetrievalResponse(BaseModel):

    query: str

    normalized_query: str

    expanded_queries: List[str]

    candidate_count: int

    results: List[RetrievalResult]

    context: str