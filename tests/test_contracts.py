import json
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from gaia.science import coordinates, separation, query, parse_catalog, validate_decision, observation, validate_png
from gaia.runtime import apply_agent, object_request, failure, catalog, fink, agent_prompt
from gaia import store
from app import app


class DiagnosticTests(unittest.TestCase):
    def test_provider_diagnostic_discards_private_details(self):
        from gaia.diagnostics import diagnostic
        code, details = diagnostic('organization_spend_limit_exceeded secret-key private prompt')
        self.assertEqual(code, 'OPENAI_SPEND_LIMIT_EXCEEDED')
        self.assertNotIn('secret', json.dumps(details))
        self.assertNotIn('prompt', json.dumps(details))

    def test_optional_failure_preserves_fatal_reason(self):
        from gaia.diagnostics import record_failure
        evidence = {}
        record_failure(evidence, 'AI_HUB_CHAT', 'OPENAI_SPEND_LIMIT_EXCEEDED', fatal=True)
        record_failure(evidence, 'REPORT_EMBEDDING', 'PROVIDER_TIMEOUT')
        self.assertEqual(evidence['executionStatus'], 'FAILED')
        self.assertEqual(evidence['failureStage'], 'AI_HUB_CHAT')
        self.assertEqual(len(evidence['technicalFailures']), 2)

    def test_empty_history_never_calls_provider(self):
        from types import SimpleNamespace
        from gaia.embedding import search_previous
        iris = SimpleNamespace(sql=SimpleNamespace(exec=lambda *a: []))
        with patch.dict(sys.modules, {'iris': iris}), patch('gaia.embedding.embed') as provider:
            self.assertEqual(search_previous('any observation'), [])
            provider.assert_not_called()

    def test_indexed_history_preserves_provider_failure(self):
        from types import SimpleNamespace
        from gaia.embedding import search_previous
        iris = SimpleNamespace(sql=SimpleNamespace(exec=lambda *a: [('1',)]))
        with patch.dict(sys.modules, {'iris': iris}), patch('gaia.embedding.embed', side_effect=RuntimeError('OPENAI_SPEND_LIMIT_EXCEEDED')):
            with self.assertRaisesRegex(RuntimeError, 'OPENAI_SPEND_LIMIT_EXCEEDED'):
                search_previous('any observation')

    def test_inconclusive_semantic_filter_never_calls_provider(self):
        from gaia.embedding import search_previous
        with patch.dict(sys.modules, {'iris': object()}), patch('gaia.embedding.embed') as provider:
            self.assertEqual(search_previous('any observation',status='INCONCLUSIVE'), [])
            provider.assert_not_called()

    def test_embedding_http_failure_is_sanitized(self):
        import io
        from urllib.error import HTTPError
        from gaia.embedding import embed
        error = HTTPError('https://api.openai.com/v1/embeddings', 429, 'private', {},
                          io.BytesIO(b'{"error":{"code":"organization_spend_limit_exceeded","message":"private secret"}}'))
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-only'}), patch('gaia.embedding.urlopen', side_effect=error):
            with self.assertRaisesRegex(RuntimeError, '^OPENAI_SPEND_LIMIT_EXCEEDED$'):
                embed('test')


