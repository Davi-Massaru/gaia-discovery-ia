# Gaia Discovery AI — Review and Validation Log

## 2026-11-03 — Real DiscoveryAgent interoperability validation

Real authenticated HTTP → BusinessService → BPL → `AIHubOperation` → `Gaia.AI.DiscoveryAgent` completed two investigations, run `62c736ab-9e6e-4724-8bb0-702ff793b0d9`, reports 33/34, native interoperability session 221. Eight real agent requests/replies and schema-valid decisions routed six successful catalog queries, without fixtures. Both executions were technically OK and scientifically INCONCLUSIVE. Six authentic PNGs matched persisted streams byte for byte; semantic HTTP returned 200; a separate real 1536-dimensional embedding passed native vector SQL. Human review was not triggered. Evidence and limits: [real validation report](REAL_AGENT_INTEROP_VALIDATION.md).

## 2026-11-03 — Gaia/SIMBAD transport verification

The user's exact cone queries were reproduced through native Java PEX. Before correction, Gaia timed out (32,985 ms) and SIMBAD timed out (15,048 ms); independent Python POST controls also failed. DNS resolved both hosts to IPv4; TCP connected to Gaia but timed out to Strasbourg. The official CfA/Harvard SIMBAD mirror accepted the same ADQL with HTTP 200 and valid zero-row CSV. Standard Gaia GET likewise returned HTTP 200. ESA's own Archive page warns about intermittent instability/timeouts during DR4 preparation.

The same Java adapter now uses GET for bounded Gaia queries with a 45-second budget, and at most two attempts; SIMBAD can fail over to its official Harvard mirror. Primary SIMBAD gets a 10-second attempt budget, capped to a 5-second connect timeout, so time remains for the mirror. TLS peer/hostname validation stays enabled. Python preserves the actual allowlisted endpoint and sanitized attempt metadata; failed catalog counts are displayed as unknown. Native Operation results (Service → GaiaOperation/SimbadOperation → registered Java PEX) finally returned HTTP 200 / EMPTY for both exact queries. One intervening Gaia repeat still timed out after about 46 seconds: external instability is not claimed resolved. Existing stored reports preserve their historical evidence.

