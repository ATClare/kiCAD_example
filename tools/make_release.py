"""Package design deliverables, excluding credentials, binaries and tool caches."""
from pathlib import Path
import hashlib,json,zipfile,re
ROOT=Path(__file__).resolve().parents[1]
demo=(ROOT/'firmware/web/index.html').read_text(encoding='utf-8').replace("new URLSearchParams(location.search).has('demo')",'true')
(ROOT/'docs/dashboard-demo.html').write_text(demo,encoding='utf-8')
allowed={'.md','.py','.ps1','.ini','.h','.cpp','.html','.csv','.json','.kicad_sch','.kicad_pro','.kicad_sym','.xml','.pdf','.svg','.png','.step','.stl','.rpt','.log','.txt'}
files=[ROOT/'README.md',ROOT/'.gitignore']
for folder in ['electronics','mechanical','firmware','docs','tests','tools']:
    for p in (ROOT/folder).rglob('*'):
        if not p.is_file() or any(x in p.parts for x in ['.pio','__pycache__']):continue
        if p.name in ['secrets.h','manifest-sha256.json','host-compiler.log']:continue
        if p.suffix in allowed or p.name in ['sym-lib-table','fp-lib-table']:files.append(p)
files=sorted(set(files))
# Ensure every relative Markdown document link resolves before release.
for p in files:
    if p.suffix!='.md':continue
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' in link or link.startswith('#'):continue
        assert (p.parent/link.split('#')[0]).exists(),(p,link)
manifest={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
manifestPath=ROOT/'docs/manifest-sha256.json'
manifestPath.write_text(json.dumps(manifest,indent=2)+'\n')
out=ROOT/'deliverables';out.mkdir(exist_ok=True)
archive=out/'soil-valve-rev-a.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files+[manifestPath]:z.write(p,'soil-valve-rev-a/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert not any(n.endswith('/secrets.h') or '/.pio/' in n or '/.tools/' in n for n in z.namelist())
    assert z.testzip() is None
print(f'Packaged {len(files)+1} files; all local Markdown links resolve; ZIP integrity passed; credentials excluded.')
print(f'{archive.name}: {archive.stat().st_size:,} bytes; SHA256 {hashlib.sha256(archive.read_bytes()).hexdigest()}')
