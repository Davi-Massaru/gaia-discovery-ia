# API Request Contracts — Implementation Examples (English)

All examples below are **documented request shapes**, *not responses actually observed in this build*. The numerical coordinates and IDs are official/example values or illustrative and do not imply a scientific association. Scripts/BOs must send actual values from the preceding result.

## 1 — Find a recent Fink alert

```http
GET https://api.lsst.fink-portal.org/api/v1/tags
```

Choose an entry supported by the returned tag dictionary. Then:

```http
POST https://api.lsst.fink-portal.org/api/v1/tags
Content-Type: application/json

{"tag":"in_tns","columns":"r:diaObjectId","n":"3"}
```

Extract `r:diaObjectId` as a string; deduplicate.

## 2 — Retrieve its latest detection and photometry

```http
POST https://api.lsst.fink-portal.org/api/v1/sources
Content-Type: application/json

{"diaObjectId":"313761043604045880","columns":"r:diaObjectId,r:diaSourceId,r:ra,r:dec,r:midpointMjdTai,r:psfFlux,r:psfFluxErr","output-format":"json"}
```

This object ID is from the public Fink documentation; normally substitute the ID from step 1. `sources` returns a JSON array sorted newest first per documentation; select a detection with coordinates and a valid `diaSourceId`.

## 3 — Retrieve the three PNGs for *that* detection

```http
POST https://api.lsst.fink-portal.org/api/v1/cutouts
Content-Type: application/json

{"diaSourceId":"170050479238676547","kind":"Science"}
```

Repeat `kind=Template` and `kind=Difference`; store image/png binary streams. The sample ID is a separate documentation example; never assume it belongs to the prior sample object ID. For numeric data the Fink API alternatively documents `{"diaSourceId":"...","kind":"All","output-format":"array"}` returning `b:cutoutScience`, `b:cutoutTemplate`, `b:cutoutDifference` — but the MVP uses PNG display cutouts.

## 4 — Query ESA Gaia / SIMBAD / IRSA based on AI Hub action

One common TAP transport contract:

```http
POST <one of the three allowlisted TAP /sync URLs>
Content-Type: application/x-www-form-urlencoded

REQUEST=doQuery&LANG=ADQL&FORMAT=csv&QUERY=<urlencoded ADQL>
```

### CHECK_GAIA (example query; 5 arcsec radius)

```sql
SELECT TOP 20 source_id,ra,dec,pmra,pmdec,parallax,phot_g_mean_mag,ruwe
FROM gaiadr3.gaia_source
WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',61.9648,-48.713,0.001388889))
```

### CHECK_SIMBAD (example query; 5 arcsec radius)

```sql
SELECT TOP 20 main_id,ra,dec,otype
FROM basic
WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',61.9648,-48.713,0.001388889))
```

### CHECK_IRSA (example query; 10 arcsec radius)

```sql
SELECT TOP 20 designation,ra,dec,w1mpro,w2mpro,ph_qual
FROM allwise_p3as_psd
WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',61.9648,-48.713,0.002777778))
```

The BO's **Embedded Python** builds validated ADQL, **Java PEX** sends it, and **Embedded Python** parses and normalizes returned CSV. The example radii are provisional design defaults, not universal physical match thresholds.

## 5 — Normalized catalog result (application contract, hypothetical)

```json
{
  "runId":"r-001",
  "catalog":"SIMBAD",
  "status":"OK",
  "endpoint":"https://simbad.cds.unistra.fr/simbad/sim-tap/sync",
  "retrievedAtUtc":"2026-11-02T20:00:00Z",
  "matches":[{"sourceId":"EXAMPLE_ONLY","raDeg":61.96481,"decDeg":-48.71301,"separationArcsec":0.043,"objectType":"Galaxy"}],
  "errorCode":null
}
```

This row is **synthetic schema illustration**; no such observed crossmatch is claimed. For `EMPTY`, `matches` is `[]` after a valid zero-row CSV; for `ERROR`, include an errorCode and do not make a non-discovery inference.

## 6 — OpenAI text embedding (optional semantic-memory step, not astronomy API)

```http
POST https://api.openai.com/v1/embeddings
Authorization: Bearer ${OPENAI_API_KEY}
Content-Type: application/json

{"model":"text-embedding-3-small","input":"Concise factual alert and hypothesis description"}
```

Read `data[0].embedding`, validate a 1536-dimensional numeric vector, store in the same IRIS DiscoveryReport table and use `VECTOR_COSINE` against earlier reports. Do **not** treat cosine similarity as scientific confirmation.

## Contract test and trace requirements

- Check endpoint status/content type, required keys, numeric finiteness, column changes and binary PNG headers.
- Keep HTTP response statuses and query provenance; never use HTTP errors as `EMPTY` catalog outcomes.
- Log catalog request in the selected BO message in IRIS Visual Trace; log Java adapter invocation with correlated `runId` separately.
- Source docs and crossmatch index: [API_ENDPOINT_INDEX.md](API_ENDPOINT_INDEX.md).
