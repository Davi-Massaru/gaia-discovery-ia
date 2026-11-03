"""Run inside Embedded Python in the configured application namespace."""
import hashlib
import json
import sys
from pathlib import Path
import iris

home = iris.gref('^GaiaConfig').get(['home']) or '/opt/gaia'
sys.path.insert(0, home+'/backend')
sys.path.insert(0, '/opt/gaia/scripts')
from gaia.store import stream_bytes, report_get
from gaia.science import query, parse_catalog
from http_smoke import request

evidence = {'build': iris.system.Version.GetVersion(), 'checks': {}}
checks = evidence['checks']
checks['vectorSQL'] = list(iris.sql.exec("SELECT VECTOR_COSINE(TO_VECTOR('[1,0]',FLOAT,2),TO_VECTOR('[1,0]',FLOAT,2))"))[0][0] == 1
ids = list(iris.sql.exec('SELECT TOP 1 ID FROM Gaia_Data.DiscoveryReport ORDER BY ID DESC'))
if ids:
    report_id = str(ids[0][0])
    record = report_get(report_id)
    checks['persistedReport'] = dict(id=report_id, sessionId=record['interopSessionId'], assessment=record['assessment'])
    native = iris.cls('Gaia.Data.DiscoveryReport')._OpenId(report_id)
    for kind in ['science','template','difference']:
        status, body = request('/api/discoveries/'+report_id+'/images/'+kind)
        stored = stream_bytes(getattr(native,kind.title()+'PNG'))
        checks[kind+'ByteExact'] = status==200 and body==stored
        assert checks[kind+'ByteExact']
    adapter = iris.cls('Gaia.Interop.Adapters.TAPOutboundAdapter')._New()
    adapter.OnInit()
    obs=record['evidence']['observation']
    for code in ['GAIA','SIMBAD','IRSA']:
        endpoint,adql,radius=query(code,obs['raDeg'],obs['decDeg'])
        transport=json.loads(adapter._DispatchMethod('query',code,adql,20,10))
        result=parse_catalog(code,transport,obs['raDeg'],obs['decDeg'],adql,radius)
        checks['PEX_'+code]={'status':result['status'],'rows':len(result['matches']),
                             'httpStatus':transport['httpStatus'],'error':result.get('error'), 'elapsedMs':transport['elapsedMs']}
        print('PEX',code,checks['PEX_'+code],flush=True)
for route, expected in [('/api/discoveries',200),('/api/discoveries/999999',404),('/api/discoveries?limit=0',400),('/',200),('/assets/app.js',200),('/assets/style.css',200)]:
    status,_=request(route)
    checks['HTTP '+route]=status
    assert status==expected
status,body=request('/api/discoveries/run',{'tag':'extragalactic_new_candidate','count':1})
checks['HTTP async run']=status
assert status==202
checks['lastRunId']=json.loads(body)['runId']
Path('/opt/gaia/dist/runtime-evidence.json').write_text(json.dumps(evidence,indent=2))
print('RUNTIME_EVIDENCE_SAVED',flush=True)
