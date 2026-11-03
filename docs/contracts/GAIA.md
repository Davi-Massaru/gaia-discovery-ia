# Contract B — ESA Gaia DR3 TAP

**Endpoint:** `https://gea.esac.esa.int/tap-server/tap/sync`  
**Authentication:** none for public archive queries.  
**Role:** find possible Gaia stellar counterparts and their astrometric context.

## HTTP/TAP request

Use GET query parameters or POST `application/x-www-form-urlencoded`: `REQUEST=doQuery`, `LANG=ADQL`, `FORMAT=csv`, `QUERY=<ADQL>`.

```sql
SELECT TOP 20 source_id, ra, dec, pmra, pmdec, parallax,
              phot_g_mean_mag, ruwe
FROM gaiadr3.gaia_source
WHERE 1 = CONTAINS(
    POINT('ICRS',ra,dec),
    CIRCLE('ICRS',61.9648,-48.713,0.001388889)
)
```

The center coordinates in this example are sample values, **not a claim of a matched Fink event**. The radius shown is 5 arcseconds (`5/3600` degrees). Build the actual query from validated RA [- as degrees 0..360], Dec [-90..90] and a bounded allowed radius; do not concatenate uncontrolled user input.

## Fields mapped into `CatalogResult`

| Field | Meaning |
|---|---|
| `source_id` | Gaia DR3 source identifier (string in UI) |
| `ra`, `dec` | Reference-epoch ICRS coordinates (degrees) |
| `pmra`, `pmdec` | Proper motion components (mas/year); may be null |
| `parallax` | Parallax (mas); may be null or negative due to measurement noise |
| `phot_g_mean_mag` | Gaia G mean apparent magnitude, not LSST PSF flux |
| `ruwe` | Astrometric fit quality diagnostic, not a discovery classifier |

Calculate source-to-alert angular separation; do not equate nearest neighbor with same physical object. Gaia's astrometric reference epoch differs from Rubin observations, so nearby high-proper-motion stars need careful treatment.

## Response and status

A successful small TAP query returns CSV with columns and up to 20 catalog rows. Zero rows = `EMPTY`, invalid ADQL/HTTP/TAP error = `ERROR`. Preserve query parameters, archive name, time and normalized hits. The archive is **historical**, not a live image provider.

## Official references

- Programmatic access/TAP+ (public vs authenticated): https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access
- Gaia DR3 column reference: https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html
- Service endpoint: https://gea.esac.esa.int/tap-server/tap/sync
