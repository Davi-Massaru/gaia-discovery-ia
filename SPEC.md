# Gaia Discovery AI — Master Product Specification

**Version:** MVP 1.2 · **Language:** English · **Status:** specification only · **Target:** authorized InterSystems IRIS AI Hub EAP build 154; validate against the installed runtime.

> **Authority rule:** This is the single product-requirements entry point. The documents under `docs/` define implementation details, not additional features. If a document conflicts with this specification, this file wins. No future features or alternative architectures should be implemented implicitly.

## 1. Purpose and scientific boundaries

The **Gaia Discovery AI** investigates recent Vera C. Rubin Observatory alerts exposed by the Fink broker. It combines alert coordinates, timing, photometry and three **actual** scientific cutouts with independently published catalog data. One native IRIS AI Hub agent formulates competing hypotheses, chooses scientifically justified follow-up queries, interprets evidence after each query, and ends with a traceable preliminary investigation report.

**Central question:** *What explanations fit this alert, and which additional external evidence, if any, would materially change the assessment?*

The application does **not** prove an astronomical discovery, identify every visible pixel source, claim a neighboring catalog object is definitively the transient, or use Vector Search similarity as astronomical crossmatching. Missing catalog matches are not proof of novelty. The AI Hub acts on structured measurements and catalog results; Fink images are saved for human inspection, not presumed multimodal input.

## 2. Product behavior

1. On **Discovery Feed**, select a Fink-supported tag and fetch recent alerts. `count` is configurable **1–20, default 5**, with optional UI presets **1, 5, 10, 20**. Process alerts **sequentially**; reject invalid counts. Initial supported tag should be verified from the live Fink tag list.
2. The **Flask REST handler running via native IRIS WSGI** at the application-relative `POST /api/discoveries/run` immediately returns HTTP `202` with a `runId`; the browser does not wait for the Production, catalogs, embeddings or human review. `GET /api/discoveries/runs/{runId}` returns persisted run state and report IDs. A run returning zero alerts has `NO_ALERTS`, with **no fake report**.
3. The single `DiscoveryService` starts one `DiscoveryWorkflow` BPL in the single Production. `FinkOperation` selects unique `diaObjectId` values, fetches detections and the selected `diaSourceId`, loads **Science, Template and Difference** PNG cutouts, and preserves source identifiers as **strings**.
4. Validate RA/Dec, observation timestamp, measurement availability and image results. Invalid evidence becomes a saved, specifically explained `INCONCLUSIVE` report when an object exists; one missing image is explicitly reported, never replaced by an AI-generated picture.
5. Optional IRIS Vector Search retrieves **up to three previous stored investigations** using an embedding of the alert description; history is an analogy only. Embedding failure must not block the scientific investigation.
6. `Gaia.AI.DiscoveryAgent`, extending the native IRIS `%AI.Agent`, receives bounded current evidence and previous decisions through `AIHubOperation`. It returns a JSON decision matching [AI schema](docs/contracts/AI_HUB_DECISION.schema.json): `CHECK_GAIA`, `CHECK_SIMBAD`, `CHECK_IRSA` or `FINISH`, with hypothesis, alternative, scientific question, rationale and final assessment when finished.
7. The BPL validates every decision and routes **only the chosen** scientific catalog Operation. Each catalog may be queried at most **once per alert**; maximum **three catalog calls and four AI decisions per alert**. An agent may finish without external catalog calls. Invalid agent output causes deterministic recovery/inconclusive handling, not invented evidence or unbounded retries.
8. `GaiaOperation`, `SimbadOperation`, `IrsaOperation` prepare bounded TAP queries and interpret responses in IRIS Embedded Python, sharing **one registered Java PEX Custom TAP Outbound Adapter** for allowlisted HTTPS transport only. Fink uses a standard IRIS HTTP adapter. Status is `OK` / `EMPTY` / `ERROR` / `NOT_REQUESTED` with precise meanings and recorded provenance.
9. After each requested catalog result, normalize source coordinates, calculate angular separation, account for epoch/proper motion uncertainty where relevant, append supporting/conflicting/uncertain evidence, and **re-invoke AI Hub** to reconsider its hypothesis.
10. Save one `Gaia.Data.DiscoveryReport` for each investigated object with real binary cutouts, Fink IDs, sky position/time, initial and revised hypotheses, decisions, source/query provenance, result statuses, assessment and native `InteropSessionId`. The native session reference must correlate with actual IRIS Visual Trace; AI Hub's internal session is distinct.
11. For final `REVIEW_CANDIDATE` **only**, save `ReviewStatus=PENDING`, send an **asynchronous native** `EnsLib.Workflow.TaskRequest` from the **same** BPL to a single configured `EnsLib.Workflow.Operation` named `AstronomyReviewer`, with native Workflow Role and Inbox. Receive `EnsLib.Workflow.TaskResponse.%Action` through native BPL `<sync>` and update the **same** saved report: `ACCEPT→ACCEPTED_FOR_REVIEW`, `REJECT→REJECTED`, dispatch failures `TASK_ERROR`. Other reports use `NOT_REQUIRED`. The run's scientific status is independent of pending human review. Reviewer acceptance is **acceptance for additional investigation**, not discovery confirmation.
12. Implement the minimal two-view UI **last**: **Discovery Feed** (past reports, authentic Science thumbnail, run/tag/count controls, status) and **Investigation Report** (actual 3 images, hypothesis/evidence timeline, catalogs consulted or not consulted, similar earlier reports, human-review state, IRIS session reference). Use plain HTML/CSS/JavaScript; no manual image upload or separate reviewer page.

