"""Publish only this showcase's explicit files; preserve all other workspace work."""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'showcase-real-footage';PAGES=Path('/tmp/beforestep-pages-r3-P0-worktree')
def run(args,cwd=ROOT):subprocess.run(args,cwd=cwd,check=True)
def value(args,cwd=ROOT):return subprocess.check_output(args,cwd=cwd,text=True).strip()
def save(x):(WORK/'publication.json').write_text(json.dumps(x,ensure_ascii=False,indent=2))
site=['site/index.html','site/levels.html','site/crossing.html','site/sandbox.html','site/showcase.css','site/showcase.js','site/levels-analysis.html','site/crossing-analysis.html','site/sandbox-analysis.html','site/data/footage.json','site/media/demo-v3.mp4']
site += [str(p.relative_to(ROOT)) for p in (ROOT/'site/media/footage').glob('*') if p.suffix in ('.mp4','.jpg','.glb') and '-recording' not in p.name]
site += [str(p.relative_to(ROOT)) for p in (ROOT/'site/data/recordings').glob('*.json')]
docs=['docs/reviews/SHOWCASE_CAPTURE_LIST.md','docs/decisions.md','evidence/award/acceptance/real-footage-showcase.json']
ops=[str(p.relative_to(ROOT)) for p in (ROOT/'ops').glob('crossing_showcase_*.py')]
files=site+docs+ops
assert json.loads((WORK/'audit.json').read_text())['passed']
assert json.loads((WORK/'qc/local/result.json').read_text())['passed']
assert json.loads((WORK/'qc/local/interactions.json').read_text())['passed']
film_check=json.loads((WORK/'qc/film/verification.json').read_text())
assert film_check['automated_passed'] and film_check['visual_review'].startswith('passed')
assert hashlib.sha256((ROOT/'site/media/demo-v3.mp4').read_bytes()).hexdigest()==film_check['sha256']
state={'status':'publishing','files':files};save(state)
run(['git','add','--',*files])
staged=value(['git','diff','--cached','--name-only']).splitlines();assert set(staged)<=set(files),staged
if staged:run(['git','commit','-m','Show actual simulation footage throughout the public demo'])
state['main']=value(['git','rev-parse','HEAD']);save(state);run(['git','push','origin','main']);assert value(['git','ls-remote','origin','refs/heads/main']).split()[0]==state['main']
assert not value(['git','status','--short','--untracked-files=no'],PAGES)
run(['git','pull','--ff-only','origin','gh-pages'],PAGES)
copied=[]
for f in site+docs:
 target=PAGES/f.removeprefix('site/');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f,target);copied.append(str(target.relative_to(PAGES)))
run(['git','add','--',*copied],PAGES)
if value(['git','diff','--cached','--name-only'],PAGES):run(['git','commit','-m','Publish footage-first BeforeStep showcase'],PAGES)
state['pages']=value(['git','rev-parse','HEAD'],PAGES);save(state);run(['git','push','origin','HEAD:gh-pages'],PAGES)
assert value(['git','ls-remote','origin','refs/heads/gh-pages']).split()[0]==state['pages']
state['status']='waiting_build';save(state)
for _ in range(80):
 build=json.loads(value(['gh','api','repos/codezzzsleep/next-zenith-beforestep/pages/builds/latest']))
 if build.get('commit')==state['pages'] and build.get('status')=='built':state['build']=build;break
 if build.get('commit')==state['pages'] and build.get('status')=='errored':raise RuntimeError(build)
 time.sleep(10)
else:raise RuntimeError('Pages build still pending; resume verification, do not republish')
state['status']='built';state['public_files']=copied;save(state);print('PUBLISHED AND BUILT',state['main'],state['pages'],flush=True)
