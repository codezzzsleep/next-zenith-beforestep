"""Publish complete verified arena artifacts using the already authorized branches."""
import argparse
import concurrent.futures
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/learning/arena_v2'
PAGES=Path('/tmp/beforestep-pages-r3-P0-worktree')
EXPORT=Path('/tmp/beforestep-pages-r3-P0-export')
PUBLIC='https://codezzzsleep.github.io/next-zenith-beforestep/'
PRIVATE=Path('/root/3d/.memory/live/arena-publication')


def call(command,cwd=ROOT):subprocess.run(command,cwd=cwd,check=True)
def output(command,cwd=ROOT):return subprocess.check_output(command,cwd=cwd,text=True).strip()
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checkpoint(event):
    p=PRIVATE/'state.json';PRIVATE.mkdir(parents=True,exist_ok=True)
    previous=json.loads(p.read_text()) if p.exists() else {}
    previous.update(event=event,updated_at_unix=time.time());p.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n')
    with Path('/root/3d/MEMORY.md').open('a') as f:f.write(f'\n- Arena publication checkpoint: {event}; private ledger {p}.\n')


def verify_one(path):
    relative=str(path.relative_to(EXPORT));expected=digest(path);h=hashlib.sha256();size=0
    request=urllib.request.Request(PUBLIC+relative,headers={'Accept-Encoding':'identity','Cache-Control':'no-cache'})
    with urllib.request.urlopen(request,timeout=120) as response:
        assert response.status==200,relative
        while block:=response.read(1024*1024):h.update(block);size+=len(block)
    assert size==path.stat().st_size and h.hexdigest()==expected,relative
    return {'path':relative,'bytes':size,'sha256':expected,'verified_http_bytes':True}


