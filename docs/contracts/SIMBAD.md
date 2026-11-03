# Contract C — CDS SIMBAD TAP

**Endpoint:** `https://simbad.cds.unistra.fr/simbad/sim-tap/sync`  
**Authentication:** none for public TAP search.  
**Role:** identify published astronomical objects **near** the Rubin alert and their types.

The transport may retry a failed primary request through the [official CfA/Harvard SIMBAD mirror](https://simbad.cfa.harvard.edu/simbad/), using `/simbad/sim-tap/sync`. The selected endpoint and both attempts are preserved; no TLS verification is disabled.

## HTTP/TAP request

POST `application/x-www-form-urlencoded` with `REQUEST=doQuery`, `LANG=ADQL`, `FORMAT=csv`, `QUERY=<ADQL>` (or equivalent GET). The official SIMBAD URL guide includes TAP examples.

```sql
SELECT TOP 20 main_id, ra, dec, otype
FROM basic
WHERE 1 = CONTAINS(
    POINT('ICRS',ra,dec),
    CIRCLE('ICRS',61.9648,-48.713,0.001388889)
)
```

Example cone radius = 5 arcseconds, supplied as 5/3600 degrees. The example coordinates are illustrative. Validate the returned columns and parse CSV per actual TAP response.

## Fields mapped into `CatalogResult`

| Field | Meaning |
|---|---|
| `main_id` | SIMBAD preferred astronomical identifier |
| `ra`, `dec` | ICRS position in degrees |
| `otype` | Astronomical type label/code used by SIMBAD |

SIMBAD compiles published object information. A `main_id` for a nearby galaxy **does not** establish that the transient belongs to that galaxy. Keep separation, type and ambiguity. No hit means "not found in this query", not new discovery.

## Response and status

`OK` for parsed rows, `EMPTY` for valid zero-row response, `ERROR` for timeout, TAP error or malformed response. Limit response to 20 rows. Preserve query and service reference. This endpoint is a catalog lookup, **not an image provider**.

## Official references

- SIMBAD TAP query-by-URL examples: https://simbad.u-strasbg.fr/Pages/guide/sim-url.htx
- SIMBAD contents/identification caveats: https://simbad.cds.unistra.fr/Pages/guide/ch02.htx
- Official TAP service: https://simbad.cds.unistra.fr/simbad/sim-tap/sync
