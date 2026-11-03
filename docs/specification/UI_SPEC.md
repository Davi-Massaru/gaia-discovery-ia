# Gaia Discovery AI — User Interface Specification

**Implementation order:** Build the UI **last**, after the backend Production, external API contracts, AI Hub routing, report persistence, Vector Search and native Workflow Engine are working and validated with real data. This document defines the final presentation only; it does not request implementation now.

**Scope:** exactly two web views in one small static HTML/CSS/JavaScript application. Backend is one Flask application hosted **inside InterSystems IRIS via native WSGI**, using in-process Embedded Python for request/data handling. Its REST backend is built and tested before the UI; only the HTML/CSS/JS views are built last. No SPA framework, front-end database, third screen, image-generation service, or duplicate human-review UI.

**Authority:** This document details the root [SPEC.md](../../SPEC.md). The [class map](../implementation/CLASS_MAP.md) defines the only target implementation class inventory.

## 1. Purpose and data authenticity

The web interface lets a user request recent Rubin/Fink observations and inspect **earlier saved investigations**. Every image and scientific conclusion displayed must originate from a saved `Gaia.Data.DiscoveryReport` record. **The observation image is received from Fink, not manually uploaded**; there is no separate image-upload feature in this MVP.

Never replace a missing scientific image with a generated space picture or an invented report. Show an explicit **Image unavailable** state, and display `NOT_REQUESTED`, `OK`, `EMPTY`, or `ERROR` for each scientific catalog. The AI Hub analyzes real alert metadata and catalog evidence; UI imagery is not proof of direct multimodal AI processing.

## 2. Visual identity

- **Product name:** Gaia Discovery AI. Descriptor: *Astronomical Investigation*. Tone: observatory/scientific instrument, readable and restrained, not a sci-fi videogame.
- **Theme:** dark navy `#0B1020` background; panel `#151D30`; elevated panel `#1D2940`; text `#EBF2FF`; secondary `#A3B3CD`; interactive cyan `#55D4EF`; active/AI emphasis `#7C93FF`; subtle dividers `#33425E`.
- **Identity mark:** minimalist concentric orbit + observation point rendered as an inline SVG/CSS glyph. Text wordmark "GAIA DISCOVERY AI". Do not require external image assets or a downloaded font.
- **Typography:** system sans-serif; tabular/monospace style only for source IDs, coordinates, timestamps, status codes and numeric measurements.
- **Visual hierarchy:** observation imagery first; then the agent's scientific conclusion; then traceable evidence. Use neutral surfaces and small semantic status labels. Do not communicate status through color alone.
- **Responsive:** desktop report uses a wide image area and a compact evidence rail; mobile stacks the same data vertically. Render small 30 × 30 cutouts with pixel-preserving zoom (`image-rendering: pixelated` when enlarged), not artificial detail enhancement.

## 3. View A — Discovery Feed / Previous Reports

**Top bar:** visual mark, product name, link to the report list, and visible IRIS-connected status when the REST API responds successfully.

**Controls:** select a supported Fink tag, choose **1, 5, 10 or 20** alerts (default **5**), and press **Fetch Latest**, optional text search for previously saved report summaries (existing IRIS Vector Search), and a Refresh action. Fetch Latest submits the application-relative `POST /api/discoveries/run` (mounted externally at `/gaia/api/discoveries/run`); it does not call observatory APIs from the browser. Report status is obtained by subsequent `GET` calls, not invented by the UI.

**Main element: previous report list, newest first.** Each row/card shows:

| Element | Source | Behavior |
|---|---|---|
| Thumbnail | `/api/discoveries/{id}/images/science` | Real saved Science cutout; explicit missing-image placeholder if absent |
| Report ID and Rubin `diaObjectId` | `DiscoveryReport` | IDs preserved as strings |
| Observation date and processing date | `ObservedMjdTai`, `CreatedAt` | Label which clock is shown; do not confuse observation time with processing time |
| Initial Fink tag | `Tag` | Scientific category of alert, not agent-confirmed identity |
| AI assessment | `Assessment` | `CATALOG_CONTEXT_FOUND`, `REVIEW_CANDIDATE`, or `INCONCLUSIVE` per decision schema |
| Human review | `ReviewStatus` | Not required / Pending / Accepted for further review / Rejected / Task error (do not fabricate completed tasks) |
| Open report | Report ID | Navigate to the Investigation Report view |

