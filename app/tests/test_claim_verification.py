import os
import unittest
from unittest.mock import patch

from app.generation.article_template import build_article_html
from app.verification.claim_extractor import extract_claims
from app.verification.errors import map_gemini_error
from app.verification.inquiry_generator import generate_inquiries
from app.verification.judge import judge_claim
from app.verification.llm import generate_structured_json
from app.verification.orchestrator import ClaimVerificationOrchestrator
from google.genai.errors import ServerError, ClientError


def evidence(
    chunk_id=1,
    content="The research team began testing the model.",
    url="https://example.test/story",
):
    return {
        "id": chunk_id,
        "faiss_id": chunk_id + 100,
        "title": "Research update",
        "source": "Example News",
        "url": url,
        "content": content,
        "published_at": "2026-10-01",
        "retrieval_score": 0.8,
    }


def decision(
    verdict,
    supporting=None,
    contradicting=None,
    further=False,
):
    return {
        "verdict": verdict,
        "explanation": f"Evidence evaluation: {verdict}.",
        "supporting_evidence_indexes": supporting or [],
        "contradicting_evidence_indexes": contradicting or [],
        "further_retrieval_recommended": further,
    }


class StubRetrieval:
    def __init__(self, responses=None, error=None):
        self.responses = list(responses or [])
        self.error = error
        self.queries = []

    def run(self, db, query, top_k):
        self.queries.append(query)
        if self.error:
            raise self.error
        response = self.responses.pop(0) if self.responses else []
        return {"results": response[:top_k]}


class StubGeminiModels:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def generate_content(self, **_kwargs):
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class StubGeminiClient:
    def __init__(self, responses):
        self.models = StubGeminiModels(responses)


