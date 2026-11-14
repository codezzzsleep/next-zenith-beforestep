from pathlib import Path
import datetime,hashlib,json,os
ROOT=Path(os.environ.get('BEFORESTEP_ROOT',str(Path(__file__).resolve().parents[2]))).resolve()
OUT=Path(os.environ.get('BEFORESTEP_PRODUCTION_OUT',str(ROOT/'evidence/production-v6'))).resolve()
TOOLS=ROOT/'tools/production_v6'
def resolve(p):
 p=str(p)
 for prefix,target in [('/root/3d/final-v6/',OUT),('/root/render-v6/final-v6/',OUT),('/root/3d/next-zenith-beforestep/',ROOT),('/root/render-v6/next-zenith-beforestep/',ROOT)]:
  if p.startswith(prefix):return target/p.removeprefix(prefix)
 q=Path(p);return q if q.is_absolute() else ROOT/q
def sha(p):return hashlib.sha256(resolve(p).read_bytes()).hexdigest()
def save(p,d):
 p=resolve(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp')
 with t.open('w') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 t.replace(p)
def status(task,path,result):
 OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/'STATUS.md').open('a') as f:f.write(f'- {datetime.datetime.now(datetime.timezone.utc).isoformat()} | {task} | {path} | {result}\n')

def load_state(p):
 p=resolve(p)
 return json.loads(p.read_text()) if p.exists() else {'status':'new_local_run','live_jobs':[]}
