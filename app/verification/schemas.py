from typing import Any, List, Optional

from pydantic import BaseModel, Field


class VerificationRequest(BaseModel):
    article_id: Optional[str] = None
    article_text: str = Field(min_length=1, max_length=50000)
    sources: List[dict[str, Any]] = Field(default_factory=list)
    top_k: int = Field(default=10, ge=1, le=30)
    max_retries: int = Field(default=2, ge=0, le=3)


class ExtractedClaim(BaseModel):
    claim_id: str
    claim_text: str


class EvidenceReference(BaseModel):
    chunk_id: Optional[int] = None
    faiss_id: Optional[int] = None
    title: str = ""
    source: str = ""
    url: str = ""
    published_at: Optional[str] = None
    content: str = ""
    dense_score: Optional[float] = None
    keyword_score: Optional[float] = None
    retrieval_score: Optional[float] = None
    rerank_score: Optional[float] = None


class ClaimVerificationResult(BaseModel):
    claim_id: str
    claim_text: str
    verdict: str
    confidence: Optional[float] = None
    explanation: str
    supporting_evidence_ids: List[int] = Field(default_factory=list)
    contradicting_evidence_ids: List[int] = Field(default_factory=list)
    source_urls: List[str] = Field(default_factory=list)
    source_references: List[EvidenceReference] = Field(default_factory=list)
    evaluated_evidence: List[EvidenceReference] = Field(default_factory=list)
    retrieval_attempts: int = 0
    further_retrieval_recommended: bool = False


class VerificationSummary(BaseModel):
    total_claims: int
    supported: int
    refuted: int
    conflicting_evidence: int
    not_enough_evidence: int


class ArticleVerificationResponse(BaseModel):
    article_id: Optional[str] = None
    extracted_claims: List[ExtractedClaim]
    verification_results: List[ClaimVerificationResult]
    summary: VerificationSummary
