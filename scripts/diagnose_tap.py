"""Compare real native Java PEX TAP calls with Python connectivity controls."""
import concurrent.futures
import json
import socket
import sys
import time
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen, getproxies
from urllib.error import HTTPError
import iris

sys.path.insert(0, '/opt/gaia/backend')
from gaia.science import query, parse_catalog
from gaia import store

RA, DEC = 34.8900102405, -6.0029708111
result = {'coordinates': [RA, DEC], 'proxySchemes': sorted(getproxies()), 'catalogs': {}}


def control(code):
    endpoint, adql, _ = query(code, RA, DEC)
    started = time.monotonic()
    data = urlencode(dict(REQUEST='doQuery', LANG='ADQL', FORMAT='csv', MAXREC=20, QUERY=adql)).encode()
    output = {}
    try:
        addresses = socket.getaddrinfo(urlsplit(endpoint).hostname, 443, type=socket.SOCK_STREAM)
        output['addressFamilies'] = sorted(set('IPv6' if row[0] == socket.AF_INET6 else 'IPv4' for row in addresses))
        with urlopen(Request(endpoint, data=data, headers={'Content-Type':'application/x-www-form-urlencoded',
                      'Accept':'text/csv', 'User-Agent':'GaiaDiscoveryAI/1.0'}), timeout=30) as response:
            body = response.read(1024*1024)
            output.update(httpStatus=response.status, contentType=response.headers.get('Content-Type'),
                          bytes=len(body), lines=len(body.splitlines()))
    except Exception as error:
        output.update(errorType=type(error).__name__, httpStatus=error.code if isinstance(error, HTTPError) else 0)
        reason = getattr(error, 'reason', None)
        if reason is not None: output['reasonType'] = type(reason).__name__
    output['elapsedMs'] = round((time.monotonic()-started)*1000)
    return output


adapter = iris.cls('Gaia.Interop.Adapters.TAPOutboundAdapter')._New()
store.check_status(adapter.OnInit())
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    controls = {code: executor.submit(control, code) for code in ['GAIA', 'SIMBAD']}
    for code in ['GAIA', 'SIMBAD']:
        endpoint, adql, radius = query(code, RA, DEC)
        raw = json.loads(adapter._DispatchMethod('query', code, adql, 20, 45 if code == 'GAIA' else 30))
        normalized = parse_catalog(code, raw, RA, DEC, adql, radius)
        result['catalogs'][code] = {'endpoint':endpoint, 'query':adql,
            'javaPEX': {key:value for key,value in raw.items() if key != 'csvBody'},
            'normalizedStatus':normalized['status'], 'matches':len(normalized['matches']),
            'pythonControl':controls[code].result()}
        print(code, json.dumps(result['catalogs'][code]), flush=True)
Path('/opt/gaia/dist/tap-diagnosis.json').write_text(json.dumps(result, indent=2))
