# Gaia Discovery AI — Implementation and Bonus Proof Plan

**Objective:** earn technology bonuses through product functionality, not decorative components. **Target:** up to 16 technology-bonus points, not guaranteed.

## Python-first implementation policy

Follow the canonical [Python First policy](../../SPEC.md): Embedded Python implements application/data behavior; ObjectScript supplies necessary IRIS-native glue; Java is restricted to the one PEX custom TAP adapter. Verify build-154 compatibility.

## Delivery gates

The UI is implemented only after all backend/runtime features pass. ZPM publication and final screenshots follow UI integration; the gates below track capability proofs, not strict chronology.

| Gate | Implementation outcome | Potential cumulative technology points |
|---|---|---:|
| A | Working Fink images, adaptive native AI Hub, BPL, saved report and REST responses; Docker runtime (**UI intentionally last**) | 2 |
| B | Java PEX **custom TAP adapter** registered once and used by three catalog BOs | 7 |
| C | Embedded Python angular math and report embedding + IRIS `VECTOR_COSINE` prior-case retrieval | 12 |
| D | One real Workflow Engine reviewer task, acceptance/rejection stored on report | 14 |
| E | ZPM published and verified on a clean compatible image, including Java gateway/proxy configuration | **16** |

Points are additive **opportunities** only; final rules and evidence determine eligibility.

## Functional purpose of each bonus

1. **Java PEX + Custom Adapter:** one small reusable outbound TAP HTTP transport for ESA Gaia, CDS SIMBAD and NASA IRSA. Java PEX class `com.gaia.discovery.pex.TapOutboundAdapter`, one generated proxy `Gaia.Interop.Adapters.TAPOutboundAdapter`; no redundant native adapter or Java Business Operation. It handles HTTPS, form encoding, fixed endpoints, timeout and byte-size limits; Embedded Python in catalog BOs parses CSV and normalizes astronomy evidence. See [adapter contract](../contracts/JAVA_PEX_TAP_ADAPTER.md).
2. **Embedded Python:** primary language inside IRIS for Fink/TAP payload handling, ADQL, catalog CSV/JSON interpretation, numerical astronomy, evidence construction, report SQL and short-text embedding generation. Report text calls OpenAI with the same key already used for AI Hub. No Python Gateway, worker or external database.
3. **IRIS Vector Search:** existing report table stores `SearchEmbedding`, and new alerts retrieve top-three prior conclusions with IRIS `VECTOR_COSINE` SQL. Search results are historical analogies, never independent scientific proof. See [vector contract](../contracts/VECTOR_HISTORY.md).
4. **Workflow Engine (+2 potential):** `DiscoveryWorkflow` already exists; reuse it. Configure **one native** `EnsLib.Workflow.Operation` named `AstronomyReviewer`, `AutoCreateRole=1`, assign a Workflow user. Persist a `REVIEW_CANDIDATE` report, send native `EnsLib.Workflow.TaskRequest` through async `<call>` with `%Actions="ACCEPT,REJECT"`, receive `EnsLib.Workflow.TaskResponse.%Action` through the **same BPL** `<sync>`, update existing `ReviewStatus`. `ACCEPT` merely advances the scientific candidate. No additional BPL, workflow class, callback, reviewer frontend or task database. See [Component 07](../specification/components/07_REPORT_REVIEW.md).
5. **Docker:** one IRIS EAP build 154 container hosting the Production, java gateway, SQL and web UI; no Java sidecar needed.
6. **ZPM:** package IRIS code, UI, Java adapter JAR and reproducible gateway/proxy registration. Validate release-specific installation limitations and require a clean-install test before claiming success.

## Test matrix

| Case | Proof |
|---|---|
| Fink input | Real alert, 3 Fink image cutouts and observation coordinates stored |
| Adaptive agent | 2 alerts take different BPL branches; unneeded catalogs are never queried |
| Java PEX adapter | Confirm class registration, proxy, Java gateway, and Gaia/SIMBAD/IRSA live TAP responses |
| Embedded Python | Real in-process angular distance calculation stored with catalog evidence |
| Vector retrieval | At least 2 saved report vectors, search uses actual IRIS `VECTOR_COSINE`; new AI input includes prior references |
| Empty history | A first run succeeds with no historical reports |
| Embedding failure | Report saves and UI remains available; history warning is recorded |
| Human workflow | Candidate creates task; native Inbox action completes; `ReviewStatus` updates |
| No extra containers | Production, Java gateway, and UI work using the documented IRIS deployment |
| Reinstall | Published ZPM clean install restores all necessary classes, assets, Flask WSGI callable/dependency/web application configuration and Java registration |

## Deployment risk gates

- The **PEX Java registration and invocation API** must be verified in the actual EAP 154 image before coding the adapter's method signatures. A fake `Ens.OutboundAdapter` class does not qualify as Java PEX.
- The **SQL vector type and embedding model configuration** must be verified against the installed IRIS runtime. Do not paste examples from newer builds without executing a smoke test.
- Configure `OPENAI_API_KEY` through ignored `.env` or a supported secure provider configuration; no `NASA_API_KEY`, `DEMO_KEY` or credentials for TAP catalogs.
- The **native Workflow Engine** must demonstrate actual task creation and completion, not a plain BPL switch that mimics human review.
- A **Community Idea** remains optional and should be implemented only when it directly improves the product.

## Official references

- [Contest bonuses](https://community.intersystems.com/post/technology-bonuses-intersystems-programming-contest-ai-agents-interoperability-workflows)
- [Java PEX adapters](https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EPEX_outbound)
- [PEX registration](https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EPEX_register)
- [Vector SQL](https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSQL_vecsearch)
- [Workflow Engine](https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EGWF_overview)
