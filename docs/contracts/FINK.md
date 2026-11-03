# Contract A — Fink / Rubin LSST REST API

**Base:** `https://api.lsst.fink-portal.org`  
**Authentication:** none for public REST queries. Data available promptly through the REST database; **not** a push livestream.  
**Role:** source of newly received alerts, scientific coordinates, photometry, and cutout images.

## Endpoints actually used

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| GET | `/api/v1/tags` | Discover supported tags | none | JSON dictionary of tag names and `API support` |
| POST | `/api/v1/schema` | Verify available source fields at start-up or integration test | `{"endpoint":"/api/v1/sources"}` | JSON schema/field descriptors |
| POST | `/api/v1/tags` | Query latest alert objects by supported tag | JSON `tag`, `n`, `columns` | JSON array; `r:diaObjectId` |
| POST | `/api/v1/sources` | Query detections and measurements for a diaObject | JSON `diaObjectId`, `columns`, `output-format` | JSON array; `r:diaSourceId`, coordinates/time/flux |
| POST | `/api/v1/cutouts` | Fetch each of three actual images | JSON `diaSourceId`, `kind` | PNG binary (by default) |

### Example requests (documented patterns)

```http
GET https://api.lsst.fink-portal.org/api/v1/tags
```

```http
POST https://api.lsst.fink-portal.org/api/v1/tags
Content-Type: application/json

{"tag":"extragalactic_new_candidate","n":"3","columns":"r:diaObjectId"}
```

`in_tns` and `mdwarf_flare` are alternative supported tags for demonstration; verify actual `API support` at runtime. Returned rows can repeat the same object; deduplicate. Alert counts are bounded.

```http
POST https://api.lsst.fink-portal.org/api/v1/sources
Content-Type: application/json

{"diaObjectId":"313761043604045880","columns":"r:diaObjectId,r:diaSourceId,r:ra,r:dec,r:midpointMjdTai,r:psfFlux,r:psfFluxErr","output-format":"json"}
```

The ID in this sample is **a documented example**, not a live observation produced by our implementation. For production, pass the ID obtained from `/tags`. Use the schema discovery endpoint to verify field existence for the deployed API; Fink schemas evolve over time.

```http
POST https://api.lsst.fink-portal.org/api/v1/cutouts
Content-Type: application/json

{"diaSourceId":"170050479238676547","kind":"Science"}
```

Repeat with `kind` = `Template` and `Difference`. Without `output-format`, Fink's image documentation describes PNG output. For scientific numeric arrays, `{"kind":"All","output-format":"array"}` returns `b:cutoutScience`, `b:cutoutTemplate`, `b:cutoutDifference` as JSON. MVP uses PNG for display and saves original bytes; do not confuse PNG with FITS/variance planes.

### Cross-system fields

- Use `r:ra`, `r:dec` as the source position in degrees; `r:midpointMjdTai` as timestamp (MJD TAI).
- `r:psfFlux`, `r:psfFluxErr` represent LSST photometric measurements; do not compare numerical values directly to Gaia magnitude or WISE magnitudes.
- `r:diaSourceId` identifies the specific detection/image, while `r:diaObjectId` groups detections for an object.
- Metadata belongs to the **event**, not necessarily all objects visible in the cutout.
- All 64-bit IDs must be transported as strings to JavaScript and stored without precision loss.

### API errors and behavior

- Empty tags or sources: no report fabricated.
- Missing optional source columns: report missingness rather than inventing values.
- Cutout failure: report incomplete image set and stop or mark inconclusive.
- Rate: a small configurable batch of 1–20 objects (default 5) per run and small column lists; Fink explicitly discourages massive extraction through REST.

### Official documentation

- General public REST vs authenticated stream: https://doc.lsst.fink-broker.org/services/summary/
- Search by tag (exact POST contract): https://doc.lsst.fink-broker.org/services/api/tagsearch/
- Object/detection retrieval: https://doc.lsst.fink-broker.org/services/api/diaobjectid/
- Cutouts (PNG, FITS, array; exact `kind` values): https://doc.lsst.fink-broker.org/services/api/imagesearch/
- Schema/field prefixes: https://doc.lsst.fink-broker.org/services/api/definitions/
- Live tags catalogue: https://api.lsst.fink-portal.org/api/v1/tags