class ClaimVerificationTests(unittest.TestCase):
    def build_orchestrator(
        self,
        verdicts,
        retrieval=None,
        max_retries=2,
    ):
        decisions = iter(verdicts)
        judge_calls = []

        def inquiry(claim_text):
            return {
                "verification_question": f"Is this true: {claim_text}?",
                "search_queries": [
                    f"alternate one: {claim_text}",
                    f"alternate two: {claim_text}",
                ],
            }

        def judge(claim, passages):
            judge_calls.append((claim, passages))
            return next(decisions)

        orchestrator = ClaimVerificationOrchestrator(
            retrieval_pipeline=retrieval or StubRetrieval(),
            top_k=5,
            max_retries=max_retries,
            inquiry_agent=inquiry,
            evidence_extractor=lambda _query, passages, limit: passages[:limit],
            judge_agent=judge,
        )
        return orchestrator, judge_calls

    def verify_one(
        self,
        verdict,
        initial=None,
        supporting=None,
        contradicting=None,
        further=False,
        retrieval=None,
        max_retries=2,
    ):
        orchestrator, judge_calls = self.build_orchestrator(
            [decision(verdict, supporting, contradicting, further)],
            retrieval,
            max_retries,
        )
        result = orchestrator.verify(
            claims=[{
                "claim_id": "claim_original",
                "claim_text": "The model is undergoing clinical testing.",
            }],
            initial_evidence=initial or [],
            db=object(),
            article_id="article-7",
        )
        return result, judge_calls, orchestrator

    def test_supported_verdict_preserves_claim_and_source_identifiers(self):
        source = evidence(chunk_id=12)
        result, _, _ = self.verify_one(
            "SUPPORTED",
            initial=[source],
            supporting=[0],
        )
        verification = result.verification_results[0]
        self.assertEqual(verification.verdict, "SUPPORTED")
        self.assertEqual(verification.claim_id, "claim_original")
        self.assertEqual(verification.supporting_evidence_ids, [12])
        self.assertEqual(verification.source_urls, [source["url"]])
        self.assertEqual(verification.source_references[0].faiss_id, 112)
        self.assertEqual(verification.confidence, None)

    def test_refuted_verdict_records_contradicting_source(self):
        result, _, _ = self.verify_one(
            "REFUTED",
            initial=[evidence(content="Testing has not started.")],
            contradicting=[0],
        )
        verification = result.verification_results[0]
        self.assertEqual(verification.verdict, "REFUTED")
        self.assertEqual(verification.contradicting_evidence_ids, [1])

    def test_conflicting_verdict_keeps_both_provenances(self):
        passages = [
            evidence(1, "The trial has started.", "https://example.test/a"),
            evidence(2, "The trial has not started.", "https://example.test/b"),
        ]
        result, _, _ = self.verify_one(
            "CONFLICTING_EVIDENCE",
            initial=passages,
            supporting=[0],
            contradicting=[1],
        )
        verification = result.verification_results[0]
        self.assertEqual(
            verification.verdict,
            "CONFLICTING_EVIDENCE",
        )
        self.assertEqual(verification.supporting_evidence_ids, [1])
        self.assertEqual(verification.contradicting_evidence_ids, [2])
        self.assertEqual(len(verification.source_urls), 2)

    def test_insufficient_evidence_stops_after_retry_limit(self):
        retrieval = StubRetrieval(responses=[[], []])
        result, judge_calls, _ = self.verify_one(
            "NOT_ENOUGH_EVIDENCE",
            retrieval=retrieval,
            max_retries=1,
        )
        verification = result.verification_results[0]
        self.assertEqual(verification.verdict, "NOT_ENOUGH_EVIDENCE")
        self.assertEqual(verification.retrieval_attempts, 2)
        self.assertEqual(len(retrieval.queries), 2)
        self.assertEqual(judge_calls, [])

    def test_retry_retrieves_new_evidence_and_rejudges(self):
        first = evidence(1, "The topic is under review.")
        second = evidence(2, "Clinical testing began in October.")
        retrieval = StubRetrieval(responses=[[second]])
        orchestrator, judge_calls = self.build_orchestrator(
            [
                decision("NOT_ENOUGH_EVIDENCE", further=True),
                decision("SUPPORTED", supporting=[1]),
            ],
            retrieval=retrieval,
            max_retries=2,
        )
        result = orchestrator.verify(
            claims=[{"claim_id": "c1", "claim_text": "Testing began."}],
            initial_evidence=[first],
            db=object(),
        )
        verification = result.verification_results[0]
        self.assertEqual(verification.verdict, "SUPPORTED")
        self.assertEqual(verification.retrieval_attempts, 2)
        self.assertEqual(len(judge_calls), 2)
        self.assertEqual(verification.supporting_evidence_ids, [2])

    def test_duplicate_retrieval_is_deduplicated_without_rejudging(self):
        original = evidence(8)
        retrieval = StubRetrieval(responses=[[dict(original)]])
        result, judge_calls, _ = self.verify_one(
            "NOT_ENOUGH_EVIDENCE",
            initial=[original],
            further=True,
            retrieval=retrieval,
            max_retries=1,
        )
        verification = result.verification_results[0]
        self.assertEqual(len(judge_calls), 1)
        self.assertEqual(verification.retrieval_attempts, 2)
        self.assertEqual(len(verification.evaluated_evidence), 1)

    def test_multiple_claims_are_counted_independently(self):
        orchestrator, _ = self.build_orchestrator([
            decision("SUPPORTED", supporting=[0]),
            decision("REFUTED", contradicting=[0]),
        ])
        result = orchestrator.verify(
            claims=[
                {"claim_id": "claim_a", "claim_text": "Claim A."},
                {"claim_id": "claim_b", "claim_text": "Claim B."},
            ],
            initial_evidence=[evidence()],
            db=object(),
        )
        self.assertEqual(
            [item.claim_id for item in result.verification_results],
            ["claim_a", "claim_b"],
        )
        self.assertEqual(result.summary.total_claims, 2)
        self.assertEqual(result.summary.supported, 1)
        self.assertEqual(result.summary.refuted, 1)

    def test_missing_metadata_does_not_create_fake_source_ids(self):
        no_ids = {
            "id": 3.5,
            "faiss_id": True,
            "content": "The team started tests.",
            "source": "Research office",
            "url": "https://example.test/announcement",
        }
        result, _, _ = self.verify_one(
            "SUPPORTED",
            initial=[no_ids],
            supporting=[0],
        )
        verification = result.verification_results[0]
        self.assertEqual(verification.supporting_evidence_ids, [])
        self.assertEqual(verification.source_urls, [no_ids["url"]])
        self.assertIsNone(verification.source_references[0].chunk_id)
        self.assertIsNone(verification.source_references[0].faiss_id)

    def test_judge_and_retrieval_failures_propagate(self):
        orchestrator, _ = self.build_orchestrator(
            [],
            retrieval=StubRetrieval(error=RuntimeError("retrieval failed")),
        )
        with self.assertRaisesRegex(RuntimeError, "retrieval failed"):
            orchestrator.verify(
                claims=[{"claim_text": "A claim."}],
                initial_evidence=[],
                db=object(),
            )

        orchestrator, _ = self.build_orchestrator(
            [],
            retrieval=StubRetrieval(),
        )
        orchestrator.judge_agent = lambda *_args: (_ for _ in ()).throw(
            RuntimeError("judge failed")
        )
        with self.assertRaisesRegex(RuntimeError, "judge failed"):
            orchestrator.verify(
                claims=[{"claim_text": "A claim."}],
                initial_evidence=[evidence()],
                db=object(),
            )

    def test_claim_extraction_deduplicates_and_assigns_stable_ids(self):
        def fake_llm(_prompt, _schema):
            return {
                "claims": [
                    "The test began in October.",
                    " The test began in October. ",
                    "The trial enrolled 20 participants.",
                ]
            }

        claims = extract_claims(
            "An article.",
            generate_json=fake_llm,
        )
        self.assertEqual(
            claims,
            [
                {
                    "claim_id": "claim_001",
                    "claim_text": "The test began in October.",
                },
                {
                    "claim_id": "claim_002",
                    "claim_text": "The trial enrolled 20 participants.",
                },
            ],
        )

    def test_claim_extraction_llm_failure_is_not_silenced(self):
        def failing_llm(_prompt, _schema):
            raise RuntimeError("LLM unavailable")

        with self.assertRaisesRegex(RuntimeError, "LLM unavailable"):
            extract_claims("Article.", generate_json=failing_llm)

    def test_judge_rejects_fabricated_evidence_indexes(self):
        def bad_llm(_prompt, _schema):
            return {
                "verdict": "SUPPORTED",
                "explanation": "A result.",
                "supporting_evidence_indexes": [4],
                "contradicting_evidence_indexes": [],
                "further_retrieval_recommended": False,
            }

        with self.assertRaisesRegex(RuntimeError, "invalid index"):
            judge_claim(
                {"claim_text": "A claim."},
                [evidence()],
                generate_json=bad_llm,
            )

    def test_generated_article_page_contains_claim_check_action(self):
        html = build_article_html(
            query="Research",
            article={
                "title": "A research update",
                "introduction": "The study reports a new result.",
                "sections": [
                    {
                        "heading": "Findings",
                        "content": "The team began testing.",
                    }
                ],
                "key_points": [],
                "conclusion": "More work remains.",
            },
            sources=[evidence(content="A source passage.")],
        )
        self.assertIn('id="verify-claims-button"', html)
        self.assertIn('fetch("/verify-article"', html)
        self.assertIn('"faiss_id": 101', html)
        self.assertIn('"published_at": "2026-10-01"', html)
        self.assertIn("The team began testing.", html)

    def test_generated_page_escapes_source_json_script_terminators(self):
        source = evidence(content='</script><script>alert("x")</script>')
        html = build_article_html(
            query="Research",
            article={
                "title": "Title",
                "introduction": "Intro",
                "sections": [],
                "key_points": [],
                "conclusion": "Conclusion",
            },
            sources=[source],
        )
        self.assertNotIn('</script><script>alert("x")', html)

    def test_gemini_503_retries_once_then_succeeds(self):
        unavailable = ServerError(
            503,
            {
                "error": {
                    "code": 503,
                    "message": "Model temporarily unavailable.",
                    "status": "UNAVAILABLE",
                }
            },
        )
        client = StubGeminiClient([
            unavailable,
            type("Response", (), {"text": '{"claims": []}'})(),
        ])
        delays = []

        result = generate_structured_json(
            "prompt",
            {"type": "OBJECT"},
            client=client,
            model_name="test-model",
            sleep=delays.append,
        )

        self.assertEqual(result, {"claims": []})
        self.assertEqual(client.models.calls, 2)
        self.assertEqual(delays, [1])

    def test_gemini_503_uses_bounded_exponential_backoff(self):
        unavailable = ServerError(
            503,
            {
                "error": {
                    "code": 503,
                    "message": "Model temporarily unavailable.",
                    "status": "UNAVAILABLE",
                }
            },
        )
        client = StubGeminiClient([
            unavailable,
            unavailable,
            type("Response", (), {"text": '{"claims": []}'})(),
        ])
        delays = []

        result = generate_structured_json(
            "prompt",
            {"type": "OBJECT"},
            client=client,
            model_name="test-model",
            sleep=delays.append,
        )

        self.assertEqual(result, {"claims": []})
        self.assertEqual(client.models.calls, 3)
        self.assertEqual(delays, [1, 2])

    def test_gemini_503_exhaustion_maps_to_clear_service_unavailable(self):
        unavailable = ServerError(
            503,
            {
                "error": {
                    "code": 503,
                    "message": "Temporary high demand.",
                    "status": "UNAVAILABLE",
                }
            },
        )
        client = StubGeminiClient([unavailable, unavailable, unavailable])
        with self.assertRaises(ServerError):
            generate_structured_json(
                "prompt",
                {"type": "OBJECT"},
                client=client,
                model_name="test-model",
                sleep=lambda _seconds: None,
            )

        mapped = map_gemini_error(unavailable, "test-model")
        self.assertEqual(mapped.status_code, 503)
        self.assertIn("Temporary high demand", mapped.detail)
        self.assertEqual(client.models.calls, 3)

    def test_inquiry_generation_needs_no_gemini_request(self):
        result = generate_inquiries(
            "  The research team began testing the model.  "
        )

        self.assertEqual(
            result["search_queries"],
            ["The research team began testing the model."],
        )
        self.assertIn(
            "The research team began testing the model.",
            result["verification_question"],
        )

    def test_per_minute_429_retries_once_after_provider_delay(self):
        rate_limit = ClientError(
            429,
            {
                "error": {
                    "code": 429,
                    "message": "Requests per minute limit exceeded.",
                    "status": "RESOURCE_EXHAUSTED",
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                            "violations": [
                                {
                                    "quotaId": (
                                        "GenerateRequestsPerMinutePerProject"
                                    ),
                                    "description": (
                                        "Generate content requests per minute "
                                        "limit exceeded."
                                    ),
                                }
                            ],
                        },
                        {
                            "@type": "type.googleapis.com/google.rpc.RetryInfo",
                            "retryDelay": "21.946s",
                        },
                    ],
                }
            },
        )
        client = StubGeminiClient([
            rate_limit,
            type("Response", (), {"text": '{"claims": []}'})(),
        ])
        delays = []

        result = generate_structured_json(
            "prompt",
            {"type": "OBJECT"},
            client=client,
            model_name="test-model",
            sleep=delays.append,
        )

        self.assertEqual(result, {"claims": []})
        self.assertEqual(client.models.calls, 2)
        self.assertEqual(delays, [21.946])

    def test_daily_429_is_not_retried_and_maps_as_quota_exhaustion(self):
        daily_quota = ClientError(
            429,
            {
                "error": {
                    "code": 429,
                    "message": "Daily quota exceeded.",
                    "status": "RESOURCE_EXHAUSTED",
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                            "violations": [
                                {
                                    "quotaId": (
                                        "GenerateRequestsPerDayPerProject"
                                    ),
                                    "description": (
                                        "Generate content requests per day "
                                        "limit exceeded."
                                    ),
                                }
                            ],
                        },
                        {
                            "@type": "type.googleapis.com/google.rpc.RetryInfo",
                            "retryDelay": "12h18m41s",
                        },
                    ],
                }
            },
        )
        client = StubGeminiClient([daily_quota])
        delays = []

        with self.assertRaises(ClientError):
            generate_structured_json(
                "prompt",
                {"type": "OBJECT"},
                client=client,
                model_name="test-model",
                sleep=delays.append,
            )

        self.assertEqual(client.models.calls, 1)
        self.assertEqual(delays, [])
        mapped = map_gemini_error(daily_quota, "test-model")
        self.assertEqual(mapped.status_code, 429)
        self.assertIn("project and model", mapped.detail)

    def test_gemini_quota_and_model_errors_are_distinguishable(self):
        quota = ClientError(
            429,
            {
                "error": {
                    "code": 429,
                    "message": "Daily quota exceeded.",
                    "status": "RESOURCE_EXHAUSTED",
                }
            },
        )
        unauthorized = ClientError(
            401,
            {
                "error": {
                    "code": 401,
                    "message": "Invalid API key.",
                    "status": "UNAUTHENTICATED",
                }
            },
        )
        not_found = ClientError(
            404,
            {
                "error": {
                    "code": 404,
                    "message": "Unknown model.",
                    "status": "NOT_FOUND",
                }
            },
        )
        self.assertEqual(map_gemini_error(quota, "model").status_code, 429)
        self.assertIn(
            "not an individual API key",
            map_gemini_error(quota, "model").detail,
        )
        auth_error = map_gemini_error(unauthorized, "model")
        self.assertEqual(auth_error.status_code, 502)
        self.assertIn("API key", auth_error.detail)
        model_error = map_gemini_error(not_found, "missing-model")
        self.assertEqual(model_error.status_code, 502)
        self.assertIn("missing-model", model_error.detail)
        self.assertIn("Unknown model", model_error.detail)

    def test_article_generation_does_not_retry_quota_errors(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            from app.generation import article_generator

        quota = ClientError(
            429,
            {
                "error": {
                    "code": 429,
                    "message": "Daily quota exceeded.",
                    "status": "RESOURCE_EXHAUSTED",
                }
            },
        )
        with (
            patch.object(article_generator, "build_prompt", return_value="prompt"),
            patch.object(article_generator, "client") as client,
            patch.object(article_generator.time, "sleep") as sleep,
        ):
            client.models.generate_content.side_effect = quota

            with self.assertRaises(ClientError):
                article_generator.generate_article(
                    "A test query",
                    [{"content": "A source passage."}],
                )

        client.models.generate_content.assert_called_once()
        sleep.assert_not_called()

    def test_invalid_gemini_json_is_reported_as_runtime_error(self):
        client = StubGeminiClient([
            type("Response", (), {"text": "not JSON"})(),
        ])

        with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
            generate_structured_json(
                "prompt",
                {"type": "OBJECT"},
                client=client,
                model_name="test-model",
            )


if __name__ == "__main__":
    unittest.main()
