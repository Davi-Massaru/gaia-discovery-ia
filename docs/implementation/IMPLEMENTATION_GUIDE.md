# Gaia Discovery AI — Implementation Guide (Python First)

**Authority:** [SPEC.md](../../SPEC.md). **Exact class list:** [CLASS_MAP.md](CLASS_MAP.md). **Input/output contracts:** [CLASS_CONTRACTS.md](CLASS_CONTRACTS.md). **Status:** design, not compiled source. Prefer the referenced per-component document; do not generate more classes than the map.

## Implementation rules

- **Embedded Python** implements scientific and application logic inside IRIS: Fink/TAP validation, ADQL, normalization, angular distance, JSON, AI context/decision schema checks, report writes and Vector Search integration wherever the installed runtime supports.
- **ObjectScript** remains a thin native layer for `Ens.*` Business Hosts, BPL, messages, persistent schema and build-verified AI Hub SDK integration. Flask WSGI, hosted natively by IRIS, owns HTTP routes; no native `%CSP.REST` dispatch class.
- **Java** is limited to `TapOutboundAdapter` extending the supported PEX outbound adapter class, for allowlisted TAP HTTPS transport. One registered proxy is shared by all three TAP BOs.
- Do not create an extra custom Agent `.cls`, Workflow Operation subclass, separate Workflow BPL, reviewer API/UI, per-source custom adapter, independent history store, queue/microservice or future architecture.
- Validate actual method signatures/classes installed in AI Hub EAP build 154 before writing vendor-facing code. Prototype/sample pseudocode is **not proof of compilation**.

## Phase 0 — Validate environment and external contracts

1. Confirm the locally authorized IRIS EAP image, interoperability-enabled namespace and native `%AI.Agent`/`%AI.Provider` SDK API. Never redistribute EAP image.
2. Validate public REST/TAP contracts: [Fink](../contracts/FINK.md), [Gaia](../contracts/GAIA.md), [SIMBAD](../contracts/SIMBAD.md), [IRSA](../contracts/IRSA.md). Run `python scripts/verify_contracts.py` where network access permits; distinguish failed tests from verified calls.
3. Inspect PEX Java SDK registration, gateway, proxy naming, native adapter `ADAPTER` parameter. Verify IRIS SQL vector support and native Workflow TaskRequest/TaskResponse properties in installed build.
4. Verify the installed EAP build supports native IRIS **WSGI (experimental)** and can import `flask` and `iris` in-process; configure a WSGI application mount `/gaia` with Python module `app`, callable `app`, directory containing `backend/app.py`, namespace and explicit auth settings. No separate Flask server. See [WSGI contract](../contracts/WSGI_API.md). Keep `OPENAI_API_KEY` in user-managed, gitignored `.env`; do not require credentials for public astronomical sources.

## Phase 1 — Functional interoperability foundation

5. Implement `DiscoveryRequest`/`DiscoveryResponse` (two message classes only) and `DiscoveryService` (one adapterless Business Service), with bounded payloads and a `runId`.
6. Implement `FinkOperation` through the standard outbound HTTP adapter, parse real detections and stream actual `Science|Template|Difference` PNGs from the same `diaSourceId`; strings for 64-bit IDs. A run with zero alerts returns `NO_ALERTS` without fake reports.
7. Implement one registered Java PEX TAP outbound adapter, gateway/proxy and three distinct catalog Operations; Python builds safe bounded ADQL, decodes CSV and computes source separation. No direct TAP HTTP bypass around the adapter in final tests.
8. Implement native AI Hub agent configuration and one `AIHubOperation`, produce schema-validated decisions. Implement `DiscoveryWorkflow` **one BPL** with actual `switch` branches and no unconditional all-catalog execution. Max 3 distinct catalog calls, 4 AI decisions per investigated object.

## Phase 2 — Persistence and optional history

9. Implement the sole `%Persistent` `DiscoveryReport` with real image streams, EvidenceJSON, decisions, source statuses, `InteropSessionId` and `ReviewStatus`.
10. Implement `ReportEmbedding` and `VECTOR(FLOAT,1536)` historical search over **saved reports**; retrieve up to 3 before agent decision and index final summaries after report save. Failed embedding is nonblocking.
11. Implement a bounded run-status store (IRIS global with cleanup), independent of report review, with states `ACCEPTED|RUNNING|COMPLETED|NO_ALERTS|FAILED`. Configurable fetch `count` range 1–20, default 5, process sequentially.

