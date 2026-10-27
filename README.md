# TrustNews

## TrustNews: A Multi-Agent Evidence-Grounded RAG Framework for Automated News Article Generation

TrustNews is an AI-assisted news generation system designed to produce trustworthy and evidence-grounded science and technology news articles.

The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from continuously updated trusted news sources before generating an article.

## Current Implementation

### Phase 1 - Knowledge and Retrieval Pipeline

The current implementation includes:

- RSS feed ingestion
- Article cleaning
- Text chunking
- BGE embeddings
- FAISS vector storage
- PostgreSQL metadata storage
- Semantic news retrieval
- FastAPI REST API

### Module 4 - Claim Verification

After generating an article, open its article page and select **Extract and
verify claims**. TrustNews extracts factual claims from the article, checks
them against the supplied sources, and can retrieve additional evidence using
the existing hybrid retrieval pipeline. Verification questions and initial
search queries are built from each claim locally, avoiding an extra Gemini
request per claim. Results use `SUPPORTED`, `REFUTED`,
`CONFLICTING_EVIDENCE`, or `NOT_ENOUGH_EVIDENCE`; relevance scores are not
treated as confidence.

The same workflow is available through `POST /verify-article`. Its JSON body
accepts `article_text`, optional `article_id`, a `sources` array, `top_k`, and
`max_retries`. The response includes extracted claims, verdicts, source
provenance, retrieval attempts, and a per-article summary. Confidence is
currently returned as `null` because the LLM score is not calibrated.

Set `GEMINI_API_KEY` and, if needed, `GEMINI_MODEL` in `.env`. The model
defaults to `gemini-2.5-flash`; it must be available to the configured Gemini
API key and support content generation.

Run the deterministic Module 4 tests from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest app.tests.test_claim_verification -v
```
