# IRIS Internal Message Contracts (Application Design)

**Status:** design-level contracts for `Ens.*` messages, **not yet compiled classes**. Native `%Status` and message signatures must be verified against EAP build 154. Use typed fields on IRIS request/response classes; JSON examples below document wire/logic shapes only. Keep stream binary outside context JSON.

## Shared envelope

Every IRIS message includes: `runId` (string), `diaObjectId` (string when applicable), `interopSessionId`/native correlation identity, `messageType`, `status` (`OK|EMPTY|ERROR` for API responses), `errorCode` (sanitized nullable). An uncalled catalog has `NOT_REQUESTED` status in the **aggregate evidence**, not an actual network response.

| Request → response | Required logical fields | Consumer |
|---|---|---|
| `DiscoveryRunRequest → DiscoveryRunResponse` | `tag`, `1 <= count <= 20` → `runId`, `state` | REST / `DiscoveryService` |
| `FinkRequest → FinkResponse` | `operation: LIST_BY_TAG|GET_SOURCES|GET_CUTOUT`, ID/tag; return observation metadata or image stream refs | `DiscoveryWorkflow` |
| `DecisionRequest → DecisionResponse` | observation, evidence statuses, past cases, actionsDone, remainingBudget → validated agent schema | `DiscoveryWorkflow` |
| `CatalogRequest → CatalogResponse` | `catalog`, alert RA/Dec, radiusArcsec → status, matches, request/endpoint provenance | `DiscoveryWorkflow` |
| `DiscoveryReportResult` | `reportId`, saved assessment, `reviewStatus`, `interopSessionId` | REST and workflow task coordination |

**Class mapping:** Implement the two typed envelopes `Gaia.Interop.Messages.DiscoveryRequest` and `Gaia.Interop.Messages.DiscoveryResponse`. The named `DiscoveryRunRequest`, `FinkRequest/Response`, `DecisionRequest/Response`, `CatalogRequest/Response`, and `DiscoveryReportResult` below are **logical message variants**, not additional `.cls` files. Each envelope includes a validated `kind` discriminator and only bounded data or image stream references. Do not create separate classes for every variant.

**Decision response schema:** use [`AI_HUB_DECISION.schema.json`](AI_HUB_DECISION.schema.json). A new report is persisted after the agent finishes or a deterministic failure occurs; do not rely on LLM-generated IDs or timestamps.

## Evidence aggregate (internal object)

```json
{
  "runId":"RUN_ID",
  "diaObjectId":"FINK_OBJECT_ID",
  "observedMjdTai":null,
  "raDeg":null,
  "decDeg":null,
  "finkImages":{"science":"IRIS_STREAM_REF","template":"IRIS_STREAM_REF","difference":"IRIS_STREAM_REF"},
  "catalogs":{
    "GAIA":{"status":"NOT_REQUESTED","matches":[]},
    "SIMBAD":{"status":"NOT_REQUESTED","matches":[]},
    "IRSA":{"status":"NOT_REQUESTED","matches":[]}
  },
  "historicalAnalogies":[],
  "decisionHistory":[],
  "interopSessionId":"INTEROP_SESSION_ID"
}
```

This is a **template**; actual observation coordinates/time must come from Fink and the image entries must be stream references, not invented bytes.

## Lifecycle invariants

1. `LIST_BY_TAG` with no alerts -> run status `NO_ALERTS`, not a fictional report.
2. For each object, the selected `diaSourceId` must be returned by that object's `/sources` call.
3. No catalog Operation runs unless chosen by valid AI action. At most three distinct catalog actions.
4. `OK/EMPTY/ERROR` are mutually exclusive and grounded in actual remote response parsing; `NOT_REQUESTED` means no BPL call.
5. Final `REVIEW_CANDIDATE` -> **save report first**; existing BPL async `<call>` to `AstronomyReviewer` using **native** `EnsLib.Workflow.TaskRequest` with `%Subject`, `%Message`, `%Actions="ACCEPT,REJECT"`. Native `<sync>` receives `EnsLib.Workflow.TaskResponse.%Action`; update the same report's `ReviewStatus`. This is **not** a new `DiscoveryRequest`/`DiscoveryResponse` message variant and needs no custom workflow message subclasses. REST returns `202` independently of human waiting. `TASK_ERROR` marks failed task submission, not a positive review result.
6. Persist each action/reason, requested catalog, source status, endpoint, retrieval timestamp and `interopSessionId` to support Message Trace verification.
7. Distinguish AI Hub Session from native IRIS Interoperability Session.
