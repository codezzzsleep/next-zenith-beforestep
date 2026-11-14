"""Publish only the reviewed 180-second recording and its native video homepage."""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'real-footage-180';PAGES=Path('/tmp/beforestep-pages-r3-P0-worktree')
def value(args,cwd=ROOT):return subprocess.check_output(args,cwd=cwd,text=True).strip()
def run(args,cwd=ROOT):subprocess.run(args,cwd=cwd,check=True)
def save(state):(WORK/'publication.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
audit=json.loads((WORK/'audit.json').read_text());assert audit['passed'] and audit['visual_review']=='passed'
assert json.loads((WORK/'qc/local/result.json').read_text())['passed']
assert hashlib.sha256((ROOT/'site/media/demo-v4.mp4').read_bytes()).hexdigest()==audit['film_sha256']
files=['site/index.html','site/real-footage.css','site/real-footage.js','site/data/real-footage-180.json','site/media/demo-v4.mp4','site/media/demo-v4-clean.mp4','site/media/demo-v4.zh.vtt','docs/reviews/REAL_FOOTAGE_180.md','docs/decisions.md','docs/video.md','evidence/award/acceptance/real-footage-180.json']
files += [str(p.relative_to(ROOT)) for folder in ['site/media/real-footage','site/data/real-footage-sources','site/data/real-footage-chapters'] for p in (ROOT/folder).glob('*') if p.is_file() and '-recording' not in p.name]
files += [str(p.relative_to(ROOT)) for p in (ROOT/'ops').glob('crossing_real_footage_*.py')]
state={'status':'publishing','files':files};save(state);run(['git','add','--',*files]);assert set(value(['git','diff','--cached','--name-only']).splitlines())<=set(files)
run(['git','commit','-m','Present the complete 180-second recorded simulation with native chapter playback'])
state['main']=value(['git','rev-parse','HEAD']);save(state);run(['git','push','origin','main']);assert value(['git','ls-remote','origin','refs/heads/main']).split()[0]==state['main']
assert not value(['git','status','--short','--untracked-files=no'],PAGES);run(['git','pull','--ff-only','origin','gh-pages'],PAGES)
public=[]
for name in files:
 if name.startswith('ops/'):continue
 target=PAGES/name.removeprefix('site/');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target);public.append(str(target.relative_to(PAGES)))
run(['git','add','--',*public],PAGES);run(['git','commit','-m','Publish recorded action chapters and the WebGL-independent video homepage'],PAGES)
state['pages']=value(['git','rev-parse','HEAD'],PAGES);state['public_files']=public;save(state);run(['git','push','origin','HEAD:gh-pages'],PAGES);state['status']='waiting_build';save(state)
for _ in range(80):
 build=json.loads(value(['gh','api','repos/codezzzsleep/next-zenith-beforestep/pages/builds/latest']))
 if build.get('commit')==state['pages'] and build.get('status')=='built':state.update(status='built',build=build);save(state);break
 if build.get('commit')==state['pages'] and build.get('status')=='errored':raise RuntimeError(build)
 time.sleep(10)
else:raise RuntimeError('Build pending: resume checks against publication.json; do not republish')
print('NATIVE VIDEO HOMEPAGE AND 180 SECOND FILM PUBLISHED',state['main'],state['pages'],flush=True)
