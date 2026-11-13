"""Retain terminal addendum development evidence without repacking old trials."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'evidence/crossing/development'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while block:=f.read(1<<20):h.update(block)
    return h.hexdigest()

def bundle(tag,files):
    target=PUBLIC/(tag+'.tar.gz');manifest=PUBLIC/(tag+'-manifest.json')
    if manifest.exists():return json.loads(manifest.read_text())
    assert not target.exists(),'Unfinished archive: preserve and recover explicitly'
    rows=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in files]
    with tarfile.open(target,'w:gz',compresslevel=1) as tar:
        for p in files:tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    # This one archive integrity check also binds the public member list.
    bypath={r['path']:r for r in rows}
    with tarfile.open(target,'r:gz') as tar:
        assert len(tar.getmembers())==len(rows)
        for member in tar:
            h=hashlib.sha256();f=tar.extractfile(member)
            while block:=f.read(1<<20):h.update(block)
            assert h.hexdigest()==bypath[member.name]['sha256'],member.name
    report={'schema':'beforestep-crossing-development-evidence/v1','path':str(target.relative_to(ROOT)),
            'bytes':target.stat().st_size,'sha256':digest(target),'member_sha_check':'passed',
            'download':'https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/'+str(target.relative_to(ROOT)),
            'members':rows,'excluded_from_test_statistics':True}
    manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');return report

if __name__=='__main__':
    PUBLIC.mkdir(exist_ok=True)
    files=[]
    for revision in ['scene-dev-v1','scene-dev-v2','scene-dev-v3']:
        for p in (ROOT/'outputs/crossing/development'/revision).rglob('*'):
            if not p.is_file() or any(part.startswith('lux') or part=='decision' for part in p.parts):continue
            files.append(p)
    files += [ROOT/'evidence/crossing'/name for name in ['development-blindness.json','development-blindness-v1.json','development-validity.json']]
    zero=bundle('addendum1-zero-paid',sorted(set(files)))
    gait=[]
    for name in ['gait-v93-substep','gait-v94-fullframe','gait-v95-force']:
        gait += [p for p in (ROOT/'outputs/crossing/calibration'/name).rglob('*') if p.is_file() and not p.name.endswith('.coordinator.lock')]
    latest=bundle('development-v93-95',sorted(gait))
    index={'schema':'beforestep-crossing-addendum1-artifacts/v1','existing_calibration':'evidence/crossing/calibration/capability-v72-manifest.json',
        'older_development':'evidence/crossing/development/development-v92-manifest.json',
        'addendum1_zero_paid':zero,'development_v93_95':latest}
    (PUBLIC/'addendum1-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'zero_paid_bytes':zero['bytes'],'v93_95_bytes':latest['bytes'],'member_sha_checks':'passed'}))
