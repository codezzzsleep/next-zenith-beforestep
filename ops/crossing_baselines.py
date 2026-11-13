"""Run both zero-paid wheel-only capability matrices, preserving terminal trials."""
import sys,os,json,time,argparse,shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'ops'))
from crossing_calibrate import run_fixed
from experimental.crossing.runtime import OUT,write,sha
HEIGHTS=[.04,.06,.08,.10,.12,.15,.18,.22];DEPTHS=[.10,.20,.30,.40];ANGLES=[0,-5,5]

def one(args):
    h,d,a,m,attempt,seconds=args
    folder=OUT/'calibration'/attempt/f'{m}-h{h:.3f}-d{d:.3f}-a{a:+.1f}'
    return run_fixed(h,d,a,m,folder,seconds)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',default='baseline-v1');ap.add_argument('--seconds',type=float,default=40.);options=ap.parse_args();attempt=options.attempt
    ledger=OUT/'jobs.json';jobs=json.loads(ledger.read_text()) if ledger.exists() else {'schema':'beforestep-crossing-jobs/v1','jobs':{},'new_lux_tasks':0}
    name='baselines' if attempt=='baseline-v1' else attempt
    previous=jobs['jobs'].get(name,{})
    jobs['jobs'][name]={'attempts':previous.get('attempts',[])+[{k:v for k,v in previous.items() if k!='attempts'}] if previous else [],'status':'running','pid':os.getpid(),'output':str((OUT/'calibration'/attempt).relative_to(ROOT)),'trials':192,'workers':2,'source_sha256':{p:sha(ROOT/p) for p in ['ops/crossing_calibrate.py','ops/crossing_baselines.py','experimental/crossing/runtime.py']}}
    write(ledger,jobs)
    source=OUT/'calibration'/attempt/'source';source.mkdir(parents=True,exist_ok=True)
    for file in jobs['jobs'][name]['source_sha256']:
        target=source/Path(file).name
        if not target.exists():shutil.copy2(ROOT/file,target)
    rows=[];ts=time.monotonic()
    with ProcessPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(one,(h,d,a,m,attempt,options.seconds)) for h in HEIGHTS for d in DEPTHS for a in ANGLES for m in ['fixed','high']]
        for f in as_completed(futures):
            rows.append(f.result())
            if len(rows)%12==0:print(json.dumps({'completed':len(rows),'total':192,'wall_seconds':time.monotonic()-ts}),flush=True)
    write(OUT/'calibration'/attempt/'summary.json',{'trials':192,'results':rows})
    jobs=json.loads(ledger.read_text());jobs['jobs'][name].update(status='complete',wall_seconds=time.monotonic()-ts);write(ledger,jobs)
    print('baselines complete',flush=True)
