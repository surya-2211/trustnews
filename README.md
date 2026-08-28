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

