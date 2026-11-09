"""Probe the real native AI Hub and embedding provider with sanitized output."""
import json
import sys
from pathlib import Path
import iris

sys.path.insert(0,'/opt/gaia/backend')
from gaia.embedding import embed
from gaia.diagnostics import diagnostic
from gaia.runtime import agent_prompt
from gaia.science import validate_decision
from gaia import store
results={}
try:
    vector=embed('Gaia Discovery AI: validation of astronomical report embeddings.')
    results['embedding']={'status':'OK' if vector else 'NOT_CONFIGURED','dimensions':len(vector) if vector else 0}
except Exception as error:
    code,details=diagnostic(error)
    results['embedding']={'status':'ERROR','code':code,'diagnostic':details}
stage='AI_HUB_PROVIDER'
try:
    agent=iris.cls('Gaia.AI.DiscoveryAgent')._New()
    session=agent.CreateSession()
    evidence=store.report_get('3')['evidence']
    current={name:evidence[name] for name in ('observation','catalogs')}
    current.update(actionsDone=[],decisionHistory=[],historicalAnalogies=[])
    stage='AI_HUB_CHAT'
    answer=agent.Chat(session,agent_prompt({'current':current}))
    stage='AI_HUB_VALIDATION'
    decision=validate_decision(json.loads(answer.Content),[],0)
    results['nativeAIHub']={'status':'OK','validDecisionSchema':True,'decision':decision}
except Exception as error:
    code,details=diagnostic(error)
    results['nativeAIHub']={'status':'ERROR','code':code,'failureStage':stage,'diagnostic':details}
Path('/opt/gaia/dist/ai-probe.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results),flush=True)