class ScienceTests(unittest.TestCase):
    def test_catalog_transport_provenance_and_sanitization(self):
        endpoint, adql, radius = query('SIMBAD',1,2)
        mirror='https://simbad.cfa.harvard.edu/simbad/sim-tap/sync'
        raw=dict(status='OK',httpStatus=200,elapsedMs=6010,endpoint=mirror,csvBody='main_id,ra,dec,otype\n',
                 attempts=[dict(endpoint=endpoint,errorType='SocketTimeoutException',errorCode='TAP_TIMEOUT',failurePhase='CONNECT_TLS',elapsedMs=5000),
                           dict(endpoint=mirror,httpStatus=200,elapsedMs=1010)],privateDetail='not exported')
        result=parse_catalog('SIMBAD',raw,1,2,adql,radius)
        self.assertEqual(result['status'],'EMPTY')
        self.assertEqual(result['sanitized_endpoint'],mirror)
        self.assertEqual(len(result['transport']['attempts']),2)
        self.assertNotIn('privateDetail',json.dumps(result))
        raw['endpoint']='https://untrusted.example/tap'
        self.assertEqual(parse_catalog('SIMBAD',raw,1,2,adql,radius)['error'],'INVALID_TAP_ENDPOINT')

    def test_invalid_fink_detection_identifiers(self):
        row={'r:diaObjectId':'123','r:ra':1,'r:dec':2,'r:midpointMjdTai':60000,'r:psfFlux':1,'r:psfFluxErr':1}
        for identifier in [None,'',True,123.0,'1e15','None']:
            row['r:diaSourceId']=identifier
            with self.assertRaises(ValueError):observation(row,'123')

    def test_png_integrity(self):
        import struct,zlib
        def chunk(kind,body):return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)
        png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,0,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\x00'))+chunk(b'IEND',b'')
        validate_png(png)
        for invalid in [png[:8],png[:-1],png+b'junk',png[:-5]+b'xxxxx']:
            with self.assertRaises(ValueError):validate_png(invalid)
    def test_spherical_edges(self):
        self.assertAlmostEqual(separation(359.999, 0, 0.001, 0), 7.2, places=6)
        self.assertAlmostEqual(separation(0, 90, 180, 90), 0, places=6)
        self.assertAlmostEqual(separation(0, 0, 180, 0), 648000, places=6)

    def test_coordinate_bounds(self):
        for ra, dec in [(360, 0), (-1, 0), (0, 91), (math.nan, 0), (True, 0)]:
            with self.assertRaises(ValueError): coordinates(ra, dec)

    def test_adql_bounds(self):
        self.assertIn('TOP 20', query('GAIA', 1, 2)[1])
        for radius in [0, -1, 1000, math.inf]:
            with self.assertRaises(ValueError): query('GAIA', 1, 2, radius)

    def test_empty_is_not_error(self):
        _, adql, radius = query('SIMBAD', 1, 2)
        args = ('SIMBAD', dict(status='OK', httpStatus=200, csvBody='main_id,ra,dec,otype\n'), 1, 2, adql, radius)
        self.assertEqual(parse_catalog(*args)['status'], 'EMPTY')
        self.assertEqual(parse_catalog('SIMBAD', dict(status='ERROR'), 1, 2, adql, radius)['status'], 'ERROR')
        for body in ['<VOTABLE>ERROR</VOTABLE>', 'error\nbad query', 'main_id,ra,dec,otype\nstar,400,2,*']:
            self.assertEqual(parse_catalog('SIMBAD', dict(status='OK', httpStatus=200, csvBody=body), 1, 2, adql, radius)['status'], 'ERROR')

    def test_identifiers_and_proximity(self):
        _, adql, radius = query('GAIA', 1, 2)
        raw = 'source_id,ra,dec,parallax,pmra,pmdec,phot_g_mean_mag,ruwe\n9007199254740993,1,2,1,5,2,15,1\n'
        result = parse_catalog('GAIA', dict(status='OK', httpStatus=200, csvBody=raw), 1, 2, adql, radius)
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(result['matches'][0]['id'], '9007199254740993')
        self.assertEqual(result['matches'][0]['separationArcsec'], 0)
        self.assertIn('epoch', result['matches'][0])

    def test_observation_requires_real_measurements(self):
        row = {'r:diaObjectId':'9007199254740993','r:diaSourceId':'9007199254740994','r:ra':1,'r:dec':2,
               'r:midpointMjdTai':60000,'r:psfFlux':-10,'r:psfFluxErr':2}
        self.assertEqual(observation(row,row['r:diaObjectId'])['diaSourceId'],'9007199254740994')
        with self.assertRaises(ValueError): observation(row,'wrong object')
        row['r:psfFluxErr']=None
        with self.assertRaises(ValueError): observation(row,row['r:diaObjectId'])


