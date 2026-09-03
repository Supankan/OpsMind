# ADR-003: Milvus 2.6 Standalone Development Baseline

## Status
Accepted

## Date
2026-09-03

## Context
OpsMind relies on vector retrieval and semantic memory for runbook guidance and historical incident recall. Milvus offers two primary deployment topologies: Standalone (single container with embedded/external etcd and MinIO) and Distributed (sharded cluster with proxy, query nodes, data nodes, and index nodes). Additionally, Milvus server releases require matching Python SDK versions; specifically, Milvus 2.6.x introduces built-in full-text search / BM25 which requires compatible client versions.

## Decision
- **Milvus 2.6.22 Standalone** is established as the authoritative local development baseline.
- When PyMilvus integration is introduced in later passes, the project will pin to **PyMilvus 2.6.x** (such as 2.6.17), matching the server minor version. PyMilvus 3.x is explicitly excluded to avoid API mismatches.
- Distributed Milvus clustering is deferred to production hardening passes.

## Consequences
### Positive
- Predictable and resource-efficient local execution within the Windows 10 + WSL2 + Docker Desktop environment.
- Native access to Milvus 2.6 full-text search capabilities for hybrid (dense + BM25) retrieval.
- Avoids SDK incompatibilities and protocol breaks.

### Negative
- Standalone mode does not simulate multi-node distributed failure modes or partition sharding.
