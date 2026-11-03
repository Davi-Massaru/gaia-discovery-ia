"""Full native BPL + Workflow + persistence tests with isolated external fixtures."""
import json
import sys
import time
import traceback
from pathlib import Path
from unittest.mock import patch
import iris

sys.path.insert(0,'/opt/gaia/backend')
from gaia import store
from gaia.embedding import search_previous

if iris.gref('^GaiaConfig').get(['testFixtures'])!=1:
    raise RuntimeError('Refusing to run fixture tests against a real-data Production')

results={'scope':'DISPOSABLE_CONTAINER_ONLY','externalSources':'MOCKED','cases':[]}
output=Path('/opt/gaia/dist/e2e-isolated.json')


def wait(predicate, seconds=20):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        value=predicate()
        if value:return value
        time.sleep(.2)
    raise AssertionError('Timed out waiting for native BPL progress')


def start(tag,count=1):
    iris.gref('^GaiaConfig')['supportedTags']=json.dumps([tag])
    run_id=iris.cls('Gaia.Interop.DiscoveryService').StartRun(tag,count)
    return run_id


def completed(run_id):
    run=store.run_get(run_id)
    if run['status']=='FAILED':raise AssertionError('Native BPL failed: '+json.dumps(run))
    return run if run['status'] in ['COMPLETED','NO_ALERTS'] else None


def run_case(tag, count=1):
    run_id=start(tag,count)
    run=wait(lambda:completed(run_id))
    reports=[store.report_get(id) for id in run['reportIds']]
    case=dict(scenario=tag,runId=run_id,status=run['status'],reports=reports)
    results['cases'].append(case)
    print('SCIENTIFIC_RUN',tag,run['status'],len(reports),flush=True)
    return case


try:
    case=run_case('fixture-finish')
    assert len(case['reports'][0]['evidence']['decisionHistory'])==1
    assert all(c['status']=='NOT_REQUESTED' for c in case['reports'][0]['evidence']['catalogs'].values())
    case=run_case('fixture-adaptive')
    report=case['reports'][0]
    assert report['evidence']['actionsDone']==['GAIA','SIMBAD','IRSA']
    assert len(report['evidence']['decisionHistory'])==4
    assert report['evidence']['catalogs']['GAIA']['status']=='OK'
    assert report['evidence']['catalogs']['SIMBAD']['status']=='EMPTY'
    assert report['evidence']['catalogs']['IRSA']['status']=='OK'
    assert report['evidence']['catalogs']['GAIA']['matches'][0]['id']=='9007199254740993'
    assert report['assessment']=='CATALOG_CONTEXT_FOUND'
    for tag in ['fixture-invalid','fixture-missing','fixture-catalog-error']:
        case=run_case(tag)
        assert case['reports'][0]['assessment']=='INCONCLUSIVE'
    case=run_case('fixture-empty')
    assert case['status']=='NO_ALERTS' and not case['reports']

    # Two pending native tasks: run must finish before either human response.
    case=run_case('fixture-review',2)
    assert all(r['reviewStatus']=='PENDING' for r in case['reports'])
    for index,report in enumerate(case['reports']):
        tasks=list(iris.sql.exec('SELECT ID FROM EnsLib_Workflow.TaskResponse WHERE "%Subject"=?', 'Gaia report '+report['id']))
        assert len(tasks)==1
        task=iris.cls('EnsLib.Workflow.TaskResponse')._OpenId(str(tasks[0][0]))
        store.check_status(task.AssignTask('_SYSTEM'))
        store.check_status(task._Save())
        action='ACCEPT' if index==0 else 'REJECT'
        store.check_status(task.CompleteTask(action))
        store.check_status(task._Save())
    expected=['ACCEPTED_FOR_REVIEW','REJECTED']
    wait(lambda:all(store.report_get(r['id'])['reviewStatus']==status for r,status in zip(case['reports'],expected)))
    case['reports']=[store.report_get(r['id']) for r in case['reports']]
    case['nativeTaskActions']=expected
    print('BPL_NATIVE_REVIEW_REPLIES_OK',flush=True)

    # Exercise saved 1536-dimensional report vectors and production SQL, not a scalar SQL smoke check.
    vector=[1.0]+[0.0]*1535
    iris.sql.exec('UPDATE Gaia_Data.DiscoveryReport SET SearchEmbedding=NULL')
    eligible=[str(row[0]) for row in iris.sql.exec("SELECT TOP 3 ID FROM Gaia_Data.DiscoveryReport WHERE Assessment <> 'INCONCLUSIVE' ORDER BY ID DESC")]
    excluded=results['cases'][2]['reports'][0]['id']
    for report_id in eligible+[excluded]:
        iris.sql.exec('UPDATE Gaia_Data.DiscoveryReport SET SearchEmbedding=TO_VECTOR(?,FLOAT,1536) WHERE ID=?',json.dumps(vector),report_id)
    with patch('gaia.embedding.embed',return_value=vector):
        history=search_previous('ISOLATED TEST FIXTURE',3)
    assert len(history)==len(eligible) and all(abs(item['similarity']-1)<1e-6 for item in history)
    assert excluded not in [item['id'] for item in history]
    results['storedReportVectorSearch']={'status':'PASS','results':history,'embeddingProvider':'MOCKED'}

    # Disabled native operations legitimately queue messages. Remove the target
    # only in this disposable fixture Production to induce an actual dispatch error.
    production=iris.cls('Ens.Config.Production')._OpenId('Gaia.Production')
    reviewer=None
    for index in range(1,production.Items.Count()+1):
        item=production.Items.GetAt(index)
        if item.Name=='AstronomyReviewer':reviewer=item;break
    assert store.is_object(reviewer)
    production.RemoveItem(reviewer)
    store.check_status(production._Save())
    store.check_status(production.SaveToClass())
    store.check_status(iris.cls('Ens.Director').UpdateProduction(10,1))
    try:
        case=run_case('fixture-review-failure')
        wait(lambda:store.report_get(case['reports'][0]['id'])['reviewStatus']=='TASK_ERROR')
        case['reports']=[store.report_get(case['reports'][0]['id'])]
    finally:
        reviewer.Enabled=1
        production.Items.Insert(reviewer)
        store.check_status(production._Save())
        store.check_status(production.SaveToClass())
        store.check_status(iris.cls('Ens.Director').UpdateProduction(10,1))
    results['status']='PASS'
except Exception as error:
    results['status']='FAIL'
    results['error']=traceback.format_exc()
    results['nativeErrors']=[row[0] for row in iris.sql.exec('SELECT TOP 8 Text FROM Ens_Util.Log WHERE Type=2 ORDER BY ID DESC')]
    print(results['error'],flush=True)
    print(json.dumps(results['nativeErrors']),flush=True)
finally:
    output.write_text(json.dumps(results,indent=2))
    print('ISOLATED_E2E_RESULT',results['status'],flush=True)
