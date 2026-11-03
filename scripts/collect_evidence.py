"""Read actual saved reports, run state and trace references without exposing secrets."""
import json
from pathlib import Path
import iris

out=Path('/opt/gaia/dist/runtime-evidence.json')
evidence=json.loads(out.read_text()) if out.exists() else {'checks':{}}
checks=evidence['checks']
checks['reports']=[]
for row in iris.sql.exec('SELECT ID,RunId,InteropSessionId,Assessment,ReviewStatus FROM Gaia_Data.DiscoveryReport ORDER BY ID'):
    report_id,run_id,session_id,assessment,review_status=row
    headers=list(iris.sql.exec('SELECT COUNT(*) FROM Ens.MessageHeader WHERE SessionId=?',session_id))
    checks['reports'].append(dict(id=str(report_id),runId=run_id,sessionId=str(session_id),assessment=assessment,
                                  reviewStatus=review_status,traceMessageCount=headers[0][0]))
    run=iris.gref('^GaiaRuns').get([run_id])
    if run:checks.setdefault('runs',{})[run_id]=json.loads(run)
tasks=list(iris.sql.exec('SELECT ID,"%Action","%Status" FROM EnsLib_Workflow.TaskResponse WHERE "%Subject"=?',
                         'Gaia native Workflow transport test'))
checks['nativeWorkflowTransport']=[dict(id=row[0],action=row[1],status=row[2]) for row in tasks]
checks['workflowInboxAndBPLCandidateReturn']='UNVERIFIED'
checks['realAIAndEmbeddingBlocker']='organization_spend_limit_exceeded'
out.write_text(json.dumps(evidence,indent=2))
print(json.dumps({'reports':checks['reports'],'workflowTransport':checks['nativeWorkflowTransport']},indent=2))
