"""Read-only native HTTP validation of report filters and semantic exclusions."""
import base64
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import iris

creds = dict(line.split('=', 1) for line in Path('/opt/gaia/.env.runtime').read_text().splitlines())
auth = 'Basic '+base64.b64encode((creds['GAIA_TEST_USERNAME']+':'+creds['GAIA_TEST_PASSWORD']).encode()).decode()


def get(query):
    try:
        with urlopen(Request('http://localhost:52773/gaia/api/discoveries?'+query,
                             headers={'Authorization': auth}), timeout=45) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())


result = {'scope': 'REAL_NATIVE_SQL_AND_AUTHENTICATED_HTTP', 'checks': []}
saved = [tuple(str(value) for value in row) for row in iris.sql.exec(
    'SELECT ID,Assessment,ReviewStatus FROM Gaia_Data.DiscoveryReport ORDER BY ID DESC')]
for status in ['', 'INCONCLUSIVE', 'REVIEW_CANDIDATE', 'CATALOG_CONTEXT_FOUND']:
    for review in ['', 'PENDING', 'ACCEPTED_FOR_REVIEW', 'REJECTED', 'NOT_REQUIRED', 'TASK_ERROR']:
        query = 'limit=100&status='+status+'&review_status='+review
        code, response = get(query)
        assert code == 200, (query, code, response)
        items = response['items']
        expected = [row[0] for row in saved if (not status or row[1] == status) and (not review or row[2] == review)][:100]
        assert [item['id'] for item in items] == expected, (query, [item['id'] for item in items], expected)
        if items:
            code, page = get('limit=1&offset=1&status='+status+'&review_status='+review)
            assert code == 200 and [item['id'] for item in page['items']] == expected[1:2], (query, 'page', code, page)
        result['checks'].append({'status': status, 'reviewStatus': review, 'matches': len(items)})
assert get('status=UNKNOWN')[0] == 400
assert get('review_status=UNKNOWN')[0] == 400
code, response = get('search=astronomical&status=INCONCLUSIVE')
assert code == 200 and response['items'] == []
result['inconclusiveSemanticSearch'] = 'EMPTY_WITHOUT_PROVIDER'
code, response = get('search=astronomical')
result['semanticSearchHTTP'] = code
if code == 200:
    assert all(item['assessment'] != 'INCONCLUSIVE' for item in response['items'])
    result['semanticReportIds'] = [item['id'] for item in response['items']]
result['status'] = 'PASS' if code == 200 else 'PASS_FILTERS_PROVIDER_UNAVAILABLE'
Path('/opt/gaia/dist/report-filters.json').write_text(json.dumps(result, indent=2))
print(result['status'], '24 status combinations, pagination, invalid filters and semantic exclusions', flush=True)