## 3. Architecture invariants

- One **IRIS Production**, one `Gaia.Interop.DiscoveryWorkflow` BPL, one scientific agent type `Gaia.AI.DiscoveryAgent Extends %AI.Agent` (isolated instance/session per decision), one Business Service, five **application** Business Operations (`Fink`, `AIHub`, `Gaia`, `SIMBAD`, `IRSA`) plus one **native** Workflow Business Operation. No separate review BPL, database, microservice or custom Workflow class. Agent extraction preserves current provider/model/prompt, decision contracts and features; see [migration model](docs/implementation/DISCOVERY_AGENT_MIGRATION.md).
- Two typed **application message classes** (`DiscoveryRequest`, `DiscoveryResponse`) are reused with validated discriminators. Native Workflow TaskRequest/TaskResponse are **not** application message subclasses. No source-image bytes are embedded in ordinary JSON messages; reference persisted binary streams.
- Embedded Python inside IRIS owns application/domain logic, ADQL, parsing, crossmatching, prompt context, decision validation, embedding and report logic where supported. **Flask WSGI in IRIS** owns HTTP routes and response formatting, with direct in-process IRIS access; ObjectScript is minimal native Production/BPL/schema/SDK glue. Java is limited to a single registered PEX outbound adapter providing bounded transport; it does not compute astronomy or classify.
- **Web architecture:** one `backend/app.py` Flask callable named `app`, hosted **inside IRIS** by its WSGI web application (`%SYS.Python.WSGI`); the WSGI deployment path is `/gaia`. Never create `Gaia.API.DiscoveryAPI.cls`, another `%CSP.REST` application, a Flask development server, Gunicorn/Uvicorn, or a separate HTTP microservice. The existing HTTP route paths are **application-relative** (`/gaia` is prepended externally). UI assets are implemented last under `web/`. Confirm the installed EAP build supports WSGI: InterSystems documents it as an experimental feature. [WSGI contract](docs/contracts/WSGI_API.md).
- Exactly **one** persistent domain class `DiscoveryReport`. Short-lived run status may use a bounded IRIS global with cleanup, not a second domain table. Historical report search uses the existing report vector column `VECTOR(FLOAT,1536)` with `text-embedding-3-small` and the existing `OPENAI_API_KEY`.
- Public astronomy API calls do **not** require extra tokens or keys. Keep `.env` ignored by Git. Never publish or copy a user's actual `.env` into an archive.

## 4. Canonical scientific systems and contracts

| Source | Role | Application operation | Detailed contract |
|---|---|---|---|
| Fink / Rubin | alerts, detection IDs, sky position, timing, flux, authentic cutouts | `FinkOperation` | [Fink](docs/contracts/FINK.md) |
| ESA Gaia DR3 TAP | possible stellar counterparts and astrometry | `GaiaOperation` | [Gaia](docs/contracts/GAIA.md) |
| CDS SIMBAD TAP | published identities and object types near alert | `SimbadOperation` | [SIMBAD](docs/contracts/SIMBAD.md) |
| NASA IRSA AllWISE TAP | possible infrared counterparts | `IrsaOperation` | [IRSA](docs/contracts/IRSA.md) |
| OpenAI embeddings | semantic retrieval of prior saved reports | `ReportEmbedding` helper | [OpenAI](docs/contracts/OPENAI_EMBEDDINGS.md) |

Method/path/field index: [external endpoint index](docs/contracts/API_ENDPOINT_INDEX.md); machine-readable manifest: [external_endpoints.json](docs/contracts/external_endpoints.json). Apply documented crossmatch cautions from [CROSSMATCH.md](docs/contracts/CROSSMATCH.md); e.g. a potential host galaxy is not the transient itself.

## 5. Canonical assessments and source states

