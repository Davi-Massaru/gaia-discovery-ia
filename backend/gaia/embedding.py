import json
import math
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def embed(text):
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('MISSING_API_KEY')
    req = Request('https://api.openai.com/v1/embeddings',
                  data=json.dumps(dict(model='text-embedding-3-small', input=text[:12000], dimensions=1536)).encode(),
                  headers={'Authorization': 'Bearer '+key, 'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read(200000))
    except HTTPError as error:
        # Only an allowlisted diagnostic crosses the provider boundary.
        from .diagnostics import diagnostic
        try:
            body = json.loads(error.read(16384))
            detail = body.get('error', {})
            code, _ = diagnostic(str(detail.get('code', ''))+' '+str(detail.get('type', '')))
        except Exception:
            code = 'PROVIDER_ERROR'
        failure = RuntimeError(code)
        failure.code = error.code
        raise failure from None
    vector = data['data'][0]['embedding']
    if len(vector) != 1536 or any(type(x) not in (int, float) or not math.isfinite(x) for x in vector):
        raise ValueError('Invalid embedding')
    return vector


def search_previous(text, top_k=3, status='', review_status=''):
    import iris
    from .store import validate_report_filters
    validate_report_filters(status, review_status)
    if status == 'INCONCLUSIVE':
        return []
    where = "SearchEmbedding IS NOT NULL AND Assessment <> 'INCONCLUSIVE'"
    params = []
    for column, value in [('Assessment', status), ('ReviewStatus', review_status)]:
        if value:
            where += ' AND '+column+'=?'
            params.append(value)
    # No vector exists to compare: empty history is a legitimate local result,
    # independent of provider availability or credentials.
    if not list(iris.sql.exec('SELECT TOP 1 ID FROM Gaia_Data.DiscoveryReport WHERE '+where, *params)):
        return []
    vector = embed(text)
    if vector is None:
        return []
    rows = iris.sql.exec('SELECT TOP ? ID,Summary,VECTOR_COSINE(SearchEmbedding,TO_VECTOR(?,FLOAT,1536)) AS Similarity FROM Gaia_Data.DiscoveryReport WHERE '+where+' ORDER BY Similarity DESC',
                         min(max(int(top_k), 1), 3), json.dumps(vector), *params)
    return [dict(id=str(row[0]), summary=row[1], similarity=float(row[2]), caution='Semantic analogy, not an astronomical crossmatch.') for row in rows]
