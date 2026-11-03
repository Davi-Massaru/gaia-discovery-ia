# IRIS Vector Search — Previous Investigations and Conclusions

**Status:** Proposed implementation. IRIS SQL VECTOR and `VECTOR_COSINE` are documented; validate property mapping, SQL execution and embedding access in the installed build 154.

## Python-first implementation policy

Follow the canonical [Python First policy](../../SPEC.md): Embedded Python implements application/data behavior; ObjectScript supplies necessary IRIS-native glue; Java is restricted to the one PEX custom TAP adapter. Verify build-154 compatibility.

## Why it exists

Use **semantic search over past Gaia Discovery AI investigation reports** to give the AI Hub analogous previous investigations, typical evidence gaps, and human-review outcomes before it chooses a scientific test. This is **memory of the application's own prior conclusions**, not an astronomical database or proof that two detections are the same object.

The same capability powers an optional text search box within the existing **Discovery Feed**. Do not build a separate vector database, RAG framework, embedding worker, UI page or vector Business Operation.

## Data and embedding model

Store in the existing `Gaia.Data.DiscoveryReport` class (in addition to existing fields):

- `SearchText`: concise structured English text of observed transient characteristics, catalog evidence, initial/final hypotheses, final assessment, and scientific uncertainties. Do not embed raw pixel arrays, secrets, exception stack traces or entire tool transcripts.
- `SearchEmbedding`: IRIS SQL `VECTOR(FLOAT,1536)` or compatible `%Vector` property mapping.
- `EmbeddingModel`: exactly `text-embedding-3-small`, plus an optional model-version marker if required by the stored configuration.
- `ReviewStatus`: `NOT_REQUIRED`, `PENDING`, `ACCEPTED_FOR_REVIEW`, `REJECTED`, `TASK_ERROR` (native task submission failure; no human decision is a discovery confirmation).

Use **OpenAI `text-embedding-3-small`, 1536 dimensions**, with the existing `OPENAI_API_KEY` (the only external credential). Generate vectors through a small in-process Embedded Python helper, using the documented OpenAI `/v1/embeddings` contract, or the installed `%Embedding.OpenAI` integration if its configuration is verified in build 154. **Choose one**, not both. The reference architecture uses the in-process Python helper to avoid another runtime/secret store. Ensure the key does not appear in report JSON/logs.

### Query path — on new alert

1. Normalize the Fink alert measurements and classification metadata into a deterministic short English search sentence (no unsupported visual conclusions).
2. Obtain its query embedding using the same model as saved reports.
3. Perform `TOP 3` vector similarity search in IRIS SQL, excluding the current report/alert ID and rows without an embedding. Apply any review-status or evidence-quality filters deterministically.
4. Provide `reportId`, `similarity`, `previousHypothesis`, `assessment`, `reviewStatus` and compact prior conclusion to the AI Hub in a separate `historicalAnalogies` field.
5. The AI Hub may use an analogy to generate a hypothesis or select a catalog, but MUST distinguish previous application reports from independent scientific catalog evidence. Similarity is **not an astronomical classification probability**.
6. If there are no indexed cases, OpenAI embeddings are temporarily unavailable, or vector SQL fails, proceed with an empty `historicalAnalogies` array and record a non-blocking warning.

### Save path — at investigation completion

1. Persist `DiscoveryReport` and its original image evidence first, even if embedding generation fails.
2. Build `SearchText` from **the actual final report** and obtain/store one 1536-element vector.
3. When a human Workflow Engine review completes, update the report's `ReviewStatus` and regenerate the embedding only if SearchText includes that outcome. A failed re-embedding does not lose the underlying report.

## SQL contract (illustrative until tested on build 154)

Conceptual schema field, not a duplicate storage table:

```sql
-- Existing DiscoveryReport SQL table gains one vector column:
SearchEmbedding VECTOR(FLOAT,1536)
```

Illustrative top-three similarity query (use SQL parameters for all input, validated vector length):

```sql
SELECT TOP 3
    ID,
    Assessment,
    Summary,
    ReviewStatus,
    VECTOR_COSINE(SearchEmbedding, TO_VECTOR(?, FLOAT, 1536)) AS Similarity
FROM Gaia_Data.DiscoveryReport
WHERE SearchEmbedding IS NOT NULL
  AND DiaObjectId <> ?
ORDER BY Similarity DESC
```

`TO_VECTOR` input is a comma-separated numeric string serialized from the **actual query embedding**. `Gaia_Data.DiscoveryReport` is an expected SQL projection name; verify the concrete class-to-SQL mapping in build 154. **Do not** use Vector Search to join Gaia, SIMBAD and AllWISE observations; those must be correlated by coordinates/time.

For a small MVP dataset, a bounded exact cosine scan may suffice. If supported and useful for the real data volume, add a cosine HNSW index on the existing column after confirming the syntax and query plan; do not introduce a new indexing service.

## UI contract

- Discovery Feed: existing report list plus optional **Search past investigations** text field, using the existing `GET /api/discoveries?search=...` handler. Return at most 10 ranked report summaries; no new UI page.
- Investigation Report: `Similar previous investigations` section with up to 3 report links, labels, brief explanations and similarity values (clearly labeled as **textual similarity**, not scientific confidence).
- If embeddings are unavailable, normal report listing remains functional.

## Acceptance

- Two stored reports with actual generated embeddings; query returns ranked report IDs from IRIS `VECTOR_COSINE` SQL, not Python in-memory cosine search.
- New alert's AI context includes top-three prior reports when available, with provenance and human-review outcome.
- A second investigation can reference an earlier conclusion, but the AI still performs an independent catalog check when scientific validation requires it.
- An empty vector index or embedding API outage does not prevent a normal investigation or saved report.
- Reports remain searchable and visible without embeddings; no secrets enter SQL-visible fields.

## Official references

- [IRIS Vector Search](https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSQL_vecsearch)
- [IRIS SQL VECTOR datatype](https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=RSQL_datatype)
- [OpenAI embeddings HTTP API](https://developers.openai.com/api/reference/resources/embeddings/methods/create)
- [Official technology bonuses](https://community.intersystems.com/post/technology-bonuses-intersystems-programming-contest-ai-agents-interoperability-workflows)
