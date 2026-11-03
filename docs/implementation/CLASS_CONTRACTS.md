# Gaia Discovery AI — Class and Component Contracts

**Design-level interfaces only**, not vendor SDK method signatures or compiled code. For native `OnProcessInput`, `OnMessage`, BPL XML, `%SYS.Python.WSGI`, Flask routing, `Language=python`, PEX method/proxy access and AI Hub APIs, inspect the actual installed EAP build and official examples before writing executable `.cls` methods. Never translate these semantic signatures into invented SDK calls.

## 1. Request/response envelopes: exactly two application classes

`Gaia.Interop.Messages.DiscoveryRequest extends Ens.Request`:

- Required logical fields: `RunId : String`, `Kind : Enum`, `CorrelationId : String`, `PayloadJSON : bounded JSON/Text`, optional `ImageStreamRef : stream reference`.
- Kinds (logical discriminators, **not subclasses**): `START_RUN`, `LIST_BY_TAG`, `GET_SOURCES`, `GET_CUTOUT`, `AGENT_DECIDE`, `CATALOG_QUERY`, `SAVE_REPORT`.
- All Fink source identifiers and external catalog source identifiers are strings (never JavaScript JSON numbers). Binary PNGs are passed/stored as binary stream references, not encoded into model prompts.

`Gaia.Interop.Messages.DiscoveryResponse extends Ens.Response`:

- Required logical fields: `RunId`, `Kind`, `CorrelationId`, `Status`, `PayloadJSON`, `ErrorCode`, `ErrorSummary`, optional `ImageStreamRef`.
- Status: `OK` / `EMPTY` / `ERROR`; the `NOT_REQUESTED` state is in the **evidence aggregate** when a BO was not invoked, not an actual response.
- The same message contracts connect application BPL ↔ operations. Native Workflow `EnsLib.Workflow.TaskRequest/TaskResponse` remain separate and unmodified.

Authoritative canonical JSON structure: [INTERNAL_MESSAGES.md](../contracts/INTERNAL_MESSAGES.md).

## 2. Ingestion: DiscoveryService and FinkOperation

`Gaia.Interop.DiscoveryService` (adapterless Business Service):

- Semantic input: `start_run(tag: str, count: int=5) -> runId: str`.
- Verify supported Fink tag and `1 <= count <= 20`, create/record `ACCEPTED` state, dispatch to the one BPL asynchronously; the independent HTTP `202` is returned by the Flask WSGI handler.
- Do not make an HTTP request await the entire workflow or a human task.

`Gaia.Interop.Operations.FinkOperation` (IRIS Business Operation + standard HTTP outbound adapter):

- `list_by_tag(tag, limit) -> [diaObjectId: str]`
- `get_sources(diaObjectId: str) -> [detection]`
- `get_cutout(diaSourceId: str, kind: science|template|difference) -> binary stream ref`
- Validate that all three cutouts belong to the selected detection and that mandatory metadata originate from Fink. Preserve absence explicitly.
- Do not add a custom Fink adapter or a separate downloader service.

## 3. Adaptive BPL and AI Hub

`Gaia.Interop.DiscoveryWorkflow` (single `Ens.BusinessProcess.BPL`):

- State per alert: `runId`, Fink metadata, requested catalog set, up to 3 historical analogies, agent decisions (max 4), evidence status, final assessment, reportId and native InteropSessionId.
- `AGENT_DECIDE -> switch CHECK_GAIA | CHECK_SIMBAD | CHECK_IRSA | FINISH`, with action allowlisting and no duplicate checks; at most 3 catalog actions. Normalize/fold each real response into evidence before re-asking AI Hub.
- After every object report save, mark candidate report `PENDING` and enqueue a native Workflow task asynchronously; after saving/dispatching all scientific outputs, set scientific run `COMPLETED` and perform native BPL `<sync>` with correlation to `reportId` for replies. Never block browser request.
- Invalid action, result or out-of-budget path gives deterministic `INCONCLUSIVE`, preserving all evidence and errors.

`Gaia.Interop.Operations.AIHubOperation`:

- `decide(evidence, actionsDone, remainingBudget) -> validated decision JSON`.
- Build bounded prompt context in Embedded Python, call one **native** `%AI.Agent` using installed SDK binding, validate exact JSON fields/enumerations against the [decision schema](../contracts/AI_HUB_DECISION.schema.json).
- The native `%AI.Agent` is configured through the SDK, not an assumed custom `Gaia.AI.DiscoveryAgent.cls` wrapper. Record AI decisions and explanations in EvidenceJSON.

## 4. Catalog Operations with one Java PEX TAP transport

Each of `GaiaOperation`, `SimbadOperation`, `IrsaOperation`:

- Semantic interface: `query(alertRaDeg, alertDecDeg, radiusArcsec, context) -> CatalogResult`.
- Embedded Python validates coordinates, constructs bounded allowlisted ADQL, parses TAP CSV, normalizes catalog fields and computes separations through `Gaia.Science.AngularSeparation`.
- `CatalogResult = {source, status, timestamp, sanitized_endpoint, sanitized_query, matches:[{id,ra,dec,separationArcsec,...}], error?}`.
- `OK` = successful parsed nonempty results; `EMPTY` = successful parsed zero-row result; `ERROR` = HTTP, timeout, TAP error or invalid response. **Do not** silently downgrade failure to `EMPTY`.
- Assign all three BOs the **same registered PEX adapter proxy** as verified on build; `ADAPTER` is an IRIS class parameter referencing generated proxy name, not a made-up Java hostname.

