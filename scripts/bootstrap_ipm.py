"""Download the official public IPM installer; imports are a separate explicit command."""
from urllib.request import urlopen
from pathlib import Path

with urlopen('https://pm.community.intersystems.com/packages/zpm/latest/installer',timeout=60) as response:
    data=response.read(30*1024*1024)
if not data.lstrip().startswith(b'<?xml'):
    raise ValueError('Registry did not return an XML installer')
Path('/tmp/gaia-ipm-installer.xml').write_bytes(data)
print('Downloaded public IPM installer',len(data),'bytes')
