# Gaia Discovery AI — Authoritative Class and File Map

**Source of truth:** [master SPEC](../../SPEC.md). This map is a **target implementation design**. The documentation-only archive intentionally does not create fake `.cls`/Java source files, stubs with invented SDK methods, or a pretend working Production.

## Exactly one domain report; one Production; one BPL

| Class / configuration | Target source path | Role and technology |
|---|---|---|
| `Gaia.Interop.DiscoveryService` | `src/iris/Gaia/Interop/DiscoveryService.cls` | Adapterless `Ens.BusinessService`; accept/run ID, async BPL dispatch |
| `Gaia.Interop.DiscoveryWorkflow` | `src/iris/Gaia/Interop/DiscoveryWorkflow.cls` | Single `Ens.BusinessProcess.BPL` for every scientific decision **and native human task sync** |
| `Gaia.Interop.Messages.DiscoveryRequest` | `src/iris/Gaia/Interop/Messages/DiscoveryRequest.cls` | `Ens.Request`; typed bounded app input envelope |
| `Gaia.Interop.Messages.DiscoveryResponse` | `src/iris/Gaia/Interop/Messages/DiscoveryResponse.cls` | `Ens.Response`; typed bounded app response envelope |
| `Gaia.Interop.Operations.FinkOperation` | `src/iris/Gaia/Interop/Operations/FinkOperation.cls` | Standard IRIS outbound HTTP adapter; Python payload/PNG processing |
| `Gaia.Interop.Operations.AIHubOperation` | `src/iris/Gaia/Interop/Operations/AIHubOperation.cls` | Native `%AI.Agent` SDK bridge and Python decision validation |
| `Gaia.Interop.Operations.GaiaOperation` | `src/iris/Gaia/Interop/Operations/GaiaOperation.cls` | Gaia DR3 ADQL and normalization in Python; custom Java PEX TAP adapter |
| `Gaia.Interop.Operations.SimbadOperation` | `src/iris/Gaia/Interop/Operations/SimbadOperation.cls` | SIMBAD ADQL/normalization in Python; same PEX adapter |
| `Gaia.Interop.Operations.IrsaOperation` | `src/iris/Gaia/Interop/Operations/IrsaOperation.cls` | IRSA AllWISE ADQL/normalization in Python; same PEX adapter |
| `Gaia.Science.AngularSeparation` | `src/iris/Gaia/Science/AngularSeparation.cls` | Deterministic Embedded Python astronomy math |
| `Gaia.Science.ReportEmbedding` | `src/iris/Gaia/Science/ReportEmbedding.cls` | Embedded Python OpenAI embedding, IRIS SQL Vector Search integration |
| `Gaia.Data.DiscoveryReport` | `src/iris/Gaia/Data/DiscoveryReport.cls` | Sole `%Persistent` report record: images, evidence, source metadata, vector, review |

**This leaves 12 planned application `.cls` classes.** HTTP route definitions are Python functions in `backend/app.py`, not IRIS `.cls` classes.

**Other runtime components that are NOT new application `.cls` classes:**

- One native `%AI.Agent` instance configured using the **actual installed SDK**, called `GaiaDiscoveryAgent`. No additional `Gaia.AI.DiscoveryAgent.cls` wrapper unless a verified build API explicitly requires it.
- One native `EnsLib.Workflow.Operation`, **Production configuration name** `AstronomyReviewer`, with native Workflow Role of the same name, native TaskRequest/TaskResponse and built-in Inbox. No subclass, reviewer table or second BPL.
- One `com.gaia.discovery.pex.TapOutboundAdapter` Java class at `java-pex/src/main/java/com/gaia/discovery/pex/TapOutboundAdapter.java`. Register through **PEX** to generate its IRIS proxy; do not write a fake adapter-proxy `.cls`.
- One `backend/app.py` Flask WSGI callable `app`, hosted by one native IRIS WSGI web application mounted at `/gaia` using `%SYS.Python.WSGI`. Implement REST backend before UI, use in-process `iris` APIs validated on the installed image; do not introduce `%CSP.REST`, Gunicorn, Uvicorn or a second web runtime. Reference: [WSGI API contract](../contracts/WSGI_API.md).
- Docker Compose and Dockerfile only to the extent actually required for the locally authorized EAP runtime and build; ZPM `module.xml` installs the proven application and assets.
- Frontend: `web/index.html`, `web/app.js`, `web/style.css`, built **last**.

## Planned runtime source tree (not part of this specification-only archive)

```text
src/iris/Gaia/
├── Data/DiscoveryReport.cls
├── Interop/
│   ├── DiscoveryService.cls
│   ├── DiscoveryWorkflow.cls
│   ├── Messages/
│   │   ├── DiscoveryRequest.cls
│   │   └── DiscoveryResponse.cls
│   └── Operations/
│       ├── FinkOperation.cls
│       ├── AIHubOperation.cls
│       ├── GaiaOperation.cls
│       ├── SimbadOperation.cls
│       └── IrsaOperation.cls
└── Science/
    ├── AngularSeparation.cls
    └── ReportEmbedding.cls
java-pex/src/main/java/com/gaia/discovery/pex/TapOutboundAdapter.java
backend/app.py  # Flask callable app, IRIS WSGI (implement REST backend before UI)
web/index.html
web/app.js
web/style.css
compose.yaml
module.xml
```

## Component-to-source ownership

| Implementation source | Specification model | Contract |
|---|---|---|
| FinkOperation | [01 Ingestion](../specification/components/01_INGESTION.md) | [Fink API](../contracts/FINK.md) |
| DiscoveryService/BPL | [02 BPL](../specification/components/02_DISCOVERY_BPL.md) | [Internal messages](../contracts/INTERNAL_MESSAGES.md) |
| AIHubOperation/native agent | [03 AI Hub](../specification/components/03_AI_HUB.md) | [Decision JSON](../contracts/AI_HUB_DECISION.schema.json) |
| 3 TAP Operations + Java adapter | [04 Catalogs PEX](../specification/components/04_CATALOGS_PEX.md) | [PEX adapter](../contracts/JAVA_PEX_TAP_ADAPTER.md) |
| AngularSeparation | [05 Scientific normalization](../specification/components/05_SCIENTIFIC_NORMALIZATION.md) | [Crossmatch](../contracts/CROSSMATCH.md) |
| ReportEmbedding | [06 Vector](../specification/components/06_VECTOR_HISTORY.md) | [Vector history](../contracts/VECTOR_HISTORY.md) |
| DiscoveryReport + native Workflow | [07 Report + Review](../specification/components/07_REPORT_REVIEW.md) | Native task / existing report |
| Flask WSGI `backend/app.py` + web | [08 REST + UI](../specification/components/08_REST_UI.md) | [WSGI contract](../contracts/WSGI_API.md), [UI](../specification/UI_SPEC.md) |
| Compose + ZPM | [09 Deployment](../specification/components/09_DEPLOYMENT.md) | [Bonus plan](../contest/BONUS_IMPLEMENTATION_PLAN.md) |

**No redundant class**: do not generate separate message subclasses per operation, a reviewer callback BO, a reviewer Approval API, a second history/report table, a task class, or independent Java catalog operations. Test actual SDK signatures rather than inventing them.
