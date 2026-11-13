"""Publish each completed Addendum 2 block and validate its public page."""
import argparse,fcntl,hashlib,json,shutil,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PAGES=Path('/tmp/beforestep-pages-r3-P0-worktree')
PRIVATE=Path('/root/3d/.memory/live/route-publication')
PUBLIC='https://codezzzsleep.github.io/next-zenith-beforestep/'

def run(args,cwd=ROOT):subprocess.run(args,cwd=cwd,check=True)
def value(args,cwd=ROOT):return subprocess.check_output(args,cwd=cwd,text=True).strip()
def save(state):
    PRIVATE.mkdir(parents=True,exist_ok=True)
    (PRIVATE/(state['stage']+'.json')).write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--stage',required=True);ap.add_argument('--message',required=True);ap.add_argument('--skip-page-check',action='store_true');ap.add_argument('--homepage',action='store_true');ap.add_argument('--video',action='store_true');ap.add_argument('--pdf',action='store_true');a=ap.parse_args()
    PRIVATE.mkdir(parents=True,exist_ok=True)
    publication_lock=(PRIVATE/'publication.lock').open('a');fcntl.flock(publication_lock,fcntl.LOCK_EX)
    state={'stage':a.stage,'status':'running'};save(state)
    paths=['experimental/crossing/route',*[str(p.relative_to(ROOT)) for p in ROOT.glob('ops/crossing_route_*.py')],
        'README.md','docs/story.md','docs/history/README-before-addendum2.md','docs/crossing.md','docs/report.md','docs/reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM2.md',
        'docs/reviews/RESULT_WHEELLEG_CROSSING.md','evidence/crossing','site/crossing.html','site/crossing.js','site/crossing.css']
    paths+=['docs/reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM3.md','docs/video.md','site/report.html','docs/hackathon-submission.md','docs/history/hackathon-submission-before-addendum3.md']
    if a.homepage:paths+=['site/index.html','site/home.css','site/home.js','site/home-assets','site/homepage-integration.json']
    if a.video:paths+=['site/media/demo-v2.mp4','site/media/demo-v2-cover.jpg']
    if a.pdf:paths+=['site/media/report.pdf','site/media/history/addendum2']
    budget=json.loads((ROOT/'outputs/generation/crossing-budget.json').read_text())
    paths += ['assets/candidates/'+str(r['task_id']) for r in budget['tasks'] if r.get('task_id') and r['status']=='ok']
    run(['git','diff','--check']);run(['git','add',*paths])
    if value(['git','diff','--cached','--name-only']):run(['git','commit','-m',a.message])
    state['main']=value(['git','rev-parse','HEAD']);save(state)
    run(['git','push','origin','main'])
    assert value(['git','ls-remote','origin','refs/heads/main']).split()[0]==state['main']
    state['main_verified']=True;save(state)
    copied=[]
    extra=['docs/reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM3.md','docs/video.md','site/report.html','docs/hackathon-submission.md']
    if a.homepage:
        extra+=['site/index.html','site/home.css','site/home.js','site/homepage-integration.json']
        extra+=[str(p.relative_to(ROOT)) for p in (ROOT/'site/home-assets').rglob('*') if p.is_file()]
    if a.video:extra+=['site/media/demo-v2.mp4','site/media/demo-v2-cover.jpg']
    if a.pdf:extra+=['site/media/report.pdf']+[str(p.relative_to(ROOT)) for p in (ROOT/'site/media/history/addendum2').rglob('*') if p.is_file()]
    for relative in extra:
        destination=relative.removeprefix('site/');target=PAGES/destination;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,target);copied.append(destination)
    for relative in ['site/crossing.html','site/crossing.css','site/crossing.js','README.md','docs/history/README-before-addendum2.md','docs/report.md','docs/story.md','docs/crossing.md',
        'docs/reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM2.md','docs/reviews/RESULT_WHEELLEG_CROSSING.md']:
        destination=relative.removeprefix('site/');target=PAGES/destination;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,target);copied.append(destination)
    for source in (ROOT/'evidence/crossing/route').rglob('*'):
        if not source.is_file() or source.name.endswith('.tar.gz'):continue
        relative=str(source.relative_to(ROOT));target=PAGES/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);copied.append(relative)
    for relative in ['evidence/crossing/development-lux-scene-dev-v9-22005.json','evidence/crossing/development/narrow-generator-index.json','evidence/crossing/development/addendum2-threshold-closure-manifest.json']:
        target=PAGES/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,target);copied.append(relative)
    run(['git','add',*copied],PAGES)
    if value(['git','diff','--cached','--name-only'],PAGES):run(['git','commit','-m',a.message],PAGES)
    state['pages']=value(['git','rev-parse','HEAD'],PAGES);save(state)
    run(['git','push','origin','HEAD:gh-pages'],PAGES)
    assert value(['git','ls-remote','origin','refs/heads/gh-pages']).split()[0]==state['pages']
    state['pages_verified']=True;save(state)
    started=time.monotonic()
    while time.monotonic()-started<1200:
        build=json.loads(value(['gh','api','repos/codezzzsleep/next-zenith-beforestep/pages/builds/latest']))
        if build.get('commit')==state['pages'] and build.get('status')=='built':state['build']=build;break
        if build.get('commit')==state['pages'] and build.get('status')=='errored':raise RuntimeError(build.get('error'))
        time.sleep(15)
    else:raise RuntimeError('Build pending; resume read-only verification without republishing')
    if not a.skip_page_check:
        checker='ops/crossing_route_homepage.py' if a.homepage else 'ops/crossing_route_check.py'
        run([sys.executable,checker,'--url',PUBLIC,'--out',str(PRIVATE/(a.stage+'-public'))])
    verified=[]
    for relative in ['crossing.html','crossing.js','crossing.css','docs/story.md','docs/crossing.md','docs/video.md','docs/reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM3.md','evidence/crossing/route/summary.json','evidence/crossing/route/low-stone.json','evidence/crossing/route/threshold-closure.json']+(['index.html','home.css','home.js','homepage-integration.json'] if a.homepage else []):
        with urllib.request.urlopen(PUBLIC+relative,timeout=90) as response:raw=response.read()
        assert raw==(PAGES/relative).read_bytes(),relative
        verified.append({'path':relative,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
    state.update(status='complete',verified=verified);save(state)
    with Path('/root/3d/MEMORY.md').open('a') as f:f.write(f'\n补充2发布终态：{a.stage}，main {state["main"]}，Pages {state["pages"]}，远端HEAD/公网原字节相等；浏览器检查见.memory/live/route-publication。\n')
    print(json.dumps(state,ensure_ascii=False),flush=True)
