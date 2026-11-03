# Component 09 — Docker, ZPM and Bonus Demonstration

**Purpose:** reproduce the complete application using an **authorized locally available** InterSystems IRIS AI Hub EAP build 154 image; deploy IRIS classes/Production/PEX JAR/web assets in a deterministic order.

## Build and deployment sequence

1. Docker Compose starts the licensed IRIS AI Hub EAP image; use existing local image tag/build and actual startup capabilities. `.env` is gitignored and contains `OPENAI_API_KEY`; do not require ESA/NASA/Fink API keys.
2. Build the single Java PEX custom outbound adapter JAR and configure IRIS Java external-language gateway (not an additional app microservice). Register adapter and verify generated proxy class before native BO compilation.
3. Compile IRIS native classes and Embedded Python methods, configure `%AI.Provider`/native agent after verifying build-154 signatures, and configure the one Production/BPL and native Workflow role/operation.
4. Install `flask` inside the supported IRIS Python environment and register **one native WSGI web application** (`%SYS.Python.WSGI`, module `app`, callable `app`, app directory `backend/`, mount `/gaia`, correct namespace and authentication). Ensure Docker and published ZPM package restore this configuration and `backend/app.py`, and do not start a separate Flask HTTP process. Confirm WSGI availability in target EAP build; documented as experimental. Configure report SQL fields and vector operations; run actual Fink/TAP contract checks; complete two real end-to-end workflow cases with distinct agent decisions.
5. Prepare and install ZPM package with IRIS source, `backend/app.py`, WSGI app configuration, Java PEX JAR/registration instructions and Python dependencies. **After the backend is proven**, build/add the two UI static files, publish final ZPM and test a fresh install.

## Bonus evidence checklist

| Technology | Technical evidence | Intended bonus |
|---|---|---:|
| Java PEX | adapter class, registered gateway/proxy, actual TAP call from BO | 3 |
| Custom Adapter | same custom outbound adapter used in Production | 2 |
| Embedded Python | in-process `[Language = python]` methods processing live evidence | 3 |
| IRIS Vector Search | stored vectors + `VECTOR_COSINE` query in IRIS | 2 |
| Workflow Engine | same BPL async `<call>` to native `AstronomyReviewer` `EnsLib.Workflow.Operation` + Workflow Role/Inbox, `<sync>` of `TaskResponse.%Action`, existing report update | 2 |
| Docker | running authorized container, registered WSGI application and reproducible startup | 2 |
| ZPM | published package installed into compatible clean environment, including Flask/WSGI registration | 2 |

**Total targeted:** 16 *potential* points, no points guaranteed. Community Idea remains optional and does not enter this package. Do not introduce Java business logic outside PEX, another DB, an Angular/Quarkus stack, new workers, MCP or RAG orchestration solely to seek points.

**Status:** architecture only; no native build 154 compile, adapter registration, endpoint POST execution or official bonus validation has been performed in this environment.