The list is loaded from IRIS, never hardcoded demo rows. Default to the latest 20 reports; allow bounded pagination using the same `GET /api/discoveries` route. Show Empty history, API unavailable and Loading states. Do not silently fabricate results to populate the page.

**Basic layout sketch:**

```text
┌───────────────────────────────────────────────────────────────────┐
│ ◉ GAIA DISCOVERY AI               Observatory Investigation       │
├───────────────────────────────────────────────────────────────────┤
│ Tag [extragalactic...] Count [5 v] [Fetch Latest]  [Search reports] [Refresh]  │
├───────────────────────────────────────────────────────────────────┤
│ PREVIOUS INVESTIGATIONS                                           │
│ [Science]  Report #042   Rubin object ID   Review candidate       │
│            Observation date · Fink tag · Review pending   [Open] │
│ [Science]  Report #041   Rubin object ID   Known                  │
│            Observation date · Fink tag · Review not needed [Open] │
└───────────────────────────────────────────────────────────────────┘
```

## 4. View B — Investigation Report

**Header:** report ID; `diaObjectId` / `diaSourceId` (strings); Fink category; observation time; assessment; review status; Back to Reports link.

**Image section:** show the **actual three images received** from the same Fink detection, clearly labeled:

1. **Science:** actual observed region (primary image).
2. **Template:** reference region.
3. **Difference:** the difference associated with the alert.

Use saved image URLs; allow enlarge/view-original display without inventing pixels. Provide the observatory name, `diaSourceId`, observation date and data provenance directly under the images. If one image is unavailable, label it and preserve the others. Do not claim an entire sky image is available: these are small scientific cutouts.

**AI Hub Report:** display the saved `Summary` and the structured evidence in `EvidenceJSON`:

- Initial hypothesis and alternative hypothesis.
- The selected scientific question and `next_action` for every AI Hub decision.
- Revisions after each actual catalog result; no invented steps.
- Final assessment with **supporting evidence**, **conflicting evidence**, and **unresolved uncertainty**, including the outcome when inconclusive.
- Native human Workflow review state (including `TASK_ERROR`) with a note that acceptance means *accepted for further scientific review*, not a confirmed discovery; no custom reviewer controls on this page.

**Consulted Scientific Sources:** a compact table built from the recorded BPL decisions and catalog response provenance:

| Source | Query status | Details to show when available |
|---|---|---|
| Fink / Rubin | Always source of alert | Object/detection ID, tag, observation time, image provenance |
| ESA Gaia | `OK / EMPTY / ERROR / NOT_REQUESTED` | `source_id`, position, separation, parallax, proper motion, magnitude, `ruwe` |
| SIMBAD | `OK / EMPTY / ERROR / NOT_REQUESTED` | `main_id`, object type, separation |
| NASA IRSA / AllWISE | `OK / EMPTY / ERROR / NOT_REQUESTED` | Designation, W1/W2, `ph_qual`, separation |

For each **executed** source, show endpoint identity, sanitized query parameters, execution status and retrieval timestamp. A source not requested by the AI Hub remains visible as **Not requested**, distinct from an empty or failed query. Never display credentials or raw secrets.

**Related Investigations:** up to three saved similar reports returned by IRIS Vector Search, linked to their report pages with short historical conclusions. Show similarity as a retrieval signal only — not scientific identity or AI confidence. Empty history is a valid state.

**Trace reference:** display `InteropSessionId` and, if a verified native IRIS trace URL can be constructed from the installed build, a link to that trace. Otherwise display the ID as copyable text with a short instruction to find the Production session in the IRIS Management Portal. No invented deep links.

**Layout sketch:**

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ Back to Reports      REPORT #042   REVIEW_CANDIDATE   Review: Pending  │
│ Rubin diaObjectId  |  Observation date  |  Fink alert tag             │
├─────────────────────────────────────────────────────────────────────────┤
│ [SCIENCE cutout]     [TEMPLATE cutout]     [DIFFERENCE cutout]         │
│ Observatory source · diaSourceId · Real saved image provenance         │
├──────────────────────────────────────┬──────────────────────────────────┤
│ AI HUB SCIENTIFIC REPORT             │ SOURCES CONSULTED                │
│ Main / alternate hypothesis          │ Fink    OK                       │
│ Supporting / conflicting evidence    │ SIMBAD  OK  ·  source ID         │
│ Revised hypothesis timeline          │ Gaia    NOT_REQUESTED            │
│ Final conclusion / uncertainties     │ IRSA    EMPTY                    │
├──────────────────────────────────────┴──────────────────────────────────┤
│ RELATED INVESTIGATIONS: previous report links + similarity             │
│ IRIS SESSION: <InteropSessionId>                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

