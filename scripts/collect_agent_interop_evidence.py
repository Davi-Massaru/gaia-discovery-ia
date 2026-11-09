"""Collect fresh real-run evidence after validate_real_e2e.py, inside Embedded Python.

Never simulates decisions, modifies scientific outcomes or completes human tasks.
"""
import base64
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

import iris

root = Path('/opt/gaia')
sys.path.insert(0, str(root / 'backend'))
from gaia import store
from gaia.embedding import embed
from gaia.science import validate_png, validate_decision
from gaia.diagnostics import diagnostic
from gaia.runtime import agent_prompt

validation = json.loads((root / 'dist/e2e-real.json').read_text())
run_id = validation['runId']
folder = root / 'dist' / ('agent-interop-real-' + run_id)
folder.mkdir(exist_ok=True)
credentials = dict(line.split('=', 1) for line in (root / '.env.runtime').read_text().splitlines())
auth = 'Basic ' + base64.b64encode((credentials['GAIA_TEST_USERNAME'] + ':' + credentials['GAIA_TEST_PASSWORD']).encode()).decode()


def save(name, value):
    (folder / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def get(path):
    with urlopen(Request('http://localhost:52773/gaia' + path,
                         headers={'Authorization': auth}), timeout=45) as response:
        return response.status, response.read(), response.headers


production = iris.cls('Ens.Config.Production')._OpenId('Gaia.Production')
components = {str(production.Items.GetAt(i).Name): str(production.Items.GetAt(i).ClassName)
              for i in range(1, production.Items.Count() + 1)}
assert not iris.gref('^GaiaConfig').get(['testFixtures'])
assert all(not cls.startswith('GaiaTest.') for cls in components.values())
agent = iris.cls('Gaia.Interop.Operations.AIHubOperation').CreateAgent()
assert agent._ClassName(1) == 'Gaia.AI.DiscoveryAgent'
evidence = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'localTime': datetime.now(timezone(timedelta(hours=-3))).isoformat(),
    'scope': 'REAL_HTTP_PRODUCTION_BPL_AGENT_CATALOGS_PERSISTENCE',
    'mocks': False,
    'runId': run_id,
    'runtime': str(iris.system.Version.GetVersion()),
    'production': components,
    'agent': {'class': agent._ClassName(1), 'provider': str(agent.Provider.Name),
              'model': str(agent.Model), 'maxIterations': int(agent.MaxIterations),
              'promptSHA256': hashlib.sha256(str(agent.SystemPrompt).encode()).hexdigest()},
    'sourceSHA256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                     for name in ('src/iris/Gaia/AI/DiscoveryAgent.cls',
                                  'src/iris/Gaia/Interop/Operations/AIHubOperation.cls',
                                  'backend/gaia/runtime.py', 'backend/gaia/embedding.py')},
    'validationStatus': validation['status'],
    'httpChecks': validation.get('checks', {}),
    'directPEXDiagnostics': validation.get('catalogs', {}),
    'run': store.run_get(run_id),
    'reports': [],
}
save('http-validation.json', validation)
(folder / 'SYSTEM_PROMPT.txt').write_text(str(agent.SystemPrompt), encoding='utf-8')

for report_id in evidence['run']['reportIds']:
    status, raw, _ = get('/api/discoveries/' + report_id)
    report = json.loads(raw)
    assert status == 200 and report['runId'] == run_id
    assert not report['evidence'].get('testFixture')
    save('report-' + report_id + '.json', report)
    images = {}
    native = iris.cls('Gaia.Data.DiscoveryReport')._OpenId(report_id)
    for kind in ('science', 'template', 'difference'):
        if not report['images'][kind]:
            images[kind] = {'status': 'MISSING'}
            continue
        code, data, headers = get('/api/discoveries/' + report_id + '/images/' + kind)
        assert code == 200 and headers.get_content_type() == 'image/png'
        validate_png(data)
        assert data == store.stream_bytes(getattr(native, kind.title() + 'PNG'))
        filename = 'report-' + report_id + '-' + kind + '.png'
        (folder / filename).write_bytes(data)
        images[kind] = {'file': filename, 'bytes': len(data), 'byteExact': True,
                        'sha256': hashlib.sha256(data).hexdigest()}

    history = report['evidence'].get('decisionHistory', [])
    done = []
    for index, item in enumerate(history):
        decision = {key: value for key, value in item.items() if key != 'timestamp'}
        validate_decision(decision, done, index)
        if decision['next_action'].startswith('CHECK_'):
            done.append(decision['next_action'][6:])

    trace = []
    exchanges = []
    for row in iris.sql.exec(
            'SELECT ID,SourceConfigName,TargetConfigName,MessageBodyClassName,MessageBodyId '
            'FROM Ens.MessageHeader WHERE SessionId=? ORDER BY ID', report['interopSessionId']):
        entry = dict(zip(('id', 'source', 'target', 'bodyClass', 'bodyId'), list(row)))
        if entry['bodyClass'] in ('Gaia.Interop.Messages.DiscoveryRequest', 'Gaia.Interop.Messages.DiscoveryResponse'):
            body = iris.cls(entry['bodyClass'])._OpenId(str(entry['bodyId']))
            entry.update(runId=str(body.RunId), kind=str(body.Kind), correlationId=str(body.CorrelationId))
            if entry['bodyClass'].endswith('DiscoveryResponse'):
                entry.update(status=str(body.Status), errorCode=str(body.ErrorCode))
            state = json.loads(body.PayloadJSON)
            current = state.get('current', {})
            entry['diaObjectId'] = current.get('observation', {}).get('diaObjectId')
            entry['nextAction'] = current.get('next_action')
            entry['decisionsRecorded'] = len(current.get('decisionHistory', []))
            if entry['kind'] == 'AGENT_DECIDE' and entry['diaObjectId'] == report['diaObjectId']:
                exchange = {'headerId': entry['id'], 'bodyId': entry['bodyId'],
                            'source': entry['source'], 'target': entry['target']}
                if entry['target'] == 'AIHubOperation':
                    exchange['evidenceSent'] = json.loads(agent_prompt(state))
                elif entry['source'] == 'AIHubOperation':
                    exchange['validatedDecisions'] = current.get('decisionHistory', [])
                    exchange['status'] = entry.get('status')
                    exchange['failureCode'] = current.get('failureCode')
                exchanges.append(exchange)
        trace.append(entry)
    save('trace-session-' + str(report['interopSessionId']) + '.json', trace)
    save('agent-exchanges-report-' + report_id + '.json', exchanges)
    requests = [item for item in trace if item.get('target') == 'AIHubOperation'
                and item.get('kind') == 'AGENT_DECIDE' and item.get('diaObjectId') == report['diaObjectId']]
    responses = [item for item in trace if item.get('source') == 'AIHubOperation'
                 and item.get('kind') == 'AGENT_DECIDE' and item.get('diaObjectId') == report['diaObjectId']]
    assert requests, 'Missing real interoperability agent request'
    vector = list(iris.sql.exec(
        'SELECT EmbeddingModel,CASE WHEN SearchEmbedding IS NULL THEN 0 ELSE 1 END '
        'FROM Gaia_Data.DiscoveryReport WHERE ID=?', report_id))[0]
    evidence['reports'].append({
        'id': report_id, 'diaObjectId': report['diaObjectId'], 'diaSourceId': report['diaSourceId'],
        'sessionId': report['interopSessionId'], 'assessment': report['assessment'],
        'reviewStatus': report['reviewStatus'], 'executionStatus': report['evidence'].get('executionStatus'),
        'technicalFailures': report['evidence'].get('technicalFailures', []),
        'agentRequests': len(requests), 'agentResponses': len(responses),
        'validDecisions': len(history), 'decisions': history,
        'catalogActions': done, 'catalogs': report['evidence'].get('catalogs', {}),
        'images': images, 'historyStatus': report['evidence'].get('historyStatus'),
        'embeddingStatus': report['evidence'].get('embeddingStatus'),
        'savedEmbedding': bool(vector[1]), 'embeddingModel': vector[0],
    })

