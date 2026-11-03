# OpenAI Embeddings Contract for IRIS Vector History

**Purpose:** optional but targeted semantic retrieval of prior investigation reports using the **existing OpenAI key**; not an alternative astronomical observatory.

| Field | Value |
|---|---|
| HTTP | `POST https://api.openai.com/v1/embeddings` |
| Credential | `Authorization: Bearer ${OPENAI_API_KEY}` (never log or include in reports) |
| Media type | `application/json` |
| Request | `{"model":"text-embedding-3-small","input":"<short deterministic report or alert text>"}` |
| Response used | `data[0].embedding` numeric vector; `model`; `usage` if present |
| Expected dimension | 1536 with model default; validate before storing |
| Consumer | Embedded Python inside IRIS, using same key as AI Hub provider but separate text-embedding request |

**Failure:** no output / invalid length / network or quota failure -> continue investigation and persist report with `SearchEmbedding=NULL`. No secondary secrets, another vector service or unbounded retries. IRIS SQL `VECTOR_COSINE` queries only saved report vectors; do not confuse embedding similarity with physical object association.

**Official documentation:** https://platform.openai.com/docs/api-reference/embeddings/create ; [VECTOR_HISTORY.md](VECTOR_HISTORY.md). SDK/client signatures and quota/rates require deployment validation.
