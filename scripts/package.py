"""Create a distributable source/IPM archive using an explicit allowlist."""
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parent.parent
ET.parse(root/'module.xml')
out=root/'dist'
out.mkdir(exist_ok=True)
archive=out/'gaia-discovery-ai-1.0.0-beta.1.tar.gz'
paths=['src','backend','web','tests','docs','agents','SPEC.md','java-pex/src','java-pex/build/gaia-tap-pex.jar',
       'scripts','module.xml','requirements.txt',
       'Dockerfile','compose.yaml','.gitignore','.dockerignore','.env.example','README.md']
with tarfile.open(archive,'w:gz') as tar:
    for relative in paths:
        path=root/relative
        if not path.exists():raise FileNotFoundError(relative)
        if path.is_dir():
            for file in path.rglob('*'):
                if file.is_file() and '__pycache__' not in file.parts and file.suffix!='.pyc':
                    tar.add(file,arcname=str(file.relative_to(root)),recursive=False)
        else:tar.add(path,arcname=relative,recursive=False)
with tarfile.open(archive) as tar:
    names=tar.getnames()
    assert not any(Path(name).name.startswith('.env') and Path(name).name!='.env.example' for name in names)
print('Packaged',archive.name,'(credentials excluded)')