## 5. Backend contract — no extra service

The UI uses only the established **Flask WSGI** routes (relative to the IRIS mount `/gaia`):

| Method | Route | Minimum data |
|---|---|---|
| `POST` | `/api/discoveries/run` | `{tag, count}` (count 1–20; default 5) → `{runId}` indicating accepted request |
| `GET` | `/api/discoveries?limit=20&offset=0` | newest reports with ID, image availability, dates, tags, assessment, review state |
| `GET` | `/api/discoveries?search=...` | existing optional semantic search of stored report texts |
| `GET` | `/api/discoveries/runs/{runId}` | accepted/running/completed/no-alerts/failed scientific run state and report IDs; no human-review gate |
| `GET` | `/api/discoveries/{id}` | report metadata, hypothesis/decision timeline, `EvidenceJSON`, source statuses, related reports, `InteropSessionId` |
| `GET` | `/api/discoveries/runs/{runId}` | Run state (`ACCEPTED`, `RUNNING`, `COMPLETED`, `NO_ALERTS`, `FAILED`) and any report IDs; backed by a minimal bounded IRIS run-status global, not a new persistent class |
| `GET` | `/api/discoveries/{id}/images/{kind}` | authentic stored PNG, `kind=science|template|difference`, with correct `image/png` content type |

The browser builds URLs under the IRIS WSGI application mount (`/gaia`), and must not hardcode root-relative `/api` routes. `backend/app.py` implements the API; only `web/index.html`, `web/app.js`, and `web/style.css` are deferred to the UI phase. No standalone Flask server.

The backend derives source-status entries from actual recorded decisions and results. The report list and report detail must not perform network calls to Gaia, SIMBAD, IRSA or Fink. All images and AI conclusions must already be persisted in IRIS. JSON serialization must preserve 64-bit astronomy identifiers as strings.

**No new database tables:** the single existing `DiscoveryReport` plus its `EvidenceJSON`, stream images, vector fields and review status is sufficient. UI-specific fields are response projections assembled by Embedded Python. No additional custom workflow UI or browser-side API keys.

## 6. Implementation gate — UI goes last

1. Confirm real Fink image triplet was downloaded and stored in IRIS.
2. Confirm AI Hub hypothesis/decision events and catalog results were persisted with correct `NOT_REQUESTED`, `EMPTY`, `ERROR` and `OK` statuses.
3. Verify native IRIS-hosted Flask WSGI registration, imports, authentication and report queries, history and image-serving routes with simple HTTP requests before writing UI code.
4. Prove Java PEX / Custom Adapter, Embedded Python, Vector Search, native Workflow Engine, and the adaptive BPL paths using real traces.
5. **Only now implement `web/index.html`, `web/app.js`, `web/style.css`** following the two views above.
6. Package those assets with ZPM, perform the final Docker/UI smoke test, then capture authentic UI and IRIS Message Trace screenshots for the README/demo.

### UI acceptance tests

- Feed lists prior reports in newest-first order and shows a Science image thumbnail, report assessment and human review status.
- Selecting a report shows the same real Science/Template/Difference cutouts saved in IRIS; direct image endpoint bytes match the UI display.
- The AI report displays initial/revised hypotheses, documented questions, final conclusion and uncertainties with no fabricated confidence percentages.
- Sources actually queried show status and evidence; unqueried sources explicitly show **Not requested**.
- Related reports are linked and correspond to actual IRIS Vector Search results; none can be present on an empty database.
- Production session ID is available and correlates to a real IRIS Message Trace.
- Layout remains readable on desktop and mobile. It handles empty/error/missing-image states without fabricated observation imagery.

**Implementation status:** design only. All source data, SDK functions and REST responses require runtime verification in the authorized AI Hub build 154.

## Final UI implementation prerequisite

Implement last, using the persisted outputs and REST component model in [components/08_REST_UI.md](components/08_REST_UI.md). The source-of-truth evidence and internal REST/message contracts are documented at [contracts/INTERNAL_MESSAGES.md](../contracts/INTERNAL_MESSAGES.md) and [contracts/API_ENDPOINT_INDEX.md](../contracts/API_ENDPOINT_INDEX.md). The UI must show real Fink image streams, actual consulted source names/statuses, AI hypothesis timeline and previous saved reports.
