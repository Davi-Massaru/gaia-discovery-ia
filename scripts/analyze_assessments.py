"""Read-only assessment distribution and inconclusive-cause audit in Embedded Python."""
import json
import sys
from collections import Counter
from pathlib import Path

import iris

sys.path.insert(0, '/opt/gaia/backend')
from gaia.store import report_get

rows = []
for (native_id,) in iris.sql.exec('SELECT ID FROM Gaia_Data.DiscoveryReport ORDER BY ID'):
    report = report_get(str(native_id))
    evidence = report['evidence']
    catalogs = evidence.get('catalogs', {})
    decisions = evidence.get('decisionHistory', [])
    fixture = bool(evidence.get('testFixture')) or not str(report.get('diaObjectId', '')).isdecimal()
    catalog_error = any(value.get('status') == 'ERROR' for value in catalogs.values())
    context = any(value.get('status') == 'OK' and value.get('matches') for value in catalogs.values())
    if fixture:
        category = 'TEST_FIXTURE'
    elif not decisions:
        category = 'NO_AGENT_DECISION'
    elif catalog_error:
        category = 'CATALOG_QUERY_ERROR'
    elif evidence.get('executionStatus') == 'FAILED' or evidence.get('failureCode'):
        category = 'OTHER_TECHNICAL_FAILURE'
    elif report['assessment'] != 'INCONCLUSIVE':
        category = 'OTHER_ASSESSMENT'
    elif context:
        category = 'SUCCESS_WITH_CATALOG_CONTEXT_REVIEW_CALIBRATION'
    else:
        category = 'SUCCESS_WITHOUT_CATALOG_CONTEXT'
    rows.append({
        'id': str(native_id), 'assessment': report['assessment'], 'category': category,
        'executionStatus': evidence.get('executionStatus'), 'failureCode': evidence.get('failureCode'),
        'assessmentAdjustment': evidence.get('assessmentAdjustment'),
        'decisions': len(decisions),
        'catalogs': {name: {'status': value.get('status'), 'matches': len(value.get('matches', [])),
                            'nearestArcsec': value.get('matches', [{}])[0].get('separationArcsec')
                            if value.get('matches') else None}
                     for name, value in catalogs.items()},
        'finalReason': decisions[-1].get('reason') if decisions else report.get('summary'),
    })

result = {'scope': 'READ_ONLY_NO_RECLASSIFICATION', 'total': len(rows),
          'assessments': dict(Counter(row['assessment'] for row in rows)),
          'categories': dict(Counter(row['category'] for row in rows)),
          'withoutDecisionReasons': dict(Counter(row['finalReason'] for row in rows if not row['decisions'])),
          'catalogStatusCounts': {code: dict(Counter(row['catalogs'].get(code, {}).get('status', 'UNKNOWN')
                                                     for row in rows))
                                  for code in ('GAIA', 'SIMBAD', 'IRSA')},
          'reports': rows}
Path('/opt/gaia/dist/assessment-analysis.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'reports'}, indent=2))
print(json.dumps(rows[-5:], indent=2), flush=True)
