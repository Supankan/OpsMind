# ADR-002: PostgreSQL vs. Milvus Responsibilities

## Status
Accepted

## Date
2026-09-03

## Context
OpsMind manages two distinct categories of data:
1. Structured transactional data: Incidents, investigation execution runs, hypotheses, evidence records, tool execution logs, and audit trails.
2. Unstructured semantic data: Operational runbooks, service architecture documentation, troubleshooting guides, and historical postmortems.

Treating a vector store as a primary source of truth degrades data consistency and auditability, while using a relational database for high-dimensional vector search degrades retrieval performance and flexibility.

## Decision
- **PostgreSQL is the authoritative transactional source of truth**:
  - Manages incidents, investigation runs, hypothesis-evidence relationship graphs, tool call logs, recommendations, and evaluation metrics.
  - Guarantees ACID compliance, foreign key integrity, and durable audit logs.
- **Milvus is a derived semantic retrieval and memory index**:
  - Stores dense vector embeddings and lexical/BM25 representations for operational knowledge (`operational_knowledge`) and past incident memory (`incident_memory`).
  - Is strictly a downstream index; every vector chunk retains a reference (`source_id`, `source_uri`, `content_hash`) back to the canonical source document or PostgreSQL record.
  - Milvus state can be rebuilt or re-indexed from canonical sources at any time.

## Consequences
### Positive
- Robust data integrity and complete auditability for all SRE decisions and agent actions.
- Clear separation between ground-truth transactional facts and fuzzy semantic recall.
- Clean disaster recovery and re-indexing capability without data loss.

### Negative
- Requires maintaining an ingestion and synchronization pipeline to project canonical data into Milvus collections.
