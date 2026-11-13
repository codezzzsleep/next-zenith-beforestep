"""Retain all completed narrowed fixtures and real Lux outputs once."""
import argparse,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ops.crossing_development_evidence import bundle
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--name',default='narrow-generator-v9-20261113');args=parser.parse_args()
    base=ROOT/'outputs/crossing/development/scene-dev-v9'
    budget=json.loads((ROOT/'outputs/generation/crossing-budget.json').read_text())
    jobs=[r for r in budget['tasks'] if r['scene'].startswith('scene-dev-v9/')]
    assert all(r['status'] in ['ok','failed','not_submitted'] for r in jobs),'Collect every known task first'
    files=[p for p in base.rglob('*') if p.is_file() and p.suffix!='.tmp' and p.suffix!='.lock']
    for job in jobs:
        if job.get('task_id'):files.extend(p for p in (ROOT/'assets/candidates'/str(job['task_id'])).rglob('*') if p.is_file())
    files.extend(p for p in (ROOT/'evidence/crossing').glob('*.json') if 'v9' in p.name or p.name=='development-narrow-summary.json')
    files.extend(p for p in (ROOT/'outputs/crossing').glob('diagnosis-*-v9*.log') if p.is_file())
    prior_path=ROOT/'evidence/crossing/development/narrow-generator-index.json'
    prior=json.loads(prior_path.read_text()) if prior_path.exists() else None
    prior_archives=prior.get('archives',[prior['archive']]) if prior else []
    if prior and args.name!='narrow-generator-v9-20261113':
        previous={r['path']:r['sha256'] for a in prior_archives for r in a['members']}
        files=[p for p in files if previous.get(str(p.relative_to(ROOT)))!=hashlib.sha256(p.read_bytes()).hexdigest()]
    archive=bundle(args.name,sorted(set(files)))
    index={'schema':'beforestep-crossing-narrow-artifacts/v1','archive':prior_archives[0] if prior_archives else archive,'archives':prior_archives+[archive] if prior_archives else [archive],'formal_test_scenes':0,'real_task_ids':[r['task_id'] for r in jobs if r.get('task_id')]}
    (ROOT/'evidence/crossing/development/narrow-generator-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'bytes':archive['bytes'],'members':len(archive['members']),'sha_check':archive['member_sha_check']}))
