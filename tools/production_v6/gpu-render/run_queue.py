"""Run an explicitly named saved-state GPU queue without physics."""
import argparse,datetime,json,os,subprocess,fcntl
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--id',required=True);parser.add_argument('--shots',required=True);args=parser.parse_args()
code_directory=Path(__file__).resolve().parent
import sys
sys.path.insert(0,str(code_directory.parent))
from common import OUT
directory=OUT/'gpu-render'
directory.mkdir(parents=True,exist_ok=True);shots=OUT/'shots';shots.mkdir(parents=True,exist_ok=True);queue=args.shots.split(',');ledger=directory/(args.id+'-job.json')
def save(data):
    tmp=ledger.with_suffix('.json.tmp')
    with tmp.open('w') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    tmp.replace(ledger)
job={'id':args.id,'pid':os.getpid(),'status':'running','queue':queue,'completed':[],'current':None,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'physics_runs':0,'generation_tasks':0};save(job)
env=dict(os.environ,MUJOCO_GL='egl',OPENBLAS_NUM_THREADS='1')
for name in queue:
    lock=(directory/'.render-queue.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
    with (shots/(name+'-render.log')).open('w') as log:
        process=subprocess.Popen([sys.executable,str(code_directory/'render_shot.py'),'--shot',name],env=env,stdout=log,stderr=log)
        job['current']={'id':name,'pid':process.pid,'log':str(shots/(name+'-render.log')),'ledger':str(shots/(name+'.json'))};save(job);rc=process.wait()
    if rc:job.update(status='failed',returncode=rc);save(job);raise SystemExit(rc)
    row=json.loads((shots/(name+'.json')).read_text());assert row['status']=='complete'
    job['completed'].append({'id':name,'sha256':row['sha256'],'bytes':row['bytes'],'seconds_per_frame':row['total_seconds_per_frame']});job['current']=None;save(job)
    print(name,'complete',flush=True);lock.close()
job.update(status='complete',finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save(job)
