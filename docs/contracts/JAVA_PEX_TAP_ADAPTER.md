# Java PEX Custom TAP Outbound Adapter — Technical Contract

**Target:** InterSystems IRIS AI Hub EAP build 154, Java PEX support to be verified in the installed container. **Status:** documented architecture, not compiled or runtime-validated.

## Python-first implementation policy

Follow the canonical [Python First policy](../../SPEC.md): Embedded Python implements application/data behavior; ObjectScript supplies necessary IRIS-native glue; Java is restricted to the one PEX custom TAP adapter. Verify build-154 compatibility.

## Responsibility and rationale

One **custom Java PEX outbound adapter** is the transport layer for Gaia, SIMBAD and NASA IRSA TAP/ADQL calls. This is not an extra microservice and is not a generic Java gateway to every application feature. The existing `GaiaOperation`, `SimbadOperation` and `IrsaOperation` remain separate **native IRIS Business Operations**. They each construct catalog-specific bounded ADQL, parse CSV, validate astronomical fields and calculate matches in **Embedded Python methods**. They use the single PEX adapter exclusively for controlled TAP HTTP transport and receive bounded raw CSV plus transport metadata.

The official InterSystems PEX documentation supports a Java adapter extending `com.intersystems.enslib.pex.OutboundAdapter`, registration as an IRIS proxy class, and attaching that proxy to a native Business Operation with its `ADAPTER` class parameter. This is a real custom adapter and a real Java PEX component, potentially satisfying **two separate contest bonus categories** after successful runtime demonstration and organizer evaluation.

## Proposed implementation mapping

| Element | Definition |
|---|---|
| Java remote class | `com.gaia.discovery.pex.TapOutboundAdapter` |
| Java base class | `com.intersystems.enslib.pex.OutboundAdapter` |
| Built JAR | `gaia-tap-pex.jar` |
| Registered IRIS proxy | `Gaia.Interop.Adapters.TAPOutboundAdapter` *(proposed proxy name; generated during registration)* |
| Native consumers | `GaiaOperation`, `SimbadOperation`, `IrsaOperation` |
| Java connection | IRIS PEX Java external-language server / gateway configured inside the existing IRIS deployment |

**No dedicated Java Business Operation is necessary:** native catalog Business Operations can call methods on a registered Java PEX adapter. The adapter itself is not a Business Host or a separately traced BPL destination. The Production Visual Trace records the parent catalog Business Operation; for PEX execution proof also capture Java gateway diagnostics, correlated by the run/object ID.

## Adapter call contract (application-defined; not a verified PEX method signature)

`query(catalogCode, adql, maxRows, timeoutSeconds) -> TapResult`

- `catalogCode` must be one of `GAIA`, `SIMBAD`, `IRSA`. It resolves to one of the fixed documented HTTPS TAP endpoints. **No user- or LLM-provided URL.**
- `adql` must be constructed by the owning Business Operation from validated coordinates/radius and known table/column names. Reject or cap unbounded queries; never execute LLM-authored ADQL.
- `maxRows`: 1–20. `timeoutSeconds`: a bounded configured limit.
- HTTP: bounded Gaia queries use standard TAP `GET`; SIMBAD/IRSA use form-encoded `POST`, with `REQUEST=doQuery`, `LANG=ADQL`, `FORMAT=csv`, `QUERY=<url-encoded ADQL>`. Gaia has a 45-second request budget; other catalogs use 30 seconds. At most two transport attempts share the budget. SIMBAD can use the official Harvard mirror after a transient primary failure, with actual endpoint and attempts preserved in evidence.
- **Transport `TapResult`:** `{status: OK|ERROR, catalog, httpStatus, csvBody, errorCode, elapsedMs}` with a strict response-byte cap. `csvBody` is passed only to the calling Operation. **Embedded Python** parses valid CSV into up to 20 whitelisted records, setting the final application status to `OK`, `EMPTY`, or `ERROR`; never forward raw bodies to AI Hub.
- Only Python-side CSV validation may declare `EMPTY`, after a **successful, valid zero-row CSV**. HTTP failure, invalid CSV or TAP error document means `ERROR`.
- Java enforces TLS, connect/read timeouts, response-size cap and bounded retry (at most one retry for transient network errors). Python enforces row limits, catalog-specific schemas and scientific interpretation. Do not retry malformed ADQL.

## Java PEX registration and deployment

1. Verify availability of `com.intersystems.enslib.pex.OutboundAdapter`, Java version and shipped utility JAR in the installed image.
2. Build `gaia-tap-pex.jar` with the installed PEX Java dependencies (do not invent Maven coordinates).
3. Configure the **existing** IRIS Java external-language server with the required InterSystems utility JAR on the classpath. The official docs identify `$$IRISHOME/dev/java/lib/1.8/intersystems-utils-<version>.jar` (resolve the actual filename at build time).
4. Navigate to `Interoperability > Configure > Production EXtensions Components` and register remote class `com.gaia.discovery.pex.TapOutboundAdapter` with proxy name `Gaia.Interop.Adapters.TAPOutboundAdapter` and JAR classpath. Record the exact resulting proxy name.
5. Set each native catalog Operation's `ADAPTER` parameter to the registered proxy class and use the adapter's validated invocation mechanism. Compile and run live tests in build 154.
6. Package the adapter JAR and deterministic registration/configuration steps as part of the app's installation workflow. ZPM installation is incomplete until the proxy is registered and a live TAP call succeeds.

## Proof cases

- Successful Gaia, SIMBAD and IRSA catalog queries each run through this **same Java adapter**.
- IRIS Production Visual Trace contains calls to each selected catalog Business Operation; the adapter execution is evidenced through those operations plus Java gateway/adaptor diagnostics or controlled log fields.
- A URL not in the allowlist, an oversized result and a non-200 TAP response are rejected by the Java transport; Python rejects invalid ADQL inputs, malformed CSV and disallowed fields.
- An AI decision `FINISH` results in no unnecessary TAP call.

## Official references

- [PEX outbound adapters](https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EPEX_outbound)
- [PEX component registration](https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EPEX_register)
- [PEX Java external language servers](https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EPEX_object_gateway)
- [PEX Business Operations](https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EPEX_operation)
- [Official contest bonus rules](https://community.intersystems.com/post/technology-bonuses-intersystems-programming-contest-ai-agents-interoperability-workflows)
