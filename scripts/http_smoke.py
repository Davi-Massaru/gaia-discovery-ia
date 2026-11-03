"""Authenticated HTTP verification against the native IRIS WSGI mount."""
import base64
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

creds = dict(line.split('=', 1) for line in Path('/opt/gaia/.env.runtime').read_text().splitlines())
token = base64.b64encode((creds['GAIA_TEST_USERNAME']+':'+creds['GAIA_TEST_PASSWORD']).encode()).decode()


def request(path, body=None):
    req = Request('http://localhost:52773/gaia'+path,
                  data=json.dumps(body).encode() if body is not None else None,
                  headers={'Authorization': 'Basic '+token, 'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=15) as response:
            data = response.read()
            print(path, response.status, data[:200] if not data.startswith(b'\x89PNG') else 'PNG bytes: '+str(len(data)))
            return response.status, data
    except HTTPError as error:
        print(path, error.code, error.read(300))
        return error.code, None


if __name__ == '__main__':
    request('/api/discoveries')
    request('/api/discoveries/1')
    request('/api/discoveries/1/images/science')
    request('/api/discoveries/999999')
    request('/api/discoveries/run', {'tag': 'extragalactic_new_candidate', 'count': 0})
