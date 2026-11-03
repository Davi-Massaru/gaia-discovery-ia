# Cross-Source Evidence Correlation Contract

**Join key:** the sky position of the *alerted source* from Fink (`r:ra`,`r:dec`), not a visually inferred position of every star in the cutout. Supplement with the observing epoch (`r:midpointMjdTai`) and source-specific catalog metadata.

| Upstream | Identifier | Position | Other properties | Join method |
|---|---|---|---|---|
| Fink | `r:diaObjectId`, `r:diaSourceId` | `r:ra`, `r:dec` | PSF flux/error, MJD TAI | baseline |
| Gaia DR3 | `source_id` | `ra`,`dec` | `pmra`,`pmdec`,`parallax`,`phot_g_mean_mag`,`ruwe` | angular search; epoch caveat |
| SIMBAD | `main_id` | `ra`,`dec` | `otype` | angular search; contextual identity |
| AllWISE | `designation` | `ra`,`dec` | `w1mpro`,`w2mpro`,`ph_qual` | angular search; blending caution |

All identifiers remain catalog-specific strings. **No cross-system source-ID equality join exists.** Fink PSF flux cannot be directly compared to Gaia G magnitude or AllWISE W1/W2. A SIMBAD galaxy match may be a potential host but does not confirm a supernova. A missing match does not establish a novel object.

## Computation and output

- Embedded Python validates RA [0,360), Dec [-90,90], finite values and search radius. Use a great-circle distance formula, result in arcseconds.
- Apply proper motion/epoch handling to Gaia when meaningful and available, otherwise warn.
- Preserve unmatched catalog results and query outcomes; do not suppress zero rows/errors in the AI context.
- Return `CatalogResult` with up to 20 candidates and `separationArcsec` plus `qualityFlags` and `caveats`.
- Agent decides how to interpret the candidate list, not the basic geometry; it may choose the next allowed catalog or finish as inconclusive.

**Acceptance:** wrap-around RA test, pole test, empty/error status distinctions, Gaia moving-source caution, AllWISE source blending warning.
