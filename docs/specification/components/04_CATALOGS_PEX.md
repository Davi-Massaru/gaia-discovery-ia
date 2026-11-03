# Component 04 — Scientific Catalog Operations and Java PEX TAP Adapter

**Purpose:** query three scientific sources independently through one reusable **Java PEX custom outbound adapter**, with Python-built ADQL and Python-parsed evidence. This is a real transport integration, not a decoration for bonus points.

## Ownership map

| Component | Python owns | Java PEX adapter owns |
|---|---|---|
| `GaiaOperation` | Gaia ADQL, CSV field mapping, separation calculations | HTTPS TAP request and response-byte cap |
| `SimbadOperation` | SIMBAD ADQL, object type mapping, separation calculations | Same Java adapter |
| `IrsaOperation` | AllWISE ADQL, photometric field mapping, separation calculations | Same Java adapter |

**Java implementation:** remote `com.gaia.discovery.pex.TapOutboundAdapter extends com.intersystems.enslib.pex.OutboundAdapter`; register proxy as planned `Gaia.Interop.Adapters.TAPOutboundAdapter` and verify actual proxy name. A native Business Operation's `ADAPTER` parameter can reference that registered proxy. Method argument signatures are intentionally **conceptual until verified on build 154**; the vendor's official PEX registration/invocation mechanics must be followed exactly.

## Transport contract (proposed)

`submitTAP(catalog: GAIA|SIMBAD|IRSA, adql: str, timeoutSec: int) -> {httpStatus, status: OK|ERROR, bodyCsv, elapsedMs, errorCode}`. Adapter selects URL **by allowlisted catalog code** — never by an arbitrary URL supplied by the AI. HTTP `POST`, form-encoded `REQUEST=doQuery`, `LANG=ADQL`, `FORMAT=csv`, `QUERY=<ADQL>`. Reject unrecognized code, oversized request/response, redirects outside allowlist, invalid TLS and timeout; do not log credential/body secrets.

Java does **not** know Gaia/SIMBAD column semantics or classify objects. Embedded Python verifies TAP result media and valid CSV, checks row cap and column names, maps rows to `CatalogResult` with `OK|EMPTY|ERROR` and keeps request provenance and UTC retrieval timestamp. A valid zero-row response is `EMPTY`; timeout / malformed CSV / TAP service error is `ERROR`.

## Scientific queries

| Source | TAP endpoint | Table | Minimal fields | Scientific question |
|---|---|---|---|---|
| ESA Gaia DR3 | `https://gea.esac.esa.int/tap-server/tap/sync` | `gaiadr3.gaia_source` | `source_id,ra,dec,pmra,pmdec,parallax,phot_g_mean_mag,ruwe` | plausible stellar counterpart? |
| CDS SIMBAD | `https://simbad.cds.unistra.fr/simbad/sim-tap/sync` | `basic` | `main_id,ra,dec,otype` | known objects/types nearby? |
| NASA IRSA AllWISE | `https://irsa.ipac.caltech.edu/TAP/sync` | `allwise_p3as_psd` | `designation,ra,dec,w1mpro,w2mpro,ph_qual` | infrared counterparts/context? |

The cone query uses Fink `raDeg,decDeg`, and search radius in **degrees** (`radiusArcsec/3600`). Bounded `SELECT TOP 20`, allowlist columns and catalog; validate numeric coordinates/radius before interpolating into ADQL. Example queries: [`GAIA.md`](../../contracts/GAIA.md), [`SIMBAD.md`](../../contracts/SIMBAD.md), [`IRSA.md`](../../contracts/IRSA.md).

**Message contract:** BPL sends `{runId,diaObjectId,catalog,raDeg,decDeg,radiusArcsec}`; BO returns `{catalog,status,rows:[{id,raDeg,decDeg,separationArcsec,...}],requestedAtUtc,endpoint,errorCode}`. Limit 20 mapped hits; forward compact rows to AI Hub, not full raw CSV.

**Proof:** for each catalog, show a real HTTP response moving through the registered **same** Java adapter, plus three separate BO message traces. Show adapter Java log correlation; internal Java calls are not separate BPL messages. Check bonus eligibility on contest rules before asserting awarded points.

**Official PEX docs:** https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EPEX_outbound ; https://irisdocs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EPEX_register .
