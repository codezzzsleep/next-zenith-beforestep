"""Archive only completed diagnosis and input attempts; running v9 stays separate."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ops.crossing_development_evidence import bundle


if __name__=='__main__':
    revisions=['scene-dev-v6','scene-dev-v7','scene-dev-v8','input-preview-a45-d1.4','input-preview-a65-d1.4',
               'input-preview-a65-d1.8','input-front-rect-sun0','input-front-rect-sun180']
    files=[]
    for revision in revisions:files += [p for p in (ROOT/'outputs/crossing/development'/revision).rglob('*') if p.is_file() and p.suffix!='.tmp']
    files += [p for p in (ROOT/'outputs/crossing/diagnosis/input-registration-v1').rglob('*') if p.is_file()]
    files += [p for p in (ROOT/'outputs/crossing/diagnosis/observed-pose-v1').rglob('*') if p.is_file()]
    for revision in ['scene-dev-v6','scene-dev-v7','scene-dev-v8']:
        r=json.loads((ROOT/'evidence/crossing'/f'development-lux-{revision}-11002.json').read_text())
        for task in r['task_ids']:files += [p for p in (ROOT/'assets/candidates'/str(task)).rglob('*') if p.is_file()]
    files += [p for p in (ROOT/'evidence/crossing').glob('*.json') if p.name.startswith('diagnosis-') and p.name!='diagnosis-generator-v9.json']
    files += [p for p in (ROOT/'evidence/crossing').glob('development-*.json') if any(v in p.name for v in ['v6','v7','v8'])]
    r=bundle('input-diagnosis-20261113',sorted(set(files)))
    (ROOT/'evidence/crossing/development/diagnosis-index.json').write_text(json.dumps({'schema':'beforestep-crossing-diagnosis-artifacts/v1','archive':r},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'bytes':r['bytes'],'members':len(r['members']),'member_sha_check':r['member_sha_check']}))
