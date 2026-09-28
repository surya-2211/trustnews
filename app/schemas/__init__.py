from pydantic import BaseModel


class QueryRequest(BaseModel):

    query: str

    top_k: int = 5


class SearchResult(BaseModel):

    score: float

    title: str

    source: str

    url: str

    content: str