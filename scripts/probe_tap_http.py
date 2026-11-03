"""Public HTTPS controls for documented TAP services; not a production bypass."""
import concurrent.futures
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, '/opt/gaia/backend')
from gaia.science import query, parse_catalog


def probe(case):
    code, endpoint, method = case
    _, adql, radius = query(code, 34.8900102405, -6.0029708111)
    payload = urlencode(dict(REQUEST='doQuery', LANG='ADQL', FORMAT='csv', MAXREC=20, QUERY=adql)).encode()
    started = time.monotonic()
    result = dict(catalog=code, endpoint=endpoint, method=method)
    try:
        request = Request(endpoint+('?' + payload.decode() if method == 'GET' else ''),
                          data=payload if method == 'POST' else None,
                          headers={'Content-Type':'application/x-www-form-urlencoded','Accept':'text/csv','User-Agent':'GaiaDiscoveryAI/1.0'})
        with urlopen(request, timeout=45) as response:
            body = response.read(1024*1024).decode('utf-8')
            normalized = parse_catalog(code, dict(status='OK',httpStatus=response.status,csvBody=body),
                                       34.8900102405,-6.0029708111,adql,radius)
            result.update(httpStatus=response.status,contentType=response.headers.get('Content-Type'),
                          status=normalized['status'],matches=len(normalized['matches']))
    except Exception as error:
        result.update(status='ERROR',errorType=type(error).__name__,httpStatus=error.code if isinstance(error,HTTPError) else 0)
    result['elapsedMs'] = round((time.monotonic()-started)*1000)
    print(json.dumps(result),flush=True)
    return result


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(probe, [
        ('SIMBAD','https://simbad.cfa.harvard.edu/simbad/sim-tap/sync','POST'),
        ('GAIA','https://gea.esac.esa.int/tap-server/tap/sync','GET')]))
Path('/opt/gaia/dist/tap-http-controls.json').write_text(json.dumps(results,indent=2))
