# Contract D — NASA/IPAC IRSA AllWISE TAP

**Endpoint:** `https://irsa.ipac.caltech.edu/TAP/sync`  
**Authentication:** none for public small-area TAP searches.  
**Role:** find infrared catalog sources and report their photometric characteristics.

## HTTP/TAP request

Use a synchronous TAP query: POST `application/x-www-form-urlencoded` with `REQUEST=doQuery`, `LANG=ADQL`, `FORMAT=csv`, `QUERY=<ADQL>`. The IRSA TAP guide also documents GET `QUERY=<ADQL>&FORMAT=<format>`.

```sql
SELECT TOP 20 designation, ra, dec,
              w1mpro, w2mpro, ph_qual
FROM allwise_p3as_psd
WHERE 1 = CONTAINS(
    POINT('ICRS',ra,dec),
    CIRCLE('ICRS',61.9648,-48.713,0.002777778)
)
```

Example search radius = 10 arcseconds; the wider circle addresses the lower infrared angular resolution, but **does not imply the returned source is the same object**. Query center is illustrative.

## Fields mapped into `CatalogResult`

| Field | Meaning |
|---|---|
| `designation` | AllWISE source identifier |
| `ra`, `dec` | Catalog position (degrees) |
| `w1mpro`, `w2mpro` | W1/W2 profile-fit magnitudes (not comparable as raw numbers to Fink flux) |
| `ph_qual` | Photometric quality flag (interpret cautiously) |

Preserve candidate angular separation and possible blending. IRSA results are historical reference data; they are **not new Rubin images**. Nearby infrared light can belong to the host galaxy or a different blended source.

## Response and status

Successful bounded TAP results can be parsed as CSV; empty is `EMPTY`; TAP/HTTP errors are `ERROR`. Preserve query and provenance. Restrict result count to TOP 20.

## Official references

- IRSA TAP protocol/endpoints: https://irsa.ipac.caltech.edu/docs/program_interface/TAP.html
- AllWISE table and columns (IRSA official example): https://irsa.ipac.caltech.edu/docs/program_interface/astropy_TAP.html
- AllWISE source table name: `allwise_p3as_psd`
- TAP endpoint: https://irsa.ipac.caltech.edu/TAP/sync
