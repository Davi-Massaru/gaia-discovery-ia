# Contract — Flask REST via Native InterSystems IRIS WSGI

**Authority:** [SPEC.md](../../SPEC.md). **Status:** implementation contract, not compiled code. **Target:** authorized AI Hub EAP build 154; validate native WSGI, Flask package and `iris` module availability on this exact build. InterSystems documents WSGI hosting as an **experimental feature**.

## 1. Single web execution boundary

- **Python source:** `backend/app.py`; it exports exactly one Flask WSGI callable named `app` (`from flask import Flask; app = Flask(__name__)`). This is the REST entry point, not a second application server.
- **IRIS WSGI application:** web application mount `/gaia`, enabled as **WSGI**, dispatch class `%SYS.Python.WSGI`; application name `app` (Python module name without `.py`), callable name `app`, app directory = absolute deployed `backend/` directory, namespace = the application's IRIS namespace. These values must be registered through the supported build-verified web app setup (Management Portal for development; reproducible Docker/ZPM provisioning at install time).
- **Runtime access:** Flask executes in the IRIS-hosted Python environment and accesses the existing `Gaia.Interop.DiscoveryService`, `Gaia.Data.DiscoveryReport`, SQL and binary streams **in process**. Verify build-specific Embedded Python (`iris` module) class/message invocation and stream APIs against the installed classes; do not invent a vendor method name.
- **No other HTTP execution runtime:** no `Gaia.API.DiscoveryAPI.cls`, `%CSP.REST` router, separate Flask development server, Gunicorn, Uvicorn, API microservice, duplicated business logic or independent database. `flask` is the only added web dependency.
- **Authentication:** public astronomy endpoints do not require keys; this does **not** imply the app's IRIS WSGI endpoint is automatically public. Configure permitted IRIS web application authentication and authorization explicitly for the deployment, restrict write/run actions as appropriate, and never expose `OPENAI_API_KEY` or IRIS credentials in HTML/JSON. Do not assume `Unauthenticated` is enabled. Preserve same-origin requests; no extra CORS library needed.

## 2. Mount vs route paths

The IRIS web application is mounted at `/gaia`. These Flask routes are **application-relative**; external URLs include the mount prefix. Do not code browser `fetch('/api/...')` when hosted under `/gaia`.

| HTTP | Flask application route | Externally under IRIS `/gaia` | Contract |
|---|---|---|---|
| POST | `/api/discoveries/run` | `/gaia/api/discoveries/run` | `{tag,count}` with count 1–20 default 5; validate inputs; create/dispatch async run; return HTTP 202 `{runId,status:"ACCEPTED"}` promptly |
| GET | `/api/discoveries/runs/<runId>` | `/gaia/api/discoveries/runs/<runId>` | persisted scientific run state and saved report IDs, including `NO_ALERTS` |
| GET | `/api/discoveries` | `/gaia/api/discoveries` | newest-first bounded report list; `limit`, `offset`, optional `status`, `review_status` and saved-report semantic `search` |
| GET | `/api/discoveries/<id>` | `/gaia/api/discoveries/<id>` | stored report metadata, source status, hypothesis timeline, review state, InteropSessionId |
| GET | `/api/discoveries/<id>/images/<kind>` | `/gaia/api/discoveries/<id>/images/<kind>` | byte-exact PNG for `science`, `template`, `difference`; 404 when absent |

- Existing API request/response shapes from [internal messages](INTERNAL_MESSAGES.md) remain authoritative. JSON must serialize Fink 64-bit IDs **as strings**.
- The `POST /run` handler must **not** run the long BPL synchronously or await native Workflow task completion; use the adapterless `DiscoveryService` async path validated in the target IRIS build. HTTP 202 is acceptance, not scientific success.
- The final two-view UI is served within the **same WSGI app and mount**, from real `web/index.html`, `web/app.js`, `web/style.css` assets authored only in the UI phase. A small Flask static/index route can serve these files; no frontend framework or another server. Use mount-aware relative asset/API links (verify with actual IRIS Web Gateway routing).
- SQL/report/image reads are bounded and backed by saved IRIS state. Return explicit 400 (bad inputs), 404 (missing report/image/run), 503/appropriate 5xx (backend unavailable); do not invent a discovery or image to fill the page.

## 3. Registration and deployment checks

Configure through supported IRIS application creation / management facilities after verifying signatures in the installed build. This **conceptual configuration** is not a claim a script has been executed:

```text
IRIS Web Application Path  = /gaia
Type/Enable                = WSGI
DispatchClass              = %SYS.Python.WSGI
WSGIAppLocation            = <absolute deployment path>/backend
WSGIAppName                = app
WSGICallable               = app
Namespace                  = <actual configured application namespace>
Allowed authentication     = <explicit authorized deployment policy>
```

Acceptance in a real IRIS container:

1. Install Flask in IRIS Python and prove `import flask; import iris` from the application context; confirm WSGI feature exists on the EAP build.
2. Import `backend/app.py` and verify the `app` callable under the configured namespace; open `/gaia/api/discoveries` and check authorization/JSON behavior.
3. Start a real run: HTTP 202 arrives immediately with persisted `runId`; GET of run state advances independently of browser and human review.
4. Fetch one persisted report and byte-compare Science/Template/Difference PNG HTTP responses against IRIS streams. Invalid/missing IDs get proper 4xx.
5. Serve the final UI at the `/gaia` mount without broken absolute paths, CORS shortcuts or a separate server.
6. Recreate the web application on a clean Docker/ZPM install, including Python `flask` dependency and file placement. Document actual authentication and verify it.

## 4. Primary technical sources

- Official InterSystems WSGI documentation: https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=AWSGI
- InterSystems WSGI introduction with `%SYS.Python.WSGI` example: https://community.intersystems.com/post/wsgi-support-introduction
- IPM + WSGI provisioning example: https://pt.community.intersystems.com/post/rodando-aplica%C3%A7%C3%B5es-wsgi-com-ipm
