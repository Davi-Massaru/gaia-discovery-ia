"""Independent vector SQL and real-provider checks, without synthetic data."""
import json
import sys
from pathlib import Path
import iris

sys.path.insert(0, '/opt/gaia/backend')
from gaia.embedding import embed, search_previous
from gaia.diagnostics import diagnostic

result = {'embeddingProvider': 'REAL_OPENAI', 'indexedReports': list(iris.sql.exec(
    'SELECT COUNT(*) FROM Gaia_Data.DiscoveryReport WHERE SearchEmbedding IS NOT NULL'))[0][0]}
row = list(iris.sql.exec('SELECT TOP 1 ID,Summary,VECTOR_COSINE(SearchEmbedding,SearchEmbedding) FROM Gaia_Data.DiscoveryReport WHERE SearchEmbedding IS NOT NULL'))
result['storedVectorSQL'] = {'status': 'PASS' if row else 'EMPTY',
                             'reportId': str(row[0][0]) if row else None,
                             'selfSimilarity': float(row[0][2]) if row else None}
try:
    vector = embed(row[0][1] if row else 'Astronomical investigation')
    result['realEmbedding'] = {'status': 'OK', 'dimensions': len(vector)}
    rows = list(iris.sql.exec('SELECT TOP 3 ID,VECTOR_COSINE(SearchEmbedding,TO_VECTOR(?,FLOAT,1536)) AS Similarity FROM Gaia_Data.DiscoveryReport WHERE SearchEmbedding IS NOT NULL ORDER BY Similarity DESC', json.dumps(vector)))
    result['realQueryVectorSQL'] = {'status': 'PASS', 'matches': [{'id': str(r[0]), 'similarity': float(r[1])} for r in rows]}
except Exception as error:
    code, details = diagnostic(error)
    result['realEmbedding'] = {'status': 'ERROR', 'code': code, 'diagnostic': details}
try:
    result['semanticSearch'] = {'status': 'PASS', 'results': search_previous('astronomical transient')}
except Exception as error:
    code, details = diagnostic(error)
    result['semanticSearch'] = {'status': 'ERROR', 'code': code, 'diagnostic': details}
Path('/opt/gaia/dist/vector-real.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result), flush=True)