## Phase 3 — Native minimal Workflow Engine (same BPL)

12. Add native `EnsLib.Workflow.Operation` named `AstronomyReviewer`, enable `AutoCreateRole` if appropriate and explicitly assign an authorized reviewer user. Use native Workflow Inbox.
13. After saving a candidate report, store `ReviewStatus=PENDING`; in the same BPL send async `EnsLib.Workflow.TaskRequest` with `%Subject`, `%Message`, `%Actions="ACCEPT,REJECT"`. For noncandidates use `NOT_REQUIRED`. Dispatch error uses `TASK_ERROR`.
14. Once scientific work is persisted, do native BPL `<sync>` for outstanding tasks and map actual `EnsLib.Workflow.TaskResponse.%Action` (`ACCEPT` / `REJECT`) to `ACCEPTED_FOR_REVIEW` / `REJECTED` on the **existing** report. The REST `202` response already returned and must not wait for the human. Verify native BPL properties/behavior in target build. No callback service or new class.

## Phase 4 — Native IRIS WSGI / Flask REST proof, UI last

15. Implement **`backend/app.py` Flask** and register it via IRIS WSGI at `/gaia` (`WSGIAppName=app`, `WSGICallable=app`, `WSGIAppLocation` = deployed backend directory, `DispatchClass=%SYS.Python.WSGI` when configured programmatically). Use in-process IRIS API access, no `%CSP.REST` wrapper and no standalone Flask process. Test `POST /api/discoveries/run`; `GET /api/discoveries/runs/{runId}`; `GET /api/discoveries`; `GET /api/discoveries/{id}`; `GET /api/discoveries/{id}/images/{kind}`. Use persisted data only. Validate output states, image bytes, auth/key hygiene and `runId` correlation.
16. Capture real Interoperability Message Traces for at least two different AI decision routes, a changed hypothesis, correct catalog statuses and one native Workflow task acceptance/rejection. Verify Java PEX usage, Embedded Python and Vector Search through actual runtime tests.
17. **Implement UI only now:** [Discovery Feed + Investigation Report](../specification/UI_SPEC.md), plain HTML/CSS/JS, showing real images and evidence, not sample observations. Final layout must work on mobile and desktop.
18. Prepare `module.xml` during development, but **publish** ZPM/IPM only after the runtime including the UI works. Test `zpm "install gaia-discovery-ai"` in a fresh compatible environment and document external prerequisites (EAP image and local provider key). Capture screenshot evidence.

## Component references by development phase

| Phase | Read only when active |
|---|---|
| Ingestion | [01](../specification/components/01_INGESTION.md), [Fink](../contracts/FINK.md) |
| BPL, AI Hub | [02](../specification/components/02_DISCOVERY_BPL.md), [03](../specification/components/03_AI_HUB.md), [AI schema](../contracts/AI_HUB_DECISION.schema.json) |
| TAP, science | [04](../specification/components/04_CATALOGS_PEX.md), [05](../specification/components/05_SCIENTIFIC_NORMALIZATION.md), [PEX](../contracts/JAVA_PEX_TAP_ADAPTER.md) |
| Vector | [06](../specification/components/06_VECTOR_HISTORY.md), [Vector](../contracts/VECTOR_HISTORY.md) |
| Report / Workflow | [07](../specification/components/07_REPORT_REVIEW.md), [Internal messages](../contracts/INTERNAL_MESSAGES.md) |
| REST + UI | [08](../specification/components/08_REST_UI.md), [UI](../specification/UI_SPEC.md) |
| Deploy | [09](../specification/components/09_DEPLOYMENT.md), [Bonus plan](../contest/BONUS_IMPLEMENTATION_PLAN.md) |

## Definition of done / truthfulness

Run `python scripts/audit_package.py` for the **offline document check**, and execute the official API/SDK/BPL/PEX/Workflow/SQL/UI/ZPM tests with actual data before claiming runtime features or bonuses. Do not treat a screenshot mockup or valid JSON schema as an integrated test. See [validation notes](REVIEW_AND_VALIDATION.md).