class DecisionTests(unittest.TestCase):
    def test_context_is_valid_json_or_rejected(self):
        state=json.loads(object_request(json.dumps(dict(runId='test',tag='test',objects=['123'])),0))
        self.assertEqual(json.loads(agent_prompt(state))['remainingDecisions'],4)
        state['current']['oversizedUntrustedValue']='x'*60000
        with self.assertRaisesRegex(ValueError,'AI_CONTEXT_TOO_LARGE'):agent_prompt(state)
    def decision(self, action='FINISH'):
        return dict(hypothesis='Insufficient evidence',alternative=None,next_action=action,
                    question='' if action=='FINISH' else 'Stellar counterpart?',reason='Preliminary uncertainty.',
                    assessment='INCONCLUSIVE' if action=='FINISH' else None)

    def test_finish_without_catalog(self):
        self.assertEqual(validate_decision(self.decision(),[],0)['next_action'],'FINISH')

    def test_failed_catalog_cannot_become_novelty_evidence(self):
        state=json.loads(object_request(json.dumps(dict(runId='test',tag='test',objects=['123'])),0))
        state['current']['catalogs']['SIMBAD']['status']='ERROR'
        decision=self.decision();decision['assessment']='REVIEW_CANDIDATE'
        result=json.loads(apply_agent(json.dumps(state),json.dumps(decision)))['current']
        self.assertEqual(result['assessment'],'INCONCLUSIVE')
        self.assertEqual(result['assessmentAdjustment'],'INCOMPLETE_CATALOG_EVIDENCE')
        self.assertEqual(result['decisionHistory'][0]['assessment'],'REVIEW_CANDIDATE')

    def test_bounds_and_duplicates(self):
        for done, count in [(['GAIA'],1), (['GAIA','SIMBAD','IRSA'],3),([],4)]:
            with self.assertRaises(ValueError): validate_decision(self.decision('CHECK_GAIA'),done,count)
        self.assertEqual(validate_decision(self.decision(),['GAIA','SIMBAD','IRSA'],3)['assessment'],'INCONCLUSIVE')

    def test_schema_and_recovery(self):
        import jsonschema
        bad=self.decision();bad['extra']='disallowed'
        with self.assertRaises(jsonschema.ValidationError):validate_decision(bad,[],0)
        state=object_request(json.dumps(dict(runId='test',tag='test',objects=['123'])),0)
        for raw in ['', 'not json', json.dumps(bad)]:
            value=json.loads(apply_agent(state,raw))['current']
            self.assertEqual(value['assessment'],'INCONCLUSIVE')
            self.assertEqual(value['next_action'],'FINISH')

    def test_only_chosen_catalog(self):
        from types import SimpleNamespace
        state=json.loads(object_request(json.dumps(dict(runId='test',tag='test',objects=['123'])),0))
        state['current']['observation'].update(raDeg=1,decDeg=2)
        state['current']['next_action']='CHECK_GAIA'
        with self.assertRaises(ValueError):catalog(None,'SIMBAD',SimpleNamespace(Kind='CATALOG_QUERY',PayloadJSON=json.dumps(state)),SimpleNamespace())

    def test_embedding_failure_does_not_invalidate_save(self):
        from types import SimpleNamespace
        report=SimpleNamespace(_Save=lambda:1,_Id=lambda:'123')
        iris=SimpleNamespace(cls=lambda name:SimpleNamespace(_New=lambda:report))
        state=json.loads(object_request(json.dumps(dict(runId='test',tag='test',objects=['123'])),0))
        state['current']['assessment']='REVIEW_CANDIDATE'
        with patch('gaia.store.iris_module',return_value=iris),patch('gaia.store.run_update'),patch('gaia.embedding.embed',side_effect=TimeoutError):
            result=store.save_report(state,'42')
        self.assertEqual(result['reportId'],'123')
        self.assertEqual(report.Assessment,'REVIEW_CANDIDATE')
        self.assertEqual(report.ReviewStatus,'PENDING')
        self.assertEqual(result['current']['embeddingStatus'],'ERROR')

    def test_inconclusive_save_skips_embedding_provider(self):
        from types import SimpleNamespace
        report=SimpleNamespace(_Save=lambda:1,_Id=lambda:'123')
        iris=SimpleNamespace(cls=lambda name:SimpleNamespace(_New=lambda:report))
        state=json.loads(object_request(json.dumps(dict(runId='test',tag='test',objects=['123'])),0))
        state['current']['assessment']='INCONCLUSIVE'
        with patch('gaia.store.iris_module',return_value=iris),patch('gaia.store.run_update'),patch('gaia.embedding.embed') as provider:
            store.save_report(state,'42')
        provider.assert_not_called()
        self.assertEqual(json.loads(report.EvidenceJSON)['embeddingStatus'],'SKIPPED_INCONCLUSIVE')

    def test_empty_fink_has_no_fake_report(self):
        from types import SimpleNamespace
        request=SimpleNamespace(Kind='LIST_BY_TAG',PayloadJSON=json.dumps(dict(runId='test',tag='test',count=5)))
        response=SimpleNamespace()
        with patch('gaia.runtime.tags',return_value=['test']),patch('gaia.runtime.fink_json',return_value=[]),patch('gaia.store.run_update'):
            fink(None,request,response)
        self.assertEqual(response.Status,'EMPTY')
        self.assertEqual(json.loads(response.PayloadJSON)['objects'],[])
        self.assertEqual(json.loads(response.PayloadJSON)['reportIds'],[])

    def test_missing_cutouts_are_inconclusive(self):
        from types import SimpleNamespace
        state=object_request(json.dumps(dict(runId='test',tag='test',objects=['123'])),0)
        row={'r:diaObjectId':'123','r:diaSourceId':'456','r:ra':1,'r:dec':2,'r:midpointMjdTai':60000,'r:psfFlux':1,'r:psfFluxErr':1}
        host=SimpleNamespace(Fetch=lambda *args: (_ for _ in ()).throw(TimeoutError()))
        response=SimpleNamespace()
        with patch('gaia.runtime.fink_json',return_value=[row]):
            fink(host,SimpleNamespace(Kind='GET_SOURCES',PayloadJSON=state),response)
        result=json.loads(response.PayloadJSON)['current']
        self.assertEqual(result['assessment'],'INCONCLUSIVE')
        self.assertTrue(all(ref is None for ref in result['finkImages'].values()))

    def test_java_gateway_failure_is_error(self):
        from types import SimpleNamespace
        state=json.loads(object_request(json.dumps(dict(runId='test',tag='test',objects=['123'])),0))
        state['current']['observation'].update(raDeg=1,decDeg=2)
        state['current']['next_action']='CHECK_GAIA'
        response=SimpleNamespace()
        host=SimpleNamespace(Adapter=SimpleNamespace(_DispatchMethod=lambda *a:(_ for _ in ()).throw(ConnectionError())))
        catalog(host,'GAIA',SimpleNamespace(Kind='CATALOG_QUERY',PayloadJSON=json.dumps(state)),response)
        self.assertEqual(response.Status,'ERROR')
        result=json.loads(response.PayloadJSON)['current']
        self.assertEqual(result['actionsDone'],['GAIA'])
        self.assertEqual(result['catalogs']['SIMBAD']['status'],'NOT_REQUESTED')

    def test_review_updates_existing_report(self):
        from types import SimpleNamespace
        for action,status in [('ACCEPT','ACCEPTED_FOR_REVIEW'),('REJECT','REJECTED'),('DISPATCH_ERROR','TASK_ERROR')]:
            report=SimpleNamespace(Assessment='REVIEW_CANDIDATE',EvidenceJSON='{}',_Save=lambda:1)
            iris=SimpleNamespace(cls=lambda name:SimpleNamespace(_OpenId=lambda id:report))
            with patch('gaia.store.iris_module',return_value=iris):self.assertEqual(store.review('123',action),1)
            self.assertEqual(report.ReviewStatus,status)


