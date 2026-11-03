#!/usr/bin/env python3
"""Public, anonymous API smoke check for Gaia Discovery AI.

Run on an Internet-connected development machine. This checks HTTP contracts and
field availability; it does not classify or confirm astronomical objects.
"""
import csv
import io
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

FINK = "https://api.lsst.fink-portal.org/api/v1"
TAP = {
    "GAIA": "https://gea.esac.esa.int/tap-server/tap/sync",
    "SIMBAD": "https://simbad.cds.unistra.fr/simbad/sim-tap/sync",
    "IRSA": "https://irsa.ipac.caltech.edu/TAP/sync",
}
TIMEOUT = 25


def fetch(url, body=None, as_json=False):
    headers = {"User-Agent": "GaiaDiscoveryAI-ContractCheck/1.0"}
    data = None
    if body is not None:
        if as_json:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        else:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            data = urlencode(body).encode("utf-8")
    req = Request(url, data=data, headers=headers)
    with urlopen(req, timeout=TIMEOUT) as resp:
        return resp.status, resp.headers.get("Content-Type", ""), resp.read()


def fink_post(path, payload):
    status, _, raw = fetch(FINK + path, payload, as_json=True)
    obj = json.loads(raw.decode("utf-8"))
    return status, obj


def check_tap(name, ra, dec):
    radius = 10 / 3600 if name == "IRSA" else 5 / 3600
    position = f"CIRCLE('ICRS',{ra:.8f},{dec:.8f},{radius:.9f})"
    if name == "GAIA":
        query = ("SELECT TOP 5 source_id,ra,dec,parallax,pmra,pmdec,"
                 "phot_g_mean_mag,ruwe FROM gaiadr3.gaia_source "
                 f"WHERE 1=CONTAINS(POINT('ICRS',ra,dec),{position})")
    elif name == "SIMBAD":
        query = ("SELECT TOP 5 main_id,ra,dec,otype FROM basic "
                 f"WHERE 1=CONTAINS(POINT('ICRS',ra,dec),{position})")
    else:
        query = ("SELECT TOP 5 designation,ra,dec,w1mpro,w2mpro,ph_qual "
                 "FROM allwise_p3as_psd "
                 f"WHERE 1=CONTAINS(POINT('ICRS',ra,dec),{position})")
    status, content_type, raw = fetch(TAP[name], {
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query
    })
    if raw.lstrip().startswith(b"<"):
        raise RuntimeError(f"Expected CSV, received XML/TAP error: {raw[:180]!r}")
    body = raw.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(body)))
    if not rows or not rows[0]:
        raise RuntimeError("No CSV header")
    print(f"  {name}: HTTP {status}, {len(rows) - 1} rows, fields={rows[0]}")


def main():
    failures = []
    print("Gaia Discovery AI — public API check", datetime.now(timezone.utc).isoformat())
    try:
        status, _, raw = fetch(FINK + "/tags")
        tags = json.loads(raw.decode("utf-8"))
        print(f"  FINK GET /tags: HTTP {status}; {len(tags)} tags")
    except (HTTPError, URLError, TimeoutError, ValueError) as err:
        print("  ERROR Fink tags:", err)
        failures.append("FINK_TAGS")
        tags = {}

    try:
        _, schema = fink_post("/schema", {"endpoint": "/api/v1/sources"})
        print("  FINK POST /schema: OK; response type", type(schema).__name__)
    except (HTTPError, URLError, TimeoutError, ValueError) as err:
        print("  ERROR Fink schema:", err)
        failures.append("FINK_SCHEMA")

    coordinates = None
    if tags:
        for tag in ("extragalactic_new_candidate", "in_tns", "mdwarf_flare"):
            if not tags.get(tag, {}).get("API support", False):
                continue
            try:
                status, alerts = fink_post("/tags", {
                    "tag": tag, "n": "3", "columns": "r:diaObjectId"
                })
                if not isinstance(alerts, list):
                    raise ValueError("Expected JSON array of alerts")
                ids = list(dict.fromkeys(str(item["r:diaObjectId"]) for item in alerts
                                             if item.get("r:diaObjectId") is not None))
                print(f"  FINK POST /tags: HTTP {status}; tag={tag}; ids={len(ids)}")
                if not ids:
                    continue
                object_id = ids[0]
                _, sources = fink_post("/sources", {
                    "diaObjectId": object_id,
                    "columns": "r:diaObjectId,r:diaSourceId,r:ra,r:dec,r:midpointMjdTai,r:psfFlux,r:psfFluxErr",
                    "output-format": "json"
                })
                if not isinstance(sources, list) or not sources:
                    raise ValueError("No detection rows for sampled object")
                source = next((row for row in sources if row.get("r:diaSourceId")
                              and row.get("r:ra") is not None
                              and row.get("r:dec") is not None), None)
                if source is None:
                    raise ValueError("No sampled row with source ID and coordinates")
                coordinates = (float(source["r:ra"]), float(source["r:dec"]))
                source_id = str(source["r:diaSourceId"])
                print(f"  FINK POST /sources: object={object_id}; detection={source_id}; coordinates={coordinates}")
                for kind in ("Science", "Template", "Difference"):
                    status, ctype, png = fetch(FINK + "/cutouts", {
                        "diaSourceId": source_id, "kind": kind
                    }, as_json=True)
                    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
                        raise ValueError(f"{kind} did not return PNG; content_type={ctype}; head={png[:40]!r}")
                    print(f"  FINK POST /cutouts: {kind} HTTP {status}; {len(png)} PNG bytes")
                break
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as err:
                print(f"  ERROR Fink tag={tag}: {err}")
                failures.append("FINK_" + tag.upper())

    if coordinates is None:
        print("  SKIPPED TAP cross-match: no usable live Fink source coordinates found")
    else:
        ra, dec = coordinates
        for name in TAP:
            try:
                check_tap(name, ra, dec)
            except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as err:
                print(f"  ERROR {name} TAP: {err}")
                failures.append(name)

    print("Summary:", "PASS" if not failures and coordinates else "PARTIAL/FAILED")
    if failures:
        print("Failures:", ", ".join(failures))
    return 0 if not failures and coordinates else 1


if __name__ == "__main__":
    sys.exit(main())