def wait_pages(pages):
    deadline=time.monotonic()+1800
    while time.monotonic()<deadline:
        build=json.loads(output(['gh','api','repos/codezzzsleep/next-zenith-beforestep/pages/builds/latest']))
        if build.get('commit')==pages and build.get('status')=='built':return build
        if build.get('commit')==pages and build.get('status')=='errored':raise RuntimeError(build.get('error'))
        time.sleep(20)
    raise RuntimeError('Pages build did not reach built state within 30 minutes')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    PRIVATE.mkdir(parents=True,exist_ok=True)
    # Build only after all experiment identities are terminal. This preserves
    # heldout records and does not launch or rerun experiments.
    call([sys.executable,str(ROOT/'ops/build_arena_delivery.py')])
    sys.path.insert(0,str(ROOT/'ops'))
    from check_arena_integrity import BANNER
    nav=ROOT/'site/navigation.html';text=nav.read_text()
    if BANNER not in text:nav.write_text(text.replace('<main>\n','<main>\n'+BANNER,1))
    readme=ROOT/'README.md';text=readme.read_text()
    if '<!-- ARENA-V2-START -->' not in text:
        text+='''\n<!-- ARENA-V2-START -->
## 随机月面竞技场与未知占据学习

[首次封存结果与失败](docs/arena.md) · [竞技场回放](site/arena.html) · [运行前预注册](docs/arena-protocol.md)。
模型预测看不见的格子的占据概率，数值代码找路；RGB-D只有停看时更新，途中不观测。
真实Lux结果按原视角整体移植，新增Lux付费0，石头种类没有单独留出。

```bash
git lfs pull --include="assets/runtime-*.tar.gz,assets/candidates/**" --exclude=""
./setup.sh
.venv/bin/python -m pip install -r requirements-arena.txt
.venv/bin/python -m experimental.arena.cli run --seed 9200000 --method learned --out outputs/arena-new-9200000
```

输出逐场结果与trajectory.png。这是正式RGB-D观测下的几何执行代理，物理验证另列。
完整329份原GLB均以原字节保留；构建胶囊前可用ops/restore_arena_inputs.py恢复runtime-arena-capsule-metadata.tar.gz。
真实6场复现先运行.venv/bin/python ops/restore_arena_inputs.py恢复首眼输入，再用experimental.arena.cli real。
<!-- ARENA-V2-END -->
'''
        readme.write_text(text)
    summary_text=(OUT/'final-answer.md').read_text()
    record=ROOT/'docs/reviews/RESULT_ARENA_LEARNING.md';old=record.read_text()
    if '<!-- ARENA-FINAL-SUMMARY -->' not in old:
        record.write_text('# Arena v2 最终结果\n\n<!-- ARENA-FINAL-SUMMARY -->\n'+summary_text+'\n\n<!-- ARENA-EXECUTION-RECORD -->\n'+old)
    elif '<!-- ARENA-EXECUTION-RECORD -->' in old:
        history=old.split('<!-- ARENA-EXECUTION-RECORD -->',1)[1]
        record.write_text('# Arena v2 最终结果\n\n<!-- ARENA-FINAL-SUMMARY -->\n'+summary_text+'\n\n<!-- ARENA-EXECUTION-RECORD -->'+history)
    checkpoint('Result-derived report and replay built; running actual desktop/mobile and frozen-integrity checks')
    call([sys.executable,str(ROOT/'ops/check_arena_page.py'),'--out',str(OUT/'acceptance/local')])
    call([sys.executable,str(ROOT/'ops/check_arena_integrity.py'),'--out',str(OUT/'acceptance/integrity-before-publication.json')])
    custody=[]
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and path.name!='custody.json':custody.append({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':digest(path)})
    (OUT/'custody.json').write_text(json.dumps({'files':custody,'count':len(custody),'bytes':sum(r['bytes'] for r in custody)},indent=2)+'\n')
    call(['git','add','README.md','.gitattributes','docs/arena.md','docs/reviews/RESULT_ARENA_LEARNING.md','site/arena.html','site/arena.css','site/arena.js','site/navigation.html','site/data/arena.json','site/data/arena','site/media/arena','assets/models/arena_v2','evidence/learning/arena_v2','ops'])
    if output(['git','diff','--cached','--name-only']):call(['git','commit','-m','Deliver paired sparse-observation arena learning, original Lux inputs and full failures'])
    source=output(['git','rev-parse','HEAD']);call(['git','push','origin','main'])
    assert output(['git','ls-remote','origin','refs/heads/main']).split()[0]==source
    checkpoint('Main source/results pushed '+source)
    call([sys.executable,str(ROOT/'ops/export_site.py'),'--skip-builders','--out',str(EXPORT)])
    shutil.copytree(EXPORT,PAGES,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git'))
    call(['git','add','-A'],PAGES)
    if output(['git','diff','--cached','--name-only'],PAGES):call(['git','commit','-m','Publish complete arena benchmark and replay'],PAGES)
    pages=output(['git','rev-parse','HEAD'],PAGES);call(['git','push','origin','HEAD:gh-pages'],PAGES)
    checkpoint('Pages commit pushed '+pages)
    build=wait_pages(pages)
    candidates=[]
    for directory in ['data/arena','media/arena','evidence/learning/arena_v2','assets/models/arena_v2']:
        candidates.extend(p for p in (EXPORT/directory).rglob('*') if p.is_file())
    for relative in ['arena.html','arena.css','arena.js','data/arena.json','navigation.html','index.html','media/report.pdf','docs/arena.md','docs/arena-protocol.md']:
        candidates.append(EXPORT/relative)
    verified=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for item in pool.map(verify_one,sorted(set(candidates))):verified.append(item)
    for row in json.loads((EXPORT/'evidence/learning/arena_v2/public-compressed.json').read_text()) if (EXPORT/'evidence/learning/arena_v2/public-compressed.json').exists() else []:
        decoded=gzip.decompress((EXPORT/row['public']).read_bytes());assert hashlib.sha256(decoded).hexdigest()==row['sha256']
    call([sys.executable,str(ROOT/'ops/check_arena_page.py'),'--base',PUBLIC,'--out',str(PRIVATE/'browser')])
    # A follow-up documentation commit records the commits actually tested.
    # It changes no experiment or replay bytes and avoids self-referential SHAs.
    publication_note=f'''<!-- ARENA-PUBLICATION-START -->
## 发布核验

内容提交：`{source}`；首次完整公网核验的Pages提交：`{pages}`。
页面：{PUBLIC}arena.html。
本地与公网1440/390交互、冻结完整性与{len(verified)}份公开文件共{sum(r['bytes'] for r in verified)}字节均已实际通过。
验证命令见开头第7项；本节是完成实际核验后的补充记录，未重新运行封存/OOD/LLM或修改原实验记录。
<!-- ARENA-PUBLICATION-END -->
'''
    text=record.read_text()
    if '<!-- ARENA-PUBLICATION-START -->' in text:
        start=text.index('<!-- ARENA-PUBLICATION-START -->');end=text.index('<!-- ARENA-PUBLICATION-END -->',start)+len('<!-- ARENA-PUBLICATION-END -->')
        text=text[:start]+publication_note+text[end:].lstrip('\n')
    else:text+='\n'+publication_note
    record.write_text(text)
    call(['git','add','docs/reviews/RESULT_ARENA_LEARNING.md'])
    if output(['git','diff','--cached','--name-only']):call(['git','commit','-m','Record actual Arena publication commits and public verification'])
    source_record=output(['git','rev-parse','HEAD']);call(['git','push','origin','main'])
    assert output(['git','ls-remote','origin','refs/heads/main']).split()[0]==source_record
    relative='docs/reviews/RESULT_ARENA_LEARNING.md'
    shutil.copy2(record,EXPORT/relative);shutil.copy2(record,PAGES/relative)
    call(['git','add',relative],PAGES)
    if output(['git','diff','--cached','--name-only'],PAGES):call(['git','commit','-m','Record verified Arena publication on Pages'],PAGES)
    pages_record=output(['git','rev-parse','HEAD'],PAGES);call(['git','push','origin','HEAD:gh-pages'],PAGES)
    record_build=wait_pages(pages_record);verified.append(verify_one(EXPORT/relative))
    proof={'passed':True,'main':source,'pages':pages,'url':PUBLIC+'arena.html','files':verified,'verified_files':len(verified),'verified_bytes':sum(r['bytes'] for r in verified),'pages_build':build,'browser':json.loads((PRIVATE/'browser/result.json').read_text())}
    proof.update(publication_record_main=source_record,publication_record_pages=pages_record,publication_record_build=record_build)
    (PRIVATE/'final.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
    checkpoint('Full main/Pages delivery verified; final proof '+str(PRIVATE/'final.json'))
    print(json.dumps({k:proof[k] for k in ['passed','main','pages','url','verified_files','verified_bytes']},ensure_ascii=False))


if __name__=='__main__':main()
