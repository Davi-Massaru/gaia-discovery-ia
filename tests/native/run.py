"""Native agent extraction regression; run inside Embedded Python in a disposable container."""
import os
import sys
from pathlib import Path
from unittest.mock import patch

import iris

if os.environ.get('GAIA_E2E_ISOLATED') != '1':
    raise RuntimeError('Requires GAIA_E2E_ISOLATED=1 in a disposable container')

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'backend'))
from gaia.store import check_status

check_status(iris.cls('%SYSTEM.OBJ').LoadDir(str(root / 'tests/native'), 'ck', None, 1))
check_status(iris.cls('GaiaTest.AgentMigration').Run())

agent_class = iris.cls('Gaia.AI.DiscoveryAgent')
operation_class = iris.cls('Gaia.Interop.Operations.AIHubOperation')
with patch.dict(os.environ):
    for model in (None, 'gpt-4.1-mini', 'isolated-model-override', ''):
        if model is None:
            os.environ.pop('OPENAI_MODEL', None)
        else:
            os.environ['OPENAI_MODEL'] = model
        expected = 'gpt-4.1-mini' if model is None else model
        agent = agent_class._New()
        assert agent.Model == expected
        assert operation_class.Model() == expected
    for key in (None, '', 'isolated-no-network'):
        if key is None:
            os.environ.pop('OPENAI_API_KEY', None)
        else:
            os.environ['OPENAI_API_KEY'] = key
        assert agent_class.ApiKey() == (key or '')
        assert operation_class.ApiKey() == (key or '')

print('AGENT_ENVIRONMENT_COMPATIBILITY_OK', flush=True)
