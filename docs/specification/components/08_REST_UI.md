# Component 08 — IRIS-hosted Flask WSGI REST and Final UI

**Implementation timing:** build the WSGI REST backend during backend validation; implement the HTML/CSS/JS UI last.

**Purpose:** list saved investigation reports and present *the actual* Fink PNG cutouts, AI report, catalog provenance and Workflow review status. Browser is presentation only; it never queries public astronomy APIs directly.

## REST endpoints

| Method and route | Request | Output | Source |
|---|---|---|---|
| `POST /api/discoveries/run` | `{tag,count}` with count 1–20 | `202 {runId,status}` | submits to `DiscoveryService` |
| `GET /api/discoveries` | optional pagination / `search` | saved reports newest first | IRIS SQL, optional IRIS Vector Search |
| `GET /api/discoveries/{id}` | saved report ID | metadata, hypotheses, catalog states, previous cases, review and trace IDs | `DiscoveryReport` |
| `GET /api/discoveries/runs/{runId}` | returned `runId` | bounded run state and available report IDs (including `NO_ALERTS`) | IRIS run-status global |
| `GET /api/discoveries/{id}/images/{kind}` | `science|template|difference` | `image/png` actual persisted bytes, or 404 | IRIS binary streams |

**Backend:** one `backend/app.py` Flask application (`app`) hosted through a native IRIS WSGI web application (`%SYS.Python.WSGI`) mounted at `/gaia`. Paths in the table are Flask application-relative, externally `/gaia/api/...`. Use the in-process `iris` Python API to call the existing service and read IRIS SQL/streams. Do not create `Gaia.API.DiscoveryAPI.cls`, native `%CSP.REST` routes or a second web server. Validate WSGI support on EAP build 154, namespace, imports, authentication, path IDs, bounds, missing streams and secrets. [WSGI contract](../../contracts/WSGI_API.md).

## View 1 — Discovery Feed

- List previous reports with **real Science-image thumbnail**, `diaObjectId`, observed date, Fink tag, AI assessment and review status.
- Fetch Latest button, tag selector, refresh, optional historic semantic search.
- A running job shows status from persisted/backend state, not fabricated results.

## View 2 — Investigation Report

- Science / Template / Difference PNGs from **the same `diaSourceId`**, with clear provenance and image loading errors.
- AI Hub final report, initial/alternative/revised hypothesis and question/decision timeline.
- Per-source Gaia, SIMBAD, IRSA statuses: **consulted** vs `NOT_REQUESTED` vs `EMPTY` vs `ERROR`; endpoint, retrieval timestamp and angular separation for actual matches.
- Historical Vector Search results linked by report ID and labeled textual similarities.
- Saved native Workflow review status (`NOT_REQUIRED`, `PENDING`, `ACCEPTED_FOR_REVIEW`, `REJECTED`, `TASK_ERROR`), native Production `InteropSessionId` link when available; no reviewer actions in the UI.

**Visual identity:** `#0B1020` background, `#151D30` panels, `#55D4EF` accent, `#7C93FF` agent emphasis, light text. Orbit + observation point mark, system font. **Two views only; no frontend framework**. See [`UI_SPEC.md`](../UI_SPEC.md).

**Gate:** prove WSGI REST and report/image routes against persisted IRIS records before authoring UI assets; build the two-view frontend only after Fink → AI Hub → selected TAP → report persistence → Workflow/Vector backend tests have passed. Final UI fields must come from saved IRIS content, not synthetic astronomy images.