31 tests, Java compilation and structural audit passed. Image and native package were rebuilt. Evidence: `dist/tap-diagnosis-before.json`, `dist/tap-diagnosis.json`, `dist/tap-http-controls.json`, `dist/tap-operations.json`. Official context: [ESA Archive service notice](https://gea.esac.esa.int/archive/) and [SIMBAD official mirror](https://simbad.cfa.harvard.edu/simbad/).

## 2026-11-03 — Report status filters and embedding eligibility

INCONCLUSIVE reports now skip embedding generation and are excluded from historical/semantic retrieval even if an older vector exists. Ordinary listing and report details preserve them. The feed has independent scientific status and human review status filters; the API validates both and filters before pagination/ranking. Thirty unit tests and eight isolated native BPL scenarios passed, including exclusion of a deliberately indexed inconclusive fixture. Twenty-four authenticated HTTP filter combinations matched real native SQL data; pagination, invalid status 400 responses and semantic exclusions passed. Authenticated Chrome selected REVIEW_CANDIDATE + ACCEPTED_FOR_REVIEW and displayed only matching reports 30 and 31, without console errors. Evidence: `dist/report-filters.json` and `dist/report-status-filters.jpg`.

## 2026-11-03 — Native AI diagnosis and final real-data verification

This section supersedes the earlier runtime snapshot below. The key was present in `.env`, matched the container environment and matched the native operation's key getter. EAP 154 / namespace USER and installed Provider.Create, Agent.CreateSession, Agent.Chat and exception DisplayString signatures were verified. Session 35 contains two AIHubOperation ERROR responses whose original exception details had been discarded. Separate real SDK/embedding invocations reproduced the provider's spend-limit refusal. During this validation, native LLM and embedding requests began succeeding; an earlier quota failure is not evidence of a current permanent outage.

Corrected defects: native AI exceptions now preserve allowlisted failure codes and stages instead of only `AI_HUB_ERROR`; optional history/index failures are recorded separately from scientific assessment; empty indexed history returns an empty result before making an embedding request. A schema-valid model proposal can no longer turn failed catalog requests into absence/novelty evidence: final assessment stays INCONCLUSIVE and the original proposal remains in the decision timeline. Existing historical reports were not rewritten.

Actual final results:

- 27 unit/contract tests passed; eight isolated native BPL scenarios and stored-vector SQL passed, with external fixtures explicitly confined to the test container.
- Real reports 30 and 31, session 154, each contain four schema-valid native model decisions covering CHECK_GAIA, CHECK_SIMBAD, CHECK_IRSA and FINISH. These precede the final catalog-failure assessment guard.
- Final report 32, session 192, exercises that guard using four real native model decisions. Three authentic 30×30 PNGs match their stored streams byte for byte. IRSA returned one positional candidate; Gaia/SIMBAD transport failures remain errors. The report is INCONCLUSIVE with separate DEGRADED execution and catalog failure codes.
- Report 32 history search and embedding persistence succeeded; semantic REST search returned 200. An independent real OpenAI vector had 1536 dimensions and matched the stored real report 30 vector with similarity 0.999999. Stored-vector self-similarity was 1.0. No fixture embedding was inserted into the real-data database.
- A clean native database without reports or provider credentials returned `[]` for history search without mocks.
- Authenticated Chrome navigation through feed/detail succeeded. Report 32 displayed all three loaded authentic images, four decisions, source evidence, technical status and session correlation. Browser control later stopped because it could not verify the active Windows URL; final screenshot capture could not be completed. Earlier desktop visual screenshots are historical artifacts.
- Updated image built and Compose started with the standard healthcheck; final health was `healthy` with native state `warn`. Earlier runtime startup became alert/unhealthy: native System monitor reported the vendor startup error `<METHOD DOES NOT EXIST>Sharding+2^STU *Sharding,SYS.ICM`. A stable hostname prevents node-change alerts but does not fix this separate EAP defect. No monitor suppression or vendor-code patch was applied.

Changed application files: `backend/gaia/diagnostics.py`, `backend/gaia/embedding.py`, `backend/gaia/runtime.py`, `backend/gaia/store.py`, `src/iris/Gaia/Interop/Operations/AIHubOperation.cls`, `web/app.js`. Validation changes: `tests/test_contracts.py`, `tests/e2e/empty_history.py`, `scripts/diagnose_ai.py`, `scripts/probe_ai.py`, `scripts/validate_real_e2e.py`, `scripts/validate_vectors.py`, this log and README. Current machine-readable evidence is in `dist/e2e-real.json`, `dist/e2e-real-native-routing.json`, `dist/vector-real.json`, `dist/ai-runtime-diagnosis.json` and `dist/validation-summary.json`. Publication remains manual.

## 2026-11-03 — Runtime end-to-end review

The earlier documentation review below is historical. Current executable evidence is recorded in `dist/e2e-real.json`, `dist/e2e-isolated.json`, `dist/inbox-e2e.json` and `dist/ai-probe.json` in the development workspace.

| Scope | Actual result |
|---|---|
| Unit/contract/REST tests | 21 passed, including invalid Fink IDs, PNG chunk/checksum integrity, complete JSON context bounds and failure paths |
| Real HTTP → Service → BPL → Fink → report → HTTP images | Two new real reports saved as INCONCLUSIVE, three byte-exact authentic PNGs per report, native session correlation, scientific run completed |
| Real native AI Hub and OpenAI embeddings | Both blocked by the organization's enforced spend limit; no successful scientific AI decision or real embedding is claimed |
| Real Java PEX TAP | Gaia EMPTY, IRSA OK with one positional candidate; SIMBAD transport timeout/refusal remains ERROR |
| Isolated full native BPL | Eight scenarios passed with explicitly mocked external-source responses in a disposable container; three distinct catalog routes, four decisions, finish without queries, invalid output, missing cutouts, no alerts, failed catalog, batch review and dispatch failure |
| Native Workflow batch | Two distinct async call names; ACCEPT and REJECT returned through native sync and updated the correct pre-saved reports, after scientific completion |
| Native Inbox browser interaction | Actual claim + ACCEPT and claim + REJECT in the native User Portal; the same BPL updated fixture reports 36 and 45 in sessions 350 and 435 |
| Stored-report Vector Search | Actual 1536-dimensional SQL persistence and top-three retrieval passed with controlled test embeddings; not a real embedding-provider success |
| Web UI | Authenticated HTTP assets/detail/images passed; visual Gaia browser navigation remains unverified because the automation surface cannot complete HTTP Basic authentication safely |
| Publication | Intentionally manual, per user instruction; not an implementation blocker |
| Compose health | Native monitor identified a node-change alert after container recreation with durable storage. A controlled restart cleared the alert; Compose now defines a stable hostname. Final Docker health is `healthy`, with native monitor `warn` from EAP startup messages. The standard healthcheck remains enabled. |

Corrected implementation defects:

- Repeated native async call names allowed a batch process to finish after its first review response and discard later replies. Calls now use native `@context.ReviewCall` indirection and native sync waits for `@context.ReviewCalls`.
- Workflow response properties are read in thin ObjectScript glue before entering Embedded Python; owned Python strings avoid EAP native-buffer reuse problems.
- The native User Portal required an enabled native web application and `%DeepSee_Portal:U`. Configuration now enables its password-protected Inbox and defines the narrowly scoped `GaiaWorkflowUser` security role; it does not grant anonymous access or administrator roles.
- Invalid/missing Fink detection IDs, corrupt/truncated PNGs and oversized JSON contexts are rejected explicitly.
- Invalid AI-operation discriminators are rejected before provider invocation; browser error handling distinguishes a missing resource from a backend outage.
- Compose now keeps a stable `gaia-iris` hostname across container recreation while preserving its durable volume.

All fixture data, mock decisions and test-only native Operations are confined to the disposable `gaia-e2e-tests` container. They are not evidence of actual scientific observations or successful real-model decisions. The real-data container contains only actual Fink-derived reports. No change to OpenAI spending limits or public publication was attempted.

**Review date:** 2026-11-02  
**Reviewed input:** the latest conversation-delivered Gaia Discovery AI specification package and user-provided `IA_HUB.agent(9).md`.  
**Status:** documentation-level review complete. No IRIS build-154 compilation, live Fink→TAP execution, native Workflow task or Java gateway test is claimed.

## Corrections made in this reviewed package

| Finding | Correction | Evidence to check later |
|---|---|---|
| Inconsistent AI assessment term (`KNOWN` in UI vs `CATALOG_CONTEXT_FOUND` in schema) | Unified to schema's `CATALOG_CONTEXT_FOUND`, `REVIEW_CANDIDATE`, `INCONCLUSIVE` | Agent JSON validation and UI rendering |
| Image property names differed between SPEC and report model | Standardized on `SciencePNG`, `TemplatePNG`, `DifferencePNG` | Compile schema; save/retrieve 3 real PNG streams |
| Bonus plan suggested UI in an early delivery gate | Clarified that the UI is implemented **last**, after Production/REST/tests | Backend acceptance before web UI |
| Multiple copies of the lengthy Python First policy | Kept full policy in `SPEC.md`; secondary files link to it | Traceability of language responsibilities |
| Internal logical message names could be mistaken for additional `.cls` files | One typed `DiscoveryRequest` + one `DiscoveryResponse` envelope; other names are logical variants | Production message serialization |
| Asynchronous POST had no run-status query, especially for zero-alert runs | Added minimal `GET /api/discoveries/runs/{runId}` contract, backed by a bounded IRIS status global (no extra persistent domain class) | Accepted → Running → Completed/No Alerts/Failed |
| Workflow Engine was underspecified and tempted separate callback/services | Made [Component 07](../specification/components/07_REPORT_REVIEW.md) canonical: **existing BPL** async `<call>` native `TaskRequest` → one native `AstronomyReviewer` operation/role/inbox → `<sync>` native `TaskResponse.%Action`, same-report update | Prove real PENDING → ACCEPTED_FOR_REVIEW / REJECTED, and TASK_ERROR on send failure |
| Source reference for AI Hub was missing from the previous archive | Included original user-supplied file under `agents/` | Verify build-154 SDK using installed class definitions |
| SPEC had duplicate section 9 | Renumbered final component-model section | Navigation and documentation integrity |

## Source-backed external contract checks

- **Fink tags:** `GET /api/v1/tags` and `POST /api/v1/tags` (`tag`, `n`, `columns`) are documented. [Official tag-search docs](https://doc.lsst.fink-broker.org/services/api/tagsearch/).
- **Fink source IDs:** `POST /api/v1/sources` receives `diaObjectId` and returns `diaSourceId`/observation fields. [Official source-search docs](https://doc.lsst.fink-broker.org/services/api/diaobjectid/).
- **Fink images:** `POST /api/v1/cutouts` uses **diaSourceId**, `kind=Science|Template|Difference`; omit `output-format` for **PNG**. `kind=All` with `output-format=array` is a separate numeric-array contract, not the three-PNG endpoint. [Official image docs](https://doc.lsst.fink-broker.org/services/api/imagesearch/).
- **Fink schema:** `POST /api/v1/schema` with `{ "endpoint": "/api/v1/sources" }` is documented. Verify field availability from this endpoint at runtime. [Official schema docs](https://doc.lsst.fink-broker.org/services/api/definitions/).
- **Gaia, SIMBAD, NASA IRSA:** bounded TAP/ADQL `sync` queries use a catalog-specific query and return catalog fields that can be spatially correlated by RA/Dec. Each catalog is **historical scientific context** and a positionally close source is not automatically the alert's physical identity. See the contracts and linked archive documentation.
- **Java PEX adapter:** InterSystems documents Java `com.intersystems.enslib.pex.OutboundAdapter`, registration, and use from a native Business Operation. [Official PEX documentation](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EPEX_outbound). Actual proxy API needs verification on EAP build 154.
- **Bonus eligibility:** the contest specifies seven selected bonuses totaling **16 potential points**; actual use and a **published/installable** ZPM package are necessary, not documentation alone. [Official bonus rules](https://community.intersystems.com/post/technology-bonuses-intersystems-programming-contest-ai-agents-interoperability-workflows).

## Remaining mandatory runtime checks

1. Verify `EAP build 154`, namespaced `%AI.Agent` APIs and Provider/session methods by inspecting the installed runtime. `VERSION NOT CONFIRMED` by these documents alone.
2. Execute `scripts/verify_contracts.py` on an internet-enabled machine and save actual HTTP status, content type, schema fields and representative **non-fabricated** responses. No such responses are packaged here.
3. Compile a native Business Operation method using `Language = python` and prove that Fink JSON, TAP CSV and report persistence are genuinely handled **inside IRIS**.
4. Compile/register the single Java PEX outbound adapter and prove a real Gaia/SIMBAD/IRSA transport call through it; verify generated class names/signatures, Java gateway and runtime logging.
5. Verify native BPL `switch` + bounded loop + AI Hub output schema: two real alerts take different routes; errors never become false `EMPTY` values.
6. Verify `VECTOR(FLOAT,1536)`, `TO_VECTOR` and `VECTOR_COSINE` in the installed IRIS runtime using embeddings of real saved reports; historical retrieval must be explicitly labeled analogy.
7. Configure `AstronomyReviewer` as one **native `EnsLib.Workflow.Operation`** (matching Workflow Role, `AutoCreateRole=1`, authorized user assigned). Compile the **same** `DiscoveryWorkflow` BPL with async `<call>` native `EnsLib.Workflow.TaskRequest` (`%Actions="ACCEPT,REJECT"`) and `<sync>` native `EnsLib.Workflow.TaskResponse.%Action`. Verify real `PENDING → ACCEPTED_FOR_REVIEW` and `PENDING → REJECTED` updates on existing reports; `POST /run` returns before the reviewer acts. Confirm class/property syntax against installed build 154.
8. Register and test the **Flask WSGI callable** (`backend/app.py`, IRIS WSGI web application mounted at `/gaia`) including authenticated access, no Flask development server, `202` async behavior, report/image routes and correct namespace. Verify the report's actual images, original source IDs, query metadata, AI hypothesis history, selected/unused catalogs and native interoperability session ID from the REST API.
9. Implement the **two UI views last**, using only persisted IRIS data. Capture screenshots and Visual Trace from the real running application.
10. Publish the ZPM package and test clean installation of classes, Flask/WSGI callable/configuration/assets, the Java PEX artifact/proxy, and runtime configuration in a compatible authorized Docker EAP image before claiming the ZPM bonus.

## Scientific and compatibility boundaries

The input is the **Fink-detected alert source**, not an arbitrarily uploaded full-sky photograph. The MVP does not solve all objects visible in the cutout, perform general image-based object recognition, or assert a scientific discovery. Human `ACCEPT` means accepted **for further review**. A blank catalog result does not prove an unknown object. EAP SDK APIs, class definitions, registration and generated proxy methods are not treated as compiled merely because an example exists online.

## Structural audit

Run `python scripts/audit_package.py`. The script checks relative Markdown links, JSON parsing, the AI decision schema structure, the endpoint allowlist, key doc markers and Python syntax. It does **not** contact external services or certify build-154 behavior.

## 2026-11-03 — Documentation and class-boundary refactor

- Preserved all existing nine component models, thirteen external/internal contract documents, and supplied AI Hub agent reference; relocated into `docs/specification`, `docs/contracts`, `docs/implementation`, `docs/contest` with `SPEC.md` at repository root.
- Introduced [CLASS_MAP.md](CLASS_MAP.md) and [CLASS_CONTRACTS.md](CLASS_CONTRACTS.md) to keep actual `.cls` source targets and their semantic interfaces in one place. Removed the unverified extra agent wrapper `.cls` from the canonical target tree; native `%AI.Agent` remains SDK configured.
- Configurable fetch batch: 1–20, default 5, sequential. Per-alert 3 distinct TAP checks/4 AI decisions unchanged.
- Native Workflow Engine remains `EnsLib.Workflow.Operation`, TaskRequest/TaskResponse, one role and same BPL async `<call>` + `<sync>`, without custom approval classes.
- `.env` is not included. Added `.env.example` and `.gitignore`.
- **Static verification only:** no `.cls`, Docker image, PEX gateway, ZPM publication or HTTP endpoints claimed as live. Run the installation/runtime test matrix before assigning any bonus points.

## 2026-11-03 — Restore native IRIS WSGI + Flask HTTP boundary

- Corrected an unintended refactor regression: native `%CSP.REST`/`Gaia.API.DiscoveryAPI.cls` replaced the previously selected Flask application hosted by **IRIS WSGI**. The canonical design is now `backend/app.py` with Flask callable `app` registered to native `%SYS.Python.WSGI` at mount `/gaia`.
- Restored Flask WSGI throughout the root SPEC, class map/contracts, ingress/REST component model, workflow, UI, technology map, build/deployment guide, and ZPM acceptance checklist. No standalone Flask, ASGI worker, alternative HTTP server or parallel REST wrapper.
- Reduced target application `.cls` class count from 13 to **12**; added one Python WSGI file (`backend/app.py`). This does not remove any Interoperability, AI Hub, Vector Search, PEX or native Workflow component.
- Required runtime test: IRIS EAP build 154 can import Flask, register the WSGI application with correct authentication/namespace, dispatch `POST /gaia/api/discoveries/run` asynchronously, serve binary PNGs and preserve UI links under the mount prefix.
- Documentation-only correction: native WSGI is marked **experimental** in official InterSystems materials. Actual availability in contest EAP build and ZPM clean-install provisioning remain unverified.

## 2026-11-03 — DiscoveryAgent extraction

`Gaia.AI.DiscoveryAgent Extends %AI.Agent` now owns the existing provider/model/instruction configuration. `AIHubOperation` composes it and preserves its message, session, validation and failure contracts. Embedded Python domain/embedding implementations and existing ClassMethod entry points are preserved. See [migration model](DISCOVERY_AGENT_MIGRATION.md) and [class map](CLASS_MAP.md).

Validation on IRIS 2026.3.0AI build 154U: all 14 source classes and generated BPL classes compiled; 31 Python tests passed; native regression confirmed configuration equivalence, catalog/FINISH decisions, invalid output, provider/chat failures, request discrimination and environment compatibility. Eight isolated BPL/Workflow scenarios and persisted-vector SQL passed after full source compilation. Static audit of 40 required files and `git diff --check` passed. Sources/LLM responses were simulated in the disposable integration container; no paid model calls were made. New agent and Operation were compiled in the development container; the existing Compose container was not rebuilt.
