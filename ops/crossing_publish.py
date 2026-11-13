"""Publish crossing changes while retaining existing Pages and frozen results."""
import argparse,hashlib,json,shutil,subprocess,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PAGES=Path('/tmp/beforestep-pages-r3-P0-worktree')
PRIVATE=Path('/root/3d/.memory/live/crossing-publication');PUBLIC='https://codezzzsleep.github.io/next-zenith-beforestep/'

def run(args,cwd=ROOT):subprocess.run(args,cwd=cwd,check=True)
def readcmd(args,cwd=ROOT):return subprocess.check_output(args,cwd=cwd,text=True).strip()
def checkpoint(state,event):
    path=PRIVATE/(state['stage']+'.json')
    state['event']=event;state['updated_at_unix']=time.time();PRIVATE.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    with Path('/root/3d/MEMORY.md').open('a') as f:f.write('\n- Crossing publication: '+event+'；私有账本 '+str(path)+'。\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--stage',default='capability-v72');ap.add_argument('--message',default='Publish complete crossing calibration and preserve failed support constraints');a=ap.parse_args()
    state={'stage':a.stage,'status':'running'};checkpoint(state,'Publishing Addendum 1 gate and measured development results')
    run(['git','fetch','origin','main'])
    remote=readcmd(['git','rev-parse','origin/main'])
    if remote!=readcmd(['git','rev-parse','HEAD']):
        run(['git','merge-base','--is-ancestor',remote,'HEAD'])
    attributes=ROOT/'.gitattributes';text=attributes.read_text();line='evidence/crossing/**/*.tar.gz filter=lfs diff=lfs merge=lfs -text\n'
    if line not in text:attributes.write_text(text+'\n'+line)
    paths=['.gitattributes','experimental/crossing',*[str(p.relative_to(ROOT)) for p in ROOT.glob('ops/crossing_*.py')],'docs/crossing.md','docs/reviews/RESULT_ARENA_LEARNING.md','evidence/learning/arena_v2/closure.json','docs/reviews/SPEC_WHEELLEG_CROSSING.md','docs/reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM1.md','docs/reviews/RESULT_WHEELLEG_CROSSING.md','evidence/crossing','site/crossing.html','site/crossing.css','site/crossing.js']
    budget=json.loads((ROOT/'outputs/generation/crossing-budget.json').read_text())
    paths += ['assets/candidates/'+str(r['task_id']) for r in budget['tasks'] if r.get('task_id')]
    run(['git','add',*paths])
    if readcmd(['git','diff','--cached','--name-only']):run(['git','commit','-m',a.message])
    state['main']=readcmd(['git','rev-parse','HEAD']);checkpoint(state,'Source and measured baseline evidence committed '+state['main'])
    run(['git','push','origin','main'])
    assert readcmd(['git','ls-remote','origin','refs/heads/main']).split()[0]==state['main'];checkpoint(state,'Main pushed and verified '+state['main'])
    copied=[]
    for relative in ['site/crossing.html','site/crossing.css','site/crossing.js','docs/crossing.md','docs/reviews/RESULT_ARENA_LEARNING.md','evidence/learning/arena_v2/closure.json','docs/reviews/SPEC_WHEELLEG_CROSSING.md','docs/reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM1.md','docs/reviews/RESULT_WHEELLEG_CROSSING.md']:
        destination=relative.removeprefix('site/');target=PAGES/destination;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,target);copied.append(destination)
    for source in (ROOT/'evidence/crossing').rglob('*'):
        if not source.is_file() or source.suffix not in ['.json','.png','.jpg']:continue
        relative=str(source.relative_to(ROOT));target=PAGES/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);copied.append(relative)
    run(['git','add',*copied],PAGES)
    if readcmd(['git','diff','--cached','--name-only'],PAGES):run(['git','commit','-m',a.message],PAGES)
    state['pages']=readcmd(['git','rev-parse','HEAD'],PAGES);checkpoint(state,'Pages commit prepared '+state['pages'])
    run(['git','push','origin','HEAD:gh-pages'],PAGES);checkpoint(state,'Pages pushed '+state['pages'])
    start=time.monotonic()
    while time.monotonic()-start<1200:
        build=json.loads(readcmd(['gh','api','repos/codezzzsleep/next-zenith-beforestep/pages/builds/latest']))
        if build.get('commit')==state['pages'] and build.get('status')=='built':state['build']=build;break
        if build.get('commit')==state['pages'] and build.get('status')=='errored':raise RuntimeError(build.get('error'))
        time.sleep(15)
    else:raise RuntimeError('Pages build not yet terminal; resume verification without regenerating evidence')
    run([sys.executable,str(ROOT/'ops/crossing_check.py'),'--url',PUBLIC,'--out',str(PRIVATE/(a.stage+'-public'))])
    import urllib.request
    verified=[]
    for relative in ['crossing.html','crossing.css','crossing.js','docs/crossing.md','evidence/crossing/calibration/capability.json','evidence/crossing/calibration/capability-v72.json','evidence/crossing/calibration/capability-v72-manifest.json','evidence/crossing/references.json','evidence/crossing/development.json','evidence/crossing/calibration/gate.json','evidence/crossing/development-blindness.json']:
        with urllib.request.urlopen(PUBLIC+relative,timeout=90) as response:raw=response.read();assert response.status==200
        expected=(PAGES/relative).read_bytes();assert raw==expected,relative
        verified.append({'path':relative,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    state.update(status='complete',verified_public_files=verified);checkpoint(state,'Complete calibration page passed desktop/mobile and public bytes verification')
    print(json.dumps(state,ensure_ascii=False))