class RestTests(unittest.TestCase):
    def setUp(self):self.client=app.test_client()

    def test_validation(self):
        for count in [0,21,True,1.5,'5',None]:
            self.assertEqual(self.client.post('/api/discoveries/run',json={'tag':'x','count':count}).status_code,400)
        self.assertEqual(self.client.get('/api/discoveries?limit=-1').status_code,400)
        self.assertEqual(self.client.get('/api/discoveries/1/images/bad').status_code,404)
        for query in ['status=UNKNOWN','review_status=UNKNOWN']:
            self.assertEqual(self.client.get('/api/discoveries?'+query).status_code,400)

    def test_status_filters_reach_report_store(self):
        with patch('gaia.store.report_list',return_value=[]) as reports:
            response=self.client.get('/api/discoveries?status=REVIEW_CANDIDATE&review_status=PENDING&limit=1&offset=2')
        self.assertEqual(response.status_code,200)
        reports.assert_called_once_with(1,2,'','REVIEW_CANDIDATE','PENDING')

    def test_missing_resources(self):
        with patch('gaia.store.run_get',return_value=None):
            self.assertEqual(self.client.get('/api/discoveries/runs/missing').status_code,404)
        with patch('gaia.store.report_get',return_value=None):
            self.assertEqual(self.client.get('/api/discoveries/999').status_code,404)

    def test_unavailable(self):
        with patch('gaia.store.report_list',side_effect=RuntimeError('private provider detail')):
            response=self.client.get('/api/discoveries')
            self.assertEqual(response.status_code,503)
            self.assertNotIn('private',response.get_data(as_text=True))


if __name__=='__main__':unittest.main()
