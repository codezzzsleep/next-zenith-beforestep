from pathlib import Path
import datetime,hashlib,json,os
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.environ.get('BEFORESTEP_LUX_DEMO_V2_DIR',ROOT/'evidence/lux3d-demo-v2')).resolve()
BASE=ROOT/'evidence/lux3d-demo'
def sha(p):
 p=Path(p);p=p if p.is_absolute() else ROOT/p
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp')
 with t.open('w') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 t.replace(p)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
