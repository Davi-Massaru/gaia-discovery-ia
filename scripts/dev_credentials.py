"""Create a local-container reviewer for authenticated smoke tests; never package credentials."""
import iris
import secrets
from pathlib import Path

file = Path('/opt/gaia/.env.runtime')
roles = iris.cls('Security.Roles')
if not roles.Exists('GaiaWSGI'):
    status = roles.Create('GaiaWSGI', 'Use native Embedded Python for Gaia WSGI', '%Service_EmbeddedPython:U')
    if status != 1:
        raise RuntimeError('Could not create WSGI execution role')
if not file.exists():
    password = 'Gaia!' + secrets.token_urlsafe(24)
    status = iris.cls('Security.Users').Create('GaiaReviewer', '%DB_USER,%EnsRole_Operator,GaiaWSGI', password, 'Gaia local development reviewer', 'USER', '', '', 0, 1)
    if status != 1:
        raise RuntimeError('Could not create local reviewer')
    file.write_text('GAIA_TEST_USERNAME=GaiaReviewer\nGAIA_TEST_PASSWORD='+password+'\n')
    print('Local reviewer created; credentials stored in ignored .env.runtime')