# Independent real embedding health check; report eligibility rules remain untouched.
try:
    vector = embed('Real Gaia Discovery AI interoperability validation; semantic provider health check.')
    raw = json.dumps(vector)
    cosine = float(list(iris.sql.exec(
        'SELECT VECTOR_COSINE(TO_VECTOR(?,FLOAT,1536),TO_VECTOR(?,FLOAT,1536))', raw, raw))[0][0])
    assert len(vector) == 1536 and abs(cosine - 1) < 1e-5
    evidence['embeddingProviderCheck'] = {'status': 'PASS', 'dimensions': len(vector),
                                          'nativeVectorSelfCosine': cosine,
                                          'scope': 'INDEPENDENT_PROVIDER_CHECK_NO_REPORT_MODIFICATION'}
except Exception as error:
    code, details = diagnostic(error)
    evidence['embeddingProviderCheck'] = {'status': 'ERROR', 'code': code, 'details': details}

evidence['status'] = validation['status']
if not evidence['reports'] or any(not item['validDecisions'] for item in evidence['reports']):
    evidence['status'] = 'FAIL_REAL_AGENT_DECISIONS'
if evidence['embeddingProviderCheck']['status'] != 'PASS' and evidence['status'] == 'PASS':
    evidence['status'] = 'PASS_WITH_EXTERNAL_LIMITATIONS'
save('evidence.json', evidence)
lines = ['# Validação real do agente pela interoperabilidade', '',
         'Data: ' + evidence['localTime'], '',
         'Resultado: **' + evidence['status'] + '**', '',
         'Run: `' + run_id + '`', '',
         'Agente: `Gaia.AI.DiscoveryAgent`; provider `openai`; modelo `' + str(agent.Model) + '`.', '',
         'Entrada autenticada HTTP → DiscoveryService → DiscoveryWorkflow BPL → AIHubOperation → agente nativo.', '',
         'Respostas e fontes reais; nenhuma fixture ou decisão simulada.', '',
         '| Relatório | Sessão IRIS | Chamadas ao agente | Decisões válidas | Avaliação | Revisão |',
         '|---|---|---|---|---|---|']
for item in evidence['reports']:
    lines.append('| ' + ' | '.join(str(item[key]) for key in
                 ('id', 'sessionId', 'agentRequests', 'validDecisions', 'assessment', 'reviewStatus')) + ' |')
lines += ['', 'Embeddings: `' + evidence['embeddingProviderCheck']['status'] + '`; detalhes em `evidence.json`.', '',
          'Os arquivos report-*.json contêm as decisões e a evidência científica. '
          'Os arquivos trace-session-*.json correlacionam mensagens e Operations. '
          'Os PNGs foram comparados byte a byte aos streams persistidos.', '',
          'Falhas externas permanecem registradas como ERROR; INCONCLUSIVE não confirma descoberta. '
          'Tarefas humanas, quando criadas, permanecem para decisão de um revisor.']
(folder / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
with zipfile.ZipFile(str(folder) + '.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(folder.iterdir()):
        if path.is_file():
            archive.write(path, path.name)
print(json.dumps({'status': evidence['status'], 'folder': str(folder), 'runId': run_id,
                  'reports': [{key: item[key] for key in ('id', 'sessionId', 'agentRequests', 'validDecisions', 'assessment')}
                              for item in evidence['reports']],
                  'embeddingProviderCheck': evidence['embeddingProviderCheck']}, indent=2), flush=True)
