import hashlib
import math
import re
from typing import Any, Callable, Optional

from app.verification.evidence_extractor import extract_relevant_evidence
from app.verification.inquiry_generator import generate_inquiries
from app.verification.judge import VERDICTS, judge_claim
from app.verification.retrieval_agent import RetrievalAgent
from app.verification.schemas import (
    ArticleVerificationResponse,
    ClaimVerificationResult,
    EvidenceReference,
    ExtractedClaim,
    VerificationSummary,
)


UNCERTAIN_VERDICTS = {
    "NOT_ENOUGH_EVIDENCE",
    "CONFLICTING_EVIDENCE",
}


class ClaimVerificationOrchestrator:
    def __init__(
        self,
        retrieval_pipeline: Any,
        top_k: int = 10,
        max_retries: int = 2,
        inquiry_agent: Callable[[str], dict[str, Any]] = generate_inquiries,
        evidence_extractor: Callable[
            [str, list[dict[str, Any]], int], list[dict[str, Any]]
        ] = extract_relevant_evidence,
        judge_agent: Callable[
            [dict[str, Any], list[dict[str, Any]]], dict[str, Any]
        ] = judge_claim,
        retrieval_agent: Optional[RetrievalAgent] = None,
    ):
        self.top_k = top_k
        self.max_retries = max_retries
        self.inquiry_agent = inquiry_agent
        self.evidence_extractor = evidence_extractor
        self.judge_agent = judge_agent
        self.retrieval_agent = retrieval_agent or RetrievalAgent(
            retrieval_pipeline,
            top_k,
        )

    def verify(
        self,
        claims: list[dict[str, Any]],
        initial_evidence: list[dict[str, Any]],
        db: Any,
        article_id: Optional[str] = None,
    ) -> ArticleVerificationResponse:
        verification_results = [
            self._verify_claim(
                claim,
                initial_evidence,
                db,
                default_claim_id=f"claim_{index:03d}",
            )
            for index, claim in enumerate(claims, start=1)
        ]

        counts = {
            verdict: sum(
                result.verdict == verdict
                for result in verification_results
            )
            for verdict in VERDICTS
        }

        return ArticleVerificationResponse(
            article_id=article_id,
            extracted_claims=[
                ExtractedClaim(
                    claim_id=result.claim_id,
                    claim_text=result.claim_text,
                )
                for result in verification_results
            ],
            verification_results=verification_results,
            summary=VerificationSummary(
                total_claims=len(verification_results),
                supported=counts["SUPPORTED"],
                refuted=counts["REFUTED"],
                conflicting_evidence=counts["CONFLICTING_EVIDENCE"],
                not_enough_evidence=counts["NOT_ENOUGH_EVIDENCE"],
            ),
        )

    def _verify_claim(
        self,
        claim: dict[str, Any],
        initial_evidence: list[dict[str, Any]],
        db: Any,
        default_claim_id: str,
    ) -> ClaimVerificationResult:
        if not isinstance(claim, dict):
            raise ValueError("Every claim must be an object.")
        raw_claim_text = claim.get("claim_text")
        if not isinstance(raw_claim_text, str):
            raise ValueError("Every claim must contain text.")
        claim_text = " ".join(raw_claim_text.split())
        if not claim_text:
            raise ValueError("Every claim must contain non-empty claim_text.")

        claim_id = str(claim.get("claim_id") or default_claim_id)

        inquiry = self.inquiry_agent(claim_text)
        verification_question = inquiry["verification_question"]
        search_queries = inquiry["search_queries"]
        evidence = self._deduplicate(initial_evidence)
        queries_used = set()
        retrieval_attempts = 1 if evidence else 0
        retrieval_retries = 0

        if not evidence:
            query = self._next_query(
                [verification_question, *search_queries],
                queries_used,
            )
            if query:
                evidence, _ = self._retrieve(
                    db,
                    query,
                    evidence,
                )
                retrieval_attempts += 1

        extracted = self.evidence_extractor(
            verification_question,
            evidence,
            self.top_k,
        )

        if not extracted:
            decision = {
                "verdict": "NOT_ENOUGH_EVIDENCE",
                "explanation": "No relevant evidence passages were available.",
                "supporting_evidence_indexes": [],
                "contradicting_evidence_indexes": [],
                "further_retrieval_recommended": True,
            }
        else:
            decision = self.judge_agent(
                {
                    "claim_id": claim_id,
                    "claim_text": claim_text,
                },
                extracted,
            )
            self._validate_decision(decision, len(extracted))

        while (
            decision["verdict"] in UNCERTAIN_VERDICTS
            and decision["further_retrieval_recommended"]
            and retrieval_retries < self.max_retries
        ):
            query = self._next_query(search_queries, queries_used)
            if not query:
                break

            updated_evidence, added = self._retrieve(
                db,
                query,
                evidence,
            )
            retrieval_attempts += 1
            retrieval_retries += 1
            if not added:
                continue

            evidence = updated_evidence
            extracted = self.evidence_extractor(
                verification_question,
                evidence,
                self.top_k,
            )
            if not extracted:
                decision = {
                    "verdict": "NOT_ENOUGH_EVIDENCE",
                    "explanation": (
                        "No relevant evidence passages were available."
                    ),
                    "supporting_evidence_indexes": [],
                    "contradicting_evidence_indexes": [],
                    "further_retrieval_recommended": True,
                }
            else:
                decision = self.judge_agent(
                    {
                        "claim_id": claim_id,
                        "claim_text": claim_text,
                    },
                    extracted,
                )
                self._validate_decision(decision, len(extracted))

        return self._build_result(
            claim_id,
            claim_text,
            decision,
            extracted,
            retrieval_attempts,
            decision["verdict"] in UNCERTAIN_VERDICTS
            and decision["further_retrieval_recommended"],
        )

    def _retrieve(
        self,
        db: Any,
        query: str,
        existing: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], bool]:
        results = self.retrieval_agent.retrieve(db, query)
        merged = self._deduplicate([*existing, *results])
        return merged, len(merged) > len(existing)

    @staticmethod
    def _deduplicate(
        evidence: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        unique = []
        seen = set()
        for item in evidence:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, str) or not content.strip():
                continue

            if item.get("id") is not None:
                key = ("id", str(item["id"]))
            elif item.get("faiss_id") is not None:
                key = ("faiss_id", str(item["faiss_id"]))
            else:
                material = "\n".join(
                    str(item.get(field, ""))
                    for field in ("url", "title", "content")
                )
                key = ("content", hashlib.sha256(
                    material.encode("utf-8")
                ).hexdigest())

            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

    @staticmethod
    def _next_query(
        candidates: list[str],
        queries_used: set[str],
    ) -> Optional[str]:
        for query in candidates:
            if not isinstance(query, str) or not query.strip():
                continue
            normalized = re.sub(r"\s+", " ", query).strip().casefold()
            if normalized not in queries_used:
                queries_used.add(normalized)
                return query.strip()
        return None

    @staticmethod
    def _validate_decision(
        decision: dict[str, Any],
        evidence_count: int,
    ) -> None:
        if not isinstance(decision, dict):
            raise RuntimeError("Judge returned a malformed decision.")
        verdict = decision.get("verdict")
        if not isinstance(verdict, str) or verdict not in VERDICTS:
            raise RuntimeError("Judge returned an invalid verdict.")
        for field in (
            "supporting_evidence_indexes",
            "contradicting_evidence_indexes",
        ):
            indexes = decision.get(field)
            if not isinstance(indexes, list) or any(
                type(index) is not int or not 0 <= index < evidence_count
                for index in indexes
            ):
                raise RuntimeError(f"Judge returned invalid {field}.")
        if (
            decision["verdict"] == "SUPPORTED"
            and not decision["supporting_evidence_indexes"]
        ):
            raise RuntimeError("Judge marked a claim supported without evidence.")
        if (
            decision["verdict"] == "REFUTED"
            and not decision["contradicting_evidence_indexes"]
        ):
            raise RuntimeError("Judge marked a claim refuted without evidence.")
        if (
            decision["verdict"] == "CONFLICTING_EVIDENCE"
            and (
                not decision["supporting_evidence_indexes"]
                or not decision["contradicting_evidence_indexes"]
            )
        ):
            raise RuntimeError(
                "Judge marked a claim conflicting without both evidence sides."
            )
        if (
            not isinstance(decision.get("explanation"), str)
            or not decision["explanation"].strip()
        ):
            raise RuntimeError("Judge returned no explanation.")
        if not isinstance(
            decision.get("further_retrieval_recommended"),
            bool,
        ):
            raise RuntimeError("Judge returned an invalid retrieval flag.")

    @staticmethod
    def _build_result(
        claim_id: str,
        claim_text: str,
        decision: dict[str, Any],
        evidence: list[dict[str, Any]],
        attempts: int,
        further_retrieval: bool,
    ) -> ClaimVerificationResult:
        supporting_indexes = decision["supporting_evidence_indexes"]
        contradicting_indexes = decision["contradicting_evidence_indexes"]
        selected_indexes = list(dict.fromkeys(
            [*supporting_indexes, *contradicting_indexes]
        ))
        selected_evidence = [
            evidence[index]
            for index in selected_indexes
        ]
        references = [
            ClaimVerificationOrchestrator._reference(item)
            for item in selected_evidence
        ]
        supporting_ids = _available_evidence_ids(
            evidence,
            supporting_indexes,
        )
        contradicting_ids = _available_evidence_ids(
            evidence,
            contradicting_indexes,
        )
        source_urls = list(dict.fromkeys(
            ref.url for ref in references if ref.url
        ))

        return ClaimVerificationResult(
            claim_id=claim_id,
            claim_text=claim_text,
            verdict=decision["verdict"],
            confidence=None,
            explanation=decision["explanation"],
            supporting_evidence_ids=supporting_ids,
            contradicting_evidence_ids=contradicting_ids,
            source_urls=source_urls,
            source_references=references,
            evaluated_evidence=[
                ClaimVerificationOrchestrator._reference(item)
                for item in evidence
            ],
            retrieval_attempts=attempts,
            further_retrieval_recommended=further_retrieval,
        )

    @staticmethod
    def _reference(item: dict[str, Any]) -> EvidenceReference:
        published_at = item.get("published_at")
        return EvidenceReference(
            chunk_id=_optional_int(item.get("id")),
            faiss_id=_optional_int(item.get("faiss_id")),
            title=str(item.get("title") or ""),
            source=str(item.get("source") or ""),
            url=str(item.get("url") or ""),
            published_at=(
                str(published_at) if published_at is not None else None
            ),
            content=str(item.get("content") or ""),
            dense_score=_optional_float(item.get("dense_score")),
            keyword_score=_optional_float(item.get("keyword_score")),
            retrieval_score=_optional_float(item.get("retrieval_score")),
            rerank_score=_optional_float(item.get("rerank_score")),
        )


def _available_evidence_ids(
    evidence: list[dict[str, Any]],
    indexes: list[int],
) -> list[int]:
    identifiers = []
    for index in indexes:
        item = evidence[index]
        identifier = _optional_int(item.get("id"))
        if identifier is None:
            identifier = _optional_int(item.get("faiss_id"))
        if identifier is not None and identifier not in identifiers:
            identifiers.append(identifier)
    return identifiers


def _optional_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
        return int(value)
    return None


def _optional_float(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    try:
        result = float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
    if result is None:
        return None
    return result if math.isfinite(result) else None