| Type | Values |
|---|---|
| Final assessment | `CATALOG_CONTEXT_FOUND`, `REVIEW_CANDIDATE`, `INCONCLUSIVE` |
| Catalog state | `NOT_REQUESTED`, `OK`, `EMPTY`, `ERROR` |
| Human review state | `NOT_REQUIRED`, `PENDING`, `ACCEPTED_FOR_REVIEW`, `REJECTED`, `TASK_ERROR` |
| Run scientific state | `ACCEPTED`, `RUNNING`, `COMPLETED`, `NO_ALERTS`, `FAILED` |

A successfully queried catalog with no matching rows is **`EMPTY`**; timeout, transport failure, invalid TAP/CSV/error payload is **`ERROR`**; a catalog never selected by BPL is **`NOT_REQUESTED`**. A `REVIEW_CANDIDATE` requires scientific uncertainty and supporting context described in the report, never an assertion of confirmed novelty.

## 6. HTTP API exposed by IRIS-hosted Flask WSGI

| Method | Route | Behavior |
|---|---|---|
| `POST` | `/api/discoveries/run` | `{tag,count}`; `count` 1–20, default 5 → `202 {runId,status}` |
| `GET` | `/api/discoveries/runs/{runId}` | Scientific run state, progress and saved report IDs (not a review completion gate) |
| `GET` | `/api/discoveries?limit=20&offset=0` | Newest saved reports, paginated; optional text/semantic `search` |
| `GET` | `/api/discoveries/{id}` | Complete saved report, catalog statuses, hypotheses/decisions, previous cases and trace ID |
| `GET` | `/api/discoveries/{id}/images/{kind}` | Stored `image/png` binary for `science|template|difference`, else appropriate missing response |

All paths in the table are Flask application-relative; with the configured IRIS mount `/gaia`, the browser calls `/gaia/api/discoveries/...`. The browser must respect the configured mount prefix rather than hardcode root-relative `/api`. Flask performs in-process IRIS operations and returns HTTP `202` without waiting for the BPL or human approval. The same WSGI application serves the two final UI views/static files after they are implemented.

UI never directly accesses Fink, Gaia, SIMBAD, IRSA or the OpenAI API. All source data are persisted first. Preserve 64-bit astronomy IDs as strings in all JSON.

## 7. Delivery constraints and acceptance

Implement **backend and proof first, UI last**. Configure `module.xml` during development, but **publish** the ZPM/IPM package and test clean installation only after the implementation including web assets exists. Use the locally authorized IRIS EAP image; never redistribute it.

Mandatory evidence of a functioning MVP:

1. An actual public alert with real stored Science/Template/Difference cutouts and source IDs.
2. Two real AI Hub decisions producing differing BPL routes and a changed hypothesis based on actual external catalog evidence.
3. Correct `OK`, `EMPTY`, `ERROR`, `NOT_REQUESTED` handling, crossmatch distances and source query provenance.
4. A saved `DiscoveryReport`, report/vector search, working Flask WSGI REST detail/images, and the matching IRIS Message Trace session.
5. A real native Workflow task created from the same BPL and completed through native Inbox, updating the saved report.
6. Java PEX proxy/adapter used by real TAP operations, Embedded Python executed in-process, Docker and ZPM/IPM installation demonstrated, authentic data shown in both UI views.
7. Deterministic failure handling for missing cutouts, absent/invalid AI output, empty Fink response, failed OpenAI embeddings, TAP/Java gateway failure and workflow dispatch failure.

**Potential contest bonuses:** Java PEX +3, Custom Adapter +2, Embedded Python +3, Vector Search +2, native Workflow Engine +2, Docker +2, published ZPM/IPM +2 = **16 possible** (never guaranteed). See [bonus evidence plan](docs/contest/BONUS_IMPLEMENTATION_PLAN.md).

## 8. Detailed authoritative documents

- [Implementation guide](docs/implementation/IMPLEMENTATION_GUIDE.md) · [Class map](docs/implementation/CLASS_MAP.md) · [Class contracts](docs/implementation/CLASS_CONTRACTS.md)
- [Workflow](docs/specification/WORKFLOW.md) · [Component models](docs/specification/COMPONENT_MODELS.md) · [Technology map](docs/specification/TECHNOLOGY_MAP.md) · [UI](docs/specification/UI_SPEC.md)
- [Native workflow detail](docs/specification/components/07_REPORT_REVIEW.md) · [Internal messages](docs/contracts/INTERNAL_MESSAGES.md) · [AI Hub decision schema](docs/contracts/AI_HUB_DECISION.schema.json)
- [Review and validation](docs/implementation/REVIEW_AND_VALIDATION.md) · [Source reference](agents/IA_HUB.agent.md)

**Implementation status:** documents and static contract checks only. Runtime support of EAP APIs, Flask WSGI hosting and application authentication, image endpoints, registered PEX proxy, Workflow Engine and published ZPM require actual verification. Do not present planned classes as compiled source.
