# Component 05 — Scientific Field Normalization and Crossmatching

**Purpose:** convert catalog outputs into comparable, provenance-tagged *candidate associations*. This step is deterministic **Embedded Python** rather than LLM arithmetic.

## Input / output

**Input:** Fink event `(raDeg,decDeg,observedMjdTai)`, catalog rows `(id,ra,dec,fields)`, source kind, quality/null flags. **Output:** at most 20 normalized `CatalogMatch` objects `{catalog,sourceId,raDeg,decDeg,separationArcsec,rawFields,qualityFlags,caveats}` and `CatalogResult.status`.

## Crossmatch computation

For small distances use a numerically stable haversine or unit-vector great-circle separation in Python. Do **not** calculate naive straight-line `sqrt((ra1-ra2)^2+(dec1-dec2)^2)` without cos(dec) and wrap-around correction. Result in arcseconds, validated finite and >=0. Account for Gaia's reference epoch and `pmra`/`pmdec` for high-proper-motion stars when enough proper-motion data exist; otherwise mark `EPOCH_MISMATCH_POSSIBLE`.

Match radii must be explicit and source-aware, e.g. example starting tests Gaia/SIMBAD 5 arcsec; AllWISE 10 arcsec. These are **query radii**, not universal acceptance thresholds. They require scientific review/validation and must never become proof of identity automatically.

## Meaning of results

- `Fink diaObjectId`: observation-association ID; not a Gaia/SIMBAD/AllWISE identifier.
- `Gaia source_id`: an astrometric catalog source, which may be in the same region as the Fink transient.
- `SIMBAD main_id`: cataloged object's identifier/type; a nearby galaxy can be a plausible host without being the transient.
- `AllWISE designation`: infrared survey source, potentially blended or from a different epoch.
- `phot_g_mean_mag`, `w1mpro`, `w2mpro`, `psfFlux` measure different passbands/units. **Do not subtract raw values across surveys** or infer variability from a single unmatched measurement.
- `ruwe` is a quality indicator, not a novelty score; `ph_qual` is a quality flag, not proof of identity.

## Failure statuses and evidence

| Status | Allowed meaning |
|---|---|
| `OK` | valid response, 1+ rows |
| `EMPTY` | complete valid response, zero rows |
| `ERROR` | timeout, HTTP/TAP failure, malformed data, parse error |
| `NOT_REQUESTED` | AI Hub did not select this catalog |

An `ERROR` is never normalized to `EMPTY`. Preserve original source IDs and query parameters. Build agent context with at most a few best matches by separation (plus row count and ambiguity), never discard provenance.

**Test:** RA wrap across 359.999°/0.001°, negative Dec, poles, invalid/NaN, zero-row and bad-CSV responses, Gaia moving-source epoch caveat, AllWISE blending caveat. See [`CROSSMATCH.md`](../../contracts/CROSSMATCH.md).
