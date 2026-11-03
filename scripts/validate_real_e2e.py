"""Authenticated, real-data WSGI -> Production -> persisted report verification.

Run inside the development IRIS instance. No mocked source or AI decision is used.
"""
import base64
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen
import iris

sys.path.insert(0,'/opt/gaia/backend')
from gaia import store
from gaia.science import validate_png,parse_catalog,query
creds=dict(line.split('=',1) for line in Path('/opt/gaia/.env.runtime').read_text().splitlines())
auth='Basic '+base64.b64encode((creds['GAIA_TEST_USERNAME']+':'+creds['GAIA_TEST_PASSWORD']).encode()).decode()
result={'scope':'REAL_EXTERNAL_DATA','checks':{},'reports':[]}


def http(path,body=None):
    request=Request('http://localhost:52773/gaia'+path,data=None if body is None else json.dumps(body).encode(),
                    headers={'Authorization':auth,'Content-Type':'application/json'})
    try:
        with urlopen(request,timeout=15) as response:return response.status,response.read(),dict(response.headers)
    except HTTPError as error:return error.code,error.read(),dict(error.headers)


try:
    tags=json.loads(iris.gref('^GaiaConfig').get(['supportedTags']))
    tag='extragalactic_new_candidate' if 'extragalactic_new_candidate' in tags else tags[0]
    run_id=os.environ.get('GAIA_VERIFY_RUN_ID')
    if run_id:
        previous=json.loads(Path('/opt/gaia/dist/e2e-real.json').read_text())
        if previous.get('runId')==run_id:result['checks'].update(previous.get('checks',{}))
    else:
        started=time.monotonic()
        status,body,_=http('/api/discoveries/run',{'tag':tag,'count':int(os.environ.get('GAIA_VERIFY_COUNT','2'))})
        result['checks']['asyncAcceptance']={'httpStatus':status,'seconds':round(time.monotonic()-started,3)}
        assert status==202
        run_id=json.loads(body)['runId']
    result['runId']=run_id
    deadline=time.monotonic()+600
    while time.monotonic()<deadline:
        status,body,_=http('/api/discoveries/runs/'+run_id)
        assert status==200
        run=json.loads(body)
        if run['status'] in ('COMPLETED','FAILED','NO_ALERTS'):break
        time.sleep(1)
    result['run']=run
    assert run['status'] in ('COMPLETED','NO_ALERTS'),run
    for report_id in run['reportIds']:
        status,body,_=http('/api/discoveries/'+report_id)
        assert status==200
        report=json.loads(body)
        assert type(report['diaObjectId']) is str and type(report['diaSourceId']) is str
        assert not report['evidence'].get('testFixture')
        native=iris.cls('Gaia.Data.DiscoveryReport')._OpenId(report_id)
        images={}
        for kind in ('science','template','difference'):
            status,data,headers=http('/api/discoveries/'+report_id+'/images/'+kind)
            if report['images'][kind]:
                assert status==200 and headers.get('Content-Type','').startswith('image/png')
                validate_png(data)
                assert data==store.stream_bytes(getattr(native,kind.title()+'PNG'))
                images[kind]={'byteExact':True,'bytes':len(data)}
            else:assert status==404
        traces=list(iris.sql.exec('SELECT COUNT(*) FROM Ens.MessageHeader WHERE SessionId=?',report['interopSessionId']))[0][0]
        assert traces>0
        result['reports'].append(dict(id=report_id,diaObjectId=report['diaObjectId'],diaSourceId=report['diaSourceId'],
                                     assessment=report['assessment'],errors=report['evidence'].get('errors',[]),
                                     executionStatus=report['evidence'].get('executionStatus'),
                                     failureStage=report['evidence'].get('failureStage'),failureCode=report['evidence'].get('failureCode'),
                                     technicalFailures=report['evidence'].get('technicalFailures',[]),
                                     historyStatus=report['evidence'].get('historyStatus'),embeddingStatus=report['evidence'].get('embeddingStatus'),
                                     validDecisions=len(report['evidence'].get('decisionHistory',[])),
                                     decisions=report['evidence'].get('decisionHistory',[]),
                                     catalogs=report['evidence'].get('catalogs',{}),
                                     images=images,sessionId=report['interopSessionId'],traceMessages=traces))
        print('REAL_REPORT_VERIFIED',report_id,report['assessment'],flush=True)
    # Actual shared Java transport, parsed with the same catalog implementation.
    adapter=iris.cls('Gaia.Interop.Adapters.TAPOutboundAdapter')._New()
    store.check_status(adapter.OnInit())
    catalog_checks={}
    for code in ('GAIA','SIMBAD','IRSA'):
        _,adql,radius=query(code,34.8900102405,-6.0029708111)
        raw=json.loads(adapter._DispatchMethod('query',code,adql,20,30))
        normalized=parse_catalog(code,raw,34.8900102405,-6.0029708111,adql,radius)
        catalog_checks[code]=dict(status=normalized['status'],httpStatus=raw['httpStatus'],rows=len(normalized['matches']),
                                 error=normalized.get('error'),errorType=raw.get('errorType'),elapsedMs=raw['elapsedMs'])
        print('REAL_JAVA_TAP',code,catalog_checks[code],flush=True)
    result['catalogs']=catalog_checks
    for path,expected in [('/api/discoveries?limit=1&offset=0',200),('/api/discoveries/999999',404),('/api/discoveries?limit=0',400),
                          ('/api/discoveries/runs/unknown',404),('/api/discoveries/1/images/nope',404),('/',200),('/assets/app.js',200)]:
        status,_,_=http(path)
        assert status==expected,(path,status)
        result['checks'][path]=status
    # Semantic search is optional: failure must not affect report readability.
    status,_,_=http('/api/discoveries?search=astronomical%20transient')
    result['checks']['realSemanticSearchHTTP']=status
    assert status in (200,503)
    result['status']='PASS_WITH_EXTERNAL_LIMITATIONS' if any(r['errors'] or r['technicalFailures'] for r in result['reports']) or any(c['status']=='ERROR' for c in catalog_checks.values()) else 'PASS'
except Exception:
    import traceback
    result['status']='FAIL'
    result['error']=traceback.format_exc()
    print(result['error'],flush=True)
finally:
    Path('/opt/gaia/dist/e2e-real.json').write_text(json.dumps(result,indent=2))
    print('REAL_E2E_RESULT',result['status'],flush=True)
