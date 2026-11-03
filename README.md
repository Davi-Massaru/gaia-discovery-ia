# Gaia Discovery AI

Astronomical investigations of real Rubin/Fink alerts inside InterSystems IRIS AI Hub EAP 154. Requirements remain in [SPEC.md](SPEC.md).

One Production and adaptive BPL, five application Operations, two message envelopes, one report table, one shared Java PEX TAP adapter, native Workflow review, Embedded Python, IRIS Vector Search, native Flask WSGI and two browser views. No standalone Flask server is used.

## Docker

Keep the authorized EAP image and `OPENAI_API_KEY` in the ignored root `.env`; see [.env.example](.env.example). The image is never redistributed.

```powershell
docker compose build
docker compose up -d
```

Open [Gaia](http://localhost:52774/gaia/) using an authorized IRIS account. Change initial IRIS administrator passwords through native account management before browser login. Authentication remains password protected (`AutheEnabled=32`).

Assign authorized application users `GaiaWSGI`, `%DB_USER`, and `%EnsRole_Operator`. Reviewers also need `GaiaWorkflowUser`, which grants only `%DeepSee_Portal:U` for the native User Portal. `GaiaWSGI` grants Embedded Python execution and SELECT on the report table. Set `GAIA_REVIEWER` to an existing IRIS account; installation adds it to the native `AstronomyReviewer` Workflow role. The native Inbox is `/csp/user/_DeepSee.UserPortal.Workflow.zen` in the default USER namespace. Installation enables this native portal and requires password authentication. Acceptance means further investigation, never discovery confirmation.

Compose binds loopback ports (web 52774, SQL 1973 by default) and stores IRIS state in a named volume. The Java language server is the shipped `%Java Server`. The adapter is registered before Operations compile.

## Verification

```powershell
docker exec gaia-discovery-dev python3 -m unittest discover -s /opt/gaia/tests -v
docker exec gaia-discovery-dev python3 /opt/gaia/scripts/verify_contracts.py
docker exec gaia-discovery-dev python3 /opt/gaia/scripts/http_smoke.py
```

`gaia-discovery-dev` is the mounted development container used during implementation (web port 52773). Its restricted reviewer credentials are in the ignored `.env.runtime`; they are never packaged. `scripts/verify_runtime.py` runs inside Embedded Python to compare HTTP images with saved streams, execute real PEX requests, test vector SQL and submit an asynchronous run. Mocks exist only in isolated tests.

EAP 154's shipped WSGI interface decodes yielded chunks as UTF-8. The PNG route writes its existing binary stream through IRIS's native response device after WSGI headers. All three images were compared byte for byte with saved streams. Vendor classes/modules remain unchanged.

## IPM / ZPM

Use the same compatible AI Hub EAP runtime, Java SDK and IPM with automatic `requirements.txt` support. Build the adapter before packaging:

```powershell
docker exec gaia-discovery-dev sh /opt/gaia/scripts/build_java.sh
docker exec gaia-discovery-dev python3 /opt/gaia/scripts/package.py
```

In a compatible IRIS terminal with the official IPM client installed:

```objectscript
zpm "load /path/to/extracted/gaia-package"
do ##class(Ens.Director).StartProduction("Gaia.Production")
```

The manifest registers PEX before compilation, installs Python dependencies, deploys files under the writable IRIS manager directory, and configures authenticated WSGI and native Workflow. The source archive uses an explicit allowlist excluding credentials. IPM `package gaia-discovery-ai` creates the native distributable after loading.

## Executed evidence and limits

TAP reliability update: Gaia uses a bounded standard GET with a 45-second budget. SIMBAD may use its official Harvard mirror after a transient primary failure. At most two transport attempts share the request budget; actual endpoint, HTTP status, timing, phase and exception type are preserved. The exact reported Gaia/SIMBAD queries both returned HTTP 200 / EMPTY through native Production operations in the final check. Gaia remains intermittently slow; an earlier repeat still timed out. Failed catalogs display an unknown candidate count, not zero.

The feed supports independent scientific `status` and human `review_status` filters, applied before pagination and semantic ranking. INCONCLUSIVE reports remain readable/filterable but skip embedding generation (`SKIPPED_INCONCLUSIVE`) and are excluded from semantic history/search, including previously indexed rows. Thirty unit tests, 24 real HTTP filter combinations and the eight isolated BPL scenarios passed after this change.

- 27 isolated tests passed, including sanitized diagnostics, empty history without provider calls, optional failure isolation and conservative assessment when a requested catalog fails.
- Java compiled against the shipped SDK. All 12 application classes, Production and generated BPL classes compiled in EAP 154.
- A real Fink observation and three authentic cutouts were saved with native session correlation. Authenticated REST returned reports/images, 400/404 errors and HTTP 202 for asynchronous submission.
- Disposable-container integration tests exercise the actual BPL, four decisions/three catalog branches, saved reports, empty/invalid/missing-source failures, dispatch failure, and a two-candidate batch whose ACCEPT and REJECT replies update the correct reports after native sync. Only external-source responses are mocked, explicitly labeled as fixtures.
- ACCEPT and REJECT were also completed through the native Workflow Inbox in the browser and returned to the same BPL. Fixtures remain confined to the disposable test container. This testing found and fixed repeated async-call names discarding later replies, and native Workflow-field access across the Embedded Python bridge.
- Real native AI Hub produced four schema-valid decisions per alert and routed through Gaia, SIMBAD, IRSA and FINISH (sessions 154 and 192). Earlier calls reproduced OpenAI spend-limit errors, but subsequent native LLM and embedding calls succeeded. Technical failures now have separate executionStatus, failureStage, failureCode and sanitized details.
- Real 1536-dimensional embeddings, saved-report vector SQL and semantic REST search passed. Empty native history returns an empty result without contacting OpenAI. Final report 32 contains real decisions, authentic PNGs, successful embedding/history and INCONCLUSIVE assessment because requested catalogs failed.
- Real Java PEX queries returned Gaia `EMPTY` and IRSA `OK` (one positional candidate). SIMBAD still refused/timed out. Such failures remain `ERROR`.
- Docker build/Compose startup and native IPM packaging/installation passed. The EAP runtime can later report an unhealthy System monitor due to vendor startup error `<METHOD DOES NOT EXIST>Sharding+2^STU *Sharding,SYS.ICM`; its standard healthcheck remains enabled. Public publication is intentionally manual.
- Authenticated Chrome feed/detail navigation and all three actual report images were verified. The UI separates technical execution from scientific assessment. Final screenshot capture was interrupted by browser control; earlier screenshots are retained as historical evidence.

See [class contracts](docs/implementation/CLASS_CONTRACTS.md), [native WSGI documentation](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=AWSGI) and [official IPM manifest reference](https://github.com/intersystems/ipm/wiki/03.-IPM-Manifest-%28Module.xml%29). No unverified scientific result or contest bonus is claimed.
