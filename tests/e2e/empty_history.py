"""Run only against a clean native package namespace with no reports or key."""
import json
import os
import sys
import iris

sys.path.insert(0, '/tmp/gaia-vector-check')
from gaia.embedding import search_previous

assert list(iris.sql.exec('SELECT COUNT(*) FROM Gaia_Data.DiscoveryReport'))[0][0] == 0
assert not os.environ.get('OPENAI_API_KEY')
assert search_previous('empty native report history') == []
print(json.dumps({'emptyNativeHistory': 'PASS', 'reports': 0, 'providerKeyPresent': False,
                  'result': [], 'mockedComponents': False}), flush=True)
