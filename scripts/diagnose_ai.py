"""Read-only native runtime/trace diagnostics; never emit provider secrets."""
import json
import os
import sys
from pathlib import Path
import iris

sys.path.insert(0, '/opt/gaia/backend')
from gaia import store

result = {'namespace': iris.system.Process.NameSpace(), 'keyPresent': bool(os.environ.get('OPENAI_API_KEY'))}
entries = dict(line.split('=', 1) for line in Path('/opt/gaia/.env').read_text().splitlines()
               if '=' in line and not line.lstrip().startswith('#'))
key = entries.get('OPENAI_API_KEY', '').strip().strip('"').strip("'")
result['keyMatchesEnvFile'] = key == os.environ.get('OPENAI_API_KEY', '')
result['nativeKeyMatches'] = key == iris.cls('Gaia.Interop.Operations.AIHubOperation').ApiKey()
for cls, names in [('%AI.Provider', ['Create']), ('%AI.Agent', ['%New', 'CreateSession', 'Chat']),
                   ('%Exception.AbstractException', ['DisplayString'])]:
    result[cls] = [list(row) for row in iris.sql.exec(
        'SELECT Name,FormalSpec FROM %Dictionary.CompiledMethod WHERE Parent=?', cls) if row[0] in names]
report = store.report_get('3')
result['report3'] = {'sessionId': report['interopSessionId'], 'assessment': report['assessment'],
                     'errors': report['evidence'].get('errors'), 'decisions': len(report['evidence'].get('decisionHistory', [])),
                     'historyStatus': report['evidence'].get('historyStatus')}
result['session35'] = []
for row in iris.sql.exec('SELECT ID,SourceConfigName,TargetConfigName,MessageBodyClassName,MessageBodyId FROM Ens.MessageHeader WHERE SessionId=? ORDER BY ID', '35'):
    item = dict(zip(['id', 'source', 'target', 'bodyClass', 'bodyId'], row))
    if row[3] == 'Gaia.Interop.Messages.DiscoveryResponse':
        body = iris.cls(row[3])._OpenId(str(row[4]))
        item.update(status=body.Status, errorCode=body.ErrorCode)
    result['session35'].append(item)
result['embeddingColumn'] = [list(row) for row in iris.sql.exec(
    "SELECT Name,Type FROM %Dictionary.CompiledProperty WHERE Parent='Gaia.Data.DiscoveryReport' AND Name='SearchEmbedding'")]
ref = iris.gref('^GaiaRuns')
runs = [json.loads(ref.get([key[0] if isinstance(key, list) else key])) for key in ref.keys()]
result['latestRuns'] = sorted(runs, key=lambda run: run.get('createdEpoch', 0))[-2:]
result['latestHeaders'] = [list(row) for row in iris.sql.exec(
    'SELECT TOP 8 ID,SourceConfigName,TargetConfigName,MessageBodyClassName,MessageBodyId FROM Ens.MessageHeader ORDER BY ID DESC')]
result['validatedSessionTraces'] = {}
for session_id in ['154', '192']:
    result['validatedSessionTraces'][session_id] = [list(row) for row in iris.sql.exec(
        'SELECT ID,SourceConfigName,TargetConfigName,MessageBodyClassName,MessageBodyId FROM Ens.MessageHeader WHERE SessionId=? ORDER BY ID', session_id)]
Path('/opt/gaia/dist/ai-runtime-diagnosis.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result), flush=True)
