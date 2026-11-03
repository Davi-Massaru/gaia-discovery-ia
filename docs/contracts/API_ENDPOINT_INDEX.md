# External API Endpoint and Field Index

**Purpose:** single human-readable index for implementers; exact upstream service contracts and official documentation remain under the corresponding source files. **Public anonymous scientific queries only.** The only external API credential is the existing `OPENAI_API_KEY` used for AI Hub/OpenAI embeddings. Public Rubin Science Platform APIs that require tokens are **not** part of this system.

## A. Astronomical sources

| Service | Verb | Full endpoint | Content type | Required/selected input | Response fields that the MVP uses | Used in |
|---|---|---|---|---|---|---|
| Fink | `GET` | `https://api.lsst.fink-portal.org/api/v1/tags` | JSON | none | supported tag names and API support | tag selector and contract check |
| Fink | `POST` | `https://api.lsst.fink-portal.org/api/v1/schema` | JSON | `{endpoint:"/api/v1/sources"}` | field definitions for response verification | startup/test only |
| Fink | `POST` | `https://api.lsst.fink-portal.org/api/v1/tags` | JSON | `{tag,n,columns}` | `r:diaObjectId` | observation selection |
| Fink | `POST` | `https://api.lsst.fink-portal.org/api/v1/sources` | JSON | `{diaObjectId,columns,"output-format":"json"}` | `r:diaSourceId,r:ra,r:dec,r:midpointMjdTai,r:psfFlux,r:psfFluxErr` | observation metadata |
| Fink | `POST` | `https://api.lsst.fink-portal.org/api/v1/cutouts` | JSON request; PNG response | `{diaSourceId,kind}` where `kind` is Science, Template, Difference | PNG bytes | three observation images |
| Gaia Archive | `POST` | `https://gea.esac.esa.int/tap-server/tap/sync` | `application/x-www-form-urlencoded` | `REQUEST=doQuery&LANG=ADQL&FORMAT=csv&QUERY=<ADQL>` | `source_id,ra,dec,pmra,pmdec,parallax,phot_g_mean_mag,ruwe` | stellar properties |
| SIMBAD | `POST` | `https://simbad.cds.unistra.fr/simbad/sim-tap/sync` | `application/x-www-form-urlencoded` | same TAP parameters | `main_id,ra,dec,otype` | known astronomical context |
| NASA IRSA | `POST` | `https://irsa.ipac.caltech.edu/TAP/sync` | `application/x-www-form-urlencoded` | same TAP parameters | `designation,ra,dec,w1mpro,w2mpro,ph_qual` | infrared context |

**TAP ADQL:** Each search uses finite Fink RA/Dec, bounded catalog-specific radius in **degrees**, `SELECT TOP 20`, and fields above. ADQL for the three tables is in source files. TAP responses are handled by a shared Java PEX custom outbound adapter **only for transport**; the catalog BO parses CSV in Embedded Python.

## B. OpenAI embedding endpoint

| Verb | URL | Credential | Payload | Response needed |
|---|---|---|---|---|
| `POST` | `https://api.openai.com/v1/embeddings` | `Authorization: Bearer ${OPENAI_API_KEY}` | `{"model":"text-embedding-3-small","input":"..."}` | `data[0].embedding` (1536 floats by default) |

The native AI Hub Provider uses its **documented provider configuration**, not an application-defined REST endpoint contract; validate in the installed SDK. The embeddings endpoint is called from in-process Embedded Python and reuses the existing key, not an extra service credential.

## C. Cross-catalog data relationships

| Fink datum | Other system field | How correlated | Important caveat |
|---|---|---|---|
| `r:ra`, `r:dec` (degrees) | Gaia `ra,dec` | angular separation + epoch/proper-motion caveat | different reference epochs; not proof |
| same | SIMBAD `ra,dec` | angular separation | a nearby galaxy may be host, not event |
| same | AllWISE `ra,dec` | angular separation, source-aware radius | infrared blending, older epoch |
| `r:midpointMjdTai` | Gaia reference epoch | use for proper-motion consideration | MJD TAI vs epoch coordinate semantics |
| `r:psfFlux` | Gaia G / AllWISE W1,W2 magnitudes | **interpret context only** | do not directly subtract or compare units |
| `r:diaObjectId` / `r:diaSourceId` | all other IDs | **no direct shared ID join** | keep IDs as strings |
| report `SearchEmbedding` | previous `SearchEmbedding` | IRIS `VECTOR_COSINE` | textual analogy, not physical association |

## D. Sources and verification levels

- Official Fink tags https://doc.lsst.fink-broker.org/services/api/tagsearch/
- Official Fink object/source model https://doc.lsst.fink-broker.org/services/api/diaobjectid/
- Official Fink image contract https://doc.lsst.fink-broker.org/services/api/imagesearch/
- Official Fink fields/schema https://doc.lsst.fink-broker.org/services/api/definitions/
- ESA Gaia programmatic archive https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access
- SIMBAD TAP https://simbad.cds.unistra.fr/simbad/sim-tap/sync
- NASA IRSA TAP example https://irsawebops2.ipac.caltech.edu/docs/program_interface/astropy_TAP.html
- OpenAI embeddings https://platform.openai.com/docs/api-reference/embeddings/create

**Source-backed:** above HTTP endpoint patterns and named astronomical fields. **Proposed implementation:** timeouts, limits, internal statuses, persistence layout and application method signatures. **Runtime not verified here:** outbound POST responses for Fink/ESA/SIMBAD/IRSA and build-154 SDK/proxy behavior. No invented samples are represented as live data.