Java class `com.gaia.discovery.pex.TapOutboundAdapter extends com.intersystems.enslib.pex.OutboundAdapter`:

- Transports allowlisted HTTPS form-encoded TAP requests to ESA Gaia, CDS SIMBAD or NASA IRSA endpoints; enforces TLS, timeout and response-size bounds and returns bytes/status.
- Does **not** perform catalog selection, model calls, ADQL authoring, astronomy/CSV math or report writes. The actual Java method interface must follow installed PEX API / registered proxy.
- Reuse native Java gateway required by PEX; do not introduce an extra HTTP microservice.

## 5. Science, persistence, history

`Gaia.Science.AngularSeparation` (Embedded Python):

- `angular_separation_arcsec(ra1_deg, dec1_deg, ra2_deg, dec2_deg) -> float` (semantic signature; use stable great-circle formula and coordinate validation).
- Report epoch/proper-motion ambiguity; position-only proximity is not object identity.

`Gaia.Science.ReportEmbedding` (Embedded Python):

- `embed_summary(text) -> vector[1536] | None` through `text-embedding-3-small` using ignored `OPENAI_API_KEY`.
- `search_previous(alertSummary, topK=3) -> list[existing ReportId]` via actual supported IRIS `VECTOR_COSINE` SQL.
- Vector failure is nonblocking and never fabricates history or uses catalog data as vector identity.

`Gaia.Data.DiscoveryReport extends %Persistent` is the **sole** domain record with planned properties:

| Group | Properties |
|---|---|
| Identity | `RunId`, `DiaObjectId`, `DiaSourceId`, `Tag`, `CreatedAt`, `InteropSessionId` |
| Science | `RA`, `Dec`, `ObservedMjdTai`, `SciencePNG`, `TemplatePNG`, `DifferencePNG` |
| AI and evidence | `Assessment`, `Summary`, `EvidenceJSON` |
| Vector | `SearchText`, `SearchEmbedding` (`VECTOR(FLOAT,1536)` in SQL), `EmbeddingModel` |
| Human review | `ReviewStatus` (`NOT_REQUIRED`, `PENDING`, `ACCEPTED_FOR_REVIEW`, `REJECTED`, `TASK_ERROR`) |

Use actual build-supported `%Stream.GlobalBinary` (or supported equivalent) for image persistence and verify class/SQL vector declaration in IRIS before generating code. Do not store 64-bit Fink IDs in floating-point JSON numbers.

## 6. Flask WSGI REST + final UI

`backend/app.py` defines the **single Flask callable `app`** configured as an IRIS native WSGI web application (`%SYS.Python.WSGI`). It owns the routes below and uses the in-process `iris` module for persisted report access and validated async submission to `DiscoveryService`. Do not implement a `Gaia.API.DiscoveryAPI` `.cls` class or a second HTTP runtime. The routes are application-relative: IRIS mounts the app at `/gaia`, so `/api/discoveries` below is externally `/gaia/api/discoveries`. See [WSGI_API.md](../contracts/WSGI_API.md).

| Request | Required result |
|---|---|
| `POST /api/discoveries/run` `{tag,count}` | HTTP 202, `runId`, `ACCEPTED`; validate 1–20 (default 5) |
| `GET /api/discoveries/runs/{runId}` | scientific run state/progress/report IDs; bounded IRIS global, cleanup |
| `GET /api/discoveries` | newest 20 saved reports by default; bounded pagination or semantic search |
| `GET /api/discoveries/{id}` | persisted full report with AI timeline, provenance, source states, review state and trace ID |
| `GET /api/discoveries/{id}/images/{kind}` | byte-exact stored `image/png` from report stream or explicit 404 |

Flask must return bounded JSON and byte-exact image streams, with proper `202`/`404`/error statuses and without embedded credentials. WSGI configuration and authenticated access must be tested in the EAP build (experimental capability). The two final `web/` views **read only persisted IRIS responses**. The built-in native Workflow Inbox is the review UI; Gaia Discovery AI does not build another one. See [UI_SPEC.md](../specification/UI_SPEC.md).

## 7. Delivery and verification order

1. Verify real EAP SDK, native message/adapter classes, PEX registration, Fink/TAP endpoints and SQL Vector syntax.
2. Implement the two message classes, native Production/BPL, Fink and one catalog/AI Hub path, then other catalog paths.
3. Persist a scientific report and authentic cutouts. Test Vector Search, native Workflow TaskRequest/Inbox/TaskResponse, asynchronous run status and error states.
4. Validate Flask WSGI REST inside IRIS with actual responses and Message Trace; build **two-view UI last**.
5. Prove Docker and publish/test ZPM package including all web assets. Capture real traces/screenshots. See [implementation guide](IMPLEMENTATION_GUIDE.md) and [bonus evidence plan](../contest/BONUS_IMPLEMENTATION_PLAN.md).

No bonus points are guaranteed by a schema, plan or `.cls` filename; only actual implementation and judge-accepted evidence can substantiate the bonus.
