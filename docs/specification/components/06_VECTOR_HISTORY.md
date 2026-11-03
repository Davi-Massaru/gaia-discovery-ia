# Component 06 — Previous Investigations with IRIS Vector Search

**Purpose:** show the agent prior cases that may suggest useful investigative questions, and allow historical semantic search from the existing Discovery Feed. Past reports are supporting analogies, **not** identification of the current object.

**Data ownership:** one existing `%Persistent` `Gaia.Data.DiscoveryReport` table, including `SearchText`, `SearchEmbedding VECTOR(FLOAT,1536)`, `EmbeddingModel`, no separate vector DB. One Embedded Python method builds text and calls OpenAI `/v1/embeddings` with the existing `OPENAI_API_KEY` and model `text-embedding-3-small`; a supported IRIS SQL `VECTOR_COSINE` query ranks past report vectors.

## Read path

1. Build a short deterministic text from available real Fink measurements/tags (exclude images).
2. Embed this text once. On failure, continue with no analogies.
3. Search saved reports for TOP 3 non-null vectors, exclude same `diaObjectId` if present, order cosine similarity descending.
4. Return `{reportId, similarity, priorHypothesis, priorOutcome, reviewStatus}` plus provenance to the AI Hub. Explicitly label semantic similarity.

## Write path

1. Always save the report and images first.
2. Build `SearchText` from saved conclusion, source statuses and uncertainty; create embedding.
3. Update `SearchEmbedding` of the same report; index after human review only if stored search text changes.

**Constraints:** 1536 floats; enforce model/dimension match; never put API key in SQL/logs; avoid embedding full raw catalog rows, stack traces, private prompts or pixel arrays. A cold-start/no previous data case is normal. Vector history search is **not** the cross-catalog spatial join.

**Test:** two real stored reports with embeddings, a ranked `VECTOR_COSINE` result from IRIS SQL, failure to embed does not block report creation, no history does not block AI. Detailed SQL and documented model: [`VECTOR_HISTORY.md`](../../contracts/VECTOR_HISTORY.md); [`OPENAI_EMBEDDINGS.md`](../../contracts/OPENAI_EMBEDDINGS.md).
