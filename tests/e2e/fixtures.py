"""External-source fixtures, ONLY for the disposable gaia-e2e-tests container.

Nothing here is imported by production application code or packaged by IPM.
All generated observations and conclusions are explicitly test fixtures.
"""
import json
from types import SimpleNamespace
from gaia.runtime import dumps, object_request, apply_agent, failure, catalog


def fink(request, response):
    from gaia.store import run_update
    state = json.loads(request.PayloadJSON)
    if request.Kind == 'LIST_BY_TAG':
        run_update(state['runId'], status='RUNNING')
        state['objects'] = [] if state['tag'] == 'fixture-empty' else [f'FIXTURE-{i}' for i in range(state['count'])]
        state['reportIds'] = []
        run_update(state['runId'], total=len(state['objects']))
        response.Status = 'OK' if state['objects'] else 'EMPTY'
    else:
        current = state['current']
        current['observation'].update(diaSourceId='FIXTURE-DETECTION',raDeg=1.0,decDeg=2.0,
                                      observedMjdTai=60000.0,psfFlux=1.0,psfFluxErr=1.0)
        current['testFixture'] = True
        if state['tag'] == 'fixture-missing':
            failure(current, 'INCOMPLETE_CUTOUTS')
        response.Status = 'OK'
    response.PayloadJSON = dumps(state)


def agent(request, response):
    state = json.loads(request.PayloadJSON)
    done = state['current']['actionsDone']
    scenario = state['tag']
    action = 'FINISH'
    assessment = 'INCONCLUSIVE'
    if scenario == 'fixture-adaptive':
        action = ['CHECK_GAIA','CHECK_SIMBAD','CHECK_IRSA','FINISH'][len(done)]
        assessment = 'CATALOG_CONTEXT_FOUND' if action == 'FINISH' else None
    elif scenario == 'fixture-catalog-error' and not done:
        action, assessment = 'CHECK_GAIA', None
    elif scenario in ('fixture-review','fixture-review-failure'):
        assessment = 'REVIEW_CANDIDATE'
    decision = dict(hypothesis='TEST FIXTURE hypothesis revision '+str(len(done)),alternative='TEST FIXTURE alternative',
                    next_action=action,question='' if action=='FINISH' else 'TEST FIXTURE question?',
                    reason='TEST FIXTURE ONLY. Not a scientific conclusion.',assessment=assessment)
    response.PayloadJSON = apply_agent(request.PayloadJSON, 'invalid JSON' if scenario=='fixture-invalid' else dumps(decision))
    response.Status = 'OK'


def tap(code, request, response):
    state = json.loads(request.PayloadJSON)
    def transport(*args):
        if state['tag']=='fixture-catalog-error':
            return dumps(dict(status='ERROR',httpStatus=503,errorCode='TEST_FIXTURE_UNAVAILABLE'))
        bodies = {
            'GAIA': 'source_id,ra,dec,parallax,pmra,pmdec,phot_g_mean_mag,ruwe\n9007199254740993,1,2,1,1,1,15,1\n',
            'SIMBAD': 'main_id,ra,dec,otype\n',
            'IRSA': 'designation,ra,dec,w1mpro,w2mpro,ph_qual\nFIXTURE,1,2,11,10,AA\n',
        }
        return dumps(dict(status='OK',httpStatus=200,csvBody=bodies[code]))
    catalog(SimpleNamespace(Adapter=SimpleNamespace(_DispatchMethod=transport)),code,request,response)
